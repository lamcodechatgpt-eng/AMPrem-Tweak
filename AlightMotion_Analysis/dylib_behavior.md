# Kiểm tra hành vi dylib Premium

## Kết quả

Phân tích tĩnh ba biến thể dylib trong workspace:

| File | Kích thước | `mov w0,#1; ret` | Dữ liệu license |
|---|---:|---:|---|
| `extracted/.../AlightMotionCrack.dylib` | 67,616 | 1 | selector/benefit strings |
| `AMPrem.dylib` | 74,120 | 0 | JSON license `1y_t60_1w` |
| `extracted_deb/output/AMPrem.dylib` | 71,856 | 1 | JSON license `1y_t130_1w` |

Các selector/chuỗi quan sát được gồm:

- `isSubscribed`
- `isPremium`
- `hasActiveSubscription`
- `isPremiumUser`
- `isSubscriptionActive`
- `getAccountStatusAndLicenses`
- `RemoveWatermark`

## Ý nghĩa

Có bằng chứng mạnh rằng các dylib được viết để:

1. Dò và thay một số method trạng thái Premium.
2. Trả `true` vô điều kiện ở ít nhất một replacement IMP trong hai biến thể.
3. Chèn JSON license giả chứa benefit, product ID, `valid=true` và
   `autoRenewing=true`.

Nhưng đây vẫn là bằng chứng về ý đồ/cơ chế của dylib, không phải bằng chứng
Premium đã hoạt động trong AM. Còn phải qua dyld loading, ABI đúng, selector
đúng class, StoreKit flow, backend refresh và export check.

## Kết luận cho các IPA hiện tại

- IPA cũ có load command crack nhưng thiếu file tương ứng, nên vừa có dấu hiệu
  injection vừa có nguy cơ crash.
- IPA fixed không có dylib hoặc load command crack, nên không có bypass runtime.
- Sự tồn tại của JSON license hoặc `mov w0,#1; ret` trong một dylib không đủ để
  kết luận user đang có entitlement Premium thật.
