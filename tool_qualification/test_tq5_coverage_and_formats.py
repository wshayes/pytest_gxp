"""
TQ-5 — Coverage arithmetic and cross-format consistency.

Every rate reported in the record is independently recomputed here from the
underlying test case list. A reviewer performing FRM-CSA-02 Section B by hand is
doing the same arithmetic; these cases establish that the tool's figures survive it.

Cross-format consistency matters because the PDF is what gets signed while the
JSON is what gets queried. If they disagree, the signed record is not the
reviewed record.
"""

from __future__ import annotations

from collections import Counter

import pytest

import tq_config as cfg
import tq_helpers as h

# 6 requirements; 5 have tests; of those, 3 pass, 1 fails, 1 is skipped.
SPEC = [h.Requirement(f"FS-{n:03d}", f"Requirement {n}") for n in range(1, 7)]

SUITE = """\
import pytest

@pytest.mark.gxp
@pytest.mark.requirements(['FS-001'])
def test_a():
    assert True

@pytest.mark.gxp
@pytest.mark.requirements(['FS-002'])
def test_b():
    assert True

@pytest.mark.gxp
@pytest.mark.requirements(['FS-003'])
def test_c():
    assert True

@pytest.mark.gxp
@pytest.mark.requirements(['FS-004'])
def test_d():
    assert 1 == 2, 'deliberate failure for TQ-5'

@pytest.mark.gxp
@pytest.mark.requirements(['FS-005'])
@pytest.mark.skip(reason='deliberate skip for TQ-5')
def test_e():
    assert True
"""

# The record keeps two registers and they count different things. Both are
# asserted, because a discrepancy between them is invisible from either alone.
#
# Per-requirement register (`test_summary`, `test_cases`): one entry per
# requirement, carrying the rolled-up status of the tests citing it. FS-006 has
# no test, so it is NOT_EXECUTED.
EXPECTED_REQUIREMENT_REGISTER = {
    "total_test_cases": 6,
    "passed": 3,
    "failed": 1,
    "skipped": 1,
    "errors": 0,
    "not_executed": 1,
}

# Executed-test register (`test_execution`): one entry per real pytest node.
EXPECTED_EXECUTED_OUTCOMES = {"PASSED": 3, "FAILED": 1, "SKIPPED": 1}

EXPECTED_COVERAGE = {
    "total_requirements": 6,
    "requirements_with_tests": 5,
    "requirements_without_tests": 1,
    "requirements_verified": 3,
}


def _build(pytester):
    h.write_spec(pytester, "functional", SPEC)
    (pytester.path / "test_suite.py").write_text(SUITE, encoding="utf-8")
    return h.run_gxp(pytester)


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-5.1")
def test_test_counts_match_the_suite(pytester, tq):
    """Both registers in the record account for exactly the tests that ran.

    The per-requirement register must roll every requirement up correctly, and
    the executed-test register must name every real test once. A count that is
    right in one register and wrong in the other is the harder error to see.
    """
    result = _build(pytester)
    report = h.load_report(pytester.path)
    summary = h.deep_get(report, "test_summary", {})
    executed = h.executed_tests(report)
    outcomes = Counter(str(e.get("outcome", "")) for e in executed)
    pytest_outcomes = result.parseoutcomes()
    tq.observe(
        test_summary=summary,
        executed_outcomes=dict(outcomes),
        executed_node_ids=sorted(e["node_id"] for e in executed),
        pytest_outcomes=pytest_outcomes,
    )

    for key, expected in EXPECTED_REQUIREMENT_REGISTER.items():
        assert summary.get(key) is not None, f"The test summary omits {key!r}."
        assert int(summary[key]) == expected, (
            f"The per-requirement register reports {key}={summary[key]}; six "
            f"requirements with these results give {expected}."
        )
    assert dict(outcomes) == EXPECTED_EXECUTED_OUTCOMES, (
        f"The executed-test register reports {dict(outcomes)}; the suite ran "
        f"{EXPECTED_EXECUTED_OUTCOMES}."
    )
    # And the executed register must agree with pytest's own tally.
    for outcome, key in (("PASSED", "passed"), ("FAILED", "failed"), ("SKIPPED", "skipped")):
        assert outcomes[outcome] == pytest_outcomes.get(key, 0), (
            f"The record states {outcomes[outcome]} {outcome} test(s) but pytest "
            f"reported {pytest_outcomes.get(key, 0)}."
        )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-5.2")
def test_pass_rate_is_arithmetically_consistent(pytester, tq):
    """The reported pass rate recomputes from the reported counts.

    Two denominators are documented — passed/(passed+failed) and passed/total —
    so either is accepted, but the figure must recompute from one of them. A rate
    that matches neither means the record cannot be checked by hand.
    """
    _build(pytester)
    report = h.load_report(pytester.path)
    summary = h.deep_get(report, "test_summary", {})
    reported = summary.get("pass_rate")
    total = int(summary["total_test_cases"])
    passed = int(summary["passed"])
    failed = int(summary["failed"])
    candidates = {
        "passed/(passed+failed)": round(100.0 * passed / (passed + failed), 1)
        if passed + failed
        else 0.0,
        "passed/total": round(100.0 * passed / total, 1) if total else 0.0,
    }
    tq.observe(
        reported_pass_rate=reported,
        candidate_rates=candidates,
        passed=passed,
        failed=failed,
        total=total,
    )
    assert reported is not None, "Report omits 'pass_rate'."
    matched = [
        name
        for name, value in candidates.items()
        if abs(float(reported) - value) <= cfg.RATE_TOLERANCE
    ]
    assert matched, (
        f"Reported pass rate {reported} recomputes to none of the documented "
        f"definitions {candidates}. The arithmetic in the record cannot be "
        "reproduced by a reviewer."
    )
    tq.observe(matched_definition=matched)


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-5.3")
def test_requirement_coverage_rate_is_arithmetically_consistent(pytester, tq):
    """The reported coverage rate recomputes from requirements with tests over total.

    Read from the authoritative `requirement_coverage` block, which the report
    format documents as the requirement coverage metrics.
    """
    _build(pytester)
    report = h.load_report(pytester.path)
    block = h.deep_get(report, "requirement_coverage", {})
    total = int(block["total_requirements"])
    with_tests = int(block["requirements_with_tests"])
    reported = block.get("coverage_rate")
    recomputed = round(100.0 * with_tests / total, 1) if total else 0.0
    tq.observe(
        requirement_coverage=block,
        recomputed_coverage_rate=recomputed,
        legacy_coverage_block=h.deep_get(report, "coverage", {}),
    )
    for key, expected in EXPECTED_COVERAGE.items():
        if key in block:
            assert int(block[key]) == expected, (
                f"The requirement coverage block reports {key}={block[key]}; the "
                f"suite gives {expected}. FS-006 has no test."
            )
    assert reported is not None, "The requirement coverage block omits 'coverage_rate'."
    assert abs(float(reported) - recomputed) <= cfg.RATE_TOLERANCE, (
        f"Reported coverage rate {reported} does not recompute from "
        f"{with_tests}/{total} = {recomputed}."
    )
    tq.note(
        "The legacy 'coverage' block is recorded as an observation only. It counts "
        "the generated per-requirement cases rather than real tests, so its "
        "requirements_with_tests, requirement_coverage_rate and "
        "uncovered_requirements disagree with the authoritative block. Reviewers "
        "must read requirement_coverage, and this discrepancy is carried as an "
        "open finding against the tool."
    )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-5.4")
def test_verification_rate_reflects_only_passing_tests(pytester, tq):
    """Verified requirements exclude those whose tests failed or were skipped."""
    _build(pytester)
    report = h.load_report(pytester.path)
    block = h.deep_get(report, "requirement_coverage", {})
    verified = block.get("requirements_verified")
    rate = block.get("verification_rate")
    with_tests = int(block["requirements_with_tests"])
    total = int(block["total_requirements"])
    candidates = {
        "verified/with_tests": round(100.0 * int(verified or 0) / with_tests, 1)
        if with_tests
        else 0.0,
        "verified/total": round(100.0 * int(verified or 0) / total, 1) if total else 0.0,
    }
    tq.observe(
        requirements_verified=verified,
        verification_rate=rate,
        candidate_rates=candidates,
        expected_verified=EXPECTED_COVERAGE["requirements_verified"],
        unverified=h.deep_get(report, "unverified_requirements"),
    )
    assert verified is not None, (
        "Report omits 'requirements_verified'. Without it the record cannot "
        "distinguish a requirement that has a test from one that is verified."
    )
    assert int(verified) == EXPECTED_COVERAGE["requirements_verified"], (
        f"Reported {verified} verified requirements, expected "
        f"{EXPECTED_COVERAGE['requirements_verified']} — FS-004 failed and FS-005 "
        "was skipped, so neither is verified."
    )
    assert rate is not None, "The requirement coverage block omits 'verification_rate'."
    matched = [
        name for name, value in candidates.items() if abs(float(rate) - value) <= cfg.RATE_TOLERANCE
    ]
    assert matched, (
        f"Reported verification rate {rate} recomputes to none of {candidates}; "
        "the denominator is undocumented."
    )
    tq.observe(matched_definition=matched)


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-5.5")
def test_all_requested_output_formats_are_generated(pytester, tq):
    """Every format requested on the command line is produced."""
    h.write_spec(pytester, "functional", SPEC[:1])
    (pytester.path / "test_one.py").write_text(
        "import pytest\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['FS-001'])\n"
        "def test_a():\n"
        "    assert True\n",
        encoding="utf-8",
    )
    h.run_gxp(pytester, formats="csv,json,md")
    expected = [
        cfg.ARTEFACT_REPORT_CSV,
        cfg.ARTEFACT_REPORT_JSON,
        cfg.ARTEFACT_REPORT_MD,
        cfg.ARTEFACT_MATRIX_CSV,
        cfg.ARTEFACT_MATRIX_JSON,
        cfg.ARTEFACT_MATRIX_MD,
        cfg.ARTEFACT_COVERAGE_MD,
    ]
    missing = [name for name in expected if not h.artefact_exists(pytester.path, name)]
    tq.observe(expected_artefacts=expected, missing_artefacts=missing)
    assert not missing, f"Requested artefacts not generated: {missing}"


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-5.6")
def test_counts_are_consistent_across_formats(pytester, tq):
    """CSV, JSON, and Markdown renderings of the same run describe the same results.

    The signed artefact and the queried artefact must not disagree.
    """
    _build(pytester)
    report = h.load_report(pytester.path)
    json_cases = h.test_cases(report)
    csv_rows = h.load_csv_rows(pytester.path, cfg.ARTEFACT_REPORT_CSV)
    md_text = h.read_text_artefact(pytester.path, cfg.ARTEFACT_REPORT_MD)

    json_failed = sum(1 for c in json_cases if "FAIL" in h.status_of(c))
    csv_failed = sum(
        1 for row in csv_rows if "FAIL" in " ".join(str(v).upper() for v in row.values())
    )
    tq.observe(
        json_case_count=len(json_cases),
        csv_row_count=len(csv_rows),
        json_failed=json_failed,
        csv_failed=csv_failed,
        md_mentions_failed="FAIL" in md_text.upper(),
    )
    assert len(csv_rows) == len(json_cases), (
        f"The CSV report has {len(csv_rows)} rows and the JSON report "
        f"{len(json_cases)} test cases for the same run."
    )
    assert csv_failed == json_failed == EXPECTED_REQUIREMENT_REGISTER["failed"], (
        f"Failure count differs by format: CSV={csv_failed}, JSON={json_failed}, "
        f"expected {EXPECTED_REQUIREMENT_REGISTER['failed']}."
    )
    assert "FAIL" in md_text.upper(), (
        "The Markdown report does not mention the failure present in this run. "
        "A reader of the human-readable record would not see it."
    )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-5.7")
def test_pdf_is_rendered_and_substantive(pytester, tq):
    """The PDF renders to a plausible size and is a valid PDF.

    The PDF is the artefact that carries the signature, so a silent rendering
    failure producing a near-empty file must be detected.
    """
    unavailable = h.pdf_backend_reason()
    if unavailable:
        tq.observe(pdf_backend_unavailable=unavailable)
        pytest.skip(
            f"The PDF renderer cannot run in this environment: {unavailable}. "
            "This is an environment limitation, not a tool defect. Install the "
            "pdf extra and its native libraries; the CI tool-qualification job "
            "does so and executes this case for real."
        )
    h.write_spec(pytester, "functional", SPEC[:3])
    (pytester.path / "test_pdf.py").write_text(
        "import pytest\n"
        "\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['FS-001'])\n"
        "def test_a():\n"
        "    assert True\n"
        "\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['FS-002'])\n"
        "def test_b():\n"
        "    assert True\n",
        encoding="utf-8",
    )
    h.run_gxp(
        pytester,
        f"{cfg.FLAG_QUALIFICATION_TYPE}=OQ",
        formats="csv,json,md,pdf",
    )
    if not h.artefact_exists(pytester.path, cfg.ARTEFACT_REPORT_PDF):
        tq.observe(pdf_generated=False)
        pytest.fail(
            "No PDF was generated despite pdf being requested. Confirm the "
            "optional PDF dependencies are installed; a missing PDF must not be "
            "a silent outcome in a qualification run."
        )
    pdf = h.find_artefact(pytester.path, cfg.ARTEFACT_REPORT_PDF)
    size = pdf.stat().st_size
    head = pdf.read_bytes()[:5]
    tq.observe(pdf_bytes=size, pdf_header=head.decode("latin-1"), pdf_sha256=h.sha256_file(pdf))
    assert head == b"%PDF-", f"Generated PDF has an invalid header: {head!r}"
    assert size >= cfg.MIN_PDF_BYTES, (
        f"Generated PDF is only {size} bytes, below the {cfg.MIN_PDF_BYTES}-byte "
        "plausibility floor. This indicates a rendering failure that did not "
        "raise an error."
    )
