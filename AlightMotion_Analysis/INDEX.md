# Mục lục phân tích Alight Motion

## Báo cáo đọc nhanh

- `README.md` — kiến trúc và luồng hoạt động tổng thể.
- `premium_status_methods.md` — phân tích các trạng thái Premium và license.
- `dylib_behavior.md` — bằng chứng tĩnh về selector, JSON license và return-true
  trong các biến thể dylib.
- `useful_findings.md` — phát hiện bổ sung về source structure, privacy,
  dependency, Product ID và repack.
- `crash_fix.md` — nguyên nhân crash đã xác nhận và kiểm tra bản fixed IPA.
- `../StoreKitTest/DEBUG_MOCK.md` — mock Premium chỉ cho DEBUG/test target.
- `../scripts/verify_fixed_ipa.py` — kiểm tra full IPA fixed và dependency RPATH.
- `oracle_remoteconfig_productid.md` — Oracle operation, Firebase Remote Config,
  Product ID và ranh giới giữa dữ liệu tĩnh với dữ liệu live.
- `feature_flags_and_errors.md` — feature flags, bảng lỗi IAP và endpoint nội bộ.
- `effects_web_ml.md` — effect XML/shader/script, web-native bridge và CoreML
  conversion model.
- `deeplinks_packages_debug.md` — URL routing, project package format và
  DeveloperSettings/SecretMenu.
- `binary_hardening_and_signature.md` — Mach-O encryption, hardening,
  CodeDirectory và so sánh ba binary.
- `evidence.json` — bằng chứng cốt lõi dạng JSON.

## Dữ liệu kiểm kê đầy đủ

- `full_summary.json` — số lượng, dung lượng, loại file và thống kê toàn app.
- `file_manifest.csv` — đường dẫn, kích thước và SHA-256 của toàn bộ 3.517 tệp.
- `plists.json` — nội dung 219 plist/CodeResources đã parse.
- `macho_dependencies.json` — dependency và RPATH của 7 Mach-O.
- `categorized_strings.json` — chuỗi executable phân nhóm theo subsystem.
- `network_indicators.json` — URL/hostname candidates để lọc tiếp.
- `injected_dylib_strings.txt` — toàn bộ chuỗi đọc được từ dylib chèn.
- `deep_config_extract.json` — config/error/network candidates có file offset.
- `effects_inventory.json` — effect IDs, duplicate, parse errors và mod markers.
- `web_bridge_context.json` — context của WKWebView bridge trong web bundle.
- `binary_security.json` — Mach-O headers, sections và xác minh code pages.

## Công cụ tái tạo

- `../scripts/analyze_alightmotion_full.py` — chạy lại toàn bộ kiểm kê từ
  `extracted/Payload/AlightMotion.app`.

Lưu ý: `network_indicators.json` là tập candidate tự động và có false positives;
chỉ các hostname được xác nhận trong báo cáo đọc nhanh mới nên coi là chỉ dấu
mạng đáng tin cậy.
