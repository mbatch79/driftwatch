"""SCOUT — ingestion. Fetches vendor specs from their cleanest channel (git),
snapshots the file at two points in time, and hashes canonicalised content.
No opinions. No models. Cheap on purpose."""
from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MIRRORS = ROOT / "data" / "mirrors"
SNAPS = ROOT / "data" / "snapshots"


@dataclass
class Snapshot:
    source_id: str
    path: str
    commit: str
    commit_date: str
    file: Path
    sha256: str


def _run(cmd: list[str], cwd: Path | None = None) -> str:
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def load_sources() -> list[dict]:
    return yaml.safe_load((ROOT / "config" / "sources.yaml").read_text())["sources"]


def mirror(src: dict) -> Path:
    """Blobless partial clone: full history, no file contents until asked. Cheap."""
    dest = MIRRORS / src["id"]
    if not (dest / ".git").exists():
        MIRRORS.mkdir(parents=True, exist_ok=True)
        _run(["git", "clone", "--filter=blob:none", "--no-checkout", "--single-branch",
              "-b", src["branch"], "-q", src["repo"], str(dest)])
    else:
        _run(["git", "fetch", "-q", "origin", src["branch"]], cwd=dest)
    return dest


def commit_at(repo: Path, branch: str, when: datetime, path: str) -> tuple[str, str]:
    """Last commit touching `path` on or before `when`. Returns (sha, iso date)."""
    out = _run(["git", "log", "-1", "--format=%H %cI", f"--before={when.isoformat()}",
                f"origin/{branch}", "--", path], cwd=repo)
    if not out:
        raise RuntimeError(f"no commit for {path} before {when:%Y-%m-%d}")
    sha, date = out.split(" ", 1)
    return sha, date


def canonical_hash(raw: bytes, path: str) -> str:
    """Extract-then-hash: parse structured specs so whitespace/key-order churn never
    registers as a change. Markdown is hashed on stripped lines."""
    if path.endswith(".json"):
        canon = json.dumps(json.loads(raw), sort_keys=True, separators=(",", ":")).encode()
    elif path.endswith((".yaml", ".yml")):
        canon = json.dumps(yaml.safe_load(raw), sort_keys=True, separators=(",", ":")).encode()
    else:
        canon = "\n".join(l.rstrip() for l in raw.decode(errors="replace").splitlines()).encode()
    return hashlib.sha256(canon).hexdigest()


STATE = ROOT / "ledger" / "watermarks.json"


def snapshot(src: dict, path: str, label: str, when: datetime | None = None, sha: str | None = None) -> Snapshot:
    """Snapshot by date (first cycle) or by exact commit (high-water mark from the last cycle)."""
    repo = mirror(src)
    if sha is None:
        sha, date = commit_at(repo, src["branch"], when, path)
    else:
        date = _run(["git", "log", "-1", "--format=%cI", sha], cwd=repo)
    raw = subprocess.run(["git", "show", f"{sha}:{path}"], cwd=repo, check=True,
                         capture_output=True).stdout
    out = SNAPS / src["id"] / label / Path(path).name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(raw)
    return Snapshot(src["id"], path, sha, date, out, canonical_hash(raw, path))


def watermarks() -> dict[str, str]:
    return json.loads(STATE.read_text()) if STATE.exists() else {}


def save_watermarks(pairs: list[tuple[Snapshot, Snapshot]]):
    STATE.parent.mkdir(exist_ok=True)
    wm = watermarks()
    for _, a in pairs:
        wm[f"{a.source_id}:{a.path}"] = a.commit
    STATE.write_text(json.dumps(wm, indent=1, sort_keys=True))


def ingest(window_days: int = 60, incremental: bool = True) -> list[tuple[Snapshot, Snapshot]]:
    """Incremental: 'before' is the last cycle's 'after' commit for that file (nothing is
    reported twice, nothing is skipped). Falls back to the date window for any file
    with no watermark yet (first cycle, or a newly added source)."""
    now = datetime.now(timezone.utc)
    then = now - timedelta(days=window_days)
    wm = watermarks() if incremental else {}
    pairs = []
    for src in load_sources():
        if src.get("tier") != "clean":
            continue  # walled sources are not in Cycle 1
        for path in src["paths"]:
            mark = wm.get(f"{src['id']}:{path}")
            before = snapshot(src, path, "before", sha=mark) if mark else snapshot(src, path, "before", when=then)
            after = snapshot(src, path, "after", when=now)
            pairs.append((before, after))
    return pairs
