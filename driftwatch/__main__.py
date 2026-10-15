"""MARROW — orchestrates one cycle. Wakes agents in order, asks VAULT for budget,
refuses to ship if WARDEN's fail-rate trips the pause rule. Never resolves
a factual dispute itself; it only decides whether the cycle ships."""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

from . import scout, diff, warden, vault, quill, tree

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "briefs"


def _cycle_no() -> int:
    OUT.mkdir(exist_ok=True)
    return len(list(OUT.glob("cycle-*.md"))) + 1


def run_cycle(window_days: int = 60) -> int:
    t0 = time.time()
    cycle = _cycle_no()
    budget = vault.cycle_budget()
    print(f"[MARROW] cycle {cycle} · budget {budget}")

    pairs = scout.ingest(window_days)
    kinds = {s["id"]: s["diff_kind"] for s in scout.load_sources()}
    print(f"[SCOUT] {len(pairs)} file pairs snapshotted")

    findings = diff.run(pairs, kinds)
    print(f"[DIFF] {len(findings)} candidate findings")

    snaps = {(b.source_id, b.path): (b.file, a.file) for b, a in pairs}
    verdicts = warden.verify(findings, snaps, kinds)
    fr = warden.fail_rate(verdicts)
    print(f"[WARDEN] fail-rate {fr:.1f}%")

    # Cycle 1 is fully deterministic: no model tokens burned. Metered anyway.
    spend = vault.price("cheap", 0, 0)
    vault.record(cycle, {"agent": "all", "tier": "cheap", "tokens_in": 0, "tokens_out": 0,
                         "usd": spend, "wallclock_s": round(time.time() - t0, 1)})
    mode = vault.mode(spend, fr)
    print(f"[VAULT] spend ${spend:.4f} · mode {mode}")

    meta = {f"{b.source_id} · {Path(b.path).name}": {"path": b.path, "before": b.commit, "before_date": b.commit_date,
                          "after": a.commit, "after_date": a.commit_date, "changed": b.sha256 != a.sha256}
            for b, a in pairs}
    (OUT / f"cycle-{cycle}-findings.json").write_text(json.dumps(
        [{**v.finding.to_dict(), "verified": v.verified, "warden_reason": v.reason} for v in verdicts], indent=1))
    text = quill.brief(cycle, verdicts, budget, spend, mode, meta, window_days)
    if mode == "PAUSED_DELIVERY":
        text = "> DELIVERY PAUSED BY VAULT: WARDEN fail-rate over threshold. Brief retained, not shipped.\n\n" + text
    (OUT / f"cycle-{cycle}.md").write_text(text)
    print(f"[QUILL] wrote briefs/cycle-{cycle}.md")
    return cycle


def main(argv: list[str]):
    cmd = argv[1] if len(argv) > 1 else "cycle"
    if cmd == "lock":
        vault.lock(); print("[VAULT] locked")
    elif cmd == "budget":
        print(json.dumps(vault.cycle_budget(), indent=1))
    elif cmd == "revenue":
        # python -m driftwatch revenue 149.00 "dev seat #1"
        rec = {"ts": datetime.now(timezone.utc).isoformat(), "usd": float(argv[2]), "note": argv[3] if len(argv) > 3 else ""}
        with (ROOT / "ledger" / "revenue.jsonl").open("a") as f:
            f.write(json.dumps(rec) + "\n")
        print("[VAULT] revenue recorded")
    elif cmd == "cycle":
        run_cycle(int(argv[2]) if len(argv) > 2 else 60)
    elif cmd == "scan":
        # python -m driftwatch scan <repo_root> <findings.json>  — the lockfile scanner
        root, fj = Path(argv[2]), Path(argv[3])
        findings = json.loads(fj.read_text())
        vendors = tree.vendors_in_use(root)
        syms = sorted({s for f in findings for s in f["symbols"]})
        hits = tree.symbols_in_source(root, syms)
        scored = sorted(({**f, "score": tree.score(f, vendors, hits),
                          "usage": [h for s in f["symbols"] for h in hits.get(s, [])]} for f in findings if f["verified"]),
                        key=lambda f: -f["score"])
        print(json.dumps({"vendors_in_use": sorted(vendors), "findings": [f for f in scored if f["score"] > 0]}, indent=1))
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv)
