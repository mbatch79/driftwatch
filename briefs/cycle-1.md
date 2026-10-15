# Driftwatch — Cycle 1 Breaking-Change Brief
_Generated 2026-10-15 19:22 UTC · window 60 days · 221 verified findings (25 breaking, 11 deprecation, 185 additive) · 0 rejected by WARDEN_

## Coverage
| Source | File | Before (commit · date) | After (commit · date) | Changed? |
|---|---|---|---|---|
| stripe | `openapi/spec3.json` | `af5309ca` · 2026-07-29 | `bcfd59f4` · 2026-09-29 | yes |
| openai | `openapi.json` | `2186421d` · 2026-08-15 | `5068a57f` · 2026-10-15 | yes |
| twilio | `spec/json/twilio_api_v2010.json` | `591755b5` · 2026-08-11 | `157fb094` · 2026-10-06 | yes |
| twilio | `spec/json/twilio_messaging_v1.json` | `591755b5` · 2026-08-11 | `218b7821` · 2026-09-28 | yes |
| aws-sdk-js | `CHANGELOG.md` | `c41e9a98` · 2026-08-14 | `3ce8aa77` · 2026-10-14 | yes |
| shopify-api-js | `packages/apps/shopify-api/CHANGELOG.md` | `e7654fc6` · 2026-08-07 | `8868403d` · 2026-10-08 | yes |

## Findings (WARDEN-verified)

### aws-sdk-js
- **BREAKING** · New changelog section '[3.1126.0](https://github.com/aws/aws-sdk-js-v3/compare/v3.1125.0...v3.1126.0) (2026-09-03)': * **client-ecs:** Adds a critical parameter to the Amazon ECS managed daemon APIs that controls whether a daemon task failure drains the container instance. Non-critical daemon failures no longer drain the instance or block instance registration. ([2e6a07d](https://github.com/aws/aws-sdk-js-v3/commit/2e6a07d57083a221355891dfb18e9aa129e5987b)) | * **client-eks:** Deprecate EncryptionConfig resources field. Amazon EKS encrypts all Kubernetes API data with envelope encryption by default for clusters running Kubernetes version 1.28 or higher, so this field no longer affects which resources are encrypted. ([c66ca41](https://github.com/aws/aws-sdk-js-v3/commit/c66ca41b9a97108402d0e3bd8e467babc35a7bac)) _(keyword-classified from changelog; WARDEN verified the quote, not the semantics)_  
  locator `#[3.1126.0](https://github.com/aws/aws-sdk-js-v3/compare/v3.1125.0...v3.1126.0) (2026-09-03)` · c41e9a98 → 3ce8aa77
- **BREAKING** · New changelog section '[3.1128.0](https://github.com/aws/aws-sdk-js-v3/compare/v3.1127.0...v3.1128.0) (2026-09-08)': * **client-appflow:** Amazon AppFlow now supports key pair (RSA private key) authentication for the Snowflake connector. You can provide a privateKey in SnowflakeConnectorProfileCredentials, and password is no longer required. This is a non-breaking, additive change available via the AWS SDK and CLI. ([ec8753a](https://github.com/aws/aws-sdk-js-v3/commit/ec8753ad6f2305daca3d8679a8438dceaee9b4b9)) _(keyword-classified from changelog; WARDEN verified the quote, not the semantics)_  
  locator `#[3.1128.0](https://github.com/aws/aws-sdk-js-v3/compare/v3.1127.0...v3.1128.0) (2026-09-08)` · c41e9a98 → 3ce8aa77
- **DEPRECATION** · New changelog section '[3.1120.0](https://github.com/aws/aws-sdk-js-v3/compare/v3.1119.0...v3.1120.0) (2026-08-27)': * **client-lambda-microvms:** Added InsufficientCapacityException to RunMicrovm for capacity-related failures. Added lifecycle status field (AVAILABLE, DEPRECATED) to ListManagedMicrovmImageVersions. Added ConflictException to CreateMicrovmAuthToken and CreateMicrovmShellAuthToken for unregistered MicroVMs. ([72a8ff8](https://github.com/aws/aws-sdk-js-v3/commit/72a8ff80923f172e73030a0b28d9946fb16d0ffa)) _(keyword-classified from changelog; WARDEN verified the quote, not the semantics)_  
  locator `#[3.1120.0](https://github.com/aws/aws-sdk-js-v3/compare/v3.1119.0...v3.1120.0) (2026-08-27)` · c41e9a98 → 3ce8aa77
- **DEPRECATION** · New changelog section '[3.1132.0](https://github.com/aws/aws-sdk-js-v3/compare/v3.1131.0...v3.1132.0) (2026-09-14)': * **client-sts:** Increases the maximum session token size to 4,096 bytes and removes the packed policy size limit. Adds SessionTokenSize and SessionTokenUtilization fields and a new MinimumSessionTokenSize parameter. PackedPolicySize is deprecated. ([906e0db](https://github.com/aws/aws-sdk-js-v3/commit/906e0db85730f7c72e0fceb332540c82a8cfeac1)) _(keyword-classified from changelog; WARDEN verified the quote, not the semantics)_  
  locator `#[3.1132.0](https://github.com/aws/aws-sdk-js-v3/compare/v3.1131.0...v3.1132.0) (2026-09-14)` · c41e9a98 → 3ce8aa77
- **DEPRECATION** · New changelog section '[3.1151.0](https://github.com/aws/aws-sdk-js-v3/compare/v3.1150.0...v3.1151.0) (2026-10-13)': * **client-route-53-domains:** Route 53 Domains now supports premium domains. This release adds consent objects to operations on premium domains and a new GetDomainPrices API. Also, the Flags and PublicKey fields were deprecated from the DnssecKey response. ([c5cc6f5](https://github.com/aws/aws-sdk-js-v3/commit/c5cc6f506dc764122f7ed68d82cd178c94be068b)) _(keyword-classified from changelog; WARDEN verified the quote, not the semantics)_  
  locator `#[3.1151.0](https://github.com/aws/aws-sdk-js-v3/compare/v3.1150.0...v3.1151.0) (2026-10-13)` · c41e9a98 → 3ce8aa77

### openai
- **BREAKING** · Property removed from BetaResponseFunctionCallArgumentsDoneEvent: name  
  locator `/components/schemas/BetaResponseFunctionCallArgumentsDoneEvent/properties/name` · 2186421d → 5068a57f
- **BREAKING** · Property removed from CreateVoiceRequest: audio_sample  
  locator `/components/schemas/CreateVoiceRequest/properties/audio_sample` · 2186421d → 5068a57f
- **BREAKING** · Property removed from CreateVoiceRequest: consent  
  locator `/components/schemas/CreateVoiceRequest/properties/consent` · 2186421d → 5068a57f
- **BREAKING** · Property removed from CreateVoiceRequest: name  
  locator `/components/schemas/CreateVoiceRequest/properties/name` · 2186421d → 5068a57f
- **BREAKING** · Property removed from ResponseFunctionCallArgumentsDoneEvent: name  
  locator `/components/schemas/ResponseFunctionCallArgumentsDoneEvent/properties/name` · 2186421d → 5068a57f
- **BREAKING** · Enum values removed on VectorStoreFileBatchObject.object: ['vector_store.files_batch']  
  locator `/components/schemas/VectorStoreFileBatchObject/properties/object/enum` · 2186421d → 5068a57f
- **BREAKING** · Endpoint removed: POST /evals/{eval_id}/runs/{run_id}  
  locator `/paths/POST /evals/{eval_id}/runs/{run_id}` · 2186421d → 5068a57f
- **DEPRECATION** · Property deprecated on BetaMCPTool: connector_id  
  locator `/components/schemas/BetaMCPTool/properties/connector_id/deprecated` · 2186421d → 5068a57f
- **DEPRECATION** · Property deprecated on CreateImageEditRequest: response_format  
  locator `/components/schemas/CreateImageEditRequest/properties/response_format/deprecated` · 2186421d → 5068a57f
- **DEPRECATION** · Property deprecated on CreateImageRequest: response_format  
  locator `/components/schemas/CreateImageRequest/properties/response_format/deprecated` · 2186421d → 5068a57f
- **DEPRECATION** · Property deprecated on CreateImageRequest: style  
  locator `/components/schemas/CreateImageRequest/properties/style/deprecated` · 2186421d → 5068a57f
- **DEPRECATION** · Property deprecated on MCPTool: connector_id  
  locator `/components/schemas/MCPTool/properties/connector_id/deprecated` · 2186421d → 5068a57f
- **DEPRECATION** · Property deprecated on ProjectCreateRequest: geography  
  locator `/components/schemas/ProjectCreateRequest/properties/geography/deprecated` · 2186421d → 5068a57f
- **DEPRECATION** · Property deprecated on ProjectUpdateRequest: geography  
  locator `/components/schemas/ProjectUpdateRequest/properties/geography/deprecated` · 2186421d → 5068a57f
- **DEPRECATION** · Endpoint marked deprecated: POST /images/variations  
  locator `/paths/POST /images/variations/deprecated` · 2186421d → 5068a57f
- _162 additive changes (new endpoints/fields) — safe, omitted from brief; full list in findings.json_

### shopify-api-js
- **BREAKING** · New changelog section '14.0.1': - 8689457: Redact OAuth credentials from HTTP debug logs. The request body of OAuth token endpoint calls is no longer written to the debug log, and credential headers (`Authorization`, `Cookie`, `Set-Cookie`, `X-Shopify-Access-Token`, `Shopify-Storefront-Private-Token`, `X-Shopify-Storefront-Access-Token`) are replaced with `****` in API client debug logs. _(keyword-classified from changelog; WARDEN verified the quote, not the semantics)_  
  locator `#14.0.1` · e7654fc6 → 8868403d
- **BREAKING** · New changelog section '15.0.0': ### Major Changes | Shopify is dropping the `shopify-event-id` and `shopify-resource-id` headers from events deliveries, so the libraries no longer read them. Both fields are gone from the public types, which makes this a breaking change. | // eventId and resourceId are no longer set on events deliveries. _(keyword-classified from changelog; WARDEN verified the quote, not the semantics)_  
  locator `#15.0.0` · e7654fc6 → 8868403d
- **BREAKING** · New changelog section '15.0.1': - 79671d2: Set the `HttpOnly` flag on cookies by default, including the OAuth state and session cookies, so browser JavaScript can no longer read them. Pass `httpOnly: false` to opt out. Boolean cookie attributes are now written as flags, so `secure=true` is now just `secure`. _(keyword-classified from changelog; WARDEN verified the quote, not the semantics)_  
  locator `#15.0.1` · e7654fc6 → 8868403d

### stripe
- **BREAKING** · Schema removed: alma_installments  
  locator `/components/schemas/alma_installments` · af5309ca → bcfd59f4
- **BREAKING** · Property removed from bank_connections_resource_link_account_session_filters: countries  
  locator `/components/schemas/bank_connections_resource_link_account_session_filters/properties/countries` · af5309ca → bcfd59f4
- **BREAKING** · Schema removed: payment_method_details_konbini_store  
  locator `/components/schemas/payment_method_details_konbini_store` · af5309ca → bcfd59f4
- **BREAKING** · Property removed from payments_primitives_payment_records_resource_payment_method_card_details_resource_three_d_secure: cryptogram  
  locator `/components/schemas/payments_primitives_payment_records_resource_payment_method_card_details_resource_three_d_secure/properties/cryptogram` · af5309ca → bcfd59f4
- **BREAKING** · Request body field RENAMED on POST /v1/checkout/sessions: payment_method_types -> allowed_payment_method_types  
  locator `/paths/POST /v1/checkout/sessions/requestBody/properties/payment_method_types` · af5309ca → bcfd59f4
- **BREAKING** · Request body field removed on POST /v1/payment_intents: payment_method_types (successor already present: allowed_payment_method_types)  
  locator `/paths/POST /v1/payment_intents/requestBody/properties/payment_method_types` · af5309ca → bcfd59f4
- **BREAKING** · Request body field removed on POST /v1/payment_intents/{intent}/confirm: payment_method_types (successor already present: allowed_payment_method_types)  
  locator `/paths/POST /v1/payment_intents/{intent}/confirm/requestBody/properties/payment_method_types` · af5309ca → bcfd59f4
- **BREAKING** · Request body field removed on POST /v1/payment_intents/{intent}: payment_method_types (successor already present: allowed_payment_method_types)  
  locator `/paths/POST /v1/payment_intents/{intent}/requestBody/properties/payment_method_types` · af5309ca → bcfd59f4
- **BREAKING** · Request body field removed on POST /v1/payment_methods/{payment_method}: payto  
  locator `/paths/POST /v1/payment_methods/{payment_method}/requestBody/properties/payto` · af5309ca → bcfd59f4
- **BREAKING** · Request body field removed on POST /v1/setup_intents: payment_method_types (successor already present: allowed_payment_method_types)  
  locator `/paths/POST /v1/setup_intents/requestBody/properties/payment_method_types` · af5309ca → bcfd59f4
- **BREAKING** · Request body field removed on POST /v1/setup_intents/{intent}: payment_method_types (successor already present: allowed_payment_method_types)  
  locator `/paths/POST /v1/setup_intents/{intent}/requestBody/properties/payment_method_types` · af5309ca → bcfd59f4
- _23 additive changes (new endpoints/fields) — safe, omitted from brief; full list in findings.json_

### twilio
- **BREAKING** · Schema removed: whatsapp_sender_enum_status  
  locator `/components/schemas/whatsapp_sender_enum_status` · 591755b5 → 218b7821
- **BREAKING** · Schema removed: whatsapp_template_enum_category  
  locator `/components/schemas/whatsapp_template_enum_category` · 591755b5 → 218b7821

## VAULT ledger
- Trailing 30-day revenue: $0.00 (seed mode)
- Cycle compute cap: $25.00 (frontier sub-cap $15.00)
- Cycle compute spend: $0.0000
- Operating mode: **NORMAL**
