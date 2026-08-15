"""Checks on the TQ-001 report renderer.

The renderer's job is to state what a qualification run actually showed. The
failure that matters is the quiet one: a requirement reported as verified when
its case did not pass, or a register that has fallen behind the suite so that
untested cases are counted as covered. These live here rather than in
tool_qualification/ because they test the reporting tool, not pytest-gxp, and
adding them there would enrol them in the qualification case register.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

TQ_DIR = Path(__file__).resolve().parent.parent / "tool_qualification"


def _load(name: str):
    if str(TQ_DIR) not in sys.path:
        sys.path.insert(0, str(TQ_DIR))
    spec = importlib.util.spec_from_file_location(name, TQ_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tq_report = _load("tq_report")
tq_requirements = _load("tq_requirements")


def _declared_case_ids() -> set[str]:
    """Every TQ ID the suite actually declares, read from its markers."""
    ids = set()
    for path in TQ_DIR.glob("test_tq*.py"):
        ids.update(re.findall(r'@pytest\.mark\.tq_id\("([^"]+)"\)', path.read_text()))
    return ids


def _case(tq_id: str, outcome: str = "PASSED") -> dict:
    return {
        "tq_id": tq_id,
        "test": f"test_{tq_id.replace('-', '_').replace('.', '_')}",
        "purpose": "purpose",
        "outcome": outcome,
        "expected_to_fail": False,
        "duration_s": 0.1,
        "observations": {},
    }


def test_every_declared_case_is_registered_against_a_requirement():
    """The register cannot fall behind the suite without the report saying so."""
    declared = _declared_case_ids()
    registered = tq_requirements.registered_cases()
    assert declared, "no TQ cases were found; the marker pattern has changed"
    assert declared == registered, (
        f"cases missing from tq_requirements.py: {sorted(declared - registered)}; "
        f"registered but not in the suite: {sorted(registered - declared)}"
    )


def test_a_requirement_is_not_verified_when_a_case_did_not_pass():
    req_id, req = next(iter(tq_requirements.REQUIREMENTS.items()))
    all_passed = {c: _case(c) for c in req["cases"]}
    assert tq_report._requirement_status(all_passed)[req_id]["verified"]

    one_failed = dict(all_passed)
    one_failed[req["cases"][0]] = _case(req["cases"][0], "FAILED")
    assert not tq_report._requirement_status(one_failed)[req_id]["verified"]

    # A case that never ran must not be silently treated as verified either.
    none_ran = {}
    status = tq_report._requirement_status(none_ran)[req_id]
    assert not status["verified"]
    assert status["missing"] == list(req["cases"])


def test_report_marks_a_failed_run_provisional_and_names_the_case():
    cases = [_case(c) for c in tq_requirements.registered_cases()]
    cases[0]["outcome"] = "FAILED"
    text = tq_report.build_markdown(cases, {"pytest_gxp_version_installed": "9.9.9"})

    assert "PROVISIONAL" in text
    assert cases[0]["tq_id"] in text
    assert "Requirements traceability matrix" in text


def test_report_of_a_clean_run_carries_no_provisional_banner(tmp_path, monkeypatch):
    """The banner must clear when there is nothing to report, or it means nothing."""
    monkeypatch.chdir(tmp_path)
    for name in tq_report.ATTACHED_RECORDS:
        (tmp_path / name).write_text("record")

    cases = [_case(c) for c in tq_requirements.registered_cases()]
    env = {"pytest_gxp_version_installed": "9.9.9", "pinned_version_declared": "9.9.9"}
    text = tq_report.build_markdown(cases, env)

    assert "PROVISIONAL" not in text
    assert "No findings." in text
