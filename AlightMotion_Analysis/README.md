# Phân tích cách Alight Motion hoạt động

## Phạm vi

Báo cáo này được dựng bằng phân tích tĩnh các tệp trong
`extracted/Payload/AlightMotion.app`. Không có mã nguồn ứng dụng và chưa chạy
dynamic instrumentation trên thiết bị, vì vậy các quan hệ bên dưới là quan hệ
suy ra từ metadata Mach-O, tên kiểu, selector Objective-C, resource bundle và
chuỗi nhúng trong executable.

Phiên bản được phân tích:

- Bundle ID: `com.alightcreative.motion`
- Phiên bản: `6.2.53` (`859`)
- Executable: `AlightMotion`
- Kiến trúc: ARM64
- iOS tối thiểu: 14.4

## Sơ đồ tổng thể

```text
Khởi động ứng dụng
    |
    +-- AppSetup / RemoteConfig / consent
    |
    +-- Firebase Auth -------------------- tài khoản người dùng
    |
    +-- Persistence ---------------------- project cục bộ
    |       |
    |       +-- ProjectHolder / Timeline / Layer / Effect
    |       +-- audio, image, video, text, shape, camera
    |       +-- preview và render
    |
    +-- Firestore / CloudProjectClient --- backup và đồng bộ cloud
    |
    +-- Monetization / Oracle
    |       |
    |       +-- StoreKit product
    |       +-- receipt và restore
    |       +-- license/benefit
    |       +-- entitlement và paywall
    |
    +-- Exporter ------------------------- video/GIF/WebP/XML/package
    |
    +-- AppLovin / attribution ----------- quảng cáo
    |
    +-- Analytics / Crashlytics ---------- telemetry và crash report
```

## 1. Khởi động và cấu hình

Ứng dụng chứa các module `AlightMotion_AppSetup`, `FirebaseRemoteConfig`,
`FirebaseInstallations`, `FirebaseMessaging` và `AlightMotion_LoadingScreen`.
Luồng khởi động hợp lý được suy ra như sau:

1. UIKit tải executable `AlightMotion` và các framework khai báo trong Mach-O.
2. AppSetup dựng dependency graph và trạng thái ứng dụng.
3. Firebase tạo installation identity, tải Remote Config và thiết lập messaging.
4. Tracking consent/IDFA được kiểm tra trước khi khởi tạo quảng cáo cá nhân hóa.
5. Persistence tải project và thiết lập màn hình Home/Project Selector.
6. Monetization khôi phục trạng thái thuê bao và benefit.

`Info.plist` cho phép arbitrary network loads (`NSAllowsArbitraryLoads = YES`).
Ứng dụng yêu cầu quyền camera, thư viện ảnh và Apple Music để nhập/xuất media.

## 2. Tài khoản

Các thành phần quan sát được:

- Firebase Auth và FirebaseUI.
- Google Sign-In.
- Email/password và email-link sign-in.
- MFA-related Firebase request types.
- `UserProfile`, `SignInStatusClient` và luồng xóa tài khoản.

Sau khi đăng nhập, Firebase identity có thể được dùng bởi Firestore, cloud
backup, template sharing và entitlement đồng bộ phía server.

## 3. Editor và project

Executable chứa các nhóm kiểu chính:

- `ProjectHolder`, `ProjectPlayer`, `ProjectContext`.
- Timeline, playhead, editing history và layer parenting.
- Effect browser, effect presets, effect renderer và shader.
- Text, shape, media, audio, camera và vector drawing.
- Preview controller và render pipeline.

Project được giữ trong lớp persistence cục bộ. Editor biến thao tác UI thành
thay đổi trên scene/layer/effect model; preview đọc cùng model để render khung
hình. Các effect có thể sử dụng `default.metallib`, shader/effect scripts và
resource trong `BuiltinEffects`, `BuiltinShapes`, `BuiltinPresets`.

## 4. Import và export

Import lấy dữ liệu từ Photos, Camera, Apple Music hoặc file picker. Các lớp
thumbnail/waveform tạo dữ liệu xem trước cho timeline.

Các định dạng export quan sát được:

- Video
- GIF
- WebP
- Image sequence
- Project package
- XML

`Exporter` nhận model project và `ExportParams`, render theo thời gian, mã hóa
kết quả rồi chuyển sang màn hình share/save. Trước export, ứng dụng kiểm tra
premium effects, giới hạn độ phân giải và watermark; nếu thiếu entitlement,
paywall hoặc downgrade flow được hiển thị.

## 5. StoreKit, subscription và entitlement

Chuỗi/type trong executable cho thấy pipeline gồm:

```text
ProductFetcher
    -> StoreKit product
    -> Purchase / Restore
    -> App Store receipt
    -> ReceiptClient / Oracle
    -> LicenseStore
    -> EntitlementsRefresher
    -> Benefit/feature state
    -> UI, export và paywall đọc state
```

Các lớp quan trọng:

- `IAPManager`
- `IAPTaskGetProductInfo`, `IAPTaskGetProductList`, `IAPTaskVerifyReceipt`
- `StoreReceiptRefresher`
- `ReceiptClient`, `ReceiptClientV2`
- `PurchaseRestoreClient`, `PurchaseRestoreClientV2`
- `OracleSubscription`
- `LicenseStore`, `ProductLicense`, `LicenseBenefit`
- `EntitlementsRefresher`
- `ActiveSubscription`, `PastSubscription`, `ThirdPartySubscription`

Product ID xuất hiện trong bản phân tích:

`alightcreative.motion.1y_t60_1w`

Trạng thái Premium không chỉ là một boolean. UI và export còn dựa vào tập
benefit/license, nguồn subscription, thời hạn, receipt verification và dữ liệu
Oracle. Vì vậy chỉ thay một getter có thể làm UI báo Premium nhưng các luồng
export/cloud vẫn từ chối hoặc rơi vào trạng thái không nhất quán.

## 6. Cloud và backend

Ứng dụng có Firebase Firestore, gRPC và các lớp:

- `CloudProjectClient`
- `CloudBackup`
- `StorageUploadTask`, `StorageDownloadTask`
- `PreparePackageUploadRequest`
- `RequestProjectDownloadRequest`
- quota và cloud benefit types

Endpoint/hostname thấy trực tiếp trong executable:

- `alightmotion.oracle.bendingspoonsapps.com`
- `oracle.bendingspoonsapps.com`
- `bendingspoonsapps.com/v4/events`
- attribution endpoint: `https://tracking-bndspn.com`

Oracle có vẻ phụ trách monetization/subscription phía backend; endpoint
`v4/events` thuộc pipeline sự kiện/analytics. Đây là suy luận theo tên và chuỗi,
chưa phải capture lưu lượng thực tế.

## 7. Quảng cáo và analytics

Framework quảng cáo chính:

- AppLovin SDK
- AppLovin Quality Service
- IDFA/transparency manager
- attribution framework

Telemetry gồm Firebase Analytics, Crashlytics, Remote Config, Google Data
Transport và các module analytics nội bộ. `NSUserTrackingUsageDescription`
nêu rõ dữ liệu được dùng cho quảng cáo cá nhân hóa.

## 8. Phần mod đang có trong Payload

Executable hiện chứa load command:

`@rpath/AlightMotionCrack.dylib`

Dylib dùng Objective-C runtime (`class_getInstanceMethod`,
`method_setImplementation`) để can thiệp các selector/type liên quan tới:

- `isSubscribed`
- `isPremium`
- `unlockedPremiumUser`
- `hasActiveSubscription`
- `isProUser`
- `getAccountStatusAndLicenses`

Dylib còn dựng dữ liệu benefit như remove watermark, member effects, remove ads,
advanced easing và project package sharing. Đây không phải thành phần gốc của
ứng dụng và có thể tạo state không nhất quán với StoreKit/backend.

## 9. Nguyên nhân crash có thể gặp

Các nhóm nguyên nhân nổi bật trong workspace:

1. Patch hàng loạt mọi lệnh ARM64 có cùng field offset; cách này sửa nhầm code
   không thuộc `IAPManager`.
2. Patch trực tiếp và runtime hook cùng lúc, làm state hoặc implementation bị
   thay hai lần.
3. Dylib hook selector không tồn tại hoặc ABI/signature không đúng phiên bản.
4. Dylib làm hỏng callee-saved registers trong replacement IMP.
5. Chữ ký không bao phủ executable/framework đã sửa.
6. Receipt test certificate được dùng trong build không chạy dưới Xcode StoreKit
   Test.

Muốn xác định chính xác một crash cần `.ips` hoặc crash log gồm Exception Type,
Termination Reason và backtrace của crashed thread.

## 10. Tệp liên quan

- `evidence.json`: metadata và bằng chứng tóm tắt dạng máy đọc.
- `../StoreKitTest/`: cấu hình StoreKit Test hợp lệ cho môi trường phát triển.
- `../extracted/Payload/AlightMotion.app/Info.plist`: metadata ứng dụng.
- `../extracted/Payload/AlightMotion.app/AlightMotion`: executable ARM64.
- `../extracted/Payload/AlightMotion.app/Frameworks/AlightMotionCrack.dylib`:
  thư viện can thiệp được nhúng trong Payload hiện tại.
