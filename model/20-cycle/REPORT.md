# Driftwatch — 20-Cycle Conversion Model & VAULT Audit

**Status: every input is an assumption.** `ledger/revenue.jsonl` has one real row's worth of history (Cycle 1–2). This model exists to (a) find which assumption the business is most sensitive to, and (b) prove VAULT's rules behave under a plausible ramp before real money is on the line. Replace assumptions with ledger data cycle by cycle.

## Monte Carlo (300 runs, same assumptions, different dice)

| Metric | p10 | p50 | p90 |
|---|---|---|---|
| Week-20 MRR | $3,978 | $5,475 | $7,367 |
| Dev seats | 16 | 22 | 27 |
| Ops seats | 2 | 4 | 8 |
| Cumulative net revenue (20 wk) | $9,549 | $12,832 | $17,411 |
| Runs where VAULT ever left NORMAL | 0.0% | | |

## Sensitivity — what moves week-20 MRR (±40% on each assumption, single seed)

| Assumption | Base | −40% | +40% | Swing |
|---|---|---|---|---|
| `flag_rate` | 0.35 | $3,181 | $10,808 | $7,627 |
| `flagged_to_dev` | 0.12 | $3,829 | $9,155 | $5,326 |
| `dev_to_ops_weekly` | 0.02 | $6,764 | $8,767 | $2,003 |
| `content_bump_installs` | 45 | $9,162 | $8,015 | $-1,147 |
| `steady_installs` | 18 | $7,419 | $8,462 | $1,043 |
| `dev_churn_monthly` | 0.06 | $7,166 | $8,067 | $901 |
| `launch_installs` | 120 | $7,516 | $6,719 | $-797 |

**Reading:** `flag_rate` (share of Action installs whose first scan actually flags something) dominates, with `flagged_to_dev` second. Install volume barely matters. The business is a materiality business, not a traffic business — which is the thesis. The lever is the scanner catching real hits on real repos, not more HN posts.

## Week-by-week (seed 7)

| Wk | Installs | Flagged | +Dev | Dev | Ops | MRR | Net/wk | Compute | Trailing rev | Burn % | Mode |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 115 | 41 | 0 | 0 | 0 | $0 | $0 | $0.0 | $0 | — | NORMAL (seed) |
| 2 | 58 | 15 | 0 | 0 | 0 | $0 | $0 | $0.0 | $0 | — | NORMAL (seed) |
| 3 | 31 | 19 | 11 | 11 | 0 | $1,639 | $367 | $37.4 | $367 | 10.2 | NORMAL (seed) |
| 4 | 72 | 24 | 2 | 13 | 0 | $1,937 | $433 | $16.7 | $800 | 6.8 | NORMAL |
| 5 | 21 | 9 | 2 | 14 | 0 | $2,086 | $467 | $17.6 | $1,267 | 5.7 | NORMAL |
| 6 | 16 | 4 | 6 | 20 | 0 | $2,980 | $667 | $33.0 | $1,934 | 5.4 | NORMAL |
| 7 | 20 | 10 | 0 | 19 | 0 | $2,831 | $634 | $17.1 | $2,201 | 3.8 | NORMAL |
| 8 | 61 | 22 | 0 | 18 | 1 | $3,181 | $712 | $25.2 | $2,479 | 3.7 | NORMAL |
| 9 | 18 | 7 | 2 | 20 | 1 | $3,479 | $779 | $29.5 | $2,791 | 3.8 | NORMAL |
| 10 | 16 | 7 | 5 | 22 | 3 | $4,775 | $1,069 | $56.8 | $3,193 | 4.0 | NORMAL |
| 11 | 15 | 5 | 1 | 23 | 3 | $4,924 | $1,102 | $42.7 | $3,662 | 4.2 | NORMAL |
| 12 | 59 | 26 | 1 | 24 | 3 | $5,073 | $1,136 | $43.6 | $4,086 | 4.2 | NORMAL |
| 13 | 18 | 3 | 1 | 24 | 4 | $5,572 | $1,248 | $52.6 | $4,555 | 4.3 | NORMAL |
| 14 | 13 | 5 | 5 | 28 | 4 | $6,168 | $1,381 | $63.7 | $4,867 | 4.2 | NORMAL |
| 15 | 12 | 3 | 0 | 27 | 5 | $6,518 | $1,459 | $59.3 | $5,224 | 4.2 | NORMAL |
| 16 | 64 | 24 | 1 | 28 | 5 | $6,667 | $1,493 | $60.2 | $5,581 | 4.2 | NORMAL |
| 17 | 19 | 11 | 0 | 27 | 5 | $6,518 | $1,459 | $56.8 | $5,793 | 4.1 | NORMAL |
| 18 | 18 | 7 | 2 | 28 | 6 | $7,166 | $1,605 | $71.7 | $6,016 | 4.1 | NORMAL |
| 19 | 24 | 7 | 1 | 27 | 7 | $7,516 | $1,683 | $74.8 | $6,240 | 4.2 | NORMAL |
| 20 | 57 | 11 | 1 | 27 | 8 | $8,015 | $1,795 | $81.3 | $6,542 | 4.4 | NORMAL |

## VAULT audit findings (rules changed as a result)

1. **Per-cycle burn cap punished onboarding.** First run tripped DEGRADE in week 3: 11 seats booked $1,639 MRR, and the one-off tree-build compute ($37) blew the $25 seed cap. The pitch said *burn > 25% of trailing revenue*; the code enforced it per cycle. **Fixed:** `vault.mode()` now compares trailing-30-day compute to trailing-30-day revenue; the single-cycle $200 hard cap still kills a runaway.
2. **Seed allowance was a ceiling.** Once any revenue exists the seed allowance is now a floor under the revenue-derived cap, not a replacement for it.
3. After both fixes: 0 of 300 runs leave NORMAL. Steady-state burn settles at ~4% of trailing revenue — the 15% frontier sub-cap has headroom for a model-backed WARDEN later without touching the rules.

## Assumptions (edit `model.py::Assumptions`)

```json
{
 "launch_installs": 120,
 "steady_installs": 18,
 "decay_weeks": 4,
 "content_bump_every": 4,
 "content_bump_installs": 45,
 "flag_rate": 0.35,
 "flagged_to_dev": 0.12,
 "unflagged_to_dev": 0.01,
 "conv_lag_weeks": 2,
 "dev_to_ops_weekly": 0.02,
 "dev_churn_monthly": 0.06,
 "ops_churn_monthly": 0.03,
 "dev_price": 149.0,
 "ops_price": 499.0,
 "stripe_fee_pct": 0.029,
 "stripe_fee_fixed": 0.3,
 "dev_compute_weekly": 0.9,
 "ops_compute_weekly": 6.5,
 "onboarding_compute": 2.5,
 "fixed_infra_weekly": 28.0,
 "seed": 7
}
```