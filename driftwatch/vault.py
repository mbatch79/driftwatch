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
    if seed:
        total = cfg["revenue"]["seed_compute_allowance_per_cycle"]
        frontier = total * (cfg["compute"]["frontier_cap_pct_of_trailing_revenue"] / cfg["compute"]["total_cap_pct_of_trailing_revenue"])
    else:
        # weekly cycle: trailing-30-day caps scaled to a 7-day cycle
        total = rev * cfg["compute"]["total_cap_pct_of_trailing_revenue"] / 100 * 7 / 30
        frontier = rev * cfg["compute"]["frontier_cap_pct_of_trailing_revenue"] / 100 * 7 / 30
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


def mode(cycle_spend: float, warden_fail_pct: float) -> str:
    cfg = _cfg()
    b = cycle_budget()
    if warden_fail_pct > cfg["quality"]["warden_fail_rate_pause_pct"]:
        return "PAUSED_DELIVERY"
    if cycle_spend > cfg["compute"]["single_cycle_hard_cap_usd"]:
        return "KILLED"
    if not b["seed_mode"]:
        rev = b["trailing_revenue_usd"]
        if cycle_spend > rev * cfg["compute"]["hibernate_cap_pct_of_trailing_revenue"] / 100 * 7 / 30:
            return "HIBERNATE"
        if cycle_spend > b["cycle_total_cap_usd"]:
            return "DEGRADE"
    elif cycle_spend > b["cycle_total_cap_usd"]:
        return "DEGRADE"
    return "NORMAL"
