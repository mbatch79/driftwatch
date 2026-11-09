# Driftwatch — Cycle 8 Breaking-Change Brief
_Generated 2026-11-09 00:55 UTC · window 60 days · 15 verified findings (1 breaking, 2 deprecation, 12 additive) · 0 rejected by WARDEN_

## Coverage
| Source | File | Before (commit · date) | After (commit · date) | Changed? |
|---|---|---|---|---|
| stripe | `openapi/spec3.json` | `bcfd59f4` · 2026-09-29 | `bcfd59f4` · 2026-09-29 | no |
| openai | `openapi.json` | `c2aecc2f` · 2026-10-31 | `926a7b81` · 2026-11-07 | yes |
| twilio | `spec/json/twilio_api_v2010.json` | `157fb094` · 2026-10-06 | `68913624` · 2026-11-05 | yes |
| twilio | `spec/json/twilio_messaging_v1.json` | `218b7821` · 2026-09-28 | `68913624` · 2026-11-05 | yes |
| aws-sdk-js | `CHANGELOG.md` | `258c1444` · 2026-10-30 | `ea82eac3` · 2026-11-06 | yes |
| shopify-api-js | `packages/apps/shopify-api/CHANGELOG.md` | `8868403d` · 2026-10-08 | `1db24d0b` · 2026-11-06 | yes |

## Findings (WARDEN-verified)

### aws-sdk-js
- **DEPRECATION** · New changelog section '[3.1162.0](https://github.com/aws/aws-sdk-js-v3/compare/v3.1161.0...v3.1162.0) (2026-11-04)': * **client-lookoutequipment:** Amazon Lookout for Equipment reached end of support on October 7, 2026. All Lookout for Equipment APIs are now marked as deprecated. ([9a4a688](https://github.com/aws/aws-sdk-js-v3/commit/9a4a6882371e75f079bd5bc25cacac31fb889a14)) _(keyword-classified from changelog; WARDEN verified the quote, not the semantics)_  
  locator `#[3.1162.0](https://github.com/aws/aws-sdk-js-v3/compare/v3.1161.0...v3.1162.0) (2026-11-04)` · introduced in `80cb7896` (2026-11-04)
- **DEPRECATION** · New changelog section '[3.1164.0](https://github.com/aws/aws-sdk-js-v3/compare/v3.1163.0...v3.1164.0) (2026-11-06)': * **client-ram:** Adds support for using managed permission template parameters, discovering shared customer-managed permissions, and managing customer-managed permission deprecation. ([87c5566](https://github.com/aws/aws-sdk-js-v3/commit/87c5566c7552538287647f1017cc580df9c756ba)) _(keyword-classified from changelog; WARDEN verified the quote, not the semantics)_  
  locator `#[3.1164.0](https://github.com/aws/aws-sdk-js-v3/compare/v3.1163.0...v3.1164.0) (2026-11-06)` · introduced in `ea82eac3` (2026-11-06)

### openai
- _12 additive changes (new endpoints/fields) — safe, omitted from brief; full list in findings.json_

### shopify-api-js
- **BREAKING** · New changelog section '15.1.1': Update `mongodb` to ^7.8.0 to fix CVE-2026-119179 and SRV host-name validation. MongoDB server 4.4 or newer is required. The driver no longer applies `timeoutMS` or `timeoutMode`; use per-stage timeouts instead. _(keyword-classified from changelog; WARDEN verified the quote, not the semantics)_  
  locator `#15.1.1` · introduced in `1db24d0b` (2026-11-06)

## VAULT ledger
- Trailing 30-day revenue: $0.00 (seed mode)
- Cycle compute cap: $25.00 (frontier sub-cap $15.00)
- Cycle compute spend: $0.0000
- Operating mode: **NORMAL**
