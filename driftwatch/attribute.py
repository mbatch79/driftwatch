"""Commit attribution — pins every finding to the exact commit that introduced it.

DIFF compares two snapshots taken a week apart, so a finding's "after" commit is
only the end of the range, not the commit responsible. A reader who clicks that
commit may not see the change, which reads as fabrication. This walks the commits
in the range and asks WARDEN's own verifier which one first makes the finding true.

One spec parse per commit (not per finding): all findings for a file are tested
against each candidate as it is loaded.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import yaml

from . import warden
from .diff import Finding
from .scout import MIRRORS


def _run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True).stdout


def _commits(repo: Path, before_sha: str, after_sha: str, path: str) -> list[tuple[str, str]]:
    """Commits touching `path` in (before, after], oldest first."""
    out = _run(["git", "log", "--reverse", "--format=%H %cI", f"{before_sha}..{after_sha}", "--", path], repo)
    return [tuple(l.split(" ", 1)) for l in out.strip().splitlines() if l]


def _load(repo: Path, sha: str, path: str):
    raw = subprocess.run(["git", "show", f"{sha}:{path}"], cwd=repo, check=True, capture_output=True).stdout
    if path.endswith(".json"):
        return json.loads(raw)
    if path.endswith((".yaml", ".yml")):
        return yaml.safe_load(raw)
    return raw.decode(errors="replace")


def attribute(findings: list[Finding], pairs, kinds: dict[str, str]) -> dict[tuple, tuple[str, str]]:
    """Returns {(source_id, file, locator, kind): (intro_sha, intro_date)}.
    A finding with no attribution keeps the range it came from."""
    out: dict[tuple, tuple[str, str]] = {}
    by_file: dict[tuple[str, str], list[Finding]] = {}
    for f in findings:
        by_file.setdefault((f.source_id, f.file), []).append(f)

    for (b, a) in pairs:
        key = (b.source_id, b.path)
        fs = by_file.get(key)
        if not fs or b.commit == a.commit:
            continue
        repo = MIRRORS / b.source_id
        base = _load(repo, b.commit, b.path)
        pending = list(fs)
        verify = warden._verify_openapi if kinds[b.source_id] == "openapi" else warden._verify_changelog
        for sha, date in _commits(repo, b.commit, a.commit, b.path):
            if not pending:
                break
            cand = _load(repo, sha, b.path)
            still = []
            for f in pending:
                try:
                    ok, _ = verify(f, base, cand)
                except Exception:
                    ok = False
                if ok:
                    out[(f.source_id, f.file, f.locator, f.kind)] = (sha, date)
                else:
                    still.append(f)
            pending = still
    return out


def attribute_record(rec: dict) -> tuple[str, str]:
    """Attribute a finding dict that carries its own before/after range (e.g. an
    entry already published in the feed). Returns (sha, date) or ("","")."""
    from .diff import Finding
    f = Finding(rec["source_id"], rec["file"], rec["severity"], rec["kind"], rec["locator"],
                rec["detail"], rec.get("symbols", []), rec["before_commit"], rec["after_commit"])
    repo = MIRRORS / f.source_id
    kind = "openapi" if f.file.endswith((".json", ".yaml", ".yml")) else "changelog"
    verify = warden._verify_openapi if kind == "openapi" else warden._verify_changelog
    try:
        base = _load(repo, f.before_commit, f.file)
        cands = _commits(repo, f.before_commit, f.after_commit, f.file)
    except subprocess.CalledProcessError:
        return ("", "")
    for sha, date in cands:
        try:
            if verify(f, base, _load(repo, sha, f.file))[0]:
                return (sha, date)
        except Exception:
            continue
    return ("", "")
