"""QUILL — writes the brief. Templated in Cycle 1: no model call, so no
hallucination surface. Every line carries its locator and both commits."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone

from .warden import Verdict


def brief(cycle: int, verdicts: list[Verdict], budget: dict, spend: float, mode: str,
          snaps_meta: dict[str, dict], window_days: int) -> str:
    ok = [v for v in verdicts if v.verified]
    rej = [v for v in verdicts if not v.verified]
    by_src: dict[str, list[Verdict]] = defaultdict(list)
    for v in ok:
        by_src[v.finding.source_id].append(v)

    sev_order = {"BREAKING": 0, "DEPRECATION": 1, "ADDITIVE": 2}
    n = lambda s: sum(1 for v in ok if v.finding.severity == s)
    L = [f"# Driftwatch — Cycle {cycle} Breaking-Change Brief",
         f"_Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC · window {window_days} days · "
         f"{len(ok)} verified findings ({n('BREAKING')} breaking, {n('DEPRECATION')} deprecation, {n('ADDITIVE')} additive) · "
         f"{len(rej)} rejected by WARDEN_",
         "",
         "## Coverage",
         "| Source | File | Before (commit · date) | After (commit · date) | Changed? |",
         "|---|---|---|---|---|"]
    for sid, m in snaps_meta.items():
        L.append(f"| {sid.split(' · ')[0]} | `{m['path']}` | `{m['before'][:8]}` · {m['before_date'][:10]} | "
                 f"`{m['after'][:8]}` · {m['after_date'][:10]} | {'yes' if m['changed'] else 'no'} |")
    L += ["", "## Findings (WARDEN-verified)"]
    for sid, vs in sorted(by_src.items()):
        L += ["", f"### {sid}"]
        vs.sort(key=lambda v: (sev_order[v.finding.severity], v.finding.locator))
        breaking = [v for v in vs if v.finding.severity != "ADDITIVE"]
        additive = [v for v in vs if v.finding.severity == "ADDITIVE"]
        for v in breaking:
            f = v.finding
            conf = " _(keyword-classified from changelog; WARDEN verified the quote, not the semantics)_" if f.kind == "changelog_entry" else ""
            commit = (f"introduced in `{f.intro_commit[:8]}`" + (f" ({f.intro_date[:10]})" if f.intro_date else "")) if f.intro_commit else f"in range {f.before_commit[:8]} → {f.after_commit[:8]}"
            L.append(f"- **{f.severity}** · {f.detail}{conf}  \n  locator `{f.locator}` · {commit}")
        if additive:
            L.append(f"- _{len(additive)} additive changes (new endpoints/fields) — safe, omitted from brief; full list in findings.json_")
    if rej:
        L += ["", "## Rejected by WARDEN (not delivered)"]
        for v in rej:
            L.append(f"- {v.finding.kind} at `{v.finding.locator}` — {v.reason}")
    L += ["", "## VAULT ledger",
          f"- Trailing 30-day revenue: ${budget['trailing_revenue_usd']:.2f} ({'seed mode' if budget['seed_mode'] else 'revenue mode'})",
          f"- Cycle compute cap: ${budget['cycle_total_cap_usd']:.2f} (frontier sub-cap ${budget['cycle_frontier_cap_usd']:.2f})",
          f"- Cycle compute spend: ${spend:.4f}",
          f"- Operating mode: **{mode}**",
          ""]
    return "\n".join(L)
