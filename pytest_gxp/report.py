"""CSV Validation Summary Report generator."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import __version__
from .markdown_format import (
    IMAGE_EVIDENCE_TYPES,
    ApprovalSignature,
    EvidenceItem,
    QualificationType,
    Requirement,
    Specification,
    TestCase,
    ValidationFinding,
    ValidationMetadata,
)
from .provenance import utc_now_iso, utc_today
from .traceability import TraceabilityMatrix

# Risk tiers of the ``gxp_risk`` marker, most severe first. Unset ("") is least severe.
RISK_TIERS = ("high", "medium", "not-high")
_RISK_RANK = {tier: rank for rank, tier in enumerate(RISK_TIERS)}

# Outcomes that need no deviation: everything else is a non-passing result that a
# regulated record must explain with a deviation reference.
PASSING_OUTCOMES = frozenset({"PASSED", "SKIPPED", "XFAIL"})

PROVISIONAL_BANNER = "**PROVISIONAL — DRAFT RECORD. NOT FOR SIGNATURE.**"


def rollup_risk(tiers: List[str]) -> str:
    """Return the most severe risk tier of a group of tests ("" when none is set)."""
    ranked = [_RISK_RANK[tier] for tier in tiers if tier in _RISK_RANK]
    return RISK_TIERS[min(ranked)] if ranked else ""


def resolve_deviation_ref(
    node_id: str, requirement_ids: List[str], deviations: Dict[str, str]
) -> Optional[str]:
    """Look up the deviation reference for a test: nodeid first, then its requirements."""
    if not deviations:
        return None
    if node_id in deviations:
        return deviations[node_id]
    for req_id in requirement_ids:
        if req_id in deviations:
            return deviations[req_id]
    return None


class CSVValidationReport:
    """Generate CSV Validation Summary Reports."""

    def __init__(self):
        self.report_data = {}

    def generate_report(
        self,
        test_cases: List[TestCase],
        design_spec: Optional[Specification] = None,
        functional_spec: Optional[Specification] = None,
        user_spec: Optional[Specification] = None,
        traceability_matrix: Optional[TraceabilityMatrix] = None,
        test_results: Optional[Dict[str, str]] = None,
        output_path: Optional[Path] = None,
        validation_metadata: Optional[ValidationMetadata] = None,
        all_requirements: Optional[List[Requirement]] = None,
        requirement_tests: Optional[Dict[str, List[str]]] = None,
        installation_spec: Optional[Specification] = None,
        source_provenance: Optional[Dict[str, Any]] = None,
        findings: Optional[List[ValidationFinding]] = None,
        test_records: Optional[Dict[str, Dict[str, Any]]] = None,
        deviations: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Dict:
        """Generate CSV validation summary report.

        Args:
            test_cases: List of test cases
            design_spec: Design specification
            functional_spec: Functional specification
            user_spec: User specification
            traceability_matrix: Traceability matrix for coverage
            test_results: Mapping of test case ID to status
            output_path: Path to write JSON report
            validation_metadata: Qualification type, version, and approval info
            all_requirements: All requirements for coverage calculation
            requirement_tests: Mapping of requirement ID to test nodeids
            installation_spec: Installation specification
            source_provenance: Source revision of the system under test
            findings: Validation findings raised during this session
            test_records: Nodeid -> execution record of the real pytest tests
            deviations: Nodeid-or-requirement-id -> deviation reference
        """
        test_results = test_results or {}
        requirement_tests = requirement_tests or {}
        test_records = test_records or {}
        findings = findings or []
        deviations = deviations or {}

        # Calculate test execution statistics
        total_tests = len(test_cases)
        passed_tests = sum(
            1 for tc in test_cases if test_results.get(tc.id, "").upper() in ["PASSED", "PASS"]
        )
        failed_tests = sum(
            1 for tc in test_cases if test_results.get(tc.id, "").upper() in ["FAILED", "FAIL"]
        )
        skipped_tests = sum(
            1 for tc in test_cases if test_results.get(tc.id, "").upper() in ["SKIPPED", "SKIP"]
        )
        not_executed = total_tests - passed_tests - failed_tests - skipped_tests
        executed_tests = passed_tests + failed_tests

        # Errors have no requirement-level equivalent (a requirement whose test errored
        # rolls up as failed), so they are counted over the real execution register.
        error_tests = sum(1 for rec in test_records.values() if rec.get("status") == "ERROR")

        # Calculate test pass rate (passed / executed, not total)
        test_pass_rate = (passed_tests / executed_tests * 100) if executed_tests > 0 else 0
        test_execution_rate = (executed_tests / total_tests * 100) if total_tests > 0 else 0

        # Calculate requirement coverage
        total_requirements = len(all_requirements) if all_requirements else 0
        reqs_with_tests = len(requirement_tests)
        reqs_without_tests = total_requirements - reqs_with_tests
        requirement_coverage_rate = (
            (reqs_with_tests / total_requirements * 100) if total_requirements > 0 else 0
        )

        # Get coverage from traceability matrix
        traceability_coverage = {}
        if traceability_matrix:
            traceability_coverage = traceability_matrix.get_coverage_report(all_requirements)

        # Determine report title based on qualification type
        if validation_metadata:
            qual_type = validation_metadata.qualification_type
            report_title = f"{qual_type.value} Report"
        else:
            qual_type = QualificationType.OQ
            report_title = "Operational Qualification Report"

        sorted_findings = sorted(findings, key=lambda f: (f.code, f.location, f.message))

        # Resolve the deviation reference of every executed test up front: requirements
        # inherit the first reference found among the tests that verify them.
        test_deviations = {
            node_id: resolve_deviation_ref(
                node_id, list(record.get("requirement_ids", [])), deviations
            )
            for node_id, record in test_records.items()
        }
        requirement_risk: Dict[str, str] = {}
        requirement_deviation: Dict[str, Optional[str]] = {}
        for req_id, node_ids in requirement_tests.items():
            requirement_risk[req_id] = rollup_risk(
                [test_records.get(node_id, {}).get("risk_tier", "") for node_id in node_ids]
            )
            requirement_deviation[req_id] = next(
                (
                    test_deviations[node_id]
                    for node_id in sorted(node_ids)
                    if test_deviations.get(node_id)
                ),
                None,
            )

        # A record that reports failures, unexplained results or errors is a draft
        non_passing = {
            node_id: record
            for node_id, record in test_records.items()
            if record.get("status") not in PASSING_OUTCOMES
        }
        broken_count = sum(
            1 for rec in test_records.values() if rec.get("status") in ("FAILED", "ERROR")
        )
        undocumented = sum(1 for node_id in non_passing if not test_deviations.get(node_id))
        error_findings = sum(1 for f in findings if f.severity == "error")

        provisional_reasons = []
        if broken_count:
            provisional_reasons.append(f"{broken_count} test(s) failed or errored")
        if undocumented:
            provisional_reasons.append(
                f"{undocumented} non-passing test(s) without a deviation reference"
            )
        if error_findings:
            provisional_reasons.append(f"{error_findings} error-severity validation finding(s)")

        # Build report
        report = {
            "report_metadata": {
                "title": report_title,
                "qualification_type": qual_type.value,
                "generated_date": utc_now_iso(),
                "version": "1.0",
                "status": "PROVISIONAL" if provisional_reasons else "FINAL",
                "provisional_reasons": provisional_reasons,
                "generator": {"name": "pytest-gxp", "version": __version__},
                "findings_summary": {
                    "errors": sum(1 for f in findings if f.severity == "error"),
                    "warnings": sum(1 for f in findings if f.severity == "warning"),
                },
                "source_provenance": source_provenance
                or {
                    "source": "unavailable",
                    "git_commit": None,
                    "git_tag": None,
                    "git_dirty": None,
                },
            },
            "validation_info": self._build_validation_info(validation_metadata),
            "approvals": self._build_approvals_section(validation_metadata),
            "specifications": {
                "design_spec": {
                    "title": design_spec.title if design_spec else "N/A",
                    "version": design_spec.version if design_spec else "N/A",
                    "requirement_count": len(design_spec.requirements) if design_spec else 0,
                },
                "functional_spec": {
                    "title": functional_spec.title if functional_spec else "N/A",
                    "version": functional_spec.version if functional_spec else "N/A",
                    "requirement_count": (
                        len(functional_spec.requirements) if functional_spec else 0
                    ),
                },
                "user_spec": {
                    "title": user_spec.title if user_spec else "N/A",
                    "version": user_spec.version if user_spec else "N/A",
                    "requirement_count": len(user_spec.requirements) if user_spec else 0,
                },
                "installation_spec": {
                    "title": installation_spec.title if installation_spec else "N/A",
                    "version": installation_spec.version if installation_spec else "N/A",
                    "requirement_count": (
                        len(installation_spec.requirements) if installation_spec else 0
                    ),
                },
            },
            "test_execution_summary": {
                "total_tests": total_tests,
                "executed_tests": executed_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "skipped_tests": skipped_tests,
                "error_tests": error_tests,
                "not_executed_tests": not_executed,
                "test_pass_rate": test_pass_rate,
                "test_execution_rate": test_execution_rate,
            },
            "requirement_coverage": {
                "total_requirements": total_requirements,
                "requirements_with_tests": reqs_with_tests,
                "requirements_without_tests": reqs_without_tests,
                "coverage_rate": requirement_coverage_rate,
                "requirements_verified": traceability_coverage.get("requirements_verified", 0),
                "verification_rate": traceability_coverage.get("requirement_verification_rate", 0),
            },
            # Legacy field for backwards compatibility
            "test_summary": {
                "total_test_cases": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "skipped": skipped_tests,
                "errors": error_tests,
                "not_executed": not_executed,
                "pass_rate": test_pass_rate,
            },
            "coverage": traceability_coverage,
            "test_cases": [
                {
                    "id": tc.id,
                    "title": tc.title,
                    "requirements": tc.requirements,
                    "status": test_results.get(tc.id, "Not Executed"),
                    "spec_type": tc.metadata.get("spec_type", "Unknown"),
                    "expected_result": tc.expected_result,
                    "metadata": tc.metadata,
                    "risk_tier": rollup_risk(
                        [requirement_risk.get(r, "") for r in tc.requirements]
                    ),
                    "deviation_ref": next(
                        (
                            requirement_deviation[req_id]
                            for req_id in tc.requirements
                            if requirement_deviation.get(req_id)
                        ),
                        None,
                    ),
                }
                for tc in test_cases
            ],
            "test_execution": [
                {
                    "node_id": node_id,
                    "outcome": record.get("status", "NOT_EXECUTED"),
                    "reason": record.get("reason", ""),
                    "requirement_ids": list(record.get("requirement_ids", [])),
                    "risk_tier": record.get("risk_tier", ""),
                    "deviation_ref": test_deviations.get(node_id),
                }
                for node_id, record in sorted(test_records.items())
            ],
            "findings": [
                {
                    "code": f.code,
                    "severity": f.severity,
                    "message": f.message,
                    "location": f.location,
                }
                for f in sorted_findings
            ],
        }

        self.report_data = report

        # Write to file if output path provided
        if output_path:
            self.write_report(output_path)

        return report

    def _build_validation_info(self, validation_metadata: Optional[ValidationMetadata]) -> Dict:
        """Build the validation info section of the report."""
        if validation_metadata:
            return {
                "software_name": validation_metadata.software_name,
                "software_version": validation_metadata.software_version,
                "project_name": validation_metadata.project_name,
                "validation_date": validation_metadata.validation_date,
            }
        return {
            "software_name": "N/A",
            "software_version": "N/A",
            "project_name": "N/A",
            "validation_date": utc_today(),
        }

    def _format_source_revision(self, report: Dict) -> str:
        """Render the source revision of the validated system as a single line."""
        provenance = report.get("report_metadata", {}).get("source_provenance") or {}
        commit = provenance.get("git_commit")
        if not commit:
            return f"unavailable (source: {provenance.get('source', 'unavailable')})"

        revision = commit
        if provenance.get("git_tag"):
            revision += f" (tag {provenance['git_tag']})"
        if provenance.get("git_dirty"):
            revision += " [uncommitted changes]"
        return f"{revision} (source: {provenance.get('source', 'git')})"

    def _build_approvals_section(self, validation_metadata: Optional[ValidationMetadata]) -> Dict:
        """Build the approvals section of the report."""
        if not validation_metadata:
            return {
                "tester": None,
                "reviewer": None,
                "approver": None,
            }

        def approval_to_dict(approval: Optional[ApprovalSignature]) -> Optional[Dict]:
            if not approval or not approval.name:
                return None
            return {
                "name": approval.name,
                "role": approval.role,
                "date": approval.date,
                "signature": approval.signature_placeholder,
            }

        return {
            "tester": approval_to_dict(validation_metadata.tester),
            "reviewer": approval_to_dict(validation_metadata.reviewer),
            "approver": approval_to_dict(validation_metadata.approver),
        }

    def _build_evidence_section(
        self, evidence_items: List[EvidenceItem], inline_images: bool = True
    ) -> List[str]:
        """Build the objective evidence section for markdown reports.

        Args:
            evidence_items: List of evidence items to include
            inline_images: If True, display images inline; otherwise just link to them
        """
        if not evidence_items:
            return []

        lines = [
            "## Objective Evidence",
            "",
            f"Total evidence items: {len(evidence_items)}",
            "",
        ]

        # Group evidence by test
        evidence_by_test: Dict[str, List[EvidenceItem]] = {}
        for item in evidence_items:
            test_id = item.test_id
            if test_id not in evidence_by_test:
                evidence_by_test[test_id] = []
            evidence_by_test[test_id].append(item)

        # Render each test's evidence with inline images
        for test_id, items in sorted(evidence_by_test.items()):
            # Create anchor for linking from test cases table
            anchor_id = test_id.replace("::", "_").replace("/", "_").replace(".", "_")
            lines.extend(
                [
                    f'<a id="evidence-{anchor_id}"></a>',
                    f"### {test_id}",
                    "",
                ]
            )

            for item in items:
                reqs = ", ".join(item.requirement_ids) if item.requirement_ids else "-"
                lines.extend(
                    [
                        f"**{item.id}**: {item.description}",
                        "",
                        f"- **Type:** {item.evidence_type.value}",
                        f"- **Requirements:** {reqs}",
                        f"- **Timestamp:** {item.timestamp}",
                        "",
                    ]
                )

                if item.evidence_type in IMAGE_EVIDENCE_TYPES:
                    if inline_images:
                        lines.extend([f"![{item.description}]({item.file_path})", ""])
                else:
                    lines.extend(self._build_session_details(item))

            lines.append("")

        return lines

    def _build_session_details(self, item: EvidenceItem) -> List[str]:
        """Render non-image evidence (an unscripted session record) as a bullet list."""
        meta = item.metadata or {}
        observations = meta.get("observations") or []
        defects = meta.get("defects") or []
        lines = [
            f"- **Charter:** {self._cell(meta.get('charter', '-'))}",
            f"- **Tester:** {self._cell(meta.get('tester', '-'))}",
            f"- **Duration:** {meta.get('duration_minutes', '-')} minutes",
            "- **Observations:**",
        ]
        lines.extend(f"    - {self._cell(obs)}" for obs in observations)
        lines.append("- **Defects:**")
        lines.extend(f"    - {self._cell(defect)}" for defect in defects)
        if not defects:
            lines.append("    - none")
        lines.append("")
        return lines

    def _get_evidence_by_requirement(
        self, evidence_items: List[EvidenceItem]
    ) -> Dict[str, List[EvidenceItem]]:
        """Build a mapping of requirement IDs to evidence items."""
        evidence_by_req: Dict[str, List[EvidenceItem]] = {}
        for item in evidence_items:
            for req_id in item.requirement_ids:
                if req_id not in evidence_by_req:
                    evidence_by_req[req_id] = []
                evidence_by_req[req_id].append(item)
        return evidence_by_req

    def _get_evidence_by_test(
        self, evidence_items: List[EvidenceItem]
    ) -> Dict[str, List[EvidenceItem]]:
        """Build a mapping of test IDs to evidence items."""
        evidence_by_test: Dict[str, List[EvidenceItem]] = {}
        for item in evidence_items:
            test_id = item.test_id
            if test_id not in evidence_by_test:
                evidence_by_test[test_id] = []
            evidence_by_test[test_id].append(item)
        return evidence_by_test

    def write_report(self, output_path: Path) -> None:
        """Write report to file (JSON format)."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.report_data, f, indent=2, ensure_ascii=False)

    def write_markdown_report(
        self, output_path: Path, evidence_items: Optional[List[EvidenceItem]] = None
    ) -> None:
        """Write report in Markdown format.

        Args:
            output_path: Path to write the markdown report
            evidence_items: Optional list of evidence items to include
        """
        content = self._get_markdown_content(evidence_items=evidence_items)
        if not content:
            return

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

    def write_csv_report(self, output_path: Path) -> None:
        """Write validation report in CSV format."""
        import csv

        if not self.report_data:
            return

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Header row
            writer.writerow(
                [
                    "Test Case ID",
                    "Title",
                    "Requirements",
                    "Specification Type",
                    "Status",
                    "Deviation Ref",
                ]
            )

            # Data rows
            for tc in self.report_data.get("test_cases", []):
                writer.writerow(
                    [
                        tc["id"],
                        tc["title"],
                        ", ".join(tc["requirements"]),
                        tc["spec_type"],
                        tc["status"],
                        tc.get("deviation_ref") or "",
                    ]
                )

    def write_pdf_report(
        self, output_path: Path, evidence_items: Optional[List[EvidenceItem]] = None
    ) -> None:
        """Write report in PDF format (requires weasyprint and markdown packages).

        Args:
            output_path: Path to write the PDF report
            evidence_items: Optional list of evidence items to include
        """
        try:
            import markdown
            from weasyprint import HTML
        except ImportError as e:
            raise ImportError(
                f"PDF generation requires 'weasyprint' and 'markdown' packages. "
                f"Install with: pip install pytest-gxp[pdf]. "
                f"Original error: {e}"
            ) from e

        # Convert markdown to HTML
        md_content = self._get_markdown_content(evidence_items=evidence_items)
        html_content = markdown.markdown(md_content, extensions=["tables", "fenced_code"])

        # Add basic styling with image sizing for evidence
        html_with_style = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        h1 {{ color: #333; border-bottom: 2px solid #333; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        h3 {{ color: #666; margin-top: 20px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; font-weight: bold; }}
        .summary {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; }}
        .approval-table {{ margin-top: 50px; }}
        img {{ max-width: 100%; height: auto; margin: 10px 0; border: 1px solid #ddd; }}
    </style>
</head>
<body>
{html_content}
</body>
</html>"""

        # Generate PDF with base_url for resolving relative image paths
        output_path.parent.mkdir(parents=True, exist_ok=True)
        base_url = str(output_path.parent.absolute()) + "/"
        HTML(string=html_with_style, base_url=base_url).write_pdf(output_path)

    def _get_markdown_content(self, evidence_items: Optional[List[EvidenceItem]] = None) -> str:
        """Build the markdown body of the report.

        This is the single source for both the markdown file and the PDF, which is
        rendered from this same content.

        Args:
            evidence_items: Optional list of evidence items to include
        """
        if not self.report_data:
            return ""

        report = self.report_data
        metadata = report["report_metadata"]
        provisional = metadata.get("status") == "PROVISIONAL"
        title = metadata["title"] + (" — PROVISIONAL (DRAFT)" if provisional else "")
        md_lines = [f"# {title}", ""]
        if provisional:
            reasons = "; ".join(metadata.get("provisional_reasons", []))
            md_lines.extend([f"> {PROVISIONAL_BANNER}", f"> {reasons}", ""])

        # Validation info
        if report.get("validation_info"):
            info = report["validation_info"]
            md_lines.extend(
                [
                    "## Validation Information",
                    "",
                    f"- **Project:** {info.get('project_name', 'N/A')}",
                    f"- **Software:** {info.get('software_name', 'N/A')}",
                    f"- **Version:** {info.get('software_version', 'N/A')}",
                    f"- **Validation Date:** {info.get('validation_date', 'N/A')}",
                    f"- **Report Generated:** {report['report_metadata']['generated_date']}",
                    f"- **Source Revision:** {self._format_source_revision(report)}",
                    "",
                ]
            )

        # Approvals section
        approvals = report.get("approvals", {})
        has_approvals = any(approvals.get(role) for role in ["tester", "reviewer", "approver"])
        if has_approvals:
            md_lines.extend(
                [
                    "## Approvals",
                    "",
                    "| Role | Name | Date | Signature |",
                    "|------|------|------|-----------|",
                ]
            )
            for role in ["tester", "reviewer", "approver"]:
                approval = approvals.get(role)
                if approval:
                    md_lines.append(
                        f"| {approval['role']} | {approval['name']} | "
                        f"{approval['date']} | {approval['signature']} |"
                    )
            md_lines.append("")

        md_lines.extend(self._build_findings_section(report.get("findings", [])))

        # Specifications section
        specs = report["specifications"]
        md_lines.extend(["## Specifications", ""])
        for key, heading in (
            ("design_spec", "Design Specification"),
            ("functional_spec", "Functional Specification"),
            ("user_spec", "User Specification"),
        ):
            md_lines.extend(
                [
                    f"### {heading}",
                    f"- **Title:** {specs[key]['title']}",
                    f"- **Version:** {specs[key]['version']}",
                    f"- **Requirements:** {specs[key]['requirement_count']}",
                    "",
                ]
            )

        # Test Execution Summary
        test_exec = report.get("test_execution_summary", report.get("test_summary", {}))
        total = test_exec.get("total_tests", test_exec.get("total_test_cases", 0))
        pass_rate = test_exec.get("test_pass_rate", test_exec.get("pass_rate", 0))
        md_lines.extend(
            [
                "## Test Execution Summary",
                "",
                f"- **Total Tests:** {total}",
                f"- **Executed:** {test_exec.get('executed_tests', 'N/A')}",
                f"- **Passed:** {test_exec.get('passed_tests', test_exec.get('passed', 0))}",
                f"- **Failed:** {test_exec.get('failed_tests', test_exec.get('failed', 0))}",
                f"- **Skipped:** {test_exec.get('skipped_tests', test_exec.get('skipped', 0))}",
                f"- **Errors:** {test_exec.get('error_tests', test_exec.get('errors', 0))}",
                "- **Not Executed:** "
                f"{test_exec.get('not_executed_tests', test_exec.get('not_executed', 0))}",
                f"- **Test Pass Rate:** {pass_rate:.1f}%",
            ]
        )
        if "test_execution_rate" in test_exec:
            md_lines.append(f"- **Test Execution Rate:** {test_exec['test_execution_rate']:.1f}%")
        md_lines.append("")

        # Requirement Coverage Summary
        req_cov = report.get("requirement_coverage", {})
        if req_cov:
            md_lines.extend(
                [
                    "## Requirement Coverage Summary",
                    "",
                    f"- **Total Requirements:** {req_cov.get('total_requirements', 0)}",
                    f"- **Requirements with Tests:** {req_cov.get('requirements_with_tests', 0)}",
                    "- **Requirements without Tests:** "
                    f"{req_cov.get('requirements_without_tests', 0)}",
                    f"- **Requirement Coverage Rate:** {req_cov.get('coverage_rate', 0):.1f}%",
                    "",
                    "- **Requirements Verified (passing tests):** "
                    f"{req_cov.get('requirements_verified', 0)}",
                    f"- **Verification Rate:** {req_cov.get('verification_rate', 0):.1f}%",
                    "",
                ]
            )

        # Build mapping of requirements to evidence for linking
        evidence_by_req: Dict[str, List[EvidenceItem]] = {}
        if evidence_items:
            evidence_by_req = self._get_evidence_by_requirement(evidence_items)

        # Test Cases table with evidence links
        md_lines.extend(
            [
                "## Test Cases",
                "",
                "| Test Case ID | Title | Requirements | Status | Evidence |",
                "|--------------|-------|--------------|--------|----------|",
            ]
        )

        for tc in report.get("test_cases", []):
            reqs = ", ".join(tc["requirements"])
            # Find evidence for this test case's requirements
            evidence_links = []
            for req_id in tc["requirements"]:
                for ev in evidence_by_req.get(req_id, []):
                    # Create anchor link to evidence section
                    anchor_id = ev.test_id.replace("::", "_").replace("/", "_").replace(".", "_")
                    evidence_links.append(f"[{ev.id}](#evidence-{anchor_id})")
            evidence_str = ", ".join(evidence_links) if evidence_links else "-"
            md_lines.append(
                f"| {tc['id']} | {self._cell(tc['title'])} | {reqs} | {tc['status']} | "
                f"{evidence_str} |"
            )

        md_lines.append("")
        md_lines.extend(self._build_test_execution_section(report.get("test_execution", [])))

        # Objective Evidence section with inline images
        if evidence_items:
            md_lines.extend(self._build_evidence_section(evidence_items))

        return "\n".join(md_lines)

    @staticmethod
    def _deviation_cell(record: Dict[str, Any]) -> str:
        """Render a deviation reference: an unexplained non-passing result is flagged."""
        ref = record.get("deviation_ref")
        if ref:
            return str(ref)
        return "**MISSING**" if record.get("outcome") not in PASSING_OUTCOMES else "—"

    @staticmethod
    def _cell(text: Any) -> str:
        """Render free text safely inside a markdown table cell."""
        return str(text).replace("|", "\\|").replace("\n", " ")

    def _build_findings_section(self, findings: List[Dict[str, str]]) -> List[str]:
        """Build the validation findings section; empty when there is nothing to report."""
        if not findings:
            return []

        lines = [
            "## Validation Findings",
            "",
            "| Severity | Code | Location | Message |",
            "|----------|------|----------|---------|",
        ]
        for finding in findings:
            lines.append(
                f"| {finding['severity']} | {finding['code']} | "
                f"{finding.get('location') or '-'} | {self._cell(finding['message'])} |"
            )
        lines.append("")
        return lines

    def _build_test_execution_section(self, test_execution: List[Dict[str, Any]]) -> List[str]:
        """Build the table of real pytest tests and their outcomes."""
        if not test_execution:
            return []

        lines = [
            "## Test Execution",
            "",
            "| Node ID | Outcome | Requirements | Deviation Ref | Reason |",
            "|---------|---------|--------------|---------------|--------|",
        ]
        for record in test_execution:
            reqs = ", ".join(record.get("requirement_ids") or []) or "-"
            reason = self._cell(record.get("reason", "")) or "-"
            lines.append(
                f"| {record['node_id']} | {record['outcome']} | {reqs} | "
                f"{self._deviation_cell(record)} | {reason} |"
            )
        lines.append("")
        return lines
