"""Tests for the CSV validation report generator."""



from pytest_gxp.markdown_format import Requirement, Specification, SpecType, TestCase
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
        assert report_data["specifications"]["functional_spec"]["title"] == "Functional Specification"

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
        report.generate_report([sample_test_case], None, functional_spec, None, None, None, output_path)

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

