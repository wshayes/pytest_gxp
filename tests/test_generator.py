"""Tests for the test case generator."""



from pytest_gxp.generator import TestCaseGenerator
from pytest_gxp.markdown_format import Requirement, Specification, SpecType
from pytest_gxp.parser import SpecificationParser


class TestTestCaseGenerator:
    """Test cases for TestCaseGenerator."""

    def test_generate_test_cases_from_functional_spec(self, sample_specification):
        """Test generating test cases from functional specification."""
        parser = SpecificationParser()
        generator = TestCaseGenerator(parser)

        test_cases = generator.generate_test_cases(None, sample_specification)

        assert len(test_cases) == 1
        assert test_cases[0].id == "TEST-FS-001"
        assert test_cases[0].title == "Test FS-001: User Login"
        assert "FS-001" in test_cases[0].requirements

    def test_generate_test_cases_from_design_spec(self, temp_dir):
        """Test generating test cases from design specification."""
        parser = SpecificationParser()
        generator = TestCaseGenerator(parser)

        design_spec = Specification(
            spec_type=SpecType.DESIGN,
            title="Design Spec",
            version="1.0",
            requirements=[
                Requirement(
                    id="DS-001",
                    title="Test Design",
                    description="Design requirement",
                    spec_type=SpecType.DESIGN,
                )
            ],
        )

        test_cases = generator.generate_test_cases(design_spec, None)
        assert len(test_cases) == 1
        assert test_cases[0].id == "TEST-DS-001"

    def test_generate_test_cases_prioritizes_functional(self, temp_dir):
        """Test that functional specs are prioritized over design specs."""
        parser = SpecificationParser()
        generator = TestCaseGenerator(parser)

        design_spec = Specification(
            spec_type=SpecType.DESIGN,
            title="Design Spec",
            version="1.0",
            requirements=[
                Requirement(
                    id="DS-001",
                    title="Design Req",
                    description="Design requirement",
                    spec_type=SpecType.DESIGN,
                )
            ],
        )

        functional_spec = Specification(
            spec_type=SpecType.FUNCTIONAL,
            title="Functional Spec",
            version="1.0",
            requirements=[
                Requirement(
                    id="FS-001",
                    title="Functional Req",
                    description="Functional requirement",
                    spec_type=SpecType.FUNCTIONAL,
                )
            ],
        )

        test_cases = generator.generate_test_cases(design_spec, functional_spec)
        assert len(test_cases) == 2
        # Functional should come first
        assert test_cases[0].id == "TEST-FS-001"
        assert test_cases[1].id == "TEST-DS-001"

    def test_generate_test_cases_no_duplicates(self, temp_dir):
        """Test that duplicate requirement IDs are not duplicated in test cases."""
        parser = SpecificationParser()
        generator = TestCaseGenerator(parser)

        design_spec = Specification(
            spec_type=SpecType.DESIGN,
            title="Design Spec",
            version="1.0",
            requirements=[
                Requirement(
                    id="REQ-001",
                    title="Same ID",
                    description="Design requirement",
                    spec_type=SpecType.DESIGN,
                )
            ],
        )

        functional_spec = Specification(
            spec_type=SpecType.FUNCTIONAL,
            title="Functional Spec",
            version="1.0",
            requirements=[
                Requirement(
                    id="REQ-001",
                    title="Same ID",
                    description="Functional requirement",
                    spec_type=SpecType.FUNCTIONAL,
                )
            ],
        )

        test_cases = generator.generate_test_cases(design_spec, functional_spec)
        # Should only have one test case, not two
        assert len(test_cases) == 1

    def test_extract_steps_from_description(self):
        """Test extracting steps from requirement description."""
        parser = SpecificationParser()
        generator = TestCaseGenerator(parser)

        description = """This is a requirement.

1. First step
2. Second step
3. Third step
"""
        steps = generator._extract_steps_from_description(description)
        # Should extract the numbered steps (may include description line)
        assert len(steps) >= 3
        step_text = " ".join(steps)
        assert "First step" in step_text
        assert "Second step" in step_text
        assert "Third step" in step_text

    def test_extract_steps_from_bullet_list(self):
        """Test extracting steps from bullet list."""
        parser = SpecificationParser()
        generator = TestCaseGenerator(parser)

        description = """Requirement description.

- First item
- Second item
"""
        steps = generator._extract_steps_from_description(description)
        assert len(steps) >= 2

    def test_extract_steps_no_list(self):
        """Test extracting steps when no list is present."""
        parser = SpecificationParser()
        generator = TestCaseGenerator(parser)

        description = "Simple requirement description without steps."
        steps = generator._extract_steps_from_description(description)
        assert len(steps) > 0
        assert description in steps[0] or "Verify requirement is met" in steps

    def test_generate_expected_result(self):
        """Test generating expected result from requirement."""
        parser = SpecificationParser()
        generator = TestCaseGenerator(parser)

        description = """Requirement description.

Expected Result: The system should work correctly.
"""
        result = generator._generate_expected_result(
            Requirement(
                id="REQ-001",
                title="Test",
                description=description,
                spec_type=SpecType.FUNCTIONAL,
            )
        )
        assert "work correctly" in result.lower()

    def test_generate_expected_result_default(self):
        """Test default expected result when not specified."""
        parser = SpecificationParser()
        generator = TestCaseGenerator(parser)

        req = Requirement(
            id="REQ-001",
            title="Test Requirement",
            description="Simple description",
            spec_type=SpecType.FUNCTIONAL,
        )
        result = generator._generate_expected_result(req)
        assert "REQ-001" in result
        assert "Test Requirement" in result

    def test_requirement_to_test_case(self, sample_requirement):
        """Test converting requirement to test case."""
        parser = SpecificationParser()
        generator = TestCaseGenerator(parser)

        test_case = generator._requirement_to_test_case(sample_requirement, [sample_requirement])

        assert test_case.id == "TEST-FS-001"
        assert test_case.title == "Test FS-001: User Login"
        assert "FS-001" in test_case.requirements
        assert len(test_case.steps) > 0
        assert test_case.metadata["requirement_id"] == "FS-001"

