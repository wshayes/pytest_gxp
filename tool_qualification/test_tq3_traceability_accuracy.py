"""
TQ-3 — Traceability accuracy.

Traceability is the central claim of the record. These cases establish that the
mapping is correct in both directions and that it does not over-report: a matrix
that attributes a test to a requirement it does not verify is worse than no
matrix, because it looks like assurance.
"""

from __future__ import annotations

import pytest

import tq_config as cfg
import tq_helpers as h

SPEC = [
    h.Requirement("FS-001", "First requirement"),
    h.Requirement("FS-002", "Second requirement"),
    h.Requirement("FS-003", "Third requirement, deliberately untested"),
    h.Requirement("FS-004", "Fourth requirement, multiply tested"),
]


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-3.1")
def test_test_is_attributed_to_its_requirement_only(pytester, tq):
    """A test marked for one requirement is attributed to that requirement and no other."""
    h.write_spec(pytester, "functional", SPEC)
    (pytester.path / "test_attrib.py").write_text(
        "import pytest\n"
        "\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['FS-001'])\n"
        "def test_only_fs_001():\n"
        "    assert True\n"
        "\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['FS-002'])\n"
        "def test_only_fs_002():\n"
        "    assert True\n",
        encoding="utf-8",
    )
    h.run_gxp(pytester)

    report = h.load_report(pytester.path)
    executed = {e["node_id"]: e.get("requirement_ids", []) for e in h.executed_tests(report)}
    pairs = h.matrix_pairs(pytester.path)
    tq.observe(
        executed_requirement_map=executed,
        matrix_pairs=sorted(f"{r}<-{t}" for r, t in pairs),
    )

    first = h.executed_by_node(report, "test_only_fs_001")
    second = h.executed_by_node(report, "test_only_fs_002")
    assert first["requirement_ids"] == ["FS-001"], (
        f"The test marked for FS-001 is attributed to {first['requirement_ids']}. "
        "Cross-attribution overstates coverage."
    )
    assert second["requirement_ids"] == ["FS-002"], (
        f"The test marked for FS-002 is attributed to {second['requirement_ids']}."
    )

    # The matrix must make the same statement, keyed by the real node id.
    nodes_for_fs_001 = {t for r, t in pairs if r == "FS-001"}
    nodes_for_fs_002 = {t for r, t in pairs if r == "FS-002"}
    assert any("test_only_fs_001" in t for t in nodes_for_fs_001), (
        f"The matrix does not trace FS-001 to its test; it lists {sorted(nodes_for_fs_001)}."
    )
    assert not any("test_only_fs_002" in t for t in nodes_for_fs_001), (
        f"The matrix attributes the FS-002 test to FS-001: {sorted(nodes_for_fs_001)}."
    )
    assert not any("test_only_fs_001" in t for t in nodes_for_fs_002), (
        f"The matrix attributes the FS-001 test to FS-002: {sorted(nodes_for_fs_002)}."
    )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-3.2")
def test_multi_requirement_marker_produces_one_entry_per_requirement(pytester, tq):
    """A test marked for several requirements is traced to each of them."""
    h.write_spec(pytester, "functional", SPEC)
    (pytester.path / "test_multi.py").write_text(
        "import pytest\n"
        "\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['FS-001', 'FS-002'])\n"
        "def test_covers_two():\n"
        "    assert True\n",
        encoding="utf-8",
    )
    h.run_gxp(pytester)

    pairs = h.matrix_pairs(pytester.path)
    covered = {req for req, _ in pairs}
    tq.observe(matrix_pairs=sorted(f"{r}<-{t}" for r, t in pairs))
    assert {"FS-001", "FS-002"} <= covered, (
        f"Multi-requirement marker did not produce an entry for each requirement. "
        f"Covered: {sorted(covered)}"
    )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-3.3")
def test_multiple_tests_for_one_requirement_are_all_listed(pytester, tq):
    """All tests verifying a requirement appear against it, not only the first."""
    h.write_spec(pytester, "functional", SPEC)
    (pytester.path / "test_repeat.py").write_text(
        "import pytest\n"
        "\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['FS-004'])\n"
        "def test_fs_004_positive():\n"
        "    assert True\n"
        "\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['FS-004'])\n"
        "def test_fs_004_boundary():\n"
        "    assert True\n"
        "\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['FS-004'])\n"
        "def test_fs_004_negative():\n"
        "    assert True\n",
        encoding="utf-8",
    )
    h.run_gxp(pytester)

    pairs = h.matrix_pairs(pytester.path)
    entries = sorted(t for r, t in pairs if r == "FS-004")
    executed = sorted(
        e["node_id"]
        for e in h.executed_tests(h.load_report(pytester.path))
        if "FS-004" in e.get("requirement_ids", [])
    )
    tq.observe(fs_004_matrix_entries=entries, fs_004_executed=executed)
    for suffix in ("positive", "boundary", "negative"):
        assert any(suffix in entry for entry in entries), (
            f"The matrix has no entry naming the {suffix!r} test of FS-004; it "
            f"lists {entries}. Losing the negative-path test from the record "
            "would leave negative testing unevidenced."
        )
    assert len(executed) == 3, (
        f"{len(executed)} test(s) recorded against FS-004, three verify it: {executed}."
    )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-3.4")
def test_untested_requirement_is_reported_as_uncovered(pytester, tq):
    """A requirement with no linked test is identified as uncovered.

    This is the primary negative control on the coverage claim.
    """
    h.write_spec(pytester, "functional", SPEC)
    (pytester.path / "test_partial.py").write_text(
        "import pytest\n"
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
        "@pytest.mark.requirements(['FS-004'])\n"
        "def test_fs_004():\n"
        "    assert True\n",
        encoding="utf-8",
    )
    h.run_gxp(pytester)

    coverage_md = h.read_text_artefact(pytester.path, cfg.ARTEFACT_COVERAGE_MD)
    report = h.load_report(pytester.path)
    with_tests = h.deep_get(report, "requirements_with_tests")
    total = h.deep_get(report, "total_requirements")
    tq.observe(
        fs_003_named_in_coverage_report="FS-003" in coverage_md,
        requirements_with_tests=with_tests,
        total_requirements=total,
    )
    assert "FS-003" in coverage_md, (
        "The untested requirement FS-003 is not named in the coverage report. "
        "An uncovered requirement that is not surfaced cannot be dispositioned, "
        "and the qualification would claim completeness it does not have."
    )
    if with_tests is not None and total is not None:
        assert int(with_tests) == int(total) - 1, (
            f"Coverage arithmetic does not reflect the uncovered requirement: "
            f"{with_tests} of {total} reported as having tests, expected "
            f"{int(total) - 1}."
        )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-3.5")
def test_orphan_test_referencing_unknown_requirement_is_flagged(pytester, tq):
    """A test citing a requirement ID absent from the specifications is reported.

    Without this, a typo in a requirement marker orphans the test silently: the
    requirement appears untested and the test appears to verify nothing.
    """
    h.write_spec(pytester, "functional", [h.Requirement("FS-001", "The only real requirement")])
    (pytester.path / "test_orphan.py").write_text(
        "import pytest\n"
        "\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['FS-001'])\n"
        "def test_real():\n"
        "    assert True\n"
        "\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['FS-999'])\n"
        "def test_typo_in_requirement_id():\n"
        "    assert True\n",
        encoding="utf-8",
    )
    result = h.run_gxp(pytester)
    output = "\n".join(result.outlines)
    report = h.load_report(pytester.path)
    orphans = h.findings(report, "unknown-requirement-ref")
    tq.observe(
        orphan_findings=orphans,
        findings_section_printed="GxP validation findings" in output,
        exit_code=result.ret,
    )
    assert orphans, (
        "No 'unknown-requirement-ref' finding was raised for a test citing "
        "FS-999, which does not exist in any specification. Findings present: "
        f"{[f.get('code') for f in h.findings(report)]}."
    )
    assert [f["location"] for f in orphans] == ["test_orphan.py::test_typo_in_requirement_id"], (
        "The finding does not locate the offending test by node id, so the "
        f"reviewer cannot find the typo: {orphans}."
    )
    assert all("FS-999" in f["message"] for f in orphans), (
        f"The finding does not name the unknown requirement: {orphans}."
    )
    assert "GxP validation findings" in output, (
        "The orphan test is not surfaced in the console output."
    )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-3.6")
def test_matrix_and_report_agree_on_coverage(pytester, tq):
    """The traceability matrix and the validation report describe the same coverage."""
    h.write_spec(pytester, "functional", SPEC)
    (pytester.path / "test_mixed.py").write_text(
        "import pytest\n"
        "\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['FS-001'])\n"
        "def test_a():\n"
        "    assert True\n"
        "\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['FS-002', 'FS-004'])\n"
        "def test_b():\n"
        "    assert True\n",
        encoding="utf-8",
    )
    h.run_gxp(pytester)

    report = h.load_report(pytester.path)
    matrix_reqs = {req for req, _ in h.matrix_pairs(pytester.path)}
    # Requirements the record claims were actually exercised.
    executed_reqs = {
        req for entry in h.executed_tests(report) for req in entry.get("requirement_ids", [])
    }
    # Every requirement must still appear in the per-requirement register, so an
    # untested one is visible rather than absent.
    listed_reqs = {req for case in h.test_cases(report) for req in h.requirements_of(case)}
    matrix_nodes = {
        req: {t for r, t in h.matrix_pairs(pytester.path) if r == req} for req in matrix_reqs
    }
    tq.observe(
        matrix_requirements=sorted(matrix_reqs),
        executed_requirements=sorted(executed_reqs),
        listed_requirements=sorted(listed_reqs),
        fs_003_matrix_entries=sorted(matrix_nodes.get("FS-003", set())),
    )

    tested = {"FS-001", "FS-002", "FS-004"}
    assert executed_reqs == tested, (
        f"The executed-test register claims {sorted(executed_reqs)} were "
        f"exercised; the suite exercises {sorted(tested)}."
    )
    assert tested <= matrix_reqs, (
        f"Matrix omits tested requirements: {sorted(tested - matrix_reqs)}"
    )
    assert "FS-003" in listed_reqs, (
        "FS-003 is absent from the report's requirement register entirely, so an "
        "untested requirement silently leaves the scope of qualification."
    )
    assert "FS-003" not in executed_reqs, (
        "FS-003 has no test but the record names it as exercised by one."
    )
    fs_003_statuses = [
        h.status_of(c) for c in h.test_cases(report) if "FS-003" in h.requirements_of(c)
    ]
    tq.observe(fs_003_statuses=fs_003_statuses)
    assert fs_003_statuses and not any("PASS" in s for s in fs_003_statuses), (
        f"FS-003 has no test yet is recorded with status {fs_003_statuses}."
    )
    assert not any("test_a" in t or "test_b" in t for t in matrix_nodes.get("FS-003", set())), (
        "The matrix attributes an executed test to the untested requirement "
        f"FS-003: {sorted(matrix_nodes.get('FS-003', set()))}."
    )
