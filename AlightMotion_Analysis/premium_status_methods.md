# Phân tích các trạng thái Premium của Alight Motion

## Kết luận ngắn

Sáu tên được hỏi không nằm ở cùng một tầng:

| Tên | Có trong executable AM | Có trong dylib crack | Vai trò hợp lý |
|---|---:|---:|---|
| `isSubscribed` | Có, nhiều vị trí | Có | Trạng thái thuê bao trên model/store cụ thể |
| `isPremium` | Có, nhiều vị trí | Có | Trạng thái Premium tổng hợp hoặc property của nhiều model |
| `unlockedPremiumUser` | Có, một chuỗi rõ ràng | Có | Flag/case biểu diễn người dùng đã mở Premium |
| `hasActiveSubscription` | Không thấy chuỗi ASCII | Có | Selector dò thử của dylib; chưa chứng minh là API AM 6.2.53 |
| `isProUser` | Không thấy chuỗi ASCII | Có | Selector dò thử của dylib; chưa chứng minh là API AM 6.2.53 |
| `getAccountStatusAndLicenses` | Có | Có | Tên endpoint/API lấy account status và danh sách license |

Ngoài sáu tên này, AM 6.2.53 có bằng chứng mạnh hơn cho
`IAPManager.isPremiumUser`, một Swift stored `Bool` tại offset instance `+0x3A`.
Đây là trạng thái client cục bộ, không đồng nghĩa với toàn bộ entitlement hệ
thống.

## Mô hình trạng thái thực tế

Các symbol/type trong executable cho thấy trạng thái trả phí được xây theo
nhiều tầng:

```text
StoreKit product và transaction
        |
        v
App Store receipt / restore
        |
        v
ReceiptClient / Oracle backend
        |
        v
Account status + licenses
        |
        v
LicenseStore / EntitlementsRefresher
        |
        +--> subscription state
        +--> benefit set
        +--> IAPManager flags
        |
        v
isPremium / isSubscribed / paywall / export checks
```

Do đó ứng dụng có thể đồng thời có:

- Một transaction StoreKit hợp lệ.
- Một subscription record đang hoạt động.
- Một license do Oracle trả về.
- Một tập benefit cụ thể.
- Boolean cache dùng cho UI/editor.

Các giá trị này có thể lệch nhau trong lúc khởi động, refresh, mất mạng hoặc
đăng nhập/chuyển tài khoản.

## `isSubscribed`

Chuỗi này xuất hiện tại nhiều vùng của executable, gồm cả metadata/type data.
Điều đó cho thấy tên được dùng bởi hơn một model hoặc framework, không thể mặc
định mọi method cùng tên đều có cùng ý nghĩa.

Vai trò hợp lý:

1. Đọc một subscription object hoặc store state.
2. Cho biết người dùng hiện có record thuê bao, nhưng chưa chắc record còn hạn.
3. Được dùng để chọn UI/paywall hoặc routing liên quan tới subscription.

Nó không nhất thiết kiểm tra benefit. Một subscription có thể tồn tại nhưng đã
hết hạn, bị revoke, thuộc tier khác hoặc đang chờ backend link.

Dylib crack dùng `sel_registerName("isSubscribed")` rồi tìm method theo runtime.
Nếu tìm được, nó có thể thay implementation. Vì không ràng buộc class cụ thể,
cách dò toàn cục có nguy cơ tác động nhầm class có selector trùng tên.

## `isPremium`

`isPremium` xuất hiện nhiều lần trong executable, bên cạnh các tên
`isPremiumFeature` và `isPremiumUser`. Đây là bằng chứng rằng “premium” được dùng
ở nhiều context:

- Property trên account/subscription state.
- Property của effect/project/template cho biết nội dung cần Premium.
- Giá trị tổng hợp để UI quyết định hiển thị paywall.
- Giá trị analytics hoặc serialized model.

Vì vậy `isPremium == true` trên một object có thể chỉ có nghĩa “effect này là
premium”, không phải “người dùng hiện là premium”. Runtime hook mọi method tên
`isPremium` là không an toàn: nó có thể biến mọi asset thành premium thay vì cấp
quyền truy cập cho user, hoặc làm sai logic filter/render.

## `unlockedPremiumUser`

Tên này có một chuỗi rõ ràng trong executable tại file offset `0x2B4F140`.
Hình thức tên gợi ý một case/state trong state machine hoặc enum biểu diễn kết
quả unlock, hơn là nguồn xác thực gốc.

Luồng hợp lý:

```text
license/entitlement refresh thành công
    -> reducer/state manager nhận benefit Premium
    -> phát state/action unlockedPremiumUser
    -> UI bỏ paywall hoặc refresh nội dung
```

Nếu đây là enum case/action, coi nó như một boolean selector sẽ sai ABI. Chỉ có
chuỗi trong metadata chưa đủ để kết luận tồn tại Objective-C instance method
`-unlockedPremiumUser`.

## `hasActiveSubscription`

Không tìm thấy chuỗi ASCII này trong executable AM 6.2.53, nhưng nó có trong
`AlightMotionCrack.dylib`.

Kết luận có độ tin cậy cao:

- Dylib chuẩn bị selector này để dò runtime.
- Phân tích hiện tại chưa chứng minh AM 6.2.53 triển khai selector đó.
- Nếu `class_getInstanceMethod` trả `NULL`, một dylib viết đúng phải bỏ qua.

Nó có thể đến từ phiên bản AM khác, một dependency dùng Swift không export tên
theo ASCII, hoặc đơn giản là danh sách selector “thử vận may” của tác giả mod.

## `isProUser`

Tương tự `hasActiveSubscription`, tên này không xuất hiện trong executable nhưng
có trong dylib. Trong AM hiện tại, thuật ngữ quan sát được nhiều hơn là Premium,
license, benefit và subscription; “Pro” không phải bằng chứng chắc chắn cho API
thật.

Không nên dùng sự tồn tại của chuỗi trong dylib để kết luận đây là method gốc của
AM. Cần runtime class/method enumeration hoặc Swift metadata resolution trên
thiết bị để xác nhận.

## `getAccountStatusAndLicenses`

Chuỗi này xuất hiện trong executable tại file offset `0x289E1A0`. Nó có hình thức
tên operation/endpoint, không phải boolean getter.

Dựa trên các type `ReceiptClient`, `OracleSubscription`, `LicenseStore`,
`EntitlementsRefresher` và hostname Oracle, luồng hợp lý là:

1. Client tập hợp account identity và receipt/purchase context.
2. Gửi request tới dịch vụ Oracle.
3. Backend xác minh hoặc liên kết giao dịch với account.
4. Response trả trạng thái và mảng license.
5. Mỗi license chứa type, store, product, validity, renewal/link status và
   benefits.
6. Client cập nhật `LicenseStore` và tính entitlement cho từng feature.

Đây là tầng có sức nặng cao hơn một boolean UI. Một response có `isPremium=true`
nhưng thiếu benefit như `RemoveWatermark` vẫn có thể khiến export áp watermark.

Trong source thử nghiệm của workspace, một `NSURLProtocol` được viết để bắt URL
có tên operation này và thay JSON response. Đó là logic của tweak trong
workspace, không phải cách backend gốc của AM hoạt động và không phải bằng chứng
về schema chính thức.

## `IAPManager.isPremiumUser` — bằng chứng cụ thể hơn

Swift metadata trong executable cho thấy `IAPManager` có các field:

| Instance offset | Field |
|---:|---|
| `+0x38` | `isSpooner` |
| `+0x39` | `isFreeUser` |
| `+0x3A` | `isPremiumUser` |
| `+0x3B` | `experiments` |
| `+0x3C` | `isDataCollectionEnabled` |

Getter đã được nhận diện trong nghiên cứu workspace đọc byte tại `+0x3A` và trả
về một Swift `Bool`. Có 42 vị trí đọc field này trong executable. Điều này phù
hợp với việc `IAPManager` cache trạng thái để nhiều màn hình đọc nhanh.

Quan trọng: 42 lệnh `LDRB [register, #0x3A]` không đồng nghĩa cả 42 đều đọc
`IAPManager.isPremiumUser`; các class khác cũng có thể có field tại offset
`0x3A`. Vì vậy quét và sửa toàn bộ pattern theo offset đã gây nguy cơ crash.

## Cách dylib hiện tại xử lý các tên này

Dylib chứa các API Objective-C runtime:

- `objc_getClass`
- `sel_registerName`
- `class_getInstanceMethod`
- `method_getImplementation`
- `method_setImplementation`

Cơ chế tổng quát:

1. Dylib được dyld nạp qua `@rpath/AlightMotionCrack.dylib`.
2. Constructor/load routine chạy khi ứng dụng khởi động.
3. Nó tạo selector từ các chuỗi trạng thái Premium.
4. Nó tìm method trên class mục tiêu hoặc duyệt class runtime.
5. Nếu method tồn tại, implementation được thay bằng hàm khác.

Rủi ro kỹ thuật:

- Tên method trùng trên nhiều class nhưng ý nghĩa khác nhau.
- Return type không phải `BOOL` nhưng bị thay bằng hàm trả `BOOL`.
- Swift method không exposed qua Objective-C nên không tìm thấy.
- Class chưa được load khi constructor chạy.
- Thay implementation sau khi object đã cache state không cập nhật toàn bộ hệ
  thống.
- Backend/license refresh chạy sau đó và ghi đè state.

## Mức độ chắc chắn

| Nhận định | Độ chắc chắn |
|---|---|
| `isSubscribed`, `isPremium`, `unlockedPremiumUser` có chuỗi trong AM | Cao |
| `getAccountStatusAndLicenses` là operation/API liên quan account/license | Cao |
| `hasActiveSubscription`, `isProUser` là API thật của AM 6.2.53 | Thấp |
| `IAPManager.isPremiumUser` là Swift Bool tại `+0x3A` | Cao |
| Mọi occurrence `isPremium` đều chỉ trạng thái user | Sai |
| Một boolean duy nhất quyết định toàn bộ Premium | Không phù hợp bằng chứng |

Để nâng các phần suy luận thành kết luận runtime cần crash-safe tracing trên bản
development: liệt kê class sở hữu selector, type encoding, backtrace caller và
state trước/sau `EntitlementsRefresher`.
