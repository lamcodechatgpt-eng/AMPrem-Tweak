# Mach-O hardening, encryption và chữ ký

## Executable chính

`AlightMotion` là Mach-O ARM64 executable, build cho:

```text
Minimum iOS: 14.4
SDK:         26.2
Entry point: file offset 0x98B4
```

Header flags:

```text
NOUNDEFS
DYLDLINK
TWOLEVEL
WEAK_DEFINES
BINDS_TO_WEAK
PIE
HAS_TLV_DESCRIPTORS
```

PIE cho phép ASLR. Segment protections:

| Segment | Protection |
|---|---|
| `__TEXT` | read + execute |
| `__DATA_CONST` | read + write at load representation |
| `__DATA` | read + write |
| `__LINKEDIT` | read |

Không có segment RWX.

## Trạng thái giải mã

Executable vẫn có `LC_ENCRYPTION_INFO_64`:

```text
cryptoff  = 0x4000
cryptsize = 0x2D44000
cryptid   = 0
```

`cryptid=0` nghĩa vùng code hiện không được FairPlay mã hóa. Đây là executable
đã decrypt, dù load command encryption vẫn còn.

## CodeDirectory verification

Executable chính có `LC_CODE_SIGNATURE`:

```text
offset = 55,620,448
size   = 708,112
```

Có hai CodeDirectory:

- SHA-1, 13.580 code pages.
- SHA-256, 13.580 code pages.

Tôi đã hash lại toàn bộ page 4.096 byte tới `codeLimit`. Kết quả:

```text
AlightMotion: 0 mismatch ở cả SHA-1 và SHA-256
```

Điều này chứng minh chữ ký nhúng hiện khớp nội dung executable chính, gồm cả
load command nạp `AlightMotionCrack.dylib`. Không chứng minh toàn bộ app bundle
hợp lệ, vì nested dylib/resource sealing là lớp riêng.

## `AlightMotion_patched`

`AlightMotion_patched` có cùng:

- Kích thước.
- UUID.
- Load commands.
- Segments và sections.
- Code signature blob.

Nhưng nó khác 8 byte code tại hai cụm offset. CodeDirectory verification:

```text
SHA-1:   mismatch page 8664
SHA-256: mismatch page 8664
```

Page 8664 bao phủ file offset `0x21D8000–0x21D8FFF`, đúng vùng patch getter
`0x21D8D5C/0x21D8D64`. Vì vậy `_patched` chắc chắn có chữ ký stale và không thể
dùng nguyên trạng mà không ký lại.

## Dylib được chèn

`AlightMotionCrack.dylib`:

```text
Type:        ARM64 dylib
Minimum iOS: 14.0
SDK:         18.5
Size:        67,616 bytes
CodeSignature: không có
```

Dylib không có `LC_CODE_SIGNATURE`/CodeDirectory. Trên thiết bị iOS bình thường,
signer phải ký nested dylib trong quá trình resign. Nếu công cụ chỉ ký executable
chính mà bỏ qua dylib, dyld có thể từ chối load hoặc AM crash ngay khi mở.

Dylib được build bằng SDK 18.5, trong khi app dùng SDK 26.2. Chênh lệch SDK không
tự nó gây lỗi vì dylib chỉ phụ thuộc API cơ bản, nhưng cho thấy dylib được build
riêng và không cùng pipeline với app.

Dependencies của dylib:

- Objective-C runtime.
- Foundation/CoreFoundation.
- UIKit.
- StoreKit.
- libSystem.

## Quy mô metadata executable

Ước tính trực tiếp từ section sizes:

| Metadata | Số lượng/kích thước |
|---|---:|
| Objective-C class list entries | 3.515 |
| Non-lazy classes | 30 |
| Objective-C categories | 43 |
| Selector references | 24.189 |
| Class references | 2.406 |
| Ivar offset entries | 8.123 |
| Swift type descriptor references | 5.849 |
| Swift protocol descriptor references | 9.971 |
| Swift field metadata | 355.948 byte |
| Swift reflection strings | 301.182 byte |

Đây là binary rất lớn, gồm cả app code và nhiều dependency link tĩnh. Việc quét
mọi class/selector rồi hook theo tên ngắn có xác suất đụng nhầm implementation
cao.

## Ý nghĩa với lỗi crash

Ưu tiên kiểm tra theo thứ tự:

1. Signer có ký `Frameworks/AlightMotionCrack.dylib` không.
2. IPA có dùng `AlightMotion` hay vô tình đổi sang `_patched` chưa ký lại.
3. Bundle CodeResources có được tái tạo không.
4. Crash log có `code signature invalid`, `Library not loaded` hoặc dyld reason
   không.
5. Nếu dyld qua được, mới kiểm tra constructor và runtime method replacement.

## Dữ liệu tái tạo

- `binary_security.json`: headers, flags, segments, sections, dependency,
  encryption và CodeDirectory results.
- `../scripts/analyze_macho_security.py`: script tái tạo phân tích.
