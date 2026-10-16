"""VAULT — treasury. Enforces config/vault.yaml. Computes the cycle's compute
budget from trailing revenue, meters spend, and decides the operating mode.
Other agents ask VAULT for budget; they never set it."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CFG = ROOT / "config" / "vault.yaml"
LEDGER = ROOT / "ledger"
LOCK = LEDGER / "vault.lock"


class VaultError(RuntimeError):
    pass


def _cfg() -> dict:
    LEDGER.mkdir(exist_ok=True)
    digest = hashlib.sha256(CFG.read_bytes()).hexdigest()
    if LOCK.exists() and LOCK.read_text().strip() != digest:
        raise VaultError("vault.yaml changed without re-locking. Refusing to run. Human must `python -m driftwatch lock`.")
    return yaml.safe_load(CFG.read_text())


def lock():
    LEDGER.mkdir(exist_ok=True)
    LOCK.write_text(hashlib.sha256(CFG.read_bytes()).hexdigest())


def trailing_revenue() -> float:
    f = LEDGER / "revenue.jsonl"
    if not f.exists():
        return 0.0
    cfg = _cfg()
    cutoff = datetime.now(timezone.utc).timestamp() - cfg["revenue"]["trailing_window_days"] * 86400
    return sum(r["usd"] for r in map(json.loads, f.read_text().splitlines())
               if datetime.fromisoformat(r["ts"]).timestamp() >= cutoff)


def cycle_budget() -> dict:
    cfg = _cfg()
    rev = trailing_revenue()
    seed = rev < cfg["revenue"]["seed_floor"]
    # Weekly cycle: trailing-30-day caps scaled to a 7-day cycle. The seed allowance is a
    # FLOOR while revenue is below seed_floor (so the swarm can run before customers exist),
    # never a ceiling on top of real revenue — audit of the 20-cycle model showed a week with
    # 11 new seats booked tripping DEGRADE purely on onboarding compute. (Cycle 2 fix.)
    rev_total = rev * cfg["compute"]["total_cap_pct_of_trailing_revenue"] / 100 * 7 / 30
    rev_frontier = rev * cfg["compute"]["frontier_cap_pct_of_trailing_revenue"] / 100 * 7 / 30
    if seed:
        seed_total = cfg["revenue"]["seed_compute_allowance_per_cycle"]
        total = max(seed_total, rev_total)
        frontier = max(seed_total * (cfg["compute"]["frontier_cap_pct_of_trailing_revenue"] / cfg["compute"]["total_cap_pct_of_trailing_revenue"]), rev_frontier)
    else:
        total, frontier = rev_total, rev_frontier
    total = min(total, cfg["compute"]["single_cycle_hard_cap_usd"])
    return {"trailing_revenue_usd": round(rev, 2), "seed_mode": seed,
            "cycle_total_cap_usd": round(total, 2), "cycle_frontier_cap_usd": round(frontier, 2)}


def price(tier: str, tokens_in: int, tokens_out: int) -> float:
    p = _cfg()["compute"]["prices"][tier]
    return tokens_in / 1e6 * p["input"] + tokens_out / 1e6 * p["output"]


def record(cycle: int, entry: dict):
    f = LEDGER / "compute.jsonl"
    entry = {"ts": datetime.now(timezone.utc).isoformat(), "cycle": cycle, **entry}
    with f.open("a") as fh:
        fh.write(json.dumps(entry) + "\n")


def trailing_compute() -> float:
    f = LEDGER / "compute.jsonl"
    if not f.exists():
        return 0.0
    cutoff = datetime.now(timezone.utc).timestamp() - _cfg()["revenue"]["trailing_window_days"] * 86400
    return sum(r["usd"] for r in map(json.loads, f.read_text().splitlines())
               if datetime.fromisoformat(r["ts"]).timestamp() >= cutoff)


def mode(cycle_spend: float, warden_fail_pct: float) -> str:
    """Burn is judged on the trailing window, not one cycle, so a lumpy onboarding week
    doesn't trip DEGRADE while the seats it onboarded are paying. The single-cycle hard
    cap still kills a runaway cycle outright."""
    cfg = _cfg()
    b = cycle_budget()
    if warden_fail_pct > cfg["quality"]["warden_fail_rate_pause_pct"]:
        return "PAUSED_DELIVERY"
    if cycle_spend > cfg["compute"]["single_cycle_hard_cap_usd"]:
        return "KILLED"
    rev = b["trailing_revenue_usd"]
    burn = trailing_compute()  # includes this cycle once recorded
    floor = cfg["revenue"]["seed_compute_allowance_per_cycle"] * 4 if b["seed_mode"] else 0.0
    if burn > max(floor, rev * cfg["compute"]["hibernate_cap_pct_of_trailing_revenue"] / 100):
        return "HIBERNATE"
    if burn > max(floor, rev * cfg["compute"]["total_cap_pct_of_trailing_revenue"] / 100):
        return "DEGRADE"
    return "NORMAL"
