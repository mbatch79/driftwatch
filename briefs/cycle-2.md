# Driftwatch — Cycle 2 Breaking-Change Brief
_Generated 2026-10-16 08:20 UTC · window 60 days · 3 verified findings (0 breaking, 3 deprecation, 0 additive) · 0 rejected by WARDEN_

## Coverage
| Source | File | Before (commit · date) | After (commit · date) | Changed? |
|---|---|---|---|---|
| stripe | `openapi/spec3.json` | `bcfd59f4` · 2026-09-29 | `bcfd59f4` · 2026-09-29 | no |
| openai | `openapi.json` | `5068a57f` · 2026-10-15 | `5bdf71b6` · 2026-10-16 | yes |
| twilio | `spec/json/twilio_api_v2010.json` | `157fb094` · 2026-10-06 | `157fb094` · 2026-10-06 | no |
| twilio | `spec/json/twilio_messaging_v1.json` | `218b7821` · 2026-09-28 | `218b7821` · 2026-09-28 | no |
| aws-sdk-js | `CHANGELOG.md` | `3ce8aa77` · 2026-10-14 | `3ce8aa77` · 2026-10-14 | no |
| shopify-api-js | `packages/apps/shopify-api/CHANGELOG.md` | `8868403d` · 2026-10-08 | `8868403d` · 2026-10-08 | no |

## Findings (WARDEN-verified)

### openai
- **DEPRECATION** · Property deprecated on CreateImageEditRequest: user  
  locator `/components/schemas/CreateImageEditRequest/properties/user/deprecated` · 5068a57f → 5bdf71b6
- **DEPRECATION** · Property deprecated on CreateImageRequest: user  
  locator `/components/schemas/CreateImageRequest/properties/user/deprecated` · 5068a57f → 5bdf71b6
- **DEPRECATION** · Property deprecated on EditImageBodyJsonParam: user  
  locator `/components/schemas/EditImageBodyJsonParam/properties/user/deprecated` · 5068a57f → 5bdf71b6

## VAULT ledger
- Trailing 30-day revenue: $0.00 (seed mode)
- Cycle compute cap: $25.00 (frontier sub-cap $15.00)
- Cycle compute spend: $0.0000
- Operating mode: **NORMAL**
