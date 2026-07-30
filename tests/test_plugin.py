"""Tests for pytest plugin hooks."""

import json

import pytest

FUNCTIONAL_SPEC = """# Functional Specification

## Version: 1.0

### FS-001: User Login

#### Description
The application shall allow users to log in.

### FS-002: Input Validation

#### Description
The application shall validate all input.
"""


def _write_spec(pytester, content=FUNCTIONAL_SPEC, name="functional_specification.md"):
    """Write a specification where the plugin looks for it by default."""
    spec_dir = pytester.path / "gxp_spec_files"
    spec_dir.mkdir(exist_ok=True)
    (spec_dir / name).write_text(content, encoding="utf-8")
    return spec_dir


def _run_gxp(pytester, *extra_args):
    """Run the inner pytest session in GxP mode and return (result, report json)."""
    result = pytester.runpytest_subprocess(
        "--gxp",
        "--gxp-spec-files=gxp_spec_files",
        "--gxp-report-files=gxp_report_files",
        "--gxp-output-formats=json",
        *extra_args,
    )
    report_path = pytester.path / "gxp_report_files" / "csv_validation_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}
    return result, report


class TestPluginHooks:
    """Test cases for pytest plugin hooks."""

    def test_pytest_addoption(self, pytestconfig):
        """Test that plugin options are added."""
        # Verify options exist
        assert hasattr(pytestconfig.option, "gxp") or pytestconfig.getoption("--gxp") is not None

    def test_pytest_configure_without_gxp_flag(self, pytestconfig):
        """Test plugin configuration without --gxp flag."""
        # Plugin should not crash when --gxp is not used
        # This is more of an integration test
        pass

    def test_gxp_marker_registered(self, pytestconfig):
        """Test that GxP markers are registered."""
        markers = pytestconfig.getini("markers")
        gxp_markers = [m for m in markers if "gxp" in m.lower()]
        assert len(gxp_markers) > 0

    def test_requirements_marker_registered(self, pytestconfig):
        """Test that requirements marker is registered."""
        markers = pytestconfig.getini("markers")
        req_markers = [m for m in markers if "requirements" in m.lower()]
        assert len(req_markers) > 0


class TestFindings:
    """Findings raised during a real GxP session."""

    def test_unknown_requirement_reference(self, pytester):
        """A marker citing an unknown requirement is reported and lands in the report."""
        _write_spec(pytester)
        pytester.makepyfile(
            test_unknown="""
            import pytest

            @pytest.mark.requirements(["FS-404"])
            def test_orphan():
                assert True
            """
        )

        result, report = _run_gxp(pytester)

        result.stdout.fnmatch_lines(
            [
                "*GxP validation findings*",
                "*ERROR unknown-requirement-ref*FS-404*",
            ]
        )
        orphans = [f for f in report["findings"] if f["code"] == "unknown-requirement-ref"]
        assert len(orphans) == 1
        assert orphans[0]["location"] == "test_unknown.py::test_orphan"
        assert report["report_metadata"]["findings_summary"]["errors"] >= 1


class TestExecutionRecord:
    """Every test phase must reach the validation record with its reason."""

    def test_all_outcomes_are_classified(self, pytester):
        """Setup errors, skips, xfails and xpasses are recorded, not silently dropped."""
        _write_spec(pytester)
        pytester.makepyfile(
            test_outcomes="""
            import pytest

            @pytest.fixture
            def broken_fixture():
                raise RuntimeError("fixture exploded")

            @pytest.mark.requirements(["FS-001"])
            def test_setup_error(broken_fixture):
                assert True

            @pytest.mark.requirements(["FS-001"])
            def test_skipped():
                pytest.skip("not applicable in this environment")

            @pytest.mark.requirements(["FS-002"])
            @pytest.mark.xfail(reason="known defect DEF-1")
            def test_xfailing():
                assert False

            @pytest.mark.requirements(["FS-002"])
            @pytest.mark.xfail(reason="already fixed upstream")
            def test_xpassing():
                assert True

            @pytest.mark.requirements(["FS-002"])
            def test_passing():
                assert True
            """
        )

        _result, report = _run_gxp(pytester)

        outcomes = {rec["node_id"]: rec for rec in report["test_execution"]}
        assert outcomes["test_outcomes.py::test_setup_error"]["outcome"] == "ERROR"
        assert "fixture exploded" in outcomes["test_outcomes.py::test_setup_error"]["reason"]
        assert outcomes["test_outcomes.py::test_skipped"]["outcome"] == "SKIPPED"
        assert "not applicable" in outcomes["test_outcomes.py::test_skipped"]["reason"]
        assert outcomes["test_outcomes.py::test_xfailing"]["outcome"] == "XFAIL"
        assert "known defect DEF-1" in outcomes["test_outcomes.py::test_xfailing"]["reason"]
        assert outcomes["test_outcomes.py::test_xpassing"]["outcome"] == "XPASS"
        assert outcomes["test_outcomes.py::test_passing"]["outcome"] == "PASSED"

        # Node ids are the real ones, sorted, and requirements travel with them
        assert list(outcomes) == sorted(outcomes)
        assert outcomes["test_outcomes.py::test_passing"]["requirement_ids"] == ["FS-002"]

        # A setup error is counted as an error, and its requirement does not pass
        assert report["test_summary"]["errors"] == 1
        assert report["test_execution_summary"]["error_tests"] == 1
        statuses = {tc["id"]: tc["status"] for tc in report["test_cases"]}
        assert statuses["TEST-FS-001"] == "FAILED"
        assert statuses["TEST-FS-002"] == "PASSED"

    def test_matrix_names_real_tests(self, pytester):
        """The traceability matrix gains a Test Node ID column filled with real nodeids."""
        _write_spec(pytester)
        pytester.makepyfile(
            test_matrix="""
            import pytest

            @pytest.mark.requirements(["FS-001"])
            def test_login():
                assert True
            """
        )

        _run_gxp(pytester, "--gxp-output-formats=json,csv")

        matrix = (pytester.path / "gxp_report_files" / "traceability_matrix.csv").read_text()
        assert "Test Node ID" in matrix.splitlines()[0]
        assert "test_matrix.py::test_login" in matrix


class TestRiskMarker:
    """The gxp_risk marker is declared to plain pytest and validated in GxP mode."""

    def test_marker_registered_on_plain_run(self, pytester):
        """A run without --gxp still documents the marker in `pytest --markers`."""
        result = pytester.runpytest_subprocess("--markers")

        result.stdout.fnmatch_lines(["*@pytest.mark.gxp_risk(tier)*high, medium, not-high*"])

    def test_invalid_tier_is_a_warning_finding(self, pytester):
        """An unknown tier is reported and treated as unset, not fatal."""
        _write_spec(pytester)
        pytester.makepyfile(
            test_risk="""
            import pytest

            @pytest.mark.requirements(["FS-001"])
            @pytest.mark.gxp_risk("critical")
            def test_typo_tier():
                assert True
            """
        )

        result, report = _run_gxp(pytester)

        assert result.ret == 0
        invalid = [f for f in report["findings"] if f["code"] == "invalid-risk-tier"]
        assert len(invalid) == 1
        assert invalid[0]["severity"] == "warning"
        assert invalid[0]["location"] == "test_risk.py::test_typo_tier"
        assert report["test_execution"][0]["risk_tier"] == ""

    def test_risk_tier_reaches_matrix_and_report(self, pytester):
        """A valid tier travels to the report registers and the matrix column."""
        _write_spec(pytester)
        pytester.makepyfile(
            test_risk="""
            import pytest

            @pytest.mark.requirements(["FS-001"])
            @pytest.mark.gxp_risk("high")
            def test_high_risk(gxp_evidence):
                gxp_evidence.record_unscripted_session(
                    charter="Explore login",
                    tester="A. Tester",
                    duration_minutes=5,
                    observations=["nothing unexpected"],
                )
            """
        )

        _result, report = _run_gxp(pytester, "--gxp-output-formats=json,csv")

        assert report["test_execution"][0]["risk_tier"] == "high"
        matrix = (pytester.path / "gxp_report_files" / "traceability_matrix.csv").read_text()
        assert "Risk Tier" in matrix.splitlines()[0]
        assert "high" in matrix


class TestStrictGate:
    """--gxp-strict turns error-severity findings into a non-zero exit status."""

    HIGH_RISK_TEST = """
        import pytest

        @pytest.mark.requirements(["FS-001"])
        @pytest.mark.gxp_risk("high")
        def test_high_risk_without_evidence():
            assert True
        """

    def test_high_risk_without_evidence_fails_under_strict(self, pytester):
        """A high-risk requirement with no objective evidence fails the strict gate."""
        _write_spec(pytester)
        pytester.makepyfile(test_strict=self.HIGH_RISK_TEST)

        result, report = _run_gxp(pytester, "--gxp-strict")

        assert result.ret != 0
        result.stdout.fnmatch_lines(["*GxP STRICT FAILURE*", "*high-risk-no-evidence*FS-001*"])
        gate = [f for f in report["findings"] if f["code"] == "high-risk-no-evidence"]
        assert len(gate) == 1
        assert gate[0]["severity"] == "error"
        assert gate[0]["location"] == "FS-001"

    def test_same_run_passes_without_strict(self, pytester):
        """Enabling the plugin alone must not change the pass/fail verdict."""
        _write_spec(pytester)
        pytester.makepyfile(test_strict=self.HIGH_RISK_TEST)

        result, report = _run_gxp(pytester)

        assert result.ret == 0
        assert report["report_metadata"]["status"] == "PROVISIONAL"


class TestDeviations:
    """Deviation references arrive from a file, not from edits to controlled tests."""

    FAILING_TEST = """
        import pytest

        @pytest.mark.requirements(["FS-001"])
        def test_known_failure():
            assert False, "known defect"
        """

    def test_missing_reference_is_an_error_finding(self, pytester):
        """A failing test with no deviation reference is flagged and the record is a draft."""
        _write_spec(pytester)
        pytester.makepyfile(test_dev=self.FAILING_TEST)

        _result, report = _run_gxp(pytester)

        missing = [f for f in report["findings"] if f["code"] == "missing-deviation-ref"]
        assert len(missing) == 1
        assert missing[0]["location"] == "test_dev.py::test_known_failure"
        assert report["test_execution"][0]["deviation_ref"] is None
        assert report["report_metadata"]["status"] == "PROVISIONAL"

    def test_reference_from_file_is_honoured(self, pytester):
        """The reference reaches the report verbatim and clears the finding."""
        _write_spec(pytester)
        pytester.makepyfile(test_dev=self.FAILING_TEST)
        (pytester.path / "deviations.json").write_text(
            json.dumps({"test_dev.py::test_known_failure": "DEV-2026-014"}), encoding="utf-8"
        )

        _result, report = _run_gxp(pytester, "--gxp-deviations=deviations.json")

        assert report["test_execution"][0]["deviation_ref"] == "DEV-2026-014"
        assert not [f for f in report["findings"] if f["code"] == "missing-deviation-ref"]

    def test_missing_file_is_a_warning_not_a_crash(self, pytester):
        """An unreadable deviation file leaves an empty map and a warning finding."""
        _write_spec(pytester)
        pytester.makepyfile(
            test_dev="""
            import pytest

            @pytest.mark.requirements(["FS-001"])
            def test_passing():
                assert True
            """
        )

        result, report = _run_gxp(pytester, "--gxp-deviations=nope.json")

        assert result.ret == 0
        errors = [f for f in report["findings"] if f["code"] == "deviation-file-error"]
        assert len(errors) == 1
        assert errors[0]["severity"] == "warning"


@pytest.mark.gxp
@pytest.mark.requirements(["FS-001"])
def test_example_gxp_test():
    """Example GxP test that should be recognized by the plugin."""
    assert True


@pytest.mark.gxp
def test_example_gxp_test_no_requirements():
    """Example GxP test without requirements marker."""
    assert True
