"""Public backfill report. Regenerable from the repo: `python -m driftwatch report`.

Every row links to the commit that introduced the change (attribute.py), so a
reader can open the vendor's own diff and see it.
"""
from __future__ import annotations

import collections
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

VENDOR = {"stripe": "Stripe", "openai": "OpenAI", "twilio": "Twilio",
          "aws-sdk-js": "AWS SDK for JavaScript v3", "shopify-api-js": "Shopify API (JS)"}
REPO = {"stripe": "stripe/openapi", "openai": "openai/openai-openapi", "twilio": "twilio/twilio-oai",
        "aws-sdk-js": "aws/aws-sdk-js-v3", "shopify-api-js": "Shopify/shopify-app-js"}
ORDER = {"BREAKING": 0, "DEPRECATION": 1, "ADDITIVE": 2}

CSS = """
:root{--ink:#1b1f2a;--muted:#5b6270;--rule:#e4e7ec;--wash:#f6f7f9;--del:#b42318;--dep:#b54708;
--sans:"IBM Plex Sans",system-ui,sans-serif;--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace}
*{box-sizing:border-box}html{font-size:17px}
body{margin:0;color:var(--ink);font-family:var(--sans);line-height:1.55;background:#fff}
.wrap{max-width:760px;margin:0 auto;padding:0 20px}
header{padding:28px 0 0}header .wrap{display:flex;justify-content:space-between;align-items:baseline;gap:16px;flex-wrap:wrap}
.brand{font-weight:600;text-decoration:none;color:inherit}
nav a{color:var(--muted);text-decoration:none;margin-left:18px;font-size:.94rem}
h1{font-size:clamp(1.7rem,4.2vw,2.3rem);line-height:1.15;letter-spacing:-.02em;font-weight:600;margin:56px 0 14px;max-width:22ch}
.lede{font-size:1.08rem;color:var(--muted);margin:0 0 28px;max-width:60ch}
h2{font-size:1.2rem;font-weight:600;margin:52px 0 4px}
.sub{color:var(--muted);font-size:.92rem;margin:0 0 10px}
table{width:100%;border-collapse:collapse;font-size:.95rem;table-layout:fixed}
td{padding:10px 10px 10px 0;border-bottom:1px solid var(--rule);vertical-align:top;overflow-wrap:anywhere}
td.sev{white-space:nowrap;width:7.5em;font-weight:500}
td.breaking{color:var(--del)}td.deprecation{color:var(--dep)}td.none{color:var(--muted)}
.loc{font-family:var(--mono);font-size:.78rem;color:var(--muted);margin-top:3px}.loc a{color:inherit}
.kw{font-size:.78rem;color:var(--muted);border:1px solid var(--rule);border-radius:3px;padding:0 5px;margin-left:4px;white-space:nowrap}
.method{background:var(--wash);border:1px solid var(--rule);border-radius:6px;padding:14px 16px;font-size:.94rem;margin:28px 0}
.method p{margin:0 0 8px}.method p:last-child{margin:0}
.toc{font-size:.94rem;color:var(--muted);margin:0 0 8px}.toc a{color:inherit;margin-right:14px}
.cta{margin:56px 0 0;padding:18px 0 0;border-top:1px solid var(--rule)}.cta p{max-width:62ch}
.btn{display:inline-block;padding:9px 14px;border:1px solid var(--ink);border-radius:5px;text-decoration:none;font-weight:500;font-size:.94rem;background:var(--ink);color:#fff;margin-right:8px}
.btn.ghost{background:transparent;color:var(--ink)}
footer{margin:72px 0 40px;font-size:.9rem;color:var(--muted)}
@media(max-width:520px){html{font-size:16px}tr{display:block;border-bottom:1px solid var(--rule);padding:6px 0}td{display:block;border:0;width:auto}}
"""


def _clean(detail: str) -> str:
    return re.sub(r"^New changelog section '([^']+)': ", r"Release \1 — ", detail)


def build(findings: list[dict], window: str, out: Path) -> Path:
    esc = html.escape
    by = collections.defaultdict(list)
    for f in findings:
        by[f["source_id"]].append(f)
    tot = collections.Counter(f["severity"] for f in findings)
    order = [s for s in ["stripe", "openai", "shopify-api-js", "twilio", "aws-sdk-js"] if s in by]

    secs = []
    for sid in order:
        fs = sorted(by[sid], key=lambda f: (ORDER[f["severity"]], f["locator"]))
        c = collections.Counter(f["severity"] for f in fs)
        rows = []
        for f in fs:
            if f["severity"] == "ADDITIVE":
                continue
            sha = f.get("intro_commit") or ""
            if sha:
                when = (f.get("intro_date") or "")[:10]
                cite = f'<a href="https://github.com/{REPO[sid]}/commit/{sha}">{sha[:8]}</a>' + (f" · {when}" if when else "")
            else:
                cite = f'range {f["before_commit"][:8]} → {f["after_commit"][:8]} (exact commit not pinned)'
            kw = ' <span class="kw">keyword-classified</span>' if f["kind"] == "changelog_entry" else ""
            rows.append(f'<tr><td class="sev {f["severity"].lower()}">{f["severity"].title()}</td>'
                        f'<td>{esc(_clean(f["detail"]))}{kw}<div class="loc">{esc(f["locator"])} · {cite}</div></td></tr>')
        secs.append(f'<h2 id="{sid}">{VENDOR[sid]}</h2>'
                    f'<p class="sub">{c.get("BREAKING",0)} breaking · {c.get("DEPRECATION",0)} deprecation · '
                    f'{c.get("ADDITIVE",0)} additive (new endpoints and fields, not listed)</p>'
                    f'<table>{"".join(rows) or chr(60)+"tr><td colspan=2 class=none>No breaking or deprecation changes in the window.</td></tr>"}</table>')

    toc = "".join(f'<a href="#{s}">{VENDOR[s]}</a>' for s in order)
    pinned = sum(1 for f in findings if f.get("intro_commit"))
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{window}: API breaking changes</title>
<meta name="description" content="Every verified breaking change and deprecation in the Stripe, OpenAI, Shopify, Twilio and AWS SDK specs, {window}, each linked to the commit that introduced it.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>
<header><div class="wrap"><a class="brand" href="/driftwatch/">Driftwatch</a>
<nav><a href="/driftwatch/#pricing">Pricing</a><a href="https://github.com/mbatch79/driftwatch">Source</a></nav></div></header>
<main class="wrap">
<h1>60 days of API breaking changes you probably didn't read about</h1>
<p class="lede">Every verified breaking change and deprecation in the published specs of Stripe, OpenAI, Shopify, Twilio and the AWS JavaScript SDK, {window}. {tot['BREAKING']} breaking, {tot['DEPRECATION']} deprecations, {tot['ADDITIVE']} additive, out of {len(findings)} verified changes. {pinned} of {len(findings)} link to the exact commit that introduced them — open it and check.</p>
<p class="toc">{toc}</p>
<div class="method"><p><b>How this was produced.</b> A deterministic pipeline pulled each vendor's own machine-readable spec from its GitHub repository, structurally diffed consecutive versions (endpoints, parameters, request and response fields, schema types, enums, deprecation flags) and classified each change. A second, independent step re-located every finding in the raw spec from its locator alone; anything it could not reproduce was discarded. A third step walked the commits in the range and pinned each finding to the first commit where it became true. No language model was involved in detection, verification or attribution.</p>
<p>OpenAPI findings are exact. AWS and Shopify entries come from release-note changelogs and are keyword-classified: the quoted line is verified to exist, the severity is a heuristic, and they're marked. Specs track each vendor's newest API version, so "removed" means removed in the newest version; check against the version you pin.</p></div>
{''.join(secs)}
<div class="cta"><p>This list is the whole feed. The useful version is the one filtered to the fields and endpoints your own code calls, delivered the week it happens. The free GitHub Action does that on every build against your lockfile; the paid plans do it against your source.</p>
<a class="btn ghost" href="/driftwatch/#free">Add the free Action</a><a class="btn" href="/driftwatch/#pricing">See plans</a></div>
</main>
<footer class="wrap"><p>Driftwatch is operated by Re-Batch Studio (Simpel Pty Ltd, ABN 44 103 034 797), Sale, Victoria, Australia. Pipeline, briefs and ledger: <a href="https://github.com/mbatch79/driftwatch">github.com/mbatch79/driftwatch</a>. Raw data: <a href="https://raw.githubusercontent.com/mbatch79/driftwatch/main/feed/latest/findings.json">findings.json</a>.</p></footer>
</body></html>"""
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page)
    return out
