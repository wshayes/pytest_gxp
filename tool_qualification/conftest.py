"""
TQ-001 suite configuration.

The qualification suite generates its own record: every test case appends a JSON
line to tq_evidence.jsonl containing its TQ identifier, outcome, and the values
actually observed. That file is the objective evidence for the tool
qualification and is attached to the TQ-001 report.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

import pytest

import tq_config as cfg

EVIDENCE_FILE = Path(os.environ.get("TQ_EVIDENCE_FILE", "tq_evidence.jsonl")).resolve()
ENVIRONMENT_FILE = Path(os.environ.get("TQ_ENVIRONMENT_FILE", "tq_environment.json")).resolve()


def pytest_configure(config: pytest.Config) -> None:
    # Markers are declared in tool_qualification/pytest.ini, which is also what
    # isolates this run from the project's own pytest configuration.
    _write_environment_record()


def _installed_version() -> str | None:
    try:
        from importlib.metadata import version

        return version(cfg.DISTRIBUTION_NAME)
    except Exception:  # noqa: BLE001 - absence is itself the observation
        return None


def _git(*args: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", *args], capture_output=True, text=True, timeout=15, check=False
        )
        return out.stdout.strip() or None
    except Exception:  # noqa: BLE001
        return None


def _write_environment_record() -> None:
    """Capture the qualification environment. Required by FRM-CSA-03."""
    record = {
        "captured_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "pinned_version_declared": cfg.PINNED_VERSION,
        "pytest_gxp_version_installed": _installed_version(),
        "pytest_version": pytest.__version__,
        "python_version": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "hostname": platform.node(),
        # Timestamp interpretation depends on it, so the record must state it.
        "tz_env": os.environ.get("TZ"),
        "local_timezone": dt.datetime.now().astimezone().tzname(),
        "tq_suite_commit": _git("rev-parse", "HEAD"),
        "tq_suite_tag": _git("describe", "--tags", "--exact-match"),
        "tq_suite_dirty": bool(_git("status", "--porcelain")),
    }
    ENVIRONMENT_FILE.write_text(json.dumps(record, indent=2), encoding="utf-8")


class TQRecord:
    """Evidence accumulator for one qualification test case."""

    def __init__(self, tq_id: str, node_name: str, purpose: str) -> None:
        self.tq_id = tq_id
        self.node_name = node_name
        self.purpose = purpose
        self.observations: dict[str, object] = {}
        self.started_utc = dt.datetime.now(dt.timezone.utc).isoformat()

    def observe(self, **values: object) -> None:
        """Record an observed value as objective evidence for this case."""
        for key, value in values.items():
            self.observations[key] = _jsonable(value)

    def note(self, message: str) -> None:
        self.observations.setdefault("notes", []).append(message)  # type: ignore[union-attr]


def _jsonable(value: object) -> object:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    return repr(value)


@pytest.fixture
def tq(request: pytest.FixtureRequest):
    marker = request.node.get_closest_marker("tq_id")
    tq_id = marker.args[0] if marker and marker.args else "TQ-UNASSIGNED"
    purpose = (request.node.function.__doc__ or "").strip().splitlines()
    record = TQRecord(tq_id, request.node.name, purpose[0] if purpose else "")
    request.node.stash[_TQ_STASH] = record
    yield record


_TQ_STASH = pytest.StashKey["TQRecord | None"]()
_REPORT_STASH = pytest.StashKey[str]()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call":
        return
    record = item.stash.get(_TQ_STASH, None)
    if record is None:
        return
    entry = {
        "tq_id": record.tq_id,
        "test": record.node_name,
        "purpose": record.purpose,
        "started_utc": record.started_utc,
        "completed_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "outcome": report.outcome.upper(),
        "expected_to_fail": bool(item.get_closest_marker("gap")),
        "duration_s": round(report.duration, 3),
        "observations": record.observations,
    }
    if report.failed and report.longreprtext:
        entry["failure_detail"] = report.longreprtext[-2000:]
    with open(EVIDENCE_FILE, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


def pytest_sessionstart(session: pytest.Session) -> None:
    # Start a clean evidence record for each qualification run.
    if EVIDENCE_FILE.exists():
        EVIDENCE_FILE.unlink()


def pytest_terminal_summary(terminalreporter, exitstatus, config) -> None:  # noqa: ARG001
    terminalreporter.write_sep("=", "TQ-001 qualification record")
    terminalreporter.write_line(f"Evidence   : {EVIDENCE_FILE}")
    terminalreporter.write_line(f"Environment: {ENVIRONMENT_FILE}")
    terminalreporter.write_line(
        "Attach both files to the TQ-001 report and FRM-CSA-03. "
        "Mandatory cases must all pass; gap cases must match their documented "
        "expected outcome."
    )
