"""Tests for UTC timestamps, git provenance, and the artifact manifest."""

import hashlib
import os
import subprocess
from datetime import datetime, timezone

import pytest

from pytest_gxp.provenance import (
    MANIFEST_FILENAME,
    git_provenance,
    utc_now_iso,
    utc_today,
    write_artifact_manifest,
)


def test_utc_now_iso_is_zulu_and_parsable():
    stamp = utc_now_iso()
    assert stamp.endswith("Z")

    parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None
    assert parsed.utcoffset().total_seconds() == 0
    assert parsed.microsecond == 0


def test_utc_today_matches_utc_date():
    assert utc_today() == datetime.now(timezone.utc).strftime("%Y-%m-%d")


def git_repo(path):
    """Create a git repository with a single empty commit, or skip if git is absent."""
    env = dict(
        os.environ,
        GIT_AUTHOR_NAME="Test",
        GIT_AUTHOR_EMAIL="test@example.com",
        GIT_COMMITTER_NAME="Test",
        GIT_COMMITTER_EMAIL="test@example.com",
    )
    try:
        for args in (
            ["init", "-q"],
            ["commit", "-q", "--allow-empty", "-m", "initial"],
        ):
            subprocess.run(
                ["git", "-C", str(path), *args],
                check=True,
                capture_output=True,
                env=env,
            )
    except (OSError, subprocess.CalledProcessError) as exc:  # pragma: no cover
        pytest.skip(f"git unavailable: {exc}")

    head = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return head.stdout.strip()


def test_git_provenance_reports_head_commit(temp_dir):
    head = git_repo(temp_dir)

    provenance = git_provenance(temp_dir)
    assert provenance["source"] == "git"
    assert provenance["git_commit"] == head
    assert provenance["git_tag"] is None
    assert provenance["git_dirty"] is False


def test_git_provenance_detects_dirty_tree(temp_dir):
    git_repo(temp_dir)
    (temp_dir / "untracked.txt").write_text("change")

    assert git_provenance(temp_dir)["git_dirty"] is True


def test_git_provenance_outside_repo_is_unavailable(temp_dir):
    outside = temp_dir / "plain"
    outside.mkdir()

    assert git_provenance(outside) == {
        "source": "unavailable",
        "git_commit": None,
        "git_tag": None,
        "git_dirty": None,
    }


def manifest_entries(manifest_path):
    """Return the non-comment lines of a manifest."""
    lines = manifest_path.read_text(encoding="utf-8").splitlines()
    return [line for line in lines if not line.startswith("#")]


def test_manifest_is_sorted_excludes_itself_and_digests_verify(temp_dir):
    (temp_dir / "sub").mkdir()
    (temp_dir / "b.json").write_bytes(b'{"b": 1}')
    (temp_dir / "a.md").write_bytes(b"# a\n")
    (temp_dir / "sub" / "c.png").write_bytes(b"\x89PNG")

    manifest_path = write_artifact_manifest(temp_dir)
    assert manifest_path.name == MANIFEST_FILENAME

    entries = manifest_entries(manifest_path)
    paths = [entry.split("  ", 1)[1] for entry in entries]
    assert paths == ["a.md", "b.json", "sub/c.png"]
    assert MANIFEST_FILENAME not in paths

    for entry in entries:
        digest, relpath = entry.split("  ", 1)
        expected = hashlib.sha256((temp_dir / relpath).read_bytes()).hexdigest()
        assert digest == expected


def test_manifest_header_names_the_tool(temp_dir):
    (temp_dir / "a.md").write_text("a")
    header = [
        line
        for line in write_artifact_manifest(temp_dir).read_text(encoding="utf-8").splitlines()
        if line.startswith("#")
    ]
    assert header[0] == "# pytest-gxp artifact manifest"
    assert header[1].startswith("# generated_utc: ")
    assert header[2].startswith("# tool: pytest-gxp ")


def test_manifest_entries_are_stable_across_runs(temp_dir):
    (temp_dir / "a.md").write_text("a")
    (temp_dir / "b.md").write_text("b")

    first = manifest_entries(write_artifact_manifest(temp_dir))
    second = manifest_entries(write_artifact_manifest(temp_dir))
    assert first == second
