# Kiểm tra IPA có dấu hiệu bypass Premium

Chạy từ workspace root:

```text
python scripts/check_ipa_premium_state.py AlightMotion_Premium_clean_fixed.ipa
```

Mã trả về:

- `0`: không thấy dấu hiệu injection/bypass rõ ràng.
- `1`: thấy dylib/load command/tệp patch đáng ngờ.
- `2`: IPA lỗi hoặc thiếu executable.

Checker chỉ phân tích tĩnh. Nó không thể chứng minh Premium đang hoạt động,
receipt có hợp lệ hay backend đã cấp entitlement. Để xác nhận runtime hợp lệ,
dùng StoreKit Test trong Xcode và kiểm tra `Transaction.currentEntitlements`.

Các chỉ báo được kiểm tra:

Để xác nhận runtime, dùng `StoreKitTest/PremiumRuntimeProbe.swift`. Kết quả
chỉ được coi là Premium hợp lệ khi transaction là verified, chưa bị revoke và
chưa hết hạn. Dylib, JSON license hoặc chuỗi `isPremium` không phải bằng chứng
entitlement.

- `AlightMotionCrack.dylib`, `AMPrem.dylib` và tên patch tương tự.
- `@rpath` load command trỏ tới dylib injection.
- `decrypt.day` hoặc executable `_patched`.
- Một số pattern ARM64 `mov`/`ret` chỉ dùng làm cảnh báo phụ.
- Product string và symbol liên quan Premium để hỗ trợ điều tra.
