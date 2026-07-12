# Feature flags, lỗi IAP và endpoint nội bộ

## Feature flags có giá trị cao

Trình trích tự động tìm được 711 key liên quan cấu hình/tính năng. Không phải tất
cả là Remote Config; tập này gồm remote keys, analytics event names,
localization keys và persisted flags. Những key dưới đây có quan hệ trực tiếp
với hành vi ứng dụng.

### Monetization và StoreKit

```text
subscription_ids
active_subscription_ids
active_bundle_subscription_ids
active_external_subscription_ids
is_fallback_on_bspmonetization_enabled
should_wait_for_products_fetch_before_app_start_paywall
monetization_lib_sk2_blocking_oracle_verify
monetization_lib_sk2_send_transactions_updates_to_oracle
send_local_data_to_oracle
send_receipt_to_oracle
oracle_verify
oracle_request_signatures
invalid_oracle_product
is_auto_storekit
forced_subscription_tier_key
paid_v2_user_enabled
```

Ý nghĩa kiến trúc:

- AM có thể đổi giữa IAP legacy và BSP Monetization.
- StoreKit 2 có flag riêng để chặn luồng trong lúc Oracle verify.
- Transaction updates có thể được gửi tới Oracle độc lập với local receipt.
- Product IDs, active subscriptions và external subscriptions là các danh sách
  cấu hình riêng.

### Paywall

```text
paywall_is_blocking
paywall_dismissable
paywall_style
paywall_trigger
paywall_hit_count
paywall_dismiss_count
paywall_presentation_pending
comparison_paywall_*
inverted_checkbox_paywall_*
other_options_paywall_*
max_paywall_*
pro_paywall_*
```

Ứng dụng chứa nhiều biến thể paywall được chọn bởi config/experiment, không chỉ
một màn hình mua hàng cố định.

### Premium/export

```text
benefit_premium_features
benefit_remove_watermark
benefit_future_member_features
lowest_locked_resolution
high_res_video_export_resolution
gif_export_resolution
single_export_without_wartermark
use_watermark_removal_ticket
earned_watermark_removal_ticket
is_revamped_pro_features_export_enabled
share_eligibility_watch_ads_enabled
share_eligibility_watch_ads_cap
```

Điều này củng cố rằng quyền export được quyết định theo benefit, độ phân giải,
ticket quảng cáo và feature flag; một `isPremium` boolean không bao phủ toàn bộ
luồng.

### Cloud

```text
cloud_backup_enabled
cloud_storage_quotas
cloud_storage_low_tier
cloud_storage_high_tier
upload_to_cloud
cloud_projects_subtab_seen
```

Cloud có quota/tier riêng và có thể yêu cầu benefit khác với Premium editor.

### Ads và tracking

```text
allow_personalized_ads
advertiser_id_collection_enabled
advertiser_tracking_enabled
application_tracking_enabled
is_targeted_ads_consent_popup_enabled
is_in_app_tracking_consent_enabled
idfv_in_adrequest_enabled
max_num_ads
number_of_preloaded_ads
ads_remove_watermark_watch_an_ad
```

### Editor và rollout

```text
enabled_feature_flags
server_features
overridable_features
fixed_features
new_media_replacement_logic_enabled
template_revamped_import_flow_enabled
preset_save_and_apply_enabled
is_new_templates_experience_enabled
is_templates_library_enabled_on_ipads
default_project_creation_selected_resolution
```

## Bảng lỗi IAP xác nhận từ executable

Các chuỗi sau nằm liên tiếp trong vùng `0x289D790–0x289DA14` của executable:

| Mã | Nội dung |
|---:|---|
| 21000 | Unknown Error |
| 21001 | Invalid Dependency State |
| 21002 | Invalid Delegate State |
| 21003 | Product List Unavailable |
| 21004 | Product Information Unavailable |
| 21005 | Unable to Retrieve Account Info |
| 21006 | Server Error |
| 21007 | Invalid Task |
| 21008 | Invalid Identifiers |
| 21009 | Product List Empty |
| 21015 | Registration Failure |
| 21016 | Invalid Receipt |
| 21018 | Service Unavailable |
| 21020 | Quota Limit |
| 21022 | Server Error |
| 21023 | App Store Connection Error |
| 21024 | Unverified Transaction |
| 21025 | Receipt Unavailable |

### Nhóm nguyên nhân

- `21001`, `21002`, `21007`: state machine/delegate/task nội bộ.
- `21003`, `21004`, `21008`, `21009`: tải hoặc ánh xạ StoreKit products.
- `21005`, `21006`, `21018`, `21020`, `21022`: account/backend/service.
- `21015`, `21016`, `21024`, `21025`: registration, receipt và transaction
  verification.
- `21023`: kết nối App Store.

Che alert không sửa nguồn lỗi. Ví dụ `21008` và `21009` khiến downstream không
có `SKProduct/Product`, nên paywall/purchase vẫn không thể hoàn tất.

## Endpoint có độ tin cậy cao

### Oracle

```text
https://alightmotion.oracle.bendingspoonsapps.com
https://alightmotion.preproduction.oracle.bendingspoonsapps.com
```

### Configuration/Janus

Executable chứa nhiều URL dạng:

```text
https://janus.bendingspoons.com/apps/AlightMotion/platforms/ios/settings/<id>
```

Có ít nhất tám settings document ID hard-code. Janus nhiều khả năng là một lớp
cấu hình của Bending Spoons bên cạnh Firebase Remote Config.

### Analytics/context

```text
https://api.pico.bendingspoonsapps.com/v4/events
https://api.staging.pico.bendingspoonsapps.com/v4/events
https://api.picox.bendingspoons.com/v1/events
https://spidersense.bendingspoons.com
```

### Firebase

```text
https://firebaseremoteconfig.googleapis.com
https://firebaseremoteconfigrealtime.googleapis.com
https://firebaseinstallations.googleapis.com
firestore.googleapis.com
firebasestorage.googleapis.com
identitytoolkit.googleapis.com
securetoken.googleapis.com
```

### Content và support

```text
https://alightcreative.com/appdata/am/
https://alight-fonts.firebaseapp.com/appdata/
https://guide.alightmotion.com/effects/
https://support.alightmotion.com/
```

## Phát hiện mới đáng chú ý

1. `monetization_lib_sk2_blocking_oracle_verify` cho thấy Oracle verification có
   thể chặn state StoreKit 2 thay vì chỉ chạy như analytics phụ.
2. `active_external_subscription_ids` và `third_party_unsubscription` cho thấy
   ứng dụng hỗ trợ subscription ngoài luồng App Store trong một số thị trường.
3. `oracle_request_signatures` cho thấy request Oracle có lớp xác thực/chữ ký;
   gửi JSON tự dựng không tương đương request hợp lệ của client.
4. `Janus` settings IDs hard-code cho thấy không phải mọi flag đều đến từ
   Firebase Remote Config.
5. `invalid_oracle_product` tách biệt lỗi product phía Oracle với StoreKit
   `invalidProductIdentifiers`.

## Dữ liệu thô

`deep_config_extract.json` chứa:

- 711 config/event/localization candidates có offset.
- Candidates mã lỗi và context.
- 210 network indicators có offset.

Tập raw có false positives; bảng trong báo cáo này chỉ giữ các mục đã kiểm tra
ngữ cảnh trong binary.
