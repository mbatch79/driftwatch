"""HUSTLE × VAULT — 20-cycle conversion model and treasury audit.

Simulates the funnel GitHub Action installs → Dev ($149) → Ops ($499) week by week,
then runs VAULT's real rules (vault.yaml) over the resulting revenue/compute so we can
see when the swarm leaves seed mode, when it could degrade, and what margin looks like.

EVERY NUMBER BELOW IS AN ASSUMPTION until ledger/revenue.jsonl has real rows. The point
of running it now is to know which assumption the business is most sensitive to, and to
have the audit harness ready so real data replaces the guesses cycle by cycle.
"""
from __future__ import annotations

import json
import random
from dataclasses import dataclass, asdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CFG = yaml.safe_load((ROOT / "config" / "vault.yaml").read_text())


@dataclass
class Assumptions:
    # Top of funnel: weekly new Action installs. Launch spike, decay to a steady trickle, content bumps.
    launch_installs: int = 120          # week 1 (HN / r/webdev / newsletter post)
    steady_installs: int = 18           # per week after decay
    decay_weeks: int = 4
    content_bump_every: int = 4         # a published brief/report every N weeks
    content_bump_installs: int = 45
    # Materiality gate: share of installs whose first scan actually flags something (score >= 70).
    # Below this the Action is just a green tick; conversion from a green tick is ~0.
    flag_rate: float = 0.35
    # Conversion of FLAGGED installs to Dev within 3 weeks. Flagged users have felt the pain.
    flagged_to_dev: float = 0.12
    unflagged_to_dev: float = 0.01
    conv_lag_weeks: int = 2
    # Dev -> Ops upgrade (teams needing walled sources / compliance / audit log)
    dev_to_ops_weekly: float = 0.02
    # Churn (monthly, converted to weekly)
    dev_churn_monthly: float = 0.06
    ops_churn_monthly: float = 0.03
    # Prices
    dev_price: float = 149.0
    ops_price: float = 499.0
    stripe_fee_pct: float = 0.029
    stripe_fee_fixed: float = 0.30
    # Compute (USD / customer / week). Clean sources are deterministic; the model cost is
    # WARDEN/QUILL on *scored* findings only + onboarding tree build.
    dev_compute_weekly: float = 0.90
    ops_compute_weekly: float = 6.50     # walled sources: headless + proxy + more model calls
    onboarding_compute: float = 2.50     # one-off per new seat (tree build)
    fixed_infra_weekly: float = 28.0     # hosting, proxy pool, email, monitoring
    seed: int = 7


def simulate(a: Assumptions, weeks: int = 20) -> list[dict]:
    rng = random.Random(a.seed)
    dev = ops = 0
    pending: list[tuple[int, int]] = []   # (week_due, conversions)
    rows = []
    cum_installs = cum_rev = cum_cost = 0.0
    for w in range(1, weeks + 1):
        installs = a.launch_installs if w == 1 else max(a.steady_installs,
                   int(a.launch_installs * (0.45 ** (w - 1)))) if w <= a.decay_weeks else a.steady_installs
        if w > 1 and w % a.content_bump_every == 0:
            installs += a.content_bump_installs
        installs = max(0, int(rng.gauss(installs, installs * 0.15)))
        cum_installs += installs
        flagged = sum(1 for _ in range(installs) if rng.random() < a.flag_rate)
        conv = sum(1 for _ in range(flagged) if rng.random() < a.flagged_to_dev) + \
               sum(1 for _ in range(installs - flagged) if rng.random() < a.unflagged_to_dev)
        pending.append((w + a.conv_lag_weeks, conv))
        new_dev = sum(c for due, c in pending if due == w)
        upgrades = sum(1 for _ in range(dev) if rng.random() < a.dev_to_ops_weekly)
        dev_churn = sum(1 for _ in range(dev) if rng.random() < a.dev_churn_monthly / 4.33)
        ops_churn = sum(1 for _ in range(ops) if rng.random() < a.ops_churn_monthly / 4.33)
        dev = max(0, dev + new_dev - upgrades - dev_churn)
        ops = max(0, ops + upgrades - ops_churn)
        gross = (dev * a.dev_price + ops * a.ops_price) / 4.33
        fees = gross * a.stripe_fee_pct + (dev + ops) / 4.33 * a.stripe_fee_fixed
        compute = dev * a.dev_compute_weekly + ops * a.ops_compute_weekly + (new_dev + upgrades) * a.onboarding_compute
        cost = compute + a.fixed_infra_weekly
        cum_rev += gross - fees
        cum_cost += cost
        rows.append(dict(week=w, installs=installs, flagged=flagged, new_dev=new_dev, upgrades=upgrades,
                         dev_churn=dev_churn, ops_churn=ops_churn, dev=dev, ops=ops,
                         mrr=round(dev * a.dev_price + ops * a.ops_price, 2),
                         weekly_net_rev=round(gross - fees, 2), compute=round(compute, 2), cost=round(cost, 2),
                         cum_installs=int(cum_installs), cum_net_rev=round(cum_rev, 2), cum_cost=round(cum_cost, 2)))
    return rows


def vault_audit(rows: list[dict]) -> list[dict]:
    """Apply the real vault.yaml rules to the simulated ledger, week by week."""
    c = CFG["compute"]; r = CFG["revenue"]
    out = []
    degrade_streak = 0
    for i, row in enumerate(rows):
        trailing = sum(x["weekly_net_rev"] for x in rows[max(0, i - 3):i + 1])   # ~30 days = 4 cycles
        seed = trailing < r["seed_floor"]
        rev_cap = trailing * c["total_cap_pct_of_trailing_revenue"] / 100 * 7 / 30
        cap = max(r["seed_compute_allowance_per_cycle"], rev_cap) if seed else rev_cap
        cap = min(cap, c["single_cycle_hard_cap_usd"])
        hib = None if seed else trailing * c["hibernate_cap_pct_of_trailing_revenue"] / 100 * 7 / 30
        spend = row["compute"]
        burn = sum(x["compute"] for x in rows[max(0, i - 3):i + 1])   # trailing 4 cycles
        floor = r["seed_compute_allowance_per_cycle"] * 4 if seed else 0.0
        if spend > c["single_cycle_hard_cap_usd"]:
            mode = "KILLED"
        elif burn > max(floor, trailing * c["hibernate_cap_pct_of_trailing_revenue"] / 100):
            mode = "HIBERNATE"
        elif burn > max(floor, trailing * c["total_cap_pct_of_trailing_revenue"] / 100):
            mode = "DEGRADE"
        else:
            mode = "NORMAL"
        prev = rows[i - 1]["weekly_net_rev"] if i else 0
        if prev and (row["weekly_net_rev"] - prev) / prev < -CFG["revenue_shock"]["hibernate_if_wow_drop_pct"] / 100:
            mode = "HIBERNATE"
        out.append(dict(week=row["week"], trailing_rev=round(trailing, 2), seed_mode=seed,
                        cycle_cap=round(cap, 2), compute=spend, trailing_burn=round(burn, 2),
                        burn_pct_of_trailing=round(100 * burn / trailing, 1) if trailing else None,
                        mode=mode, margin=round(row["weekly_net_rev"] - row["cost"], 2)))
    return out


def sensitivity(base: Assumptions, weeks: int = 20) -> list[dict]:
    """Which assumption moves week-20 MRR the most? ±40% on each, holding the rest."""
    keys = ["launch_installs", "steady_installs", "flag_rate", "flagged_to_dev", "dev_to_ops_weekly",
            "dev_churn_monthly", "content_bump_installs"]
    base_mrr = simulate(base, weeks)[-1]["mrr"]
    out = []
    for k in keys:
        lo, hi = dict(asdict(base)), dict(asdict(base))
        v = getattr(base, k)
        lo[k] = type(v)(v * 0.6); hi[k] = type(v)(v * 1.4)
        if isinstance(v, float) and hi[k] > 1: hi[k] = 1.0
        m_lo = simulate(Assumptions(**lo), weeks)[-1]["mrr"]
        m_hi = simulate(Assumptions(**hi), weeks)[-1]["mrr"]
        out.append(dict(assumption=k, base=v, mrr_at_minus40=m_lo, mrr_base=base_mrr, mrr_at_plus40=m_hi,
                        swing=round(m_hi - m_lo, 2)))
    return sorted(out, key=lambda d: -abs(d["swing"]))


def monte_carlo(base: Assumptions, weeks: int = 20, runs: int = 300) -> dict:
    """Same assumptions, different dice. Reports p10/p50/p90 of week-20 MRR, seats, and
    how often VAULT ever leaves NORMAL — so the single-seed table isn't mistaken for a forecast."""
    mrr, dev, ops, cum, nonnormal = [], [], [], [], 0
    for s in range(runs):
        rows = simulate(Assumptions(**{**asdict(base), "seed": s}), weeks)
        aud = vault_audit(rows)
        mrr.append(rows[-1]["mrr"]); dev.append(rows[-1]["dev"]); ops.append(rows[-1]["ops"]); cum.append(rows[-1]["cum_net_rev"])
        nonnormal += any(a["mode"] != "NORMAL" for a in aud)
    q = lambda xs, p: sorted(xs)[int(p * (len(xs) - 1))]
    return {"runs": runs,
            "week20_mrr": {"p10": q(mrr, .1), "p50": q(mrr, .5), "p90": q(mrr, .9)},
            "week20_dev_seats": {"p10": q(dev, .1), "p50": q(dev, .5), "p90": q(dev, .9)},
            "week20_ops_seats": {"p10": q(ops, .1), "p50": q(ops, .5), "p90": q(ops, .9)},
            "cum_net_rev_20wk": {"p10": q(cum, .1), "p50": q(cum, .5), "p90": q(cum, .9)},
            "pct_runs_vault_ever_non_normal": round(100 * nonnormal / runs, 1)}


def run(out_dir: Path, weeks: int = 20) -> dict:
    a = Assumptions()
    rows = simulate(a, weeks)
    audit = vault_audit(rows)
    sens = sensitivity(a, weeks)
    mc = monte_carlo(a, weeks)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "assumptions.json").write_text(json.dumps(asdict(a), indent=1))
    (out_dir / "cycles.json").write_text(json.dumps(rows, indent=1))
    (out_dir / "vault_audit.json").write_text(json.dumps(audit, indent=1))
    (out_dir / "sensitivity.json").write_text(json.dumps(sens, indent=1))
    (out_dir / "monte_carlo.json").write_text(json.dumps(mc, indent=1))
    return {"assumptions": asdict(a), "rows": rows, "audit": audit, "sensitivity": sens, "monte_carlo": mc}
