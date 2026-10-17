"""DIFF — structural comparison. Classifies every change as BREAKING, DEPRECATION
or ADDITIVE with a machine-checkable locator (JSON pointer or changelog heading)
so WARDEN can re-verify it independently. Cosmetic noise never leaves this module."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path

import yaml

from .scout import Snapshot


@dataclass
class Finding:
    source_id: str
    file: str              # which spec file within the source
    severity: str          # BREAKING | DEPRECATION | ADDITIVE
    kind: str              # endpoint_removed, param_removed, required_added, ...
    locator: str           # JSON pointer or changelog heading — WARDEN re-checks this
    detail: str
    symbols: list[str]     # endpoint paths / schema names a dependency tree can match on
    before_commit: str
    after_commit: str

    def to_dict(self):
        return asdict(self)


def _load(p: Path):
    raw = p.read_bytes()
    return json.loads(raw) if p.suffix == ".json" else yaml.safe_load(raw)


def _rename_target(old: str, added: set[str]) -> str | None:
    """A removed name with an added name that contains it (or vice versa, or
    differs only by a trailing 's') is a rename, not a deletion. Still breaking —
    the customer's code uses the old name — but the brief must say where it went."""
    for new in sorted(added):
        if old in new or new in old or old.rstrip("s") == new.rstrip("s"):
            return new
    return None


def _nullable_widening(tb, ta) -> bool:
    """OpenAPI 3.1 writes nullable as type: [T, 'null']. Old type still accepted → not breaking."""
    old = set(tb) if isinstance(tb, list) else {tb}
    new = set(ta) if isinstance(ta, list) else {ta}
    return old <= new and new - old <= {"null"}


# ---------- OpenAPI ----------

def _ops(spec: dict) -> dict[str, dict]:
    out = {}
    for path, item in (spec.get("paths") or {}).items():
        if not isinstance(item, dict):
            continue
        for m in ("get", "post", "put", "patch", "delete"):
            if m in item:
                out[f"{m.upper()} {path}"] = item[m]
    return out


def _params(op: dict) -> dict[str, dict]:
    return {f"{p.get('in')}:{p.get('name')}": p for p in op.get("parameters", []) if isinstance(p, dict)}


def _body_props(op: dict) -> dict:
    content = (op.get("requestBody") or {}).get("content") or {}
    for mt, body in content.items():
        schema = body.get("schema") or {}
        return schema
    return {}


def _schemas(spec: dict) -> dict:
    return (spec.get("components") or {}).get("schemas") or {}


def _response_shape(op: dict, spec: dict) -> tuple[str | None, dict]:
    """Success-response schema for an operation, with a one-level $ref resolved.
    Returns (ref_name_or_None, properties). Inline schemas are diffed in place;
    $ref'd ones are already covered by the components/schemas pass, so we only
    report the ref *changing* (which is a shape change for the caller)."""
    for code in ("200", "201", "default"):
        r = (op.get("responses") or {}).get(code)
        if not r:
            continue
        for mt, body in (r.get("content") or {}).items():
            sch = body.get("schema") or {}
            ref = sch.get("$ref")
            if ref:
                return ref.rsplit("/", 1)[-1], {}
            return None, sch.get("properties") or {}
    return None, {}


def diff_openapi(b: Snapshot, a: Snapshot) -> list[Finding]:
    before, after = _load(b.file), _load(a.file)
    F: list[Finding] = []
    mk = lambda sev, kind, loc, det, syms: F.append(
        Finding(b.source_id, b.path, sev, kind, loc, det, syms, b.commit, a.commit))

    ob, oa = _ops(before), _ops(after)
    for key in sorted(set(ob) - set(oa)):
        mk("BREAKING", "endpoint_removed", f"/paths/{key}", f"Endpoint removed: {key}", [key.split(" ", 1)[1]])
    for key in sorted(set(oa) - set(ob)):
        mk("ADDITIVE", "endpoint_added", f"/paths/{key}", f"Endpoint added: {key}", [key.split(" ", 1)[1]])
    for key in sorted(set(ob) & set(oa)):
        pb, pa = _params(ob[key]), _params(oa[key])
        for p in sorted(set(pb) - set(pa)):
            mk("BREAKING", "param_removed", f"/paths/{key}/parameters/{p}", f"Parameter removed on {key}: {p}", [key.split(' ',1)[1], p.split(':',1)[1]])
        for p in sorted(set(pa) - set(pb)):
            if pa[p].get("required"):
                mk("BREAKING", "required_param_added", f"/paths/{key}/parameters/{p}", f"New REQUIRED parameter on {key}: {p}", [key.split(' ',1)[1]])
        for p in sorted(set(pb) & set(pa)):
            if not pb[p].get("required") and pa[p].get("required"):
                mk("BREAKING", "param_now_required", f"/paths/{key}/parameters/{p}", f"Parameter now required on {key}: {p}", [key.split(' ',1)[1]])
        if oa[key].get("deprecated") and not ob[key].get("deprecated"):
            mk("DEPRECATION", "endpoint_deprecated", f"/paths/{key}/deprecated", f"Endpoint marked deprecated: {key}", [key.split(' ',1)[1]])
        # request body: required props added / props removed
        sb, sa = _body_props(ob[key]), _body_props(oa[key])
        rb, ra = set(sb.get("required") or []), set(sa.get("required") or [])
        for r in sorted(ra - rb):
            mk("BREAKING", "body_required_added", f"/paths/{key}/requestBody/required/{r}", f"Request body field now required on {key}: {r}", [key.split(' ',1)[1], r])
        pb2, pa2 = set((sb.get("properties") or {}).keys()), set((sa.get("properties") or {}).keys())
        added = pa2 - pb2
        for r in sorted(pb2 - pa2):
            new = _rename_target(r, added)
            if new:
                mk("BREAKING", "body_prop_renamed", f"/paths/{key}/requestBody/properties/{r}",
                   f"Request body field RENAMED on {key}: {r} -> {new}", [key.split(' ',1)[1], r])
            else:
                succ = _rename_target(r, pa2 - {r})
                note = f" (successor already present: {succ})" if succ else ""
                mk("BREAKING", "body_prop_removed", f"/paths/{key}/requestBody/properties/{r}", f"Request body field removed on {key}: {r}{note}", [key.split(' ',1)[1], r])
        # success response shape: $ref swapped, or inline fields removed / retyped
        refb, propb = _response_shape(ob[key], before)
        refa, propa = _response_shape(oa[key], after)
        if refb and refa and refb != refa:
            mk("BREAKING", "response_ref_changed", f"/paths/{key}/responses/schema", f"Success response schema changed on {key}: {refb} -> {refa}", [key.split(' ',1)[1], refb, refa])
        for r in sorted(set(propb) - set(propa)):
            mk("BREAKING", "response_prop_removed", f"/paths/{key}/responses/properties/{r}", f"Response field removed on {key}: {r}", [key.split(' ',1)[1], r])
        for r in sorted(set(propb) & set(propa)):
            tb, ta = propb[r].get("type"), propa[r].get("type")
            if tb and ta and tb != ta and not _nullable_widening(tb, ta):
                mk("BREAKING", "response_prop_type_changed", f"/paths/{key}/responses/properties/{r}/type", f"Response field type changed on {key}: {r} {tb} -> {ta}", [key.split(' ',1)[1], r])

    sb, sa = _schemas(before), _schemas(after)
    new_schemas = set(sa) - set(sb)
    for name in sorted(set(sb) - set(sa)):
        new = _rename_target(name, new_schemas)
        if new:
            mk("BREAKING", "schema_renamed", f"/components/schemas/{name}", f"Schema RENAMED: {name} -> {new}", [name, new])
        else:
            mk("BREAKING", "schema_removed", f"/components/schemas/{name}", f"Schema removed: {name}", [name])
    for name in sorted(set(sb) & set(sa)):
        pb, pa = sb[name].get("properties") or {}, sa[name].get("properties") or {}
        for prop in sorted(set(pb) - set(pa)):
            mk("BREAKING", "schema_prop_removed", f"/components/schemas/{name}/properties/{prop}", f"Property removed from {name}: {prop}", [name])
        for prop in sorted(set(pb) & set(pa)):
            tb, ta = pb[prop].get("type"), pa[prop].get("type")
            if tb and ta and tb != ta:
                if _nullable_widening(tb, ta):
                    mk("ADDITIVE", "schema_prop_nullable", f"/components/schemas/{name}/properties/{prop}/type", f"Now nullable on {name}.{prop}: {tb} -> {ta}", [name])
                else:
                    mk("BREAKING", "schema_prop_type_changed", f"/components/schemas/{name}/properties/{prop}/type", f"Type changed on {name}.{prop}: {tb} -> {ta}", [name])
            eb, ea = set(pb[prop].get("enum") or []), set(pa[prop].get("enum") or [])
            if eb and ea and (eb - ea):
                mk("BREAKING", "enum_value_removed", f"/components/schemas/{name}/properties/{prop}/enum", f"Enum values removed on {name}.{prop}: {sorted(eb-ea)}", [name])
            if pa[prop].get("deprecated") and not pb[prop].get("deprecated"):
                mk("DEPRECATION", "schema_prop_deprecated", f"/components/schemas/{name}/properties/{prop}/deprecated", f"Property deprecated on {name}: {prop}", [name])
    return F


# ---------- Changelog ----------

# Only h1/h2 open a section (release headings). h3 like "### Major Changes" stays inside its release.
HEAD = re.compile(r"^#{1,2}\s+(.*)$")
BREAK = re.compile(r"breaking|removed|no longer|drop(?:ped|s)? support|deprecat|major change|minimum (?:supported )?(?:node|python) version", re.I)


def _sections(text: str) -> dict[str, str]:
    secs, cur, buf = {}, None, []
    for line in text.splitlines():
        m = HEAD.match(line)
        if m:
            if cur:
                secs[cur] = "\n".join(buf)
            cur, buf = m.group(1).strip(), []
        else:
            buf.append(line)
    if cur:
        secs[cur] = "\n".join(buf)
    return secs


def diff_changelog(b: Snapshot, a: Snapshot) -> list[Finding]:
    sb, sa = _sections(b.file.read_text(errors="replace")), _sections(a.file.read_text(errors="replace"))
    F = []
    for head in list(sa):
        if head in sb:
            continue
        body = sa[head]
        hits = [l.strip() for l in body.splitlines() if BREAK.search(l)]
        if not hits:
            continue
        sev = "BREAKING" if re.search(r"breaking|removed|no longer|drop", " ".join(hits), re.I) else "DEPRECATION"
        syms = sorted(set(re.findall(r"`([^`\s]{3,40})`", body)) | set(re.findall(r"\*\*([\w@/-]+):\*\*", body)))[:12]
        F.append(Finding(b.source_id, b.path, sev, "changelog_entry", f"#{head}",
                         f"New changelog section '{head}': " + " | ".join(hits[:3]),
                         syms, b.commit, a.commit))
    return F


def run(pairs: list[tuple[Snapshot, Snapshot]], kinds: dict[str, str]) -> list[Finding]:
    out: list[Finding] = []
    for b, a in pairs:
        if b.sha256 == a.sha256:
            continue  # nothing material changed; never hits a model
        out += diff_openapi(b, a) if kinds[b.source_id] == "openapi" else diff_changelog(b, a)
    return out
