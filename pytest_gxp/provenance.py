"""UTC timestamps, source provenance, and artifact hashing for reproducible records."""

import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from . import __version__

MANIFEST_FILENAME = "artifact_manifest.sha256"


def utc_now_iso() -> str:
    """Return the current UTC time as ISO 8601 with second precision and a 'Z' suffix."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def utc_today() -> str:
    """Return the current UTC date as YYYY-MM-DD."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _git(root: Path, *args: str) -> Optional[str]:
    """Run a git command in root, returning stripped stdout or None on any failure."""
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def git_provenance(root: Path) -> Dict[str, Any]:
    """Describe the source revision at root.

    Returns a dict with keys ``source``, ``git_commit``, ``git_tag`` and ``git_dirty``.
    Nothing is ever fabricated: if git is unavailable or root is not a repository the
    source is reported as "unavailable" with null values.
    """
    commit = _git(root, "rev-parse", "HEAD")
    if not commit:
        return {
            "source": "unavailable",
            "git_commit": None,
            "git_tag": None,
            "git_dirty": None,
        }

    status = _git(root, "status", "--porcelain")
    return {
        "source": "git",
        "git_commit": commit,
        "git_tag": _git(root, "describe", "--tags", "--exact-match") or None,
        "git_dirty": bool(status) if status is not None else None,
    }


def write_artifact_manifest(report_dir: Path) -> Path:
    """Write a sha256sum-compatible manifest of every file under report_dir.

    The manifest itself is excluded, entries are sorted by relative path, and each
    line is ``<sha256hex>  <posix-relative-path>`` so that ``sha256sum -c`` /
    ``shasum -a 256 -c`` can verify it after stripping the comment header.
    """
    report_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = report_dir / MANIFEST_FILENAME

    entries = []
    for path in report_dir.rglob("*"):
        if not path.is_file() or path == manifest_path:
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        entries.append((path.relative_to(report_dir).as_posix(), digest))

    lines = [
        "# pytest-gxp artifact manifest",
        f"# generated_utc: {utc_now_iso()}",
        f"# tool: pytest-gxp {__version__}",
    ]
    lines.extend(f"{digest}  {relpath}" for relpath, digest in sorted(entries))

    manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return manifest_path
