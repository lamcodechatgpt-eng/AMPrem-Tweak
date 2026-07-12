# Oracle, Remote Config và Product ID hiện hành

## Kết luận

Không thể lấy **response live thật** hoặc **Product ID đầy đủ hiện hành** chỉ từ
IPA này. AM 6.2.53 tải chúng động theo account, storefront, experiment và Firebase
Remote Config. App Store công khai tên gói/giá nhưng không công bố internal
Product ID.

Những dữ liệu có thể xác nhận tĩnh được ghi dưới đây; các trường live cần log từ
development build hoặc quyền App Store Connect/Firebase Console.

## Firebase Remote Config

Production Firebase project:

```text
PROJECT_ID     alight-creative
GOOGLE_APP_ID  1:414370328124:ios:f1394131c8b84de3
STORAGE_BUCKET alight-creative.appspot.com
DATABASE_URL   https://alight-creative.firebaseio.com
```

Staging Firebase project:

```text
PROJECT_ID     alight-creative-staging
GOOGLE_APP_ID  1:1085723979695:ios:f1394131c8b84de3
STORAGE_BUCKET alight-creative-staging.appspot.com
DATABASE_URL   https://alight-creative-staging.firebaseio.com
```

Firebase SDK endpoints có trong executable:

```text
https://firebaseremoteconfig.googleapis.com
https://firebaseremoteconfigrealtime.googleapis.com
```

Các khóa cấu hình liên quan monetization được xác nhận trong binary:

```text
subscription_ids
active_subscription_ids
active_bundle_subscription_ids
active_external_subscription_ids
fallback_on_bspmonetization
is_fallback_on_bspmonetization_enabled
shouldWaitForProductsFetchBeforeIAPStartPaywall
```

Điều này cho thấy danh sách sản phẩm được tải/cấu hình động; executable chỉ giữ
fallback prefix.

## Product ID trong executable gốc

Ba prefix chắc chắn:

```text
alightcreative.motion.1w_
alightcreative.motion.1m_
alightcreative.motion.1y_
```

Chúng nằm cạnh `subscription_ids`, `fallback_on_bspmonetization` và đường dẫn
source `AppConfiguration+Dependencies.swift`.

Product ID sau chỉ tồn tại trong dylib được chèn:

```text
alightcreative.motion.1y_t60_1w
```

Vì không tồn tại nguyên vẹn trong executable gốc hoặc resource config, nó không
được coi là Product ID hiện hành đã xác minh. StoreKit trả `21008` là bằng chứng
thực tế rằng ID được request không hợp lệ trong bundle/storefront/test context
đang chạy.

## Gói thuê bao công khai hiện hành

Trang App Store hiện liệt kê nhiều SKU theo storefront, gồm:

- Weekly Subscription
- Weekly Subscription with Free Trial
- Monthly Subscription
- Yearly/Annual Subscription
- Weekly Cloud Subscription
- Yearly Cloud Subscription
- Alight Motion with Free Trial

Tên và giá thay đổi theo storefront. Danh sách công khai không chứa internal
Product ID, nên không thể ánh xạ chắc chắn từng tên vào suffix sau `1w_`, `1m_`
hoặc `1y_`.

## Oracle operation

Executable chứa operation:

```text
getAccountStatusAndLicenses
```

Các thành phần liên quan:

```text
Oracle+Request.swift
Oracle+SetupRequest.swift
Oracle+Live.swift
Oracle StateManager
AuthenticationManager
ReceiptClient / ReceiptClientV2
sendLocalReceiptToOracle
LicenseStore
EntitlementsRefresher
```

Hostname được xác nhận:

```text
alightmotion.oracle.bendingspoonsapps.com
oracle.bendingspoonsapps.com
```

### Request có thể xác nhận ở mức cấu trúc

Binary cho thấy request được dựng từ các context sau, nhưng tên field JSON chính
xác cần runtime capture để xác nhận:

- Account/authentication identity.
- App/bundle/version context.
- Device/install identifiers.
- StoreKit local receipt hoặc StoreKit 2 transaction context.
- Product/subscription information.
- Oracle experiments/configuration.

Không có request body JSON hoàn chỉnh dạng plaintext trong executable.

### Response model có thể xác nhận

Các field/model xuất hiện trong binary:

```text
activeLicenses
licenses
activeBenefits
benefits
activeSubscription
autoRenewing
orderNumber
msTime
warnings
status
```

Luồng sử dụng:

```text
Oracle response
  -> decode status/licenses
  -> LicenseStore
  -> activeBenefits / activeSubscription
  -> EntitlementsRefresher
  -> Monetization state
  -> paywall, cloud quota, export và watermark checks
```

JSON nằm trong source tweak của workspace là response **giả do tweak tự tạo**,
không phải response production đã capture. Không nên dùng nó làm schema chính
thức.

## Cách lấy dữ liệu live hợp lệ

### Có quyền Firebase/App Store Connect

1. Mở Firebase Console của project production.
2. Export template Remote Config đang active.
3. Đọc `subscription_ids` và các active product lists.
4. Đối chiếu từng ID với Subscriptions trong App Store Connect.

Đây là nguồn duy nhất xác nhận Product ID đầy đủ và trạng thái hiện hành.

### Có development build của ứng dụng

1. Chạy app từ Xcode với cấu hình development.
2. Log danh sách ID ngay trước `Product.products(for:)` hoặc
   `SKProductsRequest`.
3. Log `Product.products(for:)` result và invalid IDs.
4. Dùng Xcode Network Instruments hoặc logger nội bộ để ghi request/response đã
   được app giải mã, đồng thời che token, receipt và user identifiers.
5. Đối chiếu response với model `LicenseStore`/`EntitlementsRefresher`.

### Chỉ có IPA sideload

Không có cách đáng tin cậy để xác minh Product ID “hiện hành” từ static binary,
vì Remote Config và storefront thay đổi ngoài binary. Việc gửi request tự dựng
tới backend production cũng không chứng minh schema đúng và có thể vi phạm quyền
truy cập dịch vụ.

## Mức độ chắc chắn

| Dữ liệu | Mức chắc chắn |
|---|---|
| Firebase project production/staging | Cao |
| Remote Config keys trong binary | Cao |
| Ba Product ID prefix | Cao |
| `1y_t60_1w` là ID hiện hành | Chưa xác minh |
| Oracle operation và hostname | Cao |
| Response fields nêu trên tồn tại trong model | Cao |
| Request/response live chính xác | Cần runtime hoặc console có quyền |
