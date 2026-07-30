"""
TQ-2 — Specification parsing fidelity.

If a requirement is misparsed or silently dropped, the traceability matrix is
wrong in a way that inspection of the matrix alone cannot reveal. These cases
establish that what was authored is what was parsed.
"""

from __future__ import annotations

import pytest

import tq_config as cfg
import tq_helpers as h


def _all_four_specs(pytester):
    h.write_spec(
        pytester,
        "installation",
        [h.Requirement("IS-001", "Application deployed at pinned version")],
    )
    h.write_spec(
        pytester,
        "design",
        [h.Requirement("DS-001", "Audit trail table is append-only")],
    )
    h.write_spec(
        pytester,
        "functional",
        [
            h.Requirement(
                "FS-001",
                "Released batch record fields are immutable",
                description="Once a batch record is released, defined fields cannot be modified.",
                details=[
                    "Attempted modification is rejected.",
                    "The attempt is recorded in the audit trail.",
                ],
                expected="Modification is rejected and the attempt is logged.",
                metadata={"Priority": "High", "Category": "Data Integrity", "Owner": "QA"},
            ),
            h.Requirement("FS-002", "Report totals recalculated on render"),
        ],
    )
    h.write_spec(
        pytester,
        "user",
        [h.Requirement("US-001", "Reviewer can complete a batch review without export")],
    )
    (pytester.path / "test_all.py").write_text(
        "import pytest\n"
        "\n"
        "def _t(req):\n"
        "    pass\n"
        "\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['IS-001'])\n"
        "def test_is_001():\n"
        "    assert True\n"
        "\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['DS-001'])\n"
        "def test_ds_001():\n"
        "    assert True\n"
        "\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['FS-001'])\n"
        "def test_fs_001():\n"
        "    assert True\n"
        "\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['FS-002'])\n"
        "def test_fs_002():\n"
        "    assert True\n"
        "\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['US-001'])\n"
        "def test_us_001():\n"
        "    assert True\n",
        encoding="utf-8",
    )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-2.1")
def test_all_specification_types_are_parsed(pytester, tq):
    """Requirements from all four specification types appear in the generated records."""
    _all_four_specs(pytester)
    h.run_gxp(pytester)

    matrix = h.read_text_artefact(pytester.path, cfg.ARTEFACT_MATRIX_MD)
    report_text = h.find_artefact(pytester.path, cfg.ARTEFACT_REPORT_JSON).read_text("utf-8")
    expected = ["IS-001", "DS-001", "FS-001", "FS-002", "US-001"]
    missing_matrix = [r for r in expected if r not in matrix]
    missing_report = [r for r in expected if r not in report_text]
    tq.observe(missing_from_matrix=missing_matrix, missing_from_report=missing_report)
    assert not missing_matrix, f"Requirements absent from the traceability matrix: {missing_matrix}"
    assert not missing_report, f"Requirements absent from the validation report: {missing_report}"


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-2.2")
def test_requirement_count_matches_authored_count(pytester, tq):
    """Parsed requirements equal those authored — none dropped, none invented."""
    authored = [h.Requirement(f"FS-{n:03d}", f"Requirement {n}") for n in range(1, 13)]
    h.write_spec(pytester, "functional", authored)
    lines = ["import pytest", ""]
    for req in authored:
        fn = req.req_id.replace("-", "_").lower()
        lines += [
            "@pytest.mark.gxp",
            f"@pytest.mark.requirements(['{req.req_id}'])",
            f"def test_{fn}():",
            "    assert True",
            "",
        ]
    (pytester.path / "test_many.py").write_text("\n".join(lines), encoding="utf-8")

    h.run_gxp(pytester)
    report_text = h.find_artefact(pytester.path, cfg.ARTEFACT_REPORT_JSON).read_text("utf-8")
    found = [req.req_id for req in authored if req.req_id in report_text]
    total_reported = h.deep_get(h.load_report(pytester.path), "total_requirements")
    tq.observe(
        authored_count=len(authored),
        found_count=len(found),
        reported_total_requirements=total_reported,
        not_found=[r.req_id for r in authored if r.req_id not in found],
    )
    assert len(found) == len(authored), (
        f"{len(authored) - len(found)} authored requirement(s) do not appear in "
        "the report. Silent loss of a requirement invalidates the traceability claim."
    )
    if total_reported is not None:
        assert int(total_reported) == len(authored), (
            f"Report states {total_reported} total requirements; {len(authored)} were authored."
        )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-2.3")
def test_requirement_prefix_maps_to_correct_qualification_phase(pytester, tq):
    """Each requirement prefix is attributed to the correct specification type.

    A DS/FS requirement surfacing as PQ, or a US requirement as OQ, would place
    evidence in the wrong qualification phase.
    """
    _all_four_specs(pytester)
    h.run_gxp(pytester)

    rows = h.load_csv_rows(pytester.path, cfg.ARTEFACT_MATRIX_CSV)
    observed: dict[str, set[str]] = {}
    for row in rows:
        req = (row.get("Requirement ID") or "").strip()
        spec = (row.get("Specification Type") or "").strip()
        if req:
            observed.setdefault(req, set()).add(spec)
    tq.observe(observed_specification_types={k: sorted(v) for k, v in observed.items()})

    expectations = {
        "IS-001": "installation",
        "DS-001": "design",
        "FS-001": "functional",
        "US-001": "user",
    }
    problems = []
    for req, expected_word in expectations.items():
        types = observed.get(req)
        if not types:
            problems.append(f"{req}: absent from matrix")
            continue
        if not any(expected_word in t.lower() for t in types):
            problems.append(f"{req}: expected a {expected_word!r} type, got {sorted(types)}")
    assert not problems, "Specification type attribution errors: " + "; ".join(problems)


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-2.4")
def test_requirement_title_and_expected_result_are_preserved(pytester, tq):
    """Requirement title and expected result are carried into the record verbatim."""
    title = "Released batch record fields are immutable"
    expected = "Modification is rejected and the attempt is written to the audit trail."
    h.write_spec(
        pytester,
        "functional",
        [h.Requirement("FS-001", title, expected=expected)],
    )
    (pytester.path / "test_one.py").write_text(
        "import pytest\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['FS-001'])\n"
        "def test_fs_001():\n"
        "    assert True\n",
        encoding="utf-8",
    )
    h.run_gxp(pytester)

    md = h.read_text_artefact(pytester.path, cfg.ARTEFACT_REPORT_MD)
    matrix = h.read_text_artefact(pytester.path, cfg.ARTEFACT_MATRIX_MD)
    cases = [
        c for c in h.test_cases(h.load_report(pytester.path)) if "FS-001" in h.requirements_of(c)
    ]
    recorded = [str(c.get("expected_result", "")) for c in cases]
    tq.observe(
        title_in_human_readable=title in (md + matrix),
        recorded_expected_results=recorded,
        expected_result_in_markdown=expected in (md + matrix),
    )
    assert title in (md + matrix), (
        "The requirement title was not reproduced in the human-readable records. "
        "A reviewer cannot confirm which requirement was verified."
    )
    assert cases, "No test case in the report is associated with FS-001."
    assert any(expected in value for value in recorded), (
        "The stated expected result was not reproduced in the report record. "
        "Without it the pass determination has no documented acceptance "
        f"criterion. Recorded instead: {recorded}."
    )
    tq.note(
        "expected_result is carried in the JSON record but is not rendered in the "
        "Markdown or PDF test case table. A reviewer working from the rendered "
        "report alone must read the acceptance criterion from the specification."
    )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-2.5")
def test_metadata_key_values_are_preserved(pytester, tq):
    """Requirement metadata is captured as authored."""
    h.write_spec(
        pytester,
        "functional",
        [
            h.Requirement(
                "FS-001",
                "Metadata carrier",
                metadata={
                    "Priority": "High",
                    "Category": "Data Integrity",
                    "Owner": "QA",
                    "Traces-To": "URS-014",
                    "Risk-Tier": "1",
                },
            )
        ],
    )
    (pytester.path / "test_one.py").write_text(
        "import pytest\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['FS-001'])\n"
        "def test_fs_001():\n"
        "    assert True\n",
        encoding="utf-8",
    )
    h.run_gxp(pytester)

    blob = h.find_artefact(pytester.path, cfg.ARTEFACT_REPORT_JSON).read_text(
        "utf-8"
    ) + h.read_text_artefact(pytester.path, cfg.ARTEFACT_REPORT_MD)
    checks = {
        k: (k in blob and v in blob)
        for k, v in {"Priority": "High", "Category": "Data Integrity", "Owner": "QA"}.items()
    }
    traces = "URS-014" in blob
    tq.observe(metadata_checks=checks, traces_to_preserved=traces)
    assert all(checks.values()), (
        f"Metadata not preserved: {[k for k, v in checks.items() if not v]}"
    )
    assert traces, (
        "The Traces-To value was not carried into the record. Validation Plan "
        "Section 6.9 relies on it to link derived specifications to the controlled URS."
    )


FINDINGS_SECTION = "GxP validation findings"


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-2.6")
def test_duplicate_requirement_id_is_detected(pytester, tq):
    """A duplicated requirement ID raises a located finding rather than collapsing silently.

    Two conflicting definitions of one requirement must not be reduced to one
    without a record of which was verified.
    """
    h.write_spec(
        pytester,
        "functional",
        [
            h.Requirement("FS-001", "First definition"),
            h.Requirement("FS-001", "Conflicting second definition"),
        ],
    )
    (pytester.path / "test_one.py").write_text(
        "import pytest\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['FS-001'])\n"
        "def test_fs_001():\n"
        "    assert True\n",
        encoding="utf-8",
    )
    result = h.run_gxp(pytester)
    output = "\n".join(result.outlines)
    report = h.load_report(pytester.path)
    duplicates = h.findings(report, "duplicate-requirement-id")
    spec_file = f"{cfg.SPEC_FILES['functional']}.md"
    tq.observe(
        reported_total_requirements=h.deep_get(report, "total_requirements"),
        duplicate_findings=duplicates,
        findings_section_printed=FINDINGS_SECTION in output,
        exit_code=result.ret,
    )
    assert duplicates, (
        "No 'duplicate-requirement-id' finding was raised for a requirement "
        "defined twice. Two conflicting definitions can be collapsed without "
        f"notice. Findings present: {[f.get('code') for f in h.findings(report)]}."
    )
    assert all(f["severity"] == "error" for f in duplicates), (
        f"A duplicated requirement ID is not an error-severity finding: {duplicates}."
    )
    located = [f for f in duplicates if f.get("location", "").startswith(f"{spec_file}:")]
    assert located, (
        f"No duplicate finding is located in {spec_file} with a line number. A "
        f"finding a reviewer cannot locate is not actionable: {duplicates}."
    )
    assert all("FS-001" in f["message"] for f in duplicates), (
        f"The finding does not name the duplicated requirement: {duplicates}."
    )
    assert FINDINGS_SECTION in output, (
        f"The console output has no {FINDINGS_SECTION!r} section, so the finding "
        "is only visible to someone who opens the JSON record."
    )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-2.7")
def test_malformed_requirement_heading_is_not_silently_dropped(pytester, tq):
    """A heading that only looks like a requirement is reported, not ignored.

    Without this, a requirement can be authored, approved, and silently omitted
    from the scope of qualification.
    """
    h.write_raw_spec(
        pytester,
        "functional",
        "# Functional Specification\n"
        "\n"
        "## Version: 1.0\n"
        "\n"
        "### FS-001: Correctly formed requirement\n"
        "\n"
        "#### Description\n"
        "Well formed.\n"
        "\n"
        "Expected Result: Parsed.\n"
        "\n"
        "### FS-002 Missing the colon separator\n"
        "\n"
        "#### Description\n"
        "This heading omits the colon and so may not match the parser pattern.\n"
        "\n"
        "Expected Result: Should still be surfaced, or reported as malformed.\n",
    )
    (pytester.path / "test_one.py").write_text(
        "import pytest\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['FS-001'])\n"
        "def test_fs_001():\n"
        "    assert True\n",
        encoding="utf-8",
    )
    result = h.run_gxp(pytester)
    output = "\n".join(result.outlines)
    report = h.load_report(pytester.path)
    malformed = h.findings(report, "malformed-requirement-heading")
    spec_file = f"{cfg.SPEC_FILES['functional']}.md"
    tq.observe(
        malformed_findings=malformed,
        findings_section_printed=FINDINGS_SECTION in output,
        fs_001_parsed="FS-001"
        in h.find_artefact(pytester.path, cfg.ARTEFACT_REPORT_JSON).read_text("utf-8"),
    )
    assert malformed, (
        "A heading matching the requirement-ID shape but not the required form "
        "produced no 'malformed-requirement-heading' finding. Findings present: "
        f"{[f.get('code') for f in h.findings(report)]}."
    )
    located = [f for f in malformed if f.get("location", "").startswith(f"{spec_file}:")]
    assert located, (
        f"No malformed-heading finding is located in {spec_file} with a line number: {malformed}."
    )
    assert any("FS-002" in f["message"] for f in malformed), (
        f"The finding does not quote the offending heading: {malformed}."
    )
    assert FINDINGS_SECTION in output, f"The console output has no {FINDINGS_SECTION!r} section."
