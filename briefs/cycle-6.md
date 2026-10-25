# Driftwatch — Cycle 6 Breaking-Change Brief
_Generated 2026-10-25 23:17 UTC · window 60 days · 27 verified findings (16 breaking, 0 deprecation, 11 additive) · 0 rejected by WARDEN_

## Coverage
| Source | File | Before (commit · date) | After (commit · date) | Changed? |
|---|---|---|---|---|
| stripe | `openapi/spec3.json` | `bcfd59f4` · 2026-09-29 | `bcfd59f4` · 2026-09-29 | no |
| openai | `openapi.json` | `f88d2f78` · 2026-10-18 | `8243cc8f` · 2026-10-24 | yes |
| twilio | `spec/json/twilio_api_v2010.json` | `157fb094` · 2026-10-06 | `157fb094` · 2026-10-06 | no |
| twilio | `spec/json/twilio_messaging_v1.json` | `218b7821` · 2026-09-28 | `218b7821` · 2026-09-28 | no |
| aws-sdk-js | `CHANGELOG.md` | `3ce8aa77` · 2026-10-14 | `163a566f` · 2026-10-22 | yes |
| shopify-api-js | `packages/apps/shopify-api/CHANGELOG.md` | `8868403d` · 2026-10-08 | `8868403d` · 2026-10-08 | no |

## Findings (WARDEN-verified)

### openai
- **BREAKING** · Property removed from DecisionInputMessage: content  
  locator `/components/schemas/DecisionInputMessage/properties/content` · introduced in `290bd01b` (2026-10-22)
- **BREAKING** · Property removed from DecisionInputMessage: phase  
  locator `/components/schemas/DecisionInputMessage/properties/phase` · introduced in `290bd01b` (2026-10-22)
- **BREAKING** · Property removed from DecisionInputMessage: role  
  locator `/components/schemas/DecisionInputMessage/properties/role` · introduced in `290bd01b` (2026-10-22)
- **BREAKING** · Property removed from DecisionInputMessage: type  
  locator `/components/schemas/DecisionInputMessage/properties/type` · introduced in `290bd01b` (2026-10-22)
- **BREAKING** · Property removed from LiveDecisionInputItemParam: content  
  locator `/components/schemas/LiveDecisionInputItemParam/properties/content` · introduced in `8243cc8f` (2026-10-24)
- **BREAKING** · Property removed from LiveDecisionInputItemParam: id  
  locator `/components/schemas/LiveDecisionInputItemParam/properties/id` · introduced in `8243cc8f` (2026-10-24)
- **BREAKING** · Property removed from LiveDecisionInputItemParam: role  
  locator `/components/schemas/LiveDecisionInputItemParam/properties/role` · introduced in `8243cc8f` (2026-10-24)
- **BREAKING** · Property removed from LiveDecisionInputItemParam: type  
  locator `/components/schemas/LiveDecisionInputItemParam/properties/type` · introduced in `8243cc8f` (2026-10-24)
- **BREAKING** · Schema removed: LiveDecisionQuestionsInputParam-2  
  locator `/components/schemas/LiveDecisionQuestionsInputParam-2` · introduced in `8243cc8f` (2026-10-24)
- **BREAKING** · Property removed from LiveDecisionStoredInputItemParam: content  
  locator `/components/schemas/LiveDecisionStoredInputItemParam/properties/content` · introduced in `8243cc8f` (2026-10-24)
- **BREAKING** · Property removed from LiveDecisionStoredInputItemParam: id  
  locator `/components/schemas/LiveDecisionStoredInputItemParam/properties/id` · introduced in `8243cc8f` (2026-10-24)
- **BREAKING** · Property removed from LiveDecisionStoredInputItemParam: role  
  locator `/components/schemas/LiveDecisionStoredInputItemParam/properties/role` · introduced in `8243cc8f` (2026-10-24)
- **BREAKING** · Property removed from LiveDecisionStoredInputItemParam: type  
  locator `/components/schemas/LiveDecisionStoredInputItemParam/properties/type` · introduced in `8243cc8f` (2026-10-24)
- **BREAKING** · Schema removed: LiveDecisionTriggerInputParam-2  
  locator `/components/schemas/LiveDecisionTriggerInputParam-2` · introduced in `8243cc8f` (2026-10-24)
- **BREAKING** · Schema removed: LiveDecisionsDelegationParam-2  
  locator `/components/schemas/LiveDecisionsDelegationParam-2` · introduced in `8243cc8f` (2026-10-24)
- **BREAKING** · Schema removed: LiveDecisionsSettingsInputParam-2  
  locator `/components/schemas/LiveDecisionsSettingsInputParam-2` · introduced in `8243cc8f` (2026-10-24)
- _11 additive changes (new endpoints/fields) — safe, omitted from brief; full list in findings.json_

## VAULT ledger
- Trailing 30-day revenue: $0.00 (seed mode)
- Cycle compute cap: $25.00 (frontier sub-cap $15.00)
- Cycle compute spend: $0.0000
- Operating mode: **NORMAL**
