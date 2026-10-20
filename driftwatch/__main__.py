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

from . import scout, diff, warden, vault, quill, tree, attribute, report

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

    pairs = scout.ingest(window_days, incremental=True)
    kinds = {s["id"]: s["diff_kind"] for s in scout.load_sources()}
    n_inc = sum(1 for b, _ in pairs if f"{b.source_id}:{b.path}" in scout.watermarks())
    print(f"[SCOUT] {len(pairs)} file pairs snapshotted ({n_inc} incremental from watermark, {len(pairs)-n_inc} from {window_days}-day window)")

    findings = diff.run(pairs, kinds)
    print(f"[DIFF] {len(findings)} candidate findings")

    snaps = {(b.source_id, b.path): (b.file, a.file) for b, a in pairs}
    verdicts = warden.verify(findings, snaps, kinds)
    fr = warden.fail_rate(verdicts)

    # Pin each verified finding to the commit that actually introduced it, so a
    # reader who clicks through sees the change rather than a week-wide range.
    att = attribute.attribute([v.finding for v in verdicts if v.verified], pairs, kinds)
    for v in verdicts:
        f = v.finding
        sha, date = att.get((f.source_id, f.file, f.locator, f.kind), ("", ""))
        f.intro_commit, f.intro_date = sha, date
    n_att = sum(1 for v in verdicts if v.verified and v.finding.intro_commit)
    n_ver = sum(1 for v in verdicts if v.verified)
    print(f"[ATTRIBUTE] {n_att}/{n_ver} verified findings pinned to an exact commit")
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

    if mode != "PAUSED_DELIVERY":
        # Public feed the GitHub Action reads: cumulative verified findings, newest cycle first.
        feed = ROOT / "feed" / "latest"
        feed.mkdir(parents=True, exist_ok=True)
        prev = json.loads((feed / "findings.json").read_text()) if (feed / "findings.json").exists() else []
        fresh = [{**v.finding.to_dict(), "verified": True, "cycle": cycle} for v in verdicts if v.verified]
        seen = {(f["source_id"], f["locator"], f["kind"]) for f in fresh}
        keep = [f for f in prev if (f["source_id"], f["locator"], f["kind"]) not in seen and f.get("cycle", 0) > cycle - 9]
        (feed / "findings.json").write_text(json.dumps(fresh + keep, indent=1))
        (feed / "brief.md").write_text(text)
        scout.save_watermarks(pairs)
        print(f"[MARROW] feed published ({len(fresh)} new, {len(keep)} carried) · watermarks advanced")
    else:
        print("[MARROW] delivery paused — feed and watermarks NOT advanced; next cycle re-diffs the same range")
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
    elif cmd == "backfill":
        # Rebuild the public feed and report over a full window, with commit attribution.
        # Does not touch watermarks: the weekly cycle keeps running incrementally.
        days = int(argv[2]) if len(argv) > 2 else 60
        pairs = scout.ingest(days, incremental=False)
        kinds = {s["id"]: s["diff_kind"] for s in scout.load_sources()}
        F = diff.run(pairs, kinds)
        snaps = {(b.source_id, b.path): (b.file, a.file) for b, a in pairs}
        V = warden.verify(F, snaps, kinds)
        ok = [v.finding for v in V if v.verified]
        att = attribute.attribute(ok, pairs, kinds)
        for f in ok:
            f.intro_commit, f.intro_date = att.get((f.source_id, f.file, f.locator, f.kind), ("", ""))
        cyc = len(list(OUT.glob("cycle-*.md"))) if OUT.exists() else 1
        rows = [{**f.to_dict(), "verified": True, "cycle": cyc} for f in ok]
        # Merge, don't replace: weekly cycles catch changes that happen and reverse
        # inside the window, which an endpoint-to-endpoint comparison cannot see.
        feed = ROOT / "feed" / "latest"; feed.mkdir(parents=True, exist_ok=True)
        prev = json.loads((feed / "findings.json").read_text()) if (feed / "findings.json").exists() else []
        seen = {(r["source_id"], r["file"], r["locator"], r["kind"]) for r in rows}
        kept = 0
        for r in prev:
            k = (r["source_id"], r.get("file", ""), r["locator"], r["kind"])
            if k in seen:
                continue
            if not r.get("intro_commit"):
                sha, date = attribute.attribute_record(r)
                r["intro_commit"], r["intro_date"] = sha, date
            rows.append(r); seen.add(k); kept += 1
        print(f"[BACKFILL] merged {kept} findings from earlier cycles")
        (feed / "findings.json").write_text(json.dumps(rows, indent=1))
        dates = sorted(f.intro_date[:10] for f in ok if f.intro_date)
        window = f"{dates[0]} to {dates[-1]}" if dates else f"last {days} days"
        out = report.build(rows, window, ROOT / "docs" / "reports" / "2026-10-breaking-changes.html")
        print(f"[BACKFILL] {len(ok)} verified · {sum(1 for f in ok if f.intro_commit)} pinned to a commit")
        print(f"[BACKFILL] wrote feed/latest/findings.json and {out.relative_to(ROOT)}")
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
