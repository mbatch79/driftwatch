# Driftwatch — Cycle 7 Breaking-Change Brief
_Generated 2026-11-02 00:45 UTC · window 60 days · 7 verified findings (1 breaking, 1 deprecation, 5 additive) · 0 rejected by WARDEN_

## Coverage
| Source | File | Before (commit · date) | After (commit · date) | Changed? |
|---|---|---|---|---|
| stripe | `openapi/spec3.json` | `bcfd59f4` · 2026-09-29 | `bcfd59f4` · 2026-09-29 | no |
| openai | `openapi.json` | `8243cc8f` · 2026-10-24 | `c2aecc2f` · 2026-10-31 | yes |
| twilio | `spec/json/twilio_api_v2010.json` | `157fb094` · 2026-10-06 | `157fb094` · 2026-10-06 | no |
| twilio | `spec/json/twilio_messaging_v1.json` | `218b7821` · 2026-09-28 | `218b7821` · 2026-09-28 | no |
| aws-sdk-js | `CHANGELOG.md` | `163a566f` · 2026-10-22 | `258c1444` · 2026-10-30 | yes |
| shopify-api-js | `packages/apps/shopify-api/CHANGELOG.md` | `8868403d` · 2026-10-08 | `8868403d` · 2026-10-08 | no |

## Findings (WARDEN-verified)

### openai
- **BREAKING** · Schema RENAMED: LiveTransportDTMFSend -> LiveTransportDTMFSendParam  
  locator `/components/schemas/LiveTransportDTMFSend` · introduced in `cfe1bd3d` (2026-10-28)
- **DEPRECATION** · Endpoint marked deprecated: POST /audio/translations  
  locator `/paths/POST /audio/translations/deprecated` · introduced in `ff80a233` (2026-10-28)
- _5 additive changes (new endpoints/fields) — safe, omitted from brief; full list in findings.json_

## VAULT ledger
- Trailing 30-day revenue: $0.00 (seed mode)
- Cycle compute cap: $25.00 (frontier sub-cap $15.00)
- Cycle compute spend: $0.0000
- Operating mode: **NORMAL**
