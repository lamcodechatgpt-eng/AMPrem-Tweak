# BuiltinEffects, web bridge và CoreML model

## BuiltinEffects

Thư mục chứa 853 XML effect và một ảnh test. Kết quả parse:

- 852 XML hợp lệ.
- 1 XML lỗi cú pháp: `deepglow.xml`, mismatched tag tại dòng 93.
- 90 effect có JavaScript `<script>`.
- 812 shader nodes.
- 310 effect IDs bị trùng giữa hai hoặc nhiều file.
- Ít nhất 174 file chứa dấu vết như `modder`, `Valdex`, `Effect by` hoặc
  `Extra FX`.

### Dấu hiệu pack đã bị chỉnh sửa mạnh

Ví dụ:

```text
Manual Shake 2  — Effect by Valdex
Fake 3D         — Amazing New Extra FX from the Modder
com.mod.softbloom
com.mod.lutstealer
About Me        — ID dùng ký tự Unicode giả dạng “com.alightcreative”
```

Vì vậy `BuiltinEffects` hiện tại không thể coi là effect pack gốc của AM 6.2.53.
Nhiều file số và file tên mô tả cùng dùng chung effect ID, tạo 310 nhóm duplicate.
Tùy thứ tự loader, bản được đăng ký sau có thể ghi đè bản trước hoặc tạo kết quả
không ổn định.

### Định dạng effect

Root node thường chứa:

```xml
<effect id="..." name="..." category="..." compat="...">
```

Các input/control quan sát được:

| Node | Số lượng |
|---|---:|
| `spinner` | 3.886 |
| `texture` | 1.171 |
| `color` | 702 |
| `switch` | 654 |
| `point` | 619 |
| `slider` | 608 |
| `selector` | 548 |
| `section` | 447 |
| `xyz` | 94 |
| `tip` | 85 |
| `orient` | 50 |
| `hue-disc` | 26 |

Effect có thể dùng:

- GLSL-like fragment/vertex shader.
- JavaScript `animate(env, el, p)` để sửa transform/property theo frame.
- Texture/content input.
- Matrix như `acLayerToScreen` và API host như `AM.simplexNoise`.

JavaScript effect chạy mỗi frame có thể gây crash/lag nếu script lỗi, tạo số
không hữu hạn hoặc truy cập property không tồn tại. Shader tùy chỉnh cũng có thể
gây compile failure hoặc GPU timeout.

### Liên hệ với crash

`deepglow.xml` chắc chắn không parse được. Duplicate IDs và 174 file modded là
nguồn rủi ro riêng, không liên quan dylib Premium. Nếu app crash khi mở effect
browser hoặc project dùng effect cụ thể, cần kiểm tra effect XML/shader trước khi
quy lỗi cho StoreKit.

## Web app nhúng trong `dist`

`dist` khoảng 6,6 MB và là web app build bằng Vite/React. Thành phần chính:

- `js/index.js`: khoảng 2,45 MB.
- `js/vendor.js`: khoảng 188 KB.
- `js/web-composable-architecture.js`: khoảng 278 KB.
- Hình/video cho onboarding, free trial, rating và Bending Spoons app bundle.

Nội dung cho thấy đây chủ yếu là onboarding/paywall/cross-promotion experience,
không phải editor render engine.

### Native bridge

iOS bridge dùng hai WKScriptMessage handler:

```text
NativeFunctionExecutionHandler
WebFunctionResponseHandler
```

Web gọi native theo envelope:

```text
functionName
webInput          JSON string
webCallbackId
```

Native gọi/nhận response web theo:

```text
webOutput         JSON string
nativeCallbackId
```

Web layer còn expose function như `evaluateTrigger`. Cùng bundle hỗ trợ Android
qua `window.androidBridge`, chứng tỏ web experience được dùng chung đa nền tảng.

Nếu native output không đúng format, web tạo lỗi `nativeOutputInvalidFormat`.
Sai schema giữa native config và JavaScript bundle có thể làm onboarding/paywall
trắng hoặc treo dù app không crash ở dyld.

## CoreML conversion model

Model:

```text
wolf_alightcreative_motion_post_onboarding_2025_06_25
```

Đây là `pipelineRegressor`, gồm one-hot encoders, feature vectorizer và tree
ensemble regressor. Output duy nhất:

```text
converted: Double
```

Nó dự đoán khả năng conversion sau onboarding/paywall, không xử lý video.

### Input features

- Ngày/giờ.
- Ngôn ngữ thứ nhất, thứ hai và ngôn ngữ app.
- Timezone, region và currency.
- Phiên bản OS và model thiết bị.
- Battery level và network connection.
- Screen brightness/zoom/content size.
- Device orientation và attitude quaternion.
- Paywall style và paywall trigger.
- Push notification access.
- Ad network access.

Metadata ghi:

- 800.000 dataset rows.
- 560.000 training samples.
- Training từ 29/05/2025 đến 24/06/2025.
- Training time khoảng 18 giờ 28 phút.
- Tạo bằng Create ML 15.5.

Model có khả năng dùng để xếp hạng/chọn trải nghiệm paywall hoặc quyết định thời
điểm/biến thể presentation. Nó giải thích vì sao hai thiết bị/account có thể thấy
paywall khác nhau dù Remote Config giống nhau.

## Dữ liệu thô

- `effects_inventory.json`: thống kê từng effect, duplicate IDs và file lỗi.
- `web_bridge_context.json`: context quanh bridge calls trong JavaScript bundle.
