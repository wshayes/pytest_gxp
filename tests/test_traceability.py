"""Tests for the traceability matrix generator."""



from pytest_gxp.markdown_format import Requirement, Specification, SpecType, TestCase
from pytest_gxp.traceability import TraceabilityMatrix


class TestTraceabilityMatrix:
    """Test cases for TraceabilityMatrix."""

    def test_generate_matrix_basic(self, sample_test_case):
        """Test generating a basic traceability matrix."""
        matrix = TraceabilityMatrix()

        functional_spec = Specification(
            spec_type=SpecType.FUNCTIONAL,
            title="Functional Spec",
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

        matrix_data = matrix.generate_matrix([sample_test_case], None, functional_spec, None)

        assert len(matrix_data) == 1
        assert matrix_data[0]["Test Case ID"] == "TEST-FS-001"
        assert matrix_data[0]["Requirement ID"] == "FS-001"
        assert matrix_data[0]["Specification Type"] == "Functional"
        assert matrix_data[0]["Status"] == "Not Executed"

    def test_generate_matrix_with_user_spec(self, sample_test_case):
        """Test generating matrix with user specification."""
        matrix = TraceabilityMatrix()

        functional_spec = Specification(
            spec_type=SpecType.FUNCTIONAL,
            title="Functional Spec",
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

        user_spec = Specification(
            spec_type=SpecType.USER,
            title="User Spec",
            version="1.0",
            requirements=[
                Requirement(
                    id="US-001",
                    title="Secure Access",
                    description="User needs secure access",
                    spec_type=SpecType.USER,
                    metadata={"maps_to": ["FS-001"]},
                )
            ],
        )

        matrix_data = matrix.generate_matrix([sample_test_case], None, functional_spec, user_spec)

        assert len(matrix_data) >= 1
        # Check that user requirement mapping is attempted
        row = matrix_data[0]
        assert row["Test Case ID"] == "TEST-FS-001"
        assert row["Requirement ID"] == "FS-001"

    def test_write_csv(self, sample_test_case, temp_dir):
        """Test writing traceability matrix to CSV."""
        matrix = TraceabilityMatrix()

        functional_spec = Specification(
            spec_type=SpecType.FUNCTIONAL,
            title="Functional Spec",
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

        output_path = temp_dir / "traceability_matrix.csv"
        matrix.generate_matrix([sample_test_case], None, functional_spec, None, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "Test Case ID" in content
        assert "TEST-FS-001" in content
        assert "FS-001" in content

    def test_update_test_status(self, sample_test_case):
        """Test updating test status in matrix."""
        matrix = TraceabilityMatrix()

        functional_spec = Specification(
            spec_type=SpecType.FUNCTIONAL,
            title="Functional Spec",
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

        matrix.generate_matrix([sample_test_case], None, functional_spec, None)
        matrix.update_test_status("TEST-FS-001", "Passed")

        assert matrix.matrix_data[0]["Status"] == "Passed"

    def test_get_coverage_report(self):
        """Test generating coverage report."""
        matrix = TraceabilityMatrix()

        # Create test cases that cover both requirements
        test_case_1 = TestCase(
            id="TEST-FS-001",
            title="Test 1",
            description="Test 1",
            requirements=["FS-001"],
            steps=[],
            expected_result="Pass",
        )

        test_case_2 = TestCase(
            id="TEST-FS-002",
            title="Test 2",
            description="Test 2",
            requirements=["FS-002"],
            steps=[],
            expected_result="Pass",
        )

        functional_spec = Specification(
            spec_type=SpecType.FUNCTIONAL,
            title="Functional Spec",
            version="1.0",
            requirements=[
                Requirement(
                    id="FS-001",
                    title="User Login",
                    description="Test requirement",
                    spec_type=SpecType.FUNCTIONAL,
                ),
                Requirement(
                    id="FS-002",
                    title="Another Requirement",
                    description="Another requirement",
                    spec_type=SpecType.FUNCTIONAL,
                ),
            ],
        )

        matrix.generate_matrix([test_case_1, test_case_2], None, functional_spec, None)
        matrix.update_test_status("TEST-FS-001", "Passed")

        coverage = matrix.get_coverage_report()

        # Both requirements have tests (are in the matrix)
        assert coverage["total_requirements"] == 2
        assert coverage["requirements_with_tests"] == 2
        # Only FS-001 passed, so only 1 is verified
        assert coverage["requirements_verified"] == 1
        assert coverage["requirement_verification_rate"] == 50.0
        # FS-002 has a test but didn't pass, so it's unverified (not uncovered)
        assert "FS-002" in coverage["unverified_requirements"]

    def test_generate_matrix_multiple_test_cases(self):
        """Test generating matrix with multiple test cases."""
        matrix = TraceabilityMatrix()

        test_case_1 = TestCase(
            id="TEST-FS-001",
            title="Test 1",
            description="Test 1",
            requirements=["FS-001"],
            steps=[],
            expected_result="Pass",
        )

        test_case_2 = TestCase(
            id="TEST-FS-002",
            title="Test 2",
            description="Test 2",
            requirements=["FS-002"],
            steps=[],
            expected_result="Pass",
        )

        functional_spec = Specification(
            spec_type=SpecType.FUNCTIONAL,
            title="Functional Spec",
            version="1.0",
            requirements=[
                Requirement(
                    id="FS-001",
                    title="Req 1",
                    description="Req 1",
                    spec_type=SpecType.FUNCTIONAL,
                ),
                Requirement(
                    id="FS-002",
                    title="Req 2",
                    description="Req 2",
                    spec_type=SpecType.FUNCTIONAL,
                ),
            ],
        )

        matrix_data = matrix.generate_matrix([test_case_1, test_case_2], None, functional_spec, None)

        assert len(matrix_data) == 2
        assert matrix_data[0]["Test Case ID"] == "TEST-FS-001"
        assert matrix_data[1]["Test Case ID"] == "TEST-FS-002"

    def test_generate_matrix_empty(self):
        """Test generating matrix with no test cases."""
        matrix = TraceabilityMatrix()
        matrix_data = matrix.generate_matrix([], None, None, None)
        assert len(matrix_data) == 0

