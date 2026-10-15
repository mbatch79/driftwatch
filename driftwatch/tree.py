"""Dependency tree — the noise filter. Reads a customer's lockfile/manifest and
their source (optional) and returns what they actually touch, so DIFF findings
can be scored by usage instead of guessed from a company blurb."""
from __future__ import annotations

import json
import re
from pathlib import Path

VENDOR_PKGS = {
    "stripe": ["stripe"],
    "openai": ["openai"],
    "twilio": ["twilio"],
    "aws-sdk-js": ["@aws-sdk/"],
    "shopify-api-js": ["@shopify/shopify-api"],
}


def packages(root: Path) -> set[str]:
    names: set[str] = set()
    pj = root / "package.json"
    if pj.exists():
        d = json.loads(pj.read_text())
        for k in ("dependencies", "devDependencies"):
            names |= set((d.get(k) or {}).keys())
    lock = root / "package-lock.json"
    if lock.exists():
        d = json.loads(lock.read_text())
        names |= {k.split("node_modules/")[-1] for k in (d.get("packages") or {}) if k}
    for req in ("requirements.txt", "pyproject.toml"):
        p = root / req
        if p.exists():
            names |= set(re.findall(r"^\s*([A-Za-z0-9_.-]+)\s*[=<>~!\[]", p.read_text(), re.M))
    return {n.lower() for n in names}


def vendors_in_use(root: Path) -> set[str]:
    pk = packages(root)
    hit = set()
    for src, pats in VENDOR_PKGS.items():
        if any(any(p.startswith(pat.lower()) for p in pk) for pat in pats):
            hit.add(src)
    return hit


def symbols_in_source(root: Path, candidates: list[str]) -> dict[str, list[str]]:
    """Grep-match endpoint paths / schema names against the customer's code.
    Returns {symbol: [file:line, ...]}. This is the materiality engine: a finding
    is sev-100 because line 412 uses it, not because a model guessed."""
    hits: dict[str, list[str]] = {}
    pats = {c: re.compile("|".join(re.escape(n) for n in _needles(c))) for c in candidates if _needles(c)}
    for f in root.rglob("*"):
        if f.suffix not in {".js", ".ts", ".tsx", ".py", ".rb", ".go", ".java", ".cs"} or "node_modules" in f.parts:
            continue
        try:
            lines = f.read_text(errors="replace").splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines, 1):
            for c, pat in pats.items():
                if pat.search(line):
                    hits.setdefault(c, []).append(f"{f.relative_to(root)}:{i}")
    return hits


def _needles(symbol: str) -> list[str]:
    """"/v1/payment_intents/{intent}" -> ["payment_intents", "paymentIntents", "PaymentIntents"]
    so SDK method names match as well as raw paths. Field names match verbatim."""
    if symbol.startswith("/"):
        parts = [p for p in symbol.split("/") if p and not p.startswith("{") and p != "v1"]
        if not parts:
            return []
        snake = parts[-1]
        camel = re.sub(r"_([a-z])", lambda m: m.group(1).upper(), snake)
        return list({snake, camel, camel[:1].upper() + camel[1:]})
    return [symbol] if len(symbol) >= 4 else []


def score(finding: dict, vendors: set[str], hits: dict[str, list[str]]) -> int:
    if finding["source_id"] not in vendors:
        return 0
    base = {"BREAKING": 70, "DEPRECATION": 40, "ADDITIVE": 5}[finding["severity"]]
    if any(s in hits for s in finding["symbols"]):
        return min(100, base + 30)
    return base // 2  # vendor in use, symbol not seen: worth a digest line, not an alert
