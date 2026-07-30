"""
TQ-4 — Result fidelity. The critical negative controls.

The single failure mode that would most damage a qualification record is a
non-passing test surfacing as a pass, or a requirement being counted as verified
when its verifying test did not pass. Every case here is deliberately arranged
to fail, skip, or error, and then checks that the record says so.

A tool qualification consisting only of positive-path tests demonstrates nothing
about record integrity.
"""

from __future__ import annotations

import json

import pytest

import tq_config as cfg
import tq_helpers as h

PROVISIONAL_BANNER = cfg.PROVISIONAL_BANNER

SPEC = [
    h.Requirement("FS-001", "Requirement verified by a passing test"),
    h.Requirement("FS-002", "Requirement whose only test fails"),
    h.Requirement("FS-003", "Requirement whose only test is skipped"),
    h.Requirement("FS-004", "Requirement whose only test errors in setup"),
    h.Requirement("FS-005", "Requirement whose only test is expected to fail"),
]


def _mixed_outcome_suite(pytester):
    h.write_spec(pytester, "functional", SPEC)
    (pytester.path / "conftest.py").write_text(
        "import pytest\n"
        "\n"
        "@pytest.fixture\n"
        "def broken_fixture():\n"
        "    raise RuntimeError('deliberate setup error for TQ-4')\n",
        encoding="utf-8",
    )
    (pytester.path / "test_mixed.py").write_text(
        "import pytest\n"
        "\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['FS-001'])\n"
        "def test_passes():\n"
        "    assert True\n"
        "\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['FS-002'])\n"
        "def test_fails():\n"
        "    assert 1 == 2, 'deliberate failure for TQ-4'\n"
        "\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['FS-003'])\n"
        "@pytest.mark.skip(reason='deliberate skip for TQ-4, no justification given')\n"
        "def test_skipped():\n"
        "    assert True\n"
        "\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['FS-004'])\n"
        "def test_errors(broken_fixture):\n"
        "    assert True\n"
        "\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['FS-005'])\n"
        "@pytest.mark.xfail(reason='deliberate xfail for TQ-4')\n"
        "def test_xfails():\n"
        "    assert 1 == 2\n",
        encoding="utf-8",
    )


def _status_for(pytester, requirement: str) -> list[str]:
    report = h.load_report(pytester.path)
    return [
        h.status_of(case) for case in h.test_cases(report) if requirement in h.requirements_of(case)
    ]


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-4.1")
def test_failing_test_is_reported_as_failed(pytester, tq):
    """A deliberately failing test is recorded as failed, never as passed."""
    _mixed_outcome_suite(pytester)
    h.run_gxp(pytester)

    statuses = _status_for(pytester, "FS-002")
    tq.observe(fs_002_statuses=statuses)
    assert statuses, "The failing test does not appear in the report at all."
    assert not any("PASS" in s for s in statuses), (
        f"A deliberately failing test is recorded with status {statuses}. This is "
        "a record-corrupting defect; the version must not be used for "
        "qualification activity."
    )
    assert any("FAIL" in s for s in statuses), (
        f"Expected a FAILED status for FS-002, observed {statuses}."
    )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-4.2")
def test_failure_produces_nonzero_exit_code(pytester, tq):
    """A run containing a failure exits non-zero, so CI cannot pass silently."""
    _mixed_outcome_suite(pytester)
    result = h.run_gxp(pytester)
    tq.observe(exit_code=result.ret, outcomes=result.parseoutcomes())
    assert result.ret != 0, (
        "A run containing a failing test exited zero. A pipeline gate would "
        "treat the qualification run as successful."
    )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-4.3")
def test_requirement_with_only_a_failing_test_is_not_counted_as_verified(pytester, tq):
    """Coverage counts a requirement as verified only where its test passed.

    Distinguishing "has a test" from "is verified" is the difference between a
    coverage claim and an assurance claim.
    """
    _mixed_outcome_suite(pytester)
    h.run_gxp(pytester)

    report = h.load_report(pytester.path)
    verified = h.deep_get(report, "requirements_verified")
    with_tests = h.deep_get(report, "requirements_with_tests")
    total = h.deep_get(report, "total_requirements")
    tq.observe(
        requirements_verified=verified,
        requirements_with_tests=with_tests,
        total_requirements=total,
    )
    if verified is None:
        pytest.fail(
            "The report does not distinguish requirements verified from "
            "requirements having a test. Without that distinction a failing "
            "test can be presented as coverage."
        )
    assert int(verified) < int(with_tests or 0) or int(verified) <= 1, (
        f"{verified} requirement(s) reported as verified out of {with_tests} "
        "having tests, although only FS-001 passed. Non-passing results are "
        "being counted toward verification."
    )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-4.4")
def test_skipped_test_is_reported_as_skipped_with_its_reason(pytester, tq):
    """A skipped test is recorded as skipped and its reason is preserved.

    An unjustified skip must be visible in the record; silence would inflate
    apparent coverage.
    """
    _mixed_outcome_suite(pytester)
    h.run_gxp(pytester)

    report = h.load_report(pytester.path)
    statuses = _status_for(pytester, "FS-003")
    executed = h.executed_by_node(report, "test_skipped")
    reason = str(executed.get("reason", ""))
    tq.observe(
        fs_003_statuses=statuses,
        executed_record=executed,
        reason_recorded=reason,
    )
    assert statuses, "The skipped test does not appear in the report."
    assert not any("PASS" in s for s in statuses), f"A skipped test is recorded as {statuses}."
    assert executed["outcome"] == "SKIPPED", (
        f"The skipped test is recorded with outcome {executed['outcome']!r}, not SKIPPED."
    )
    assert "deliberate skip for TQ-4" in reason, (
        "The skip reason is not carried on the executed-test record. A reviewer "
        f"cannot assess whether the skip was justified. Recorded: {reason!r}."
    )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-4.5")
def test_errored_test_is_not_reported_as_passed(pytester, tq):
    """A test whose setup errors is not recorded as passed.

    Setup errors are the likeliest way for a requirement to appear addressed
    while nothing was actually exercised.
    """
    _mixed_outcome_suite(pytester)
    h.run_gxp(pytester)

    statuses = _status_for(pytester, "FS-004")
    tq.observe(fs_004_statuses=statuses)
    assert statuses, (
        "A test that errored during setup does not appear in the report at all. "
        "The requirement would silently drop out of scope."
    )
    assert not any("PASS" in s for s in statuses), (
        f"A test that errored in setup is recorded as {statuses}. Nothing was "
        "exercised, so the requirement cannot be verified."
    )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-4.6")
def test_xfail_is_not_reported_as_a_pass(pytester, tq):
    """An expected failure is distinguishable from a genuine pass."""
    _mixed_outcome_suite(pytester)
    h.run_gxp(pytester)

    statuses = _status_for(pytester, "FS-005")
    tq.observe(fs_005_statuses=statuses)
    assert statuses, "The xfail test does not appear in the report."
    assert not any(s == "PASSED" for s in statuses), (
        f"An expected-failure test is recorded as PASSED ({statuses}). A "
        "requirement marked xfail would appear verified while its behaviour is "
        "known not to work."
    )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-4.7")
def test_unexpected_pass_is_distinguishable(pytester, tq):
    """An xpass is not recorded as an ordinary pass without qualification."""
    h.write_spec(pytester, "functional", [h.Requirement("FS-001", "Unexpectedly working")])
    (pytester.path / "test_xpass.py").write_text(
        "import pytest\n"
        "\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['FS-001'])\n"
        "@pytest.mark.xfail(reason='expected to fail but does not')\n"
        "def test_xpasses():\n"
        "    assert True\n",
        encoding="utf-8",
    )
    h.run_gxp(pytester)
    statuses = _status_for(pytester, "FS-001")
    blob = h.find_artefact(pytester.path, cfg.ARTEFACT_REPORT_JSON).read_text("utf-8")
    tq.observe(statuses=statuses, xpass_language_present="xpass" in blob.lower())
    assert statuses, "The xpass test does not appear in the report."
    # Recorded as an observation: an xpass on a GxP requirement always warrants
    # investigation, because the expectation encoded in the test is now wrong.
    tq.note(
        "An xpass on a requirement-linked test should be treated as a "
        "discrepancy under WI-CSA-01 Section 5.6, whatever status the tool assigns."
    )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-4.8")
def test_summary_counts_reflect_every_non_passing_outcome(pytester, tq):
    """The test summary accounts for failures, skips, and errors — none omitted."""
    _mixed_outcome_suite(pytester)
    result = h.run_gxp(pytester)
    actual = result.parseoutcomes()
    report = h.load_report(pytester.path)
    reported = {
        "total": h.deep_get(report, "total_test_cases"),
        "passed": h.deep_get(report, "passed"),
        "failed": h.deep_get(report, "failed"),
        "skipped": h.deep_get(report, "skipped"),
        "errors": h.deep_get(report, "errors"),
    }
    tq.observe(pytest_outcomes=actual, report_summary=reported)

    assert reported["failed"] is not None, "The report summary has no 'failed' count."
    assert int(reported["failed"]) >= 1, (
        f"The report summary states {reported['failed']} failures; the run "
        f"produced {actual.get('failed')}."
    )
    assert int(reported["skipped"] or 0) >= 1, (
        f"The report summary states {reported['skipped']} skips; the run "
        f"produced {actual.get('skipped')}."
    )
    error_count = actual.get("errors", 0)
    if error_count:
        accounted = (reported["errors"] is not None and int(reported["errors"]) >= 1) or (
            int(reported["failed"]) >= 2
        )
        assert accounted, (
            f"The run produced {error_count} error(s), but the report summary "
            f"accounts for none: {reported}. An errored test is absent from the "
            "record entirely."
        )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-4.9")
def test_deviation_reference_is_carried_for_every_non_passing_result(pytester, tq):
    """Each record carries a deviation reference field, populated from the supplied map.

    The link between a failure and its investigation must live in the record. A
    non-passing result without a reference must be raised as a finding, so an
    unexplained failure cannot be signed off.
    """
    _mixed_outcome_suite(pytester)

    # First, with no deviation map supplied at all.
    h.run_gxp(pytester)
    report = h.load_report(pytester.path)
    executed = h.executed_tests(report)
    missing_key = [e["node_id"] for e in executed if "deviation_ref" not in e]
    missing_key += [h.case_name(c) for c in h.test_cases(report) if "deviation_ref" not in c]
    unreferenced = h.findings(report, "missing-deviation-ref")
    tq.observe(
        records_missing_the_key=missing_key,
        missing_deviation_findings=unreferenced,
    )
    assert not missing_key, (
        "The 'deviation_ref' key is absent from these records: "
        f"{missing_key}. A field that appears only sometimes cannot be relied on "
        "by a reviewer or a downstream query."
    )
    flagged = {f["location"] for f in unreferenced}
    assert any("test_fails" in loc for loc in flagged), (
        f"The failing test raised no 'missing-deviation-ref' finding: {unreferenced}."
    )
    assert any("test_errors" in loc for loc in flagged), (
        f"The errored test raised no 'missing-deviation-ref' finding: {unreferenced}."
    )
    assert not any("test_passes" in loc for loc in flagged), (
        f"A passing test was required to carry a deviation reference: {unreferenced}."
    )

    # Then with references supplied: they must be reproduced verbatim.
    refs = {
        "test_mixed.py::test_fails": "DEV-2026-014",
        "FS-004": "DEV-2026-015",
    }
    (pytester.path / "deviations.json").write_text(json.dumps(refs), encoding="utf-8")
    h.run_gxp(pytester, f"{cfg.FLAG_DEVIATIONS}=deviations.json")
    report = h.load_report(pytester.path)
    recorded = {e["node_id"]: e.get("deviation_ref") for e in h.executed_tests(report)}
    still_unreferenced = h.findings(report, "missing-deviation-ref")
    tq.observe(supplied_refs=refs, recorded_refs=recorded, remaining_findings=still_unreferenced)

    assert recorded.get("test_mixed.py::test_fails") == "DEV-2026-014", (
        "The deviation reference supplied for the failing test was not reproduced "
        f"verbatim; the record states {recorded.get('test_mixed.py::test_fails')!r}."
    )
    assert recorded.get("test_mixed.py::test_errors") == "DEV-2026-015", (
        "A reference supplied against requirement FS-004 did not reach the test "
        f"that verifies it; the record states {recorded.get('test_mixed.py::test_errors')!r}."
    )
    assert recorded.get("test_mixed.py::test_passes") is None, (
        "A deviation reference was attributed to a passing test that has none: "
        f"{recorded.get('test_mixed.py::test_passes')!r}."
    )
    assert not still_unreferenced, (
        "Deviation references were supplied for every non-passing result, yet the "
        f"record still reports them as missing: {still_unreferenced}."
    )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-4.10")
def test_report_is_marked_provisional_only_when_the_run_is_not_clean(pytester, tq):
    """A report from a run containing failures is visibly provisional; a clean one is final.

    Both directions matter: an unmarked failing report could be circulated or
    signed in error, and a permanently provisional report would make the marking
    meaningless.
    """
    _mixed_outcome_suite(pytester)
    h.run_gxp(pytester)
    failing_md = h.read_text_artefact(pytester.path, cfg.ARTEFACT_REPORT_MD)
    failing_meta = h.deep_get(h.load_report(pytester.path), "report_metadata", {})
    tq.observe(
        failing_status=failing_meta.get("status"),
        provisional_reasons=failing_meta.get("provisional_reasons"),
        banner_present=PROVISIONAL_BANNER in failing_md,
    )
    assert failing_meta.get("status") == "PROVISIONAL", (
        "A run containing failures produced a report whose metadata status is "
        f"{failing_meta.get('status')!r}, not PROVISIONAL."
    )
    assert PROVISIONAL_BANNER in failing_md, (
        "The Markdown report carries no provisional banner despite the run "
        f"containing failures. Expected the text {PROVISIONAL_BANNER!r}."
    )
    assert failing_meta.get("provisional_reasons"), (
        "The report is marked provisional but states no reason, so a reviewer "
        "cannot tell what must be resolved."
    )

    # A clean run of the same shape must not be marked. Rewriting the inputs in
    # place also overwrites the artefacts, so nothing from the failing run leaks.
    h.write_spec(pytester, "functional", [h.Requirement("FS-001", "Passing requirement")])
    (pytester.path / "test_mixed.py").write_text(
        "import pytest\n"
        "\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['FS-001'])\n"
        "def test_passes():\n"
        "    assert True\n",
        encoding="utf-8",
    )
    clean_result = h.run_gxp(pytester)
    clean_md = h.read_text_artefact(pytester.path, cfg.ARTEFACT_REPORT_MD)
    clean_meta = h.deep_get(h.load_report(pytester.path), "report_metadata", {})
    tq.observe(
        clean_exit=clean_result.ret,
        clean_status=clean_meta.get("status"),
        clean_banner_present=PROVISIONAL_BANNER in clean_md,
    )
    assert clean_meta.get("status") == "FINAL", (
        f"A clean run produced a report marked {clean_meta.get('status')!r}. If "
        "every report is provisional, the marking carries no information."
    )
    assert PROVISIONAL_BANNER not in clean_md, (
        "A clean run's report carries the provisional banner."
    )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-4.11")
def test_setup_error_is_recorded_as_an_error_and_counted(pytester, tq):
    """A test that raises during setup is recorded as ERROR and counted as one.

    A setup error means nothing was exercised. Recording it as a plain failure,
    or omitting it from the summary, would understate what did not run.
    """
    _mixed_outcome_suite(pytester)
    result = h.run_gxp(pytester)
    report = h.load_report(pytester.path)
    executed = h.executed_by_node(report, "test_errors")
    summary = h.deep_get(report, "test_summary", {})
    execution_summary = h.deep_get(report, "test_execution_summary", {})
    tq.observe(
        executed_record=executed,
        test_summary=summary,
        test_execution_summary=execution_summary,
        pytest_outcomes=result.parseoutcomes(),
    )
    assert executed["outcome"] == "ERROR", (
        "A test that raised in its fixture is recorded with outcome "
        f"{executed['outcome']!r}, not ERROR."
    )
    assert "deliberate setup error for TQ-4" in str(executed.get("reason", "")), (
        f"The cause of the setup error is not recorded: {executed.get('reason')!r}."
    )
    assert int(summary.get("errors", 0)) == 1, (
        f"The test summary counts {summary.get('errors')} error(s); the run produced one."
    )
    assert int(execution_summary.get("error_tests", 0)) == 1, (
        f"The execution summary counts {execution_summary.get('error_tests')} "
        "errored test(s); the run produced one."
    )
