# Startup và Premium checker

Chạy:

```powershell
python scripts\check_ipa_startup_and_premium.py AlightMotion_Premium_clean_fixed.ipa
```

Checker báo ba trạng thái riêng:

- `STARTUP`: lỗi deterministic trong ZIP, Info.plist, Mach-O hoặc dependency.
- `PREMIUM STATIC`: dấu hiệu dylib injection/binary patch.
- `RUNTIME`: luôn là `UNVERIFIED` nếu chưa chạy trên iOS.

Mã trả về:

- `0`: không có lỗi startup tĩnh và không có indicator bypass.
- `1`: không có lỗi startup tĩnh nhưng có indicator bypass.
- `2`: có lỗi startup deterministic hoặc IPA malformed.

Không thể chứng minh “không crash khi vào” chỉ bằng static analysis; cần crash
log hoặc chạy thật trên thiết bị. Không thể chứng minh Premium hoạt động chỉ vì
có dylib/JSON/selector; cần transaction StoreKit `.verified` còn hiệu lực.
