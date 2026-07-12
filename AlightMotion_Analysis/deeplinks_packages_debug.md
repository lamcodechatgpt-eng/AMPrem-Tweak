# Deep links, project packages và debug/secret menu

## URL schemes

`Info.plist` đăng ký:

```text
alightmotion://
com.alightcreative.motion://
fb1736402916450835://
com.googleusercontent.apps.414370328124-7sf6j4od5jsp4ggegbbjfaj1uutbpf8f://
com.googleusercontent.apps.1085723979695-cfcinsv182olfqnbt423lllvqdtck5be://
```

Hai Google callback scheme tương ứng production và staging Firebase projects.
Facebook scheme dùng cho login/callback. `alightmotion` là custom app route.

App chỉ allow-query các scheme ngoài:

```text
twitter, youtube, instagram, fb, googlegmail
```

## Universal links

Associated domains:

```text
alightcreativestaging.page.link
alightcreative.page.link
alight.link
alight.page.link
alightcreative.com
alightcreativestaging.com
```

App xử lý `NSUserActivityTypeBrowsingWeb` qua app/scene delegate. Binary có
`DeepLink`, `DeepLinkHandler`, `AppRoute`, Firebase deferred links và các flow mở
in-app universal link.

## Project package routing

Các dependency/action chính:

```text
HandleProjectPackageLink
OpenProjectPackage
ProjectPackageURLChecker
PackageImporter
ProjectPackager
ShareProjectPackageVC
```

`Info.plist` không khai báo `CFBundleDocumentTypes` hoặc UTType riêng. Vì vậy app
không công khai nhận một extension project qua document picker theo metadata;
project package chủ yếu đi qua link/share flow nội bộ.

## Cấu trúc package suy ra

Các dấu hiệu trong binary:

```text
projectfiles.zip
/projectfiles.zip
validateProjectPackageXML
amPackageVersion
maxFFVer
PackageCompatibility
PackageHEICTranscode
uploaded_package_sigs_to_urls
```

Luồng hợp lý:

1. `ProjectPackager` xuất XML metadata/project description.
2. Project files và media được gom thành `projectfiles.zip`.
3. Package metadata chứa version, feature-format max version (`maxFFVer`), tác
   giả/package ID và media references.
4. Share flow có thể upload metadata/archive và đăng ký package ID trên backend.
5. Link nhận được đi qua `ProjectPackageURLChecker`.
6. `PackageImporter` kiểm tra môi trường, compatibility và URL scheme của media.
7. Archive được giải nén, XML được validate rồi project/media được import.

Ứng dụng dùng cả `ZIPFoundation`, `SSZipArchive`, `AMZip` và gzip helpers.

## Validation và lỗi package

Các kiểm tra được xác nhận từ chuỗi:

- Staging/production mismatch.
- `maxFFVer` thiếu.
- Package không tương thích phiên bản AM.
- Metadata download error.
- Media URL có scheme không mong đợi.
- Thiếu media trong package.
- Package vượt kích thước cho phép.
- Video resolution quá cao cho thiết bị.
- Free-user maximum download size.
- Project package sharing benefit.

Do đó import package là một bề mặt crash riêng: XML sai, ZIP lỗi, duplicate file,
path/media URL bất thường hoặc feature version mới hơn app đều có thể gây lỗi.

## SecretMenu

Binary chứa nguyên một framework/module secret menu:

```text
SecretMenuActivationObserver
SecretMenuPresentationManager
SecretMenuFABContainerWindow
SecretMenuFABViewController
SecretMenuHostingController
SecretMenuExplorable
```

Menu dùng một floating action button/window riêng và có activation observer.
Feature modules có thể đăng ký item qua protocol `SecretMenuExplorable`.

### Oracle tools

```text
ExperimentsView
forceSegmentOnExperiments
CleanStorages
BackendEndpointOverride
PurchaseHistoryOverride
```

Các action đáng chú ý:

- Force experiment segment.
- Clean Oracle storages rồi chủ động crash/restart app.
- Chọn production/preproduction/staging backend.
- Override purchase history hoặc monetization state trong môi trường debug.
- Force setup response/update.

### Monetization debug

```text
Forced Subscription status
Override the real app's monetization status with a forced one.
activeSubscriptionsOverride
activeLifetimesOverride
activeBundleSubscriptionsOverride
activeExternalSubscriptionsOverride
forceDisableStoreKit
Force Finish All
```

Các chức năng này là debug capability được compile vào binary. Tuy nhiên một số
API có guard và thông báo rằng override không được gọi trong live
implementation; sự tồn tại của chuỗi không chứng minh menu production cho phép
thực thi mọi action.

### DeveloperSettingsVC

App còn có `DeveloperSettingsVC`, `DeveloperSettingsVM` và cell
`DevSettingChoiceCell`. Storyboard chứa màn hình Settings dạng table. Cùng binary
có các lựa chọn như:

- Use Staging Server.
- Network Inspector.
- Open Ad Inspector.
- Force hardcoded WebApp.
- Force crash cho Crashlytics testing.
- Feature flag/experiment overrides.

## Phân biệt với dylib crack

SecretMenu và forced subscription debug code là thành phần có trong executable
AM, khác với `AlightMotionCrack.dylib`. Nhưng chúng được thiết kế cho QA/debug và
có thể bị khóa bằng access level, build environment, server config hoặc hidden
activation. Dylib crack cố thay state ở runtime mà không đi qua các guard/debug
dependency này.

## Giá trị điều tra

Nếu có development build hợp lệ, SecretMenu là đường tốt nhất để:

- Chuyển staging/preproduction.
- Xem experiments và active feature flags.
- Kiểm tra subscription state giả lập trong QA environment.
- Làm sạch storage có kiểm soát.
- Mở network/ad inspector.

Với IPA production sideload, chỉ static analysis chưa xác định được gesture hoặc
điều kiện kích hoạt menu. Cần runtime event tracing để tìm activation path.
