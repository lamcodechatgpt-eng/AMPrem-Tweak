# Các phát hiện hữu ích bổ sung

## 1. Kiến trúc source bị lộ qua đường dẫn build

Executable giữ lại nhiều đường dẫn Swift source từ máy CI:

`/Users/distiller/project/...`

Điều này cho phép dựng lại cấu trúc module ở mức cao:

- `Alight Motion/IAP/IAPManager.swift`: IAP legacy của ứng dụng.
- `Features/Monetization`: UI và state monetization của AM.
- `ios-libs-monorepo/Monetization`: lớp StoreKit 1/2 dùng chung.
- `ios-libs-monorepo/Oracle`: backend account/license và state manager.
- `Features/Configuration`: app config, Remote Config và subscription IDs.
- `Alight Motion BSP`: dependency composition, reducer và module integration.
- `Features/Homepage`: project/template/tutorial/home state.
- `Persistence` và `PersistenceSCA`: lưu project và feature state.
- `Pico/PicoX/Wolf/SpiderSense`: analytics/context/event pipeline nội bộ.

Ứng dụng dùng Swift Composable Architecture ở nhiều feature mới. Các feature cũ
vẫn dùng UIKit/storyboard, vì vậy binary là kiến trúc lai legacy + reducer/state
management mới.

## 2. Có hai pipeline monetization

Bằng chứng source path và symbol cho thấy hai thế hệ chạy song song:

1. `Alight Motion/IAP/IAPManager.swift`: StoreKit legacy và các flag
   `isFreeUser`, `isPremiumUser`, `experiments`.
2. `ios-libs-monorepo/Monetization`: StoreKit 2, transaction updates,
   `EntitlementsRefresher`, `ReceiptClientV2` và state storage mới.

Khóa cấu hình `fallback_on_bspmonetization` cho thấy ứng dụng có cơ chế chuyển
hoặc fallback giữa IAP legacy và BSP Monetization. Đây là lý do một patch chỉ
tác động `IAPManager` có thể không thay đổi luồng paywall/export mới.

## 3. Product ID được dựng từ cấu hình

Executable gốc chỉ giữ ba prefix:

```text
alightcreative.motion.1w_
alightcreative.motion.1m_
alightcreative.motion.1y_
```

Các prefix nằm gần chuỗi `subscription_ids`, `fallback_on_bspmonetization` và
`AppConfiguration+Dependencies.swift`. Phần suffix nhiều khả năng đến từ app
configuration/Remote Config, không hard-code cố định trong executable.

`alightcreative.motion.1y_t60_1w` chỉ có trong dylib được chèn. Điều này giải
thích vì sao ép StoreKit dùng ID đó có thể trả `21008 invalidIdentifiers`.

## 4. Dependency Mach-O đáng chú ý

Executable nạp trực tiếp hoặc weak-link:

- StoreKit, PassKit và AuthenticationServices.
- Metal, MetalKit, MetalPerformanceShaders và CoreImage.
- AVFoundation, AVKit, MediaToolbox và Photos.
- CoreML; app còn chứa model onboarding đã compile.
- Firebase/Firestore/gRPC được link tĩnh hoặc nhúng qua app binary/resources.
- AppLovin SDK và AppLovin Quality Service.
- MetricKit, DeviceCheck, CryptoKit, Security và LocalAuthentication.
- MarketplaceKit và AdAttributionKit được weak-link để tương thích theo phiên
  bản iOS/khu vực.

RPATH chính là `/usr/lib/swift` và `@executable_path/Frameworks`. Load command
`@rpath/AlightMotionCrack.dylib` là thay đổi không thuộc bộ framework thương mại
gốc.

## 5. Privacy manifests

Có 37 tệp `.xcprivacy`. Tổng hợp khai báo Required Reason API:

| API category | Reason codes | Số manifest |
|---|---|---:|
| System boot time | `35F9.1` | 4 |
| UserDefaults | `1C8F.1`, `C56D.1`, `CA92.1` | 16 |
| File timestamp | `C617.1` | 7 |

Các loại dữ liệu được khai báo bởi dependency manifests gồm diagnostic data,
user ID, crash data, device ID và other data types. Không manifest nào trong
bundle khai báo `NSPrivacyTrackingDomains`, nhưng `Info.plist` vẫn có tracking
usage description và attribution endpoint. Vì vậy “không có tracking domains
trong manifest” không đồng nghĩa ứng dụng không có tracking/ads.

## 6. Kích thước và thành phần lớn

App giải nén có 3.517 tệp, tổng cộng 253.425.379 byte. Các thành phần lớn nhất:

- Hai executable `AlightMotion` và `AlightMotion_patched`: mỗi tệp 56.328.560
  byte. `_patched` là bản dư trong app bundle.
- `BuiltinEffects`: khoảng 37,7 MB.
- `AlightMotion_Monetization.bundle`: khoảng 24,8 MB.
- `Assets.car`: khoảng 15,6 MB.
- `Frameworks`: khoảng 12,6 MB.
- `AlightMotion_Popup.bundle`: khoảng 7 MB.
- `dist`: khoảng 6,6 MB, phù hợp với web content/runtime assets nhúng.

Không nên xóa `BuiltinEffects`, `Monetization.bundle`, `Assets.car` hoặc `dist`
chỉ để giảm dung lượng; chúng là resource chức năng. Các mục rõ ràng dư trong
Payload mod là `AlightMotion_patched`, marker `decrypt.day`, chữ ký cũ và
`SC_Info` khi gói sẽ được ký lại.

## 7. Dylib được chèn

`AlightMotionCrack.dylib` chỉ phụ thuộc vào Objective-C runtime, Foundation,
CoreFoundation, UIKit, StoreKit và libSystem. Nó không link trực tiếp Firebase,
Oracle hoặc thư viện networking riêng.

Điều này phù hợp với cơ chế:

- Runtime method replacement qua Objective-C.
- Tạo Foundation collection/JSON data.
- Dò URL/request hoặc StoreKit classes bằng selector động.

Nó không có khả năng tự triển khai đầy đủ backend Oracle; mọi response license
giả chỉ là dữ liệu client-side và có thể lệch schema/state của AM hiện tại.

## 8. Security và dấu hiệu repack

- Executable chính và `_patched` đều nạp dylib crack.
- Hai executable chỉ khác 8 byte; `_patched` có `mov w0,#1; ret` tại một getter.
- `AlightMotionCrack.dylib` và `_patched` không có entry trong CodeResources cũ.
- Payload còn `SC_Info`, nhưng executable đã bị thay load commands nên chữ ký và
  DRM metadata gốc không còn chứng minh tính toàn vẹn.
- `NSAllowsArbitraryLoads = YES` mở rộng phạm vi network transport được phép.
- Entitlements rời dùng `aps-environment=development`, cần phân biệt với
  entitlements thực tế trong signature sau khi ký lại.

## 9. Những dữ liệu nên dùng khi điều tra crash

Khi có crash log `.ips`, đối chiếu theo thứ tự:

1. `Termination Reason` và `Exception Type`.
2. `Binary Images` có `AlightMotionCrack.dylib` hay không.
3. Crashed thread nằm trong dyld, constructor/load, Objective-C runtime,
   StoreKit, Oracle hay render pipeline.
4. UUID/load address của binary có khớp đúng bản đã phân tích không.
5. Nếu là `Library not loaded`, kiểm tra RPATH và việc signer có ký dylib.
6. Nếu là `EXC_BAD_ACCESS`, kiểm tra replacement IMP, ABI và callee-saved
   registers.

## 10. Giới hạn của phân tích

Các báo cáo hiện tại là static analysis. Chúng xác nhận file, metadata, chuỗi,
dependency và cấu trúc Swift/Objective-C bị lộ; chúng chưa chứng minh thứ tự gọi
runtime, request body thật, response schema production hoặc class sở hữu mọi
selector. Các phần đó cần bản development chạy trên thiết bị/simulator và log có
symbolication.
