"""Traceability matrix generator for GxP specifications."""

import csv
from pathlib import Path
from typing import Dict, List, Optional, Set

from .markdown_format import Requirement, Specification, TestCase


class TraceabilityMatrix:
    """Generate traceability matrices for GxP validation."""

    def __init__(self):
        self.matrix_data = []

    def generate_matrix(
        self,
        test_cases: List[TestCase],
        design_spec: Optional[Specification] = None,
        functional_spec: Optional[Specification] = None,
        user_spec: Optional[Specification] = None,
        output_path: Optional[Path] = None,
        installation_spec: Optional[Specification] = None,
    ) -> List[Dict]:
        """Generate traceability matrix linking test cases to requirements."""
        matrix = []

        # Collect all requirements
        all_requirements = {}
        if design_spec:
            for req in design_spec.requirements:
                all_requirements[req.id] = req
        if functional_spec:
            for req in functional_spec.requirements:
                all_requirements[req.id] = req
        if user_spec:
            for req in user_spec.requirements:
                all_requirements[req.id] = req
        if installation_spec:
            for req in installation_spec.requirements:
                all_requirements[req.id] = req

        # Build matrix: one row per test case
        for test_case in test_cases:
            for req_id in test_case.requirements:
                if req_id in all_requirements:
                    req = all_requirements[req_id]
                    matrix.append(
                        {
                            "Test Case ID": test_case.id,
                            "Test Case Title": test_case.title,
                            "Requirement ID": req_id,
                            "Requirement Title": req.title,
                            "Specification Type": req.spec_type.value,
                            "User Requirement ID": self._find_user_requirement(req_id, user_spec) if user_spec else "",
                            "Status": "Not Executed",  # Will be updated after test execution
                        }
                    )

        self.matrix_data = matrix

        # Write to CSV if output path provided
        if output_path:
            self.write_csv(output_path)

        return matrix

    def _find_user_requirement(self, req_id: str, user_spec: Optional[Specification]) -> str:
        """Find corresponding user requirement ID if available."""
        if not user_spec:
            return ""

        # Simple mapping: look for similar IDs or titles
        # In a real implementation, this might use metadata or explicit mappings
        for req in user_spec.requirements:
            if req_id in req.metadata.get("maps_to", []):
                return req.id
            # Check if titles are similar
            if req.title.lower() in req_id.lower() or req_id.lower() in req.title.lower():
                return req.id

        return ""

    def write_csv(self, output_path: Path) -> None:
        """Write traceability matrix to CSV file."""
        if not self.matrix_data:
            return

        output_path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            "Test Case ID",
            "Test Case Title",
            "Requirement ID",
            "Requirement Title",
            "Specification Type",
            "User Requirement ID",
            "Status",
        ]

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.matrix_data)

    def write_json(self, output_path: Path, project_name: str = "GxP Validation Project") -> None:
        """Write traceability matrix to JSON file."""
        import json
        from datetime import datetime

        if not self.matrix_data:
            return

        output_path.parent.mkdir(parents=True, exist_ok=True)

        coverage = self.get_coverage_report()

        data = {
            "metadata": {
                "title": "Traceability Matrix",
                "project": project_name,
                "generated_date": datetime.now().isoformat(),
                "version": "1.0",
            },
            "coverage": coverage,
            "matrix": self.matrix_data,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def write_markdown(
        self, output_path: Path, project_name: str = "GxP Validation Project"
    ) -> None:
        """Write traceability matrix to Markdown file."""
        if not self.matrix_data:
            return

        output_path.parent.mkdir(parents=True, exist_ok=True)

        from datetime import datetime

        coverage = self.get_coverage_report()

        md_lines = [
            "# Traceability Matrix",
            "",
            f"**Project:** {project_name}",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d')}",
            "**Version:** 1.0",
            "",
            "## Overview",
            "",
            "This traceability matrix demonstrates the relationship between test cases, requirements from Design and Functional Specifications, and User Requirements.",
            "",
            "## Traceability Data",
            "",
            "| Test Case ID | Test Case Title | Requirement ID | Requirement Title | Specification Type | User Requirement ID | Status |",
            "|--------------|----------------|----------------|-------------------|-------------------|---------------------|--------|",
        ]

        for row in self.matrix_data:
            md_lines.append(
                f"| {row['Test Case ID']} | {row['Test Case Title']} | {row['Requirement ID']} | "
                f"{row['Requirement Title']} | {row['Specification Type']} | "
                f"{row.get('User Requirement ID', '')} | {row['Status']} |"
            )

        md_lines.extend(
            [
                "",
                "## Coverage Summary",
                "",
                f"- **Total Requirements:** {coverage['total_requirements']}",
                f"- **Covered Requirements:** {coverage['covered_requirements']}",
                f"- **Coverage Percentage:** {coverage['coverage_percentage']:.1f}%",
            ]
        )

        if coverage.get("uncovered_requirements"):
            md_lines.append(f"- **Uncovered Requirements:** {', '.join(coverage['uncovered_requirements'])}")

        md_lines.extend(["", "## Notes", "", "- All requirements should have corresponding test cases", ""])

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))

    def update_test_status(self, test_case_id: str, status: str) -> None:
        """Update the status of a test case in the matrix."""
        for row in self.matrix_data:
            if row["Test Case ID"] == test_case_id:
                row["Status"] = status

    def update_test_status_by_requirement(self, requirement_id: str, status: str) -> None:
        """Update the status of all test cases linked to a requirement.

        Args:
            requirement_id: The requirement ID to update
            status: The test status (e.g., "PASSED", "FAILED")
        """
        for row in self.matrix_data:
            if row["Requirement ID"] == requirement_id:
                # Only update if current status is worse or not set
                current = row["Status"]
                if current in ["Not Executed", "NOT_EXECUTED"]:
                    row["Status"] = status
                elif status == "FAILED":
                    row["Status"] = status
                elif status == "PASSED" and current not in ["FAILED", "Failed"]:
                    row["Status"] = status

    def get_coverage_report(self, all_requirements: Optional[List[Requirement]] = None) -> Dict:
        """Generate comprehensive coverage report from traceability matrix.

        Args:
            all_requirements: Optional list of all requirements for true coverage calculation

        Returns:
            Dictionary with coverage metrics:
            - total_requirements: Total number of requirements
            - requirements_with_tests: Requirements that have at least one test
            - requirements_without_tests: Count of requirements without tests
            - requirement_coverage_rate: % of requirements with tests
            - requirements_verified: Requirements with passing tests
            - requirement_verification_rate: % of covered requirements verified
            - uncovered_requirements: List of requirement IDs without tests
            - unverified_requirements: List of requirement IDs with tests but not passing
        """
        # Get requirements from matrix
        requirements_in_matrix: Set[str] = set()
        requirements_with_passing_tests: Set[str] = set()
        requirements_with_any_status: Set[str] = set()

        for row in self.matrix_data:
            req_id = row["Requirement ID"]
            requirements_in_matrix.add(req_id)

            status = row["Status"]
            if status not in ["Not Executed", "NOT_EXECUTED"]:
                requirements_with_any_status.add(req_id)

            if status in ["Passed", "PASSED", "pass"]:
                requirements_with_passing_tests.add(req_id)

        # Calculate total requirements from all_requirements if provided
        if all_requirements:
            total_requirement_ids = {req.id for req in all_requirements}
        else:
            total_requirement_ids = requirements_in_matrix

        requirements_with_tests = requirements_in_matrix
        requirements_without_tests = total_requirement_ids - requirements_with_tests

        # Calculate rates
        total_count = len(total_requirement_ids)
        with_tests_count = len(requirements_with_tests)
        coverage_rate = (with_tests_count / total_count * 100) if total_count > 0 else 0

        verified_count = len(requirements_with_passing_tests)
        verification_rate = (verified_count / with_tests_count * 100) if with_tests_count > 0 else 0

        return {
            # Requirement coverage metrics
            "total_requirements": total_count,
            "requirements_with_tests": with_tests_count,
            "requirements_without_tests": len(requirements_without_tests),
            "requirement_coverage_rate": coverage_rate,

            # Verification metrics
            "requirements_verified": verified_count,
            "requirement_verification_rate": verification_rate,

            # Legacy field names for backwards compatibility
            "covered_requirements": verified_count,
            "coverage_percentage": verification_rate,

            # Detail lists
            "uncovered_requirements": sorted(requirements_without_tests),
            "unverified_requirements": sorted(requirements_with_tests - requirements_with_passing_tests),
        }
