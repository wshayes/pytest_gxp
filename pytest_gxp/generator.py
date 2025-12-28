"""Test case generator from specifications."""

import re
from typing import List, Optional

from .markdown_format import Requirement, Specification, TestCase
from .parser import SpecificationParser


class TestCaseGenerator:
    """Generate pytest test cases from specifications."""

    def __init__(self, parser: SpecificationParser):
        self.parser = parser

    def generate_test_cases(
        self,
        design_spec: Optional[Specification],
        functional_spec: Optional[Specification],
        installation_spec: Optional[Specification] = None,
    ) -> List[TestCase]:
        """Generate test cases from design, functional, and installation specifications."""
        test_cases = []

        # Prioritize functional spec requirements, then design, then installation
        requirements = []
        if functional_spec:
            requirements.extend(functional_spec.requirements)
        if design_spec:
            # Add design requirements that aren't already covered
            existing_ids = {req.id for req in requirements}
            requirements.extend(
                req for req in design_spec.requirements if req.id not in existing_ids
            )
        if installation_spec:
            # Add installation requirements that aren't already covered
            existing_ids = {req.id for req in requirements}
            requirements.extend(
                req for req in installation_spec.requirements if req.id not in existing_ids
            )

        # Generate test case for each requirement
        for req in requirements:
            test_case = self._requirement_to_test_case(req, requirements)
            test_cases.append(test_case)

        return test_cases

    def _requirement_to_test_case(
        self, requirement: Requirement, all_requirements: List[Requirement]
    ) -> TestCase:
        """Convert a requirement to a test case."""
        # Generate test case ID
        test_id = f"TEST-{requirement.id}"

        # Generate test title
        test_title = f"Test {requirement.id}: {requirement.title}"

        # Generate test steps from requirement description
        steps = self._extract_steps_from_description(requirement.description)

        # Generate expected result
        expected_result = self._generate_expected_result(requirement)

        # Find related requirements (parent/child relationships)
        related_requirements = [requirement.id]
        if requirement.parent_id:
            related_requirements.append(requirement.parent_id)

        return TestCase(
            id=test_id,
            title=test_title,
            description=requirement.description,
            requirements=related_requirements,
            steps=steps,
            expected_result=expected_result,
            metadata={
                "spec_type": requirement.spec_type.value,
                "requirement_id": requirement.id,
                **requirement.metadata,
            },
        )

    def _extract_steps_from_description(self, description: str) -> List[str]:
        """Extract test steps from requirement description."""
        steps = []
        lines = description.split("\n")

        for line in lines:
            line = line.strip()
            # Look for numbered or bulleted lists
            if re.match(r"^\d+[\.\)]\s+", line) or line.startswith("- ") or line.startswith("* "):
                step = re.sub(r"^\d+[\.\)]\s+", "", line)
                step = re.sub(r"^[-*]\s+", "", step)
                if step:
                    steps.append(step)
            elif line and not line.startswith("#") and len(steps) == 0:
                # First non-header line becomes a step if no steps found
                steps.append(line)

        if not steps:
            steps = [description] if description else ["Verify requirement is met"]

        return steps

    def _generate_expected_result(self, requirement: Requirement) -> str:
        """Generate expected result for a test case."""
        # Try to extract from description
        description_lower = requirement.description.lower()
        if "expected" in description_lower or "should" in description_lower:
            # Look for expected result patterns
            lines = requirement.description.split("\n")
            for i, line in enumerate(lines):
                if "expected" in line.lower() or "should" in line.lower():
                    # Return next few lines as expected result
                    result_lines = []
                    for j in range(i, min(i + 3, len(lines))):
                        if lines[j].strip():
                            result_lines.append(lines[j].strip())
                    if result_lines:
                        return " ".join(result_lines)

        # Default expected result
        return f"Requirement {requirement.id} is satisfied: {requirement.title}"
