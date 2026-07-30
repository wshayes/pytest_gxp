"""Tests for the CSV validation report generator."""

from pytest_gxp.markdown_format import (
    EvidenceItem,
    EvidenceType,
    Requirement,
    Specification,
    SpecType,
    TestCase,
    ValidationFinding,
)
from pytest_gxp.report import CSVValidationReport
from pytest_gxp.traceability import TraceabilityMatrix


class TestCSVValidationReport:
    """Test cases for CSVValidationReport."""

    def test_generate_report_basic(self, sample_test_case):
        """Test generating a basic validation report."""
        report = CSVValidationReport()

        functional_spec = Specification(
            spec_type=SpecType.FUNCTIONAL,
            title="Functional Specification",
            version="1.0",
            requirements=[
                Requirement(
                    id="FS-001",
                    title="User Login",
                    description="Test requirement",
                    spec_type=SpecType.FUNCTIONAL,
                )
            ],
        )

        report_data = report.generate_report([sample_test_case], None, functional_spec, None)

        assert report_data["report_metadata"]["title"] == "Operational Qualification Report"
        assert "generated_date" in report_data["report_metadata"]
        assert report_data["test_summary"]["total_test_cases"] == 1
        assert (
            report_data["specifications"]["functional_spec"]["title"] == "Functional Specification"
        )

    def test_generate_report_with_test_results(self, sample_test_case):
        """Test generating report with test results."""
        report = CSVValidationReport()

        functional_spec = Specification(
            spec_type=SpecType.FUNCTIONAL,
            title="Functional Specification",
            version="1.0",
            requirements=[
                Requirement(
                    id="FS-001",
                    title="User Login",
                    description="Test requirement",
                    spec_type=SpecType.FUNCTIONAL,
                )
            ],
        )

        test_results = {"TEST-FS-001": "PASSED"}

        report_data = report.generate_report(
            [sample_test_case], None, functional_spec, None, None, test_results
        )

        assert report_data["test_summary"]["passed"] == 1
        assert report_data["test_summary"]["failed"] == 0
        assert report_data["test_cases"][0]["status"] == "PASSED"

    def test_generate_report_with_coverage(self, sample_test_case):
        """Test generating report with coverage information."""
        report = CSVValidationReport()

        functional_spec = Specification(
            spec_type=SpecType.FUNCTIONAL,
            title="Functional Specification",
            version="1.0",
            requirements=[
                Requirement(
                    id="FS-001",
                    title="User Login",
                    description="Test requirement",
                    spec_type=SpecType.FUNCTIONAL,
                )
            ],
        )

        matrix = TraceabilityMatrix()
        matrix.generate_matrix([sample_test_case], None, functional_spec, None)
        matrix.update_test_status("TEST-FS-001", "Passed")

        report_data = report.generate_report(
            [sample_test_case], None, functional_spec, None, matrix, {"TEST-FS-001": "PASSED"}
        )

        assert "coverage" in report_data
        assert report_data["coverage"]["total_requirements"] >= 0

    def test_write_report_json(self, sample_test_case, temp_dir):
        """Test writing report to JSON file."""
        report = CSVValidationReport()

        functional_spec = Specification(
            spec_type=SpecType.FUNCTIONAL,
            title="Functional Specification",
            version="1.0",
            requirements=[
                Requirement(
                    id="FS-001",
                    title="User Login",
                    description="Test requirement",
                    spec_type=SpecType.FUNCTIONAL,
                )
            ],
        )

        output_path = temp_dir / "report.json"
        report.generate_report(
            [sample_test_case], None, functional_spec, None, None, None, output_path
        )

        assert output_path.exists()
        import json

        with open(output_path) as f:
            data = json.load(f)
            assert data["report_metadata"]["title"] == "Operational Qualification Report"

    def test_write_markdown_report(self, sample_test_case, temp_dir):
        """Test writing report in Markdown format."""
        report = CSVValidationReport()

        functional_spec = Specification(
            spec_type=SpecType.FUNCTIONAL,
            title="Functional Specification",
            version="1.0",
            requirements=[
                Requirement(
                    id="FS-001",
                    title="User Login",
                    description="Test requirement",
                    spec_type=SpecType.FUNCTIONAL,
                )
            ],
        )

        report.generate_report([sample_test_case], None, functional_spec, None)
        output_path = temp_dir / "report.md"
        report.write_markdown_report(output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "# Operational Qualification Report" in content
        assert "Test Execution Summary" in content
        assert "TEST-FS-001" in content

    def test_report_statistics(self):
        """Test report statistics calculation."""
        report = CSVValidationReport()

        test_cases = [
            TestCase(
                id="TEST-001",
                title="Test 1",
                description="Test 1",
                requirements=["REQ-001"],
                steps=[],
                expected_result="Pass",
            ),
            TestCase(
                id="TEST-002",
                title="Test 2",
                description="Test 2",
                requirements=["REQ-002"],
                steps=[],
                expected_result="Pass",
            ),
        ]

        test_results = {"TEST-001": "PASSED", "TEST-002": "FAILED"}

        report_data = report.generate_report(test_cases, None, None, None, None, test_results)

        assert report_data["test_summary"]["total_test_cases"] == 2
        assert report_data["test_summary"]["passed"] == 1
        assert report_data["test_summary"]["failed"] == 1
        assert report_data["test_summary"]["pass_rate"] == 50.0

    def test_report_with_all_spec_types(self):
        """Test generating report with all specification types."""
        report = CSVValidationReport()

        design_spec = Specification(
            spec_type=SpecType.DESIGN,
            title="Design Spec",
            version="1.0",
            requirements=[],
        )

        functional_spec = Specification(
            spec_type=SpecType.FUNCTIONAL,
            title="Functional Spec",
            version="1.0",
            requirements=[],
        )

        user_spec = Specification(
            spec_type=SpecType.USER,
            title="User Spec",
            version="1.0",
            requirements=[],
        )

        report_data = report.generate_report([], design_spec, functional_spec, user_spec)

        assert report_data["specifications"]["design_spec"]["title"] == "Design Spec"
        assert report_data["specifications"]["functional_spec"]["title"] == "Functional Spec"
        assert report_data["specifications"]["user_spec"]["title"] == "User Spec"


class TestFindingsAndExecution:
    """Findings and the real-test execution register in the report."""

    FINDINGS = [
        ValidationFinding(
            code="unknown-requirement-ref",
            severity="error",
            message="Test cites requirement FS-404, which is not defined in any specification",
            location="tests/test_a.py::test_orphan",
        ),
        ValidationFinding(
            code="uncovered-requirement",
            severity="warning",
            message="Requirement FS-002 has no test coverage",
        ),
    ]

    TEST_RECORDS = {
        "tests/test_a.py::test_login": {
            "status": "PASSED",
            "reason": "",
            "requirement_ids": ["FS-001"],
        },
        "tests/test_a.py::test_broken": {
            "status": "ERROR",
            "reason": "RuntimeError: fixture exploded",
            "requirement_ids": ["FS-001"],
        },
    }

    def _report(self, sample_test_case, **kwargs):
        report = CSVValidationReport()
        report.generate_report(
            [sample_test_case],
            findings=self.FINDINGS,
            test_records=self.TEST_RECORDS,
            test_results={"TEST-FS-001": "PASSED"},
            **kwargs,
        )
        return report

    def test_findings_reach_json(self, sample_test_case):
        """Findings are summarised in the metadata and listed sorted at the top level."""
        report_data = self._report(sample_test_case).report_data

        assert report_data["report_metadata"]["findings_summary"] == {"errors": 1, "warnings": 1}
        assert [f["code"] for f in report_data["findings"]] == [
            "uncovered-requirement",
            "unknown-requirement-ref",
        ]
        assert report_data["findings"][1]["location"] == "tests/test_a.py::test_orphan"

    def test_test_execution_reaches_json(self, sample_test_case):
        """The execution register names real tests, sorted, with reasons and requirements."""
        report_data = self._report(sample_test_case).report_data

        execution = report_data["test_execution"]
        assert [rec["node_id"] for rec in execution] == [
            "tests/test_a.py::test_broken",
            "tests/test_a.py::test_login",
        ]
        assert execution[0]["outcome"] == "ERROR"
        assert execution[0]["reason"] == "RuntimeError: fixture exploded"
        assert execution[0]["requirement_ids"] == ["FS-001"]

        # test_execution follows test_cases in the report
        keys = list(report_data)
        assert keys.index("test_execution") == keys.index("test_cases") + 1

    def test_error_counts(self, sample_test_case):
        """Errors are counted from the real execution register."""
        report_data = self._report(sample_test_case).report_data

        assert report_data["test_summary"]["errors"] == 1
        assert report_data["test_execution_summary"]["error_tests"] == 1

    def test_test_cases_carry_expected_result_and_metadata(self, sample_test_case):
        """expected_result and metadata from the requirement reach the report."""
        test_case = self._report(sample_test_case).report_data["test_cases"][0]

        assert test_case["expected_result"] == "User is authenticated successfully."
        assert test_case["metadata"]["requirement_id"] == "FS-001"

    def test_markdown_sections(self, sample_test_case, temp_dir):
        """Findings and test execution render as markdown sections in the right order."""
        report = self._report(sample_test_case)
        output_path = temp_dir / "report.md"
        report.write_markdown_report(output_path)
        content = output_path.read_text()

        assert "## Validation Findings" in content
        assert "unknown-requirement-ref" in content
        assert "## Test Execution" in content
        assert "tests/test_a.py::test_broken" in content
        assert "RuntimeError: fixture exploded" in content
        assert content.index("## Validation Information") < content.index("## Validation Findings")
        assert content.index("## Validation Findings") < content.index("## Specifications")

    def test_findings_section_omitted_when_clean(self, sample_test_case, temp_dir):
        """No findings means no findings section."""
        report = CSVValidationReport()
        report.generate_report([sample_test_case])
        output_path = temp_dir / "clean.md"
        report.write_markdown_report(output_path)

        assert "## Validation Findings" not in output_path.read_text()

    def test_markdown_and_pdf_share_one_source(self, sample_test_case, temp_dir):
        """The markdown file and the PDF source come from the same builder."""
        report = self._report(sample_test_case)
        output_path = temp_dir / "report.md"
        report.write_markdown_report(output_path)

        assert output_path.read_text() == report._get_markdown_content()


class TestEvidenceRendering:
    """Only image evidence is rendered inline; session records are rendered as text."""

    def _item(self, evidence_type, file_path, metadata=None):
        return EvidenceItem(
            id="EV-0001",
            evidence_type=evidence_type,
            description="Login screen",
            file_path=file_path,
            timestamp="2026-07-29T12:00:00Z",
            test_id="tests/test_a.py::test_login",
            requirement_ids=["FS-001"],
            metadata=metadata,
        )

    def test_image_evidence_is_inlined(self):
        """An image keeps its inline markdown."""
        item = self._item(EvidenceType.SCREENSHOT, "evidence/shot.png")

        content = "\n".join(CSVValidationReport()._build_evidence_section([item]))

        assert "![Login screen](evidence/shot.png)" in content

    def test_unscripted_session_renders_as_bullet_list(self):
        """A session record is labelled, never linked as a broken image."""
        item = self._item(
            EvidenceType.UNSCRIPTED_SESSION,
            "evidence/unscripted_session_20260729T120000Z_abcd1234.json",
            metadata={
                "charter": "Explore the login flow",
                "tester": "A. Tester",
                "duration_minutes": 45,
                "observations": ["Password field accepts 300 characters"],
                "defects": ["DEF-2026-003"],
            },
        )

        content = "\n".join(CSVValidationReport()._build_evidence_section([item]))

        assert "![" not in content
        assert "- **Charter:** Explore the login flow" in content
        assert "- **Tester:** A. Tester" in content
        assert "- **Duration:** 45 minutes" in content
        assert "    - Password field accepts 300 characters" in content
        assert "    - DEF-2026-003" in content


class TestProvisionalAndDeviations:
    """Report status, deviation references and the draft banner."""

    RECORDS = {
        "tests/test_a.py::test_login": {
            "status": "PASSED",
            "reason": "",
            "requirement_ids": ["FS-001"],
            "risk_tier": "high",
        },
        "tests/test_a.py::test_broken": {
            "status": "FAILED",
            "reason": "assert False",
            "requirement_ids": ["FS-001"],
            "risk_tier": "medium",
        },
    }

    def _report(self, sample_test_case, **kwargs):
        report = CSVValidationReport()
        report.generate_report(
            [sample_test_case],
            test_results={"TEST-FS-001": "FAILED"},
            requirement_tests={"FS-001": list(self.RECORDS)},
            **kwargs,
        )
        return report

    def test_clean_run_is_final(self, sample_test_case, temp_dir):
        """A run with nothing to explain is a FINAL record with no banner."""
        report = CSVValidationReport()
        report.generate_report(
            [sample_test_case],
            test_results={"TEST-FS-001": "PASSED"},
            requirement_tests={"FS-001": ["tests/test_a.py::test_login"]},
            test_records={
                "tests/test_a.py::test_login": {
                    "status": "PASSED",
                    "reason": "",
                    "requirement_ids": ["FS-001"],
                    "risk_tier": "high",
                }
            },
        )
        metadata = report.report_data["report_metadata"]

        assert metadata["status"] == "FINAL"
        assert metadata["provisional_reasons"] == []

        output_path = temp_dir / "final.md"
        report.write_markdown_report(output_path)
        content = output_path.read_text()
        assert "PROVISIONAL" not in content
        assert content.splitlines()[0] == f"# {metadata['title']}"

    def test_failing_run_is_provisional(self, sample_test_case, temp_dir):
        """Failures, missing deviation refs and error findings each explain the draft status."""
        report = self._report(
            sample_test_case,
            test_records=self.RECORDS,
            findings=[
                ValidationFinding(
                    code="high-risk-no-evidence",
                    severity="error",
                    message="High-risk requirement FS-001 has no objective evidence",
                    location="FS-001",
                )
            ],
        )
        metadata = report.report_data["report_metadata"]

        assert metadata["status"] == "PROVISIONAL"
        assert metadata["provisional_reasons"] == [
            "1 test(s) failed or errored",
            "1 non-passing test(s) without a deviation reference",
            "1 error-severity validation finding(s)",
        ]

        output_path = temp_dir / "provisional.md"
        report.write_markdown_report(output_path)
        lines = output_path.read_text().splitlines()
        assert lines[0].endswith(" — PROVISIONAL (DRAFT)")
        assert lines[2] == "> **PROVISIONAL — DRAFT RECORD. NOT FOR SIGNATURE.**"
        assert lines[3].startswith("> 1 test(s) failed or errored; ")
        assert "**MISSING**" in "\n".join(lines)

    def test_deviation_ref_key_always_present(self, sample_test_case):
        """Both registers carry the key, null when no reference applies."""
        report_data = self._report(sample_test_case, test_records=self.RECORDS).report_data

        assert all("deviation_ref" in rec for rec in report_data["test_execution"])
        assert all("deviation_ref" in tc for tc in report_data["test_cases"])
        assert report_data["test_cases"][0]["deviation_ref"] is None
        assert report_data["test_execution"][0]["deviation_ref"] is None

    def test_deviation_ref_resolution(self, sample_test_case, temp_dir):
        """A nodeid entry wins over a requirement entry, and requirements inherit refs."""
        report = self._report(
            sample_test_case,
            test_records=self.RECORDS,
            deviations={
                "tests/test_a.py::test_broken": "DEV-2026-014",
                "FS-001": "DEV-2026-001",
            },
        )
        report_data = report.report_data
        execution = {rec["node_id"]: rec for rec in report_data["test_execution"]}

        assert execution["tests/test_a.py::test_broken"]["deviation_ref"] == "DEV-2026-014"
        assert execution["tests/test_a.py::test_login"]["deviation_ref"] == "DEV-2026-001"
        assert report_data["test_cases"][0]["deviation_ref"] == "DEV-2026-014"

        # An explained failure is no longer flagged, and only the failure remains a reason
        output_path = temp_dir / "explained.md"
        report.write_markdown_report(output_path)
        content = output_path.read_text()
        assert "DEV-2026-014" in content
        assert "**MISSING**" not in content
        assert report_data["report_metadata"]["provisional_reasons"] == [
            "1 test(s) failed or errored"
        ]

    def test_risk_tier_reaches_both_registers(self, sample_test_case):
        """A requirement's risk is the most severe tier among its tests."""
        report_data = self._report(sample_test_case, test_records=self.RECORDS).report_data

        assert report_data["test_cases"][0]["risk_tier"] == "high"
        tiers = {rec["node_id"]: rec["risk_tier"] for rec in report_data["test_execution"]}
        assert tiers["tests/test_a.py::test_broken"] == "medium"

    def test_deviation_ref_reaches_csv(self, sample_test_case, temp_dir):
        """The CSV gains a column without gaining rows."""
        report = self._report(
            sample_test_case,
            test_records=self.RECORDS,
            deviations={"FS-001": "DEV-2026-001"},
        )
        output_path = temp_dir / "report.csv"
        report.write_csv_report(output_path)
        lines = output_path.read_text().splitlines()

        assert lines[0].endswith("Deviation Ref")
        assert len(lines) == 2
        assert lines[1].endswith("DEV-2026-001")
