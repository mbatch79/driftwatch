# Driftwatch

**Dependency-aware breaking-change intelligence.** Watches the machine-readable specs of the APIs you depend on, diffs every version, verifies every finding against source, and scores it by whether *your* code actually touches it.

## Swarm

| Agent | Module | Job | Veto |
|---|---|---|---|
| SCOUT | `scout.py` | Blobless git mirror of each vendor spec; snapshot at two dates; extract-then-hash | — |
| DIFF | `diff.py` | Structural OpenAPI diff + changelog section diff; classifies BREAKING / DEPRECATION / ADDITIVE with a locator | — |
| WARDEN | `warden.py` | Re-verifies every finding from its locator alone; fail-rate > 10% pauses delivery | facts |
| QUILL | `quill.py` | Templated brief (no model call in Cycle 1) | — |
| VAULT | `vault.py` + `config/vault.yaml` | Budget from trailing revenue; degrade / hibernate / kill rules; config is hash-locked | spend |
| MARROW | `__main__.py` | Runs the cycle; ships only if WARDEN and VAULT both clear | — |
| tree | `tree.py` | Reads customer lockfile + source; grep-matches changed symbols → materiality score | — |

## Run

```
python -m driftwatch lock            # human: lock vault.yaml after any edit
python -m driftwatch budget          # what this cycle may spend
python -m driftwatch cycle 60        # ingest 60 days, diff, verify, brief -> briefs/cycle-N.md
python -m driftwatch revenue 229 "dev seat"   # record booked revenue (feeds the budget)
python -m driftwatch scan <repo> briefs/cycle-N-findings.json   # lockfile scanner (what the GitHub Action runs)
```

## Known limits (Cycle 1)
- Changelog findings are keyword-classified. WARDEN verifies the quoted line exists in the new section; it does not judge semantics. The dependency-tree score is what kills the noise.
- OpenAPI diff covers endpoints, params, request-body props, success-response shape ($ref swap, inline field removed/retyped), schema props, types, enums, deprecation flags. Nested response shapes beyond one $ref level ride on the components/schemas pass.
- Only `tier: clean` (git-hosted) sources run. Bot-walled docs sites are out of scope until priced into Ops tier.
- OpenAI's `openapi.json` on `main` moves daily; Stripe's `spec3.json` tracks the latest API version, so a removal there means "gone in the newest version", not necessarily in pinned older versions.

## Weekly cadence
`.github/workflows/cycle.yml` runs one cycle every Sunday 21:17 UTC (Mon 08:17 Melbourne) on GitHub's runners, commits `briefs/`, `feed/`, `ledger/` back, and opens a `vault`-labelled issue if the cycle ends in anything but NORMAL. Manual runs via *workflow_dispatch*. Requires the repo to live at `mbatch79/driftwatch` (the Action's default feed URL points there).

## GitHub Action
`action/action.yml` — drop into a repo; it fetches the latest public `findings.json`, scans the lockfile and source, and writes a job summary of breaking changes that touch that repo. The Dev tier is the upgrade path.

## Entity
Operated by Re-Batch Studio (Simpel Pty Ltd, ABN 44 103 034 797), ACN 103 034 797 — Sale, Victoria, Australia. Business name registered with ASIC 18 Oct 2026.
