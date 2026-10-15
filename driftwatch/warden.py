"""WARDEN — verification. Independently re-checks every DIFF finding against the
raw snapshots using only the locator. A finding WARDEN cannot reproduce is
rejected, not softened. Fail-rate above vault.quality threshold pauses delivery."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from .diff import Finding, _ops, _params, _schemas, _body_props, _sections


@dataclass
class Verdict:
    finding: Finding
    verified: bool
    reason: str


def _load(p: Path):
    raw = p.read_bytes()
    return json.loads(raw) if p.suffix == ".json" else yaml.safe_load(raw)


def _verify_openapi(f: Finding, before: dict, after: dict) -> tuple[bool, str]:
    loc = f.locator
    m = re.match(r"^/paths/([A-Z]+ [^/]*?(?:/[^/]*?)*?)(?:/parameters/([^/]+)|/deprecated|/requestBody/(required|properties)/([^/]+))?$", loc)
    if loc.startswith("/paths/"):
        # split "METHOD path" from the rest
        rest = loc[len("/paths/"):]
        key = rest
        tail = ""
        for marker in ("/parameters/", "/deprecated", "/requestBody/"):
            if marker in rest:
                key, tail = rest.split(marker, 1)
                tail = marker + tail
                break
        ob, oa = _ops(before), _ops(after)
        if f.kind == "endpoint_removed":
            return (key in ob and key not in oa), "endpoint presence re-checked"
        if f.kind == "endpoint_added":
            return (key not in ob and key in oa), "endpoint presence re-checked"
        if key not in ob or key not in oa:
            return False, "endpoint missing on one side"
        if f.kind == "param_removed":
            p = tail.split("/parameters/", 1)[1]
            return (p in _params(ob[key]) and p not in _params(oa[key])), "param presence re-checked"
        if f.kind == "required_param_added":
            p = tail.split("/parameters/", 1)[1]
            pa = _params(oa[key])
            return (p not in _params(ob[key]) and p in pa and bool(pa[p].get("required"))), "required flag re-checked"
        if f.kind == "param_now_required":
            p = tail.split("/parameters/", 1)[1]
            pb, pa = _params(ob[key]), _params(oa[key])
            return (p in pb and p in pa and not pb[p].get("required") and bool(pa[p].get("required"))), "required flag re-checked"
        if f.kind == "endpoint_deprecated":
            return (bool(oa[key].get("deprecated")) and not ob[key].get("deprecated")), "deprecated flag re-checked"
        if f.kind == "body_required_added":
            r = tail.rsplit("/", 1)[1]
            return (r in (_body_props(oa[key]).get("required") or []) and r not in (_body_props(ob[key]).get("required") or [])), "body required re-checked"
        if f.kind in ("body_prop_removed", "body_prop_renamed"):
            r = tail.rsplit("/", 1)[1]
            pb, pa = _body_props(ob[key]).get("properties") or {}, _body_props(oa[key]).get("properties") or {}
            gone = r in pb and r not in pa
            if f.kind == "body_prop_renamed":
                new = f.detail.rsplit("-> ", 1)[1]
                return (gone and new in pa and new not in pb), "rename target re-checked"
            return gone, "body prop re-checked"
    if loc.startswith("/components/schemas/"):
        parts = loc[len("/components/schemas/"):].split("/")
        name = parts[0]
        sb, sa = _schemas(before), _schemas(after)
        if f.kind == "schema_removed":
            return (name in sb and name not in sa), "schema presence re-checked"
        if f.kind == "schema_renamed":
            new = f.detail.rsplit("-> ", 1)[1]
            return (name in sb and name not in sa and new in sa and new not in sb), "rename target re-checked"
        if name not in sb or name not in sa:
            return False, "schema missing on one side"
        prop = parts[2] if len(parts) > 2 else None
        pb, pa = sb[name].get("properties") or {}, sa[name].get("properties") or {}
        if f.kind == "schema_prop_removed":
            return (prop in pb and prop not in pa), "prop presence re-checked"
        if prop not in pb or prop not in pa:
            return False, "prop missing on one side"
        if f.kind in ("schema_prop_type_changed", "schema_prop_nullable"):
            return (pb[prop].get("type") != pa[prop].get("type")), "type re-checked"
        if f.kind == "enum_value_removed":
            return bool(set(pb[prop].get("enum") or []) - set(pa[prop].get("enum") or [])), "enum re-checked"
        if f.kind == "schema_prop_deprecated":
            return (bool(pa[prop].get("deprecated")) and not pb[prop].get("deprecated")), "deprecated re-checked"
    return False, f"no verifier for kind={f.kind}"


def _verify_changelog(f: Finding, before: str, after: str) -> tuple[bool, str]:
    head = f.locator.lstrip("#")
    sb, sa = _sections(before), _sections(after)
    if head in sb or head not in sa:
        return False, "section not new on the after side"
    quoted = f.detail.split("': ", 1)[1].split(" | ")
    return all(q in sa[head] for q in quoted), "quoted lines re-located in section"


def verify(findings: list[Finding], snaps: dict[tuple[str, str], tuple[Path, Path]], kinds: dict[str, str]) -> list[Verdict]:
    cache: dict[tuple[str, str], tuple] = {}
    out = []
    for f in findings:
        k = (f.source_id, f.file)
        if k not in cache:
            b, a = snaps[k]
            cache[k] = (_load(b), _load(a)) if kinds[f.source_id] == "openapi" else (
                b.read_text(errors="replace"), a.read_text(errors="replace"))
        before, after = cache[k]
        ok, why = (_verify_openapi if kinds[f.source_id] == "openapi" else _verify_changelog)(f, before, after)
        out.append(Verdict(f, ok, why))
    return out


def fail_rate(verdicts: list[Verdict]) -> float:
    return 0.0 if not verdicts else 100.0 * sum(1 for v in verdicts if not v.verified) / len(verdicts)
