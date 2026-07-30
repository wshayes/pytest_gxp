"""Pytest plugin hooks for GxP validation."""

import json
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from _pytest.reports import TestReport

from .config import GxPConfig, load_config_from_ini, load_config_from_pyproject, merge_config
from .evidence import EvidenceCollector
from .generator import TestCaseGenerator
from .markdown_format import EvidenceItem, SpecType, ValidationFinding
from .parser import SpecificationParser
from .provenance import git_provenance, utc_now_iso, utc_today, write_artifact_manifest
from .report import (
    PASSING_OUTCOMES,
    RISK_TIERS,
    CSVValidationReport,
    resolve_deviation_ref,
    rollup_risk,
)
from .traceability import TraceabilityMatrix

# Module-level reference to config for use in hooks
_gxp_config: Optional[Config] = None

# Test outcome severity, worst first. Used to merge the setup/call/teardown phases of one
# test into a single verdict and to roll test outcomes up to their requirements.
_STATUS_RANK = {
    "ERROR": 0,
    "FAILED": 1,
    "XFAIL": 2,
    "XPASS": 3,
    "SKIPPED": 4,
    "NOT_EXECUTED": 5,
    "PASSED": 6,
}
_MAX_REASON_LENGTH = 500


def pytest_addoption(parser: Parser) -> None:
    """Add command-line options for pytest-gxp."""
    group = parser.getgroup("gxp", "GxP CSV Validation")

    # Core options
    group.addoption(
        "--gxp",
        action="store_true",
        default=False,
        help="Enable GxP CSV validation mode",
    )
    group.addoption(
        "--gxp-spec-files",
        action="store",
        default=None,
        help="Path to GxP specification files directory (default: gxp_spec_files)",
    )
    group.addoption(
        "--gxp-report-files",
        action="store",
        default=None,
        help="Path to GxP report files directory (default: gxp_report_files)",
    )

    # Qualification options
    group.addoption(
        "--gxp-qualification-type",
        action="store",
        default=None,
        choices=["IQ", "OQ", "PQ"],
        help="Qualification type: IQ (Installation), OQ (Operational), PQ (Performance)",
    )
    group.addoption(
        "--gxp-software-version",
        action="store",
        default=None,
        help="Software version being validated",
    )
    group.addoption(
        "--gxp-project-name",
        action="store",
        default=None,
        help="Project name for validation reports",
    )

    # Coverage options
    group.addoption(
        "--gxp-strict-coverage",
        action="store_true",
        default=False,
        help="Fail if any requirements lack test coverage",
    )
    group.addoption(
        "--gxp-strict",
        action="store_true",
        default=False,
        help="Fail the session if any error-severity validation finding is raised",
    )

    # Deviation options
    group.addoption(
        "--gxp-deviations",
        action="store",
        default=None,
        help="Path to a JSON map of {nodeid-or-requirement-id: deviation reference}",
    )

    # Approval options
    group.addoption(
        "--gxp-tester",
        action="store",
        default=None,
        help="Tester name for approval signature",
    )
    group.addoption(
        "--gxp-reviewer",
        action="store",
        default=None,
        help="Reviewer name for approval signature",
    )
    group.addoption(
        "--gxp-approver",
        action="store",
        default=None,
        help="Approver name for approval signature",
    )

    # Provenance options
    group.addoption(
        "--gxp-source-commit",
        action="store",
        default=None,
        help="Commit of the validated system (overrides git detection)",
    )
    group.addoption(
        "--gxp-source-tag",
        action="store",
        default=None,
        help="Tag of the validated system (overrides git detection)",
    )

    # Evidence options
    # Defaults are None so that "flag not passed" stays distinguishable from an
    # explicit choice and does not override ini/pyproject values.
    group.addoption(
        "--gxp-evidence-thumbnails",
        action="store_true",
        default=None,
        help="Generate thumbnail images for evidence (default: True)",
    )
    group.addoption(
        "--no-gxp-evidence-thumbnails",
        action="store_false",
        default=None,
        dest="gxp_evidence_thumbnails",
        help="Disable thumbnail generation for evidence",
    )

    # Output format options
    group.addoption(
        "--gxp-output-formats",
        action="store",
        default=None,
        help="Comma-separated list of output formats: csv,json,md,pdf (default: all)",
    )

    # Add ini options for configuration file support
    parser.addini("gxp_spec_files", "Path to GxP specification files directory")
    parser.addini("gxp_report_files", "Path to GxP report files directory")
    parser.addini("gxp_qualification_type", "Qualification type (IQ, OQ, PQ)")
    parser.addini("gxp_software_version", "Software version being validated")
    parser.addini("gxp_project_name", "Project name for validation reports")
    parser.addini("gxp_strict_coverage", "Fail if requirements lack coverage (true/false)")
    parser.addini("gxp_strict", "Fail on any error-severity finding (true/false)")
    parser.addini("gxp_deviations", "Path to the deviation reference map (JSON)")
    parser.addini("gxp_source_commit", "Commit of the validated system")
    parser.addini("gxp_source_tag", "Tag of the validated system")
    parser.addini("gxp_tester_name", "Tester name for approval")
    parser.addini("gxp_tester_date", "Tester date for approval")
    parser.addini("gxp_reviewer_name", "Reviewer name for approval")
    parser.addini("gxp_reviewer_date", "Reviewer date for approval")
    parser.addini("gxp_approver_name", "Approver name for approval")
    parser.addini("gxp_approver_date", "Approver date for approval")
    parser.addini("gxp_evidence_thumbnails", "Generate evidence thumbnails (true/false)")
    parser.addini("gxp_output_formats", "Output formats: csv,json,md,pdf (default: all)")


def pytest_configure(config: Config) -> None:
    """Configure pytest-gxp plugin."""
    global _gxp_config

    # Register custom markers (always, even if not enabled)
    config.addinivalue_line("markers", "gxp: mark test as GxP validation test")
    config.addinivalue_line(
        "markers", "requirements(requirement_ids): mark test with requirement IDs"
    )
    config.addinivalue_line(
        "markers",
        f"gxp_risk(tier): risk tier of the test, one of {', '.join(RISK_TIERS)}",
    )

    if not config.getoption("--gxp"):
        return

    # Store config reference for use in hooks
    _gxp_config = config

    # Load configuration from all sources
    cli_options = {
        "enabled": True,
        "spec_files": config.getoption("--gxp-spec-files"),
        "report_files": config.getoption("--gxp-report-files"),
        "qualification_type": config.getoption("--gxp-qualification-type"),
        "software_version": config.getoption("--gxp-software-version"),
        "project_name": config.getoption("--gxp-project-name"),
        "strict_coverage": config.getoption("--gxp-strict-coverage"),
        "strict": config.getoption("--gxp-strict"),
        "deviations": config.getoption("--gxp-deviations"),
        "output_formats": config.getoption("--gxp-output-formats"),
        "evidence_thumbnails": config.getoption("gxp_evidence_thumbnails"),
        "source_commit": config.getoption("--gxp-source-commit"),
        "source_tag": config.getoption("--gxp-source-tag"),
        "tester_name": config.getoption("--gxp-tester"),
        "reviewer_name": config.getoption("--gxp-reviewer"),
        "approver_name": config.getoption("--gxp-approver"),
    }

    # Load from pyproject.toml
    pyproject_config = load_config_from_pyproject(Path.cwd())

    # Load from pytest.ini
    ini_config = load_config_from_ini(config)

    # Merge all configurations
    gxp_config = merge_config(cli_options, pyproject_config, ini_config)

    # Store configuration
    config._gxp_config = gxp_config
    config._gxp_spec_files = Path(gxp_config.spec_files)
    config._gxp_report_files = Path(gxp_config.report_files)

    # Capture the source revision of the system under validation, once per session
    config._gxp_provenance = _resolve_provenance(config, gxp_config)

    # Initialize GxP components
    config._gxp_parser = SpecificationParser()
    config._gxp_generator = TestCaseGenerator(config._gxp_parser)
    config._gxp_traceability = TraceabilityMatrix()
    config._gxp_report = CSVValidationReport()
    config._gxp_test_results: Dict[str, str] = {}
    config._gxp_test_records: Dict[str, Dict[str, Any]] = {}
    config._gxp_test_requirement_map: Dict[str, List[str]] = {}
    config._gxp_test_risk: Dict[str, str] = {}
    config._gxp_findings: List[ValidationFinding] = []

    # Deviation references are assigned after investigation, so they arrive as a file
    config._gxp_deviations = _load_deviations(gxp_config.deviations, config._gxp_findings)

    # Initialize evidence collector
    config._gxp_evidence_collector = EvidenceCollector(
        config._gxp_report_files,
        generate_thumbnails=gxp_config.evidence_thumbnails,
    )


def _load_deviations(path: str, findings: List[ValidationFinding]) -> Dict[str, str]:
    """Load the deviation reference map; an unusable file is a finding, never a crash."""
    if not path:
        return {}

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("deviation file must contain a JSON object")
        return {str(key): str(value) for key, value in data.items()}
    except (OSError, ValueError) as e:
        findings.append(
            ValidationFinding(
                code="deviation-file-error",
                severity="warning",
                message=f"Could not read deviation file: {e}",
                location=str(path),
            )
        )
        return {}


def _resolve_provenance(config: Config, gxp_config: GxPConfig) -> Dict[str, Any]:
    """Determine the source revision, letting explicit config override git detection."""
    provenance = git_provenance(Path(str(config.rootdir)) if config.rootdir else Path.cwd())

    if gxp_config.source_commit or gxp_config.source_tag:
        provenance = {
            "source": "config",
            "git_commit": gxp_config.source_commit or provenance["git_commit"],
            "git_tag": gxp_config.source_tag or provenance["git_tag"],
            "git_dirty": provenance["git_dirty"],
        }

    return provenance


def pytest_collection_modifyitems(config: Config, items: List) -> None:
    """Modify collected test items for GxP validation."""
    if not config.getoption("--gxp"):
        return

    # Check if plugin was configured
    if not hasattr(config, "_gxp_parser"):
        return

    # Build test-to-requirement and test-to-risk mappings from markers
    test_requirement_map: Dict[str, List[str]] = {}
    test_risk_map: Dict[str, str] = {}
    for item in items:
        marker = item.get_closest_marker("requirements")
        if marker and marker.args:
            requirement_ids = marker.args[0]
            if isinstance(requirement_ids, (list, tuple)):
                test_requirement_map[item.nodeid] = list(requirement_ids)
            elif isinstance(requirement_ids, str):
                test_requirement_map[item.nodeid] = [requirement_ids]

        risk_marker = item.get_closest_marker("gxp_risk")
        if risk_marker and risk_marker.args:
            tier = str(risk_marker.args[0])
            if tier in RISK_TIERS:
                test_risk_map[item.nodeid] = tier
            else:
                config._gxp_findings.append(
                    ValidationFinding(
                        code="invalid-risk-tier",
                        severity="warning",
                        message=(
                            f"Unknown risk tier {tier!r}; expected one of {', '.join(RISK_TIERS)}"
                        ),
                        location=item.nodeid,
                    )
                )
    config._gxp_test_requirement_map = test_requirement_map
    config._gxp_test_risk = test_risk_map

    # Parse specifications
    spec_files_path = config._gxp_spec_files
    if spec_files_path.exists():
        specs = config._gxp_parser.parse_directory(spec_files_path)
        config._gxp_specs = specs
    else:
        config._gxp_specs = {}
        warnings.warn(
            f"GxP specification directory not found: {spec_files_path}",
            stacklevel=2,
        )

    # Findings raised while parsing the specifications
    config._gxp_findings.extend(config._gxp_parser.findings)

    # Generate test cases from specifications
    design_spec = config._gxp_specs.get(SpecType.DESIGN)
    functional_spec = config._gxp_specs.get(SpecType.FUNCTIONAL)
    installation_spec = config._gxp_specs.get(SpecType.INSTALLATION)
    user_spec = config._gxp_specs.get(SpecType.USER)

    if design_spec or functional_spec or installation_spec or user_spec:
        test_cases = config._gxp_generator.generate_test_cases(
            design_spec, functional_spec, installation_spec, user_spec
        )
        config._gxp_test_cases = test_cases

        # Generate traceability matrix data (outputs written at session finish)
        config._gxp_traceability.generate_matrix(
            test_cases,
            design_spec,
            functional_spec,
            user_spec,
            installation_spec=installation_spec,
        )
    else:
        config._gxp_test_cases = []

    # Collect all requirements for coverage checking, in a fixed spec-type order
    all_requirements = []
    for spec_type in SpecType:
        spec = config._gxp_specs.get(spec_type)
        if spec:
            all_requirements.extend(spec.requirements)
    config._gxp_all_requirements = all_requirements

    # Tests may only cite requirements that actually exist
    known_requirement_ids = {req.id for req in all_requirements}
    for nodeid, req_ids in sorted(test_requirement_map.items()):
        for req_id in req_ids:
            if req_id not in known_requirement_ids:
                config._gxp_findings.append(
                    ValidationFinding(
                        code="unknown-requirement-ref",
                        severity="error",
                        message=(
                            f"Test cites requirement {req_id}, which is not defined in "
                            "any specification"
                        ),
                        location=nodeid,
                    )
                )


def pytest_runtest_setup(item) -> None:
    """Setup before running a test."""
    if not item.config.getoption("--gxp"):
        return

    # Mark test with GxP marker if not already marked
    if not item.get_closest_marker("gxp"):
        item.add_marker(pytest.mark.gxp())


def _reason_from_report(report: TestReport) -> str:
    """Extract a one-line reason from a phase report (skip message or failure summary)."""
    longrepr = report.longrepr
    if longrepr is None:
        return ""

    crash = getattr(longrepr, "reprcrash", None)
    if crash is not None and getattr(crash, "message", None):
        text = str(crash.message)
    elif isinstance(longrepr, tuple) and len(longrepr) == 3:
        # Skips are reported as (path, lineno, "Skipped: reason")
        text = str(longrepr[2])
    else:
        text = str(longrepr)

    lines = [line for line in text.strip().splitlines() if line.strip()]
    return lines[0].strip()[:_MAX_REASON_LENGTH] if lines else ""


def _classify_report(report: TestReport) -> Optional[str]:
    """Map one test phase to a GxP status, or None when the phase carries no verdict."""
    if report.when == "setup":
        if report.skipped:
            return "SKIPPED"
        return "ERROR" if report.failed else None

    if report.when == "call":
        if hasattr(report, "wasxfail"):
            if report.passed:
                return "XPASS"
            if report.skipped:
                return "XFAIL"
        if report.failed:
            return "FAILED"
        if report.skipped:
            return "SKIPPED"
        return "PASSED"

    # Teardown only matters when it breaks
    return "ERROR" if report.failed else None


def pytest_runtest_logreport(report: TestReport) -> None:
    """Record every test phase so skips, errors and xfails reach the validation record."""
    global _gxp_config

    # Use module-level config reference
    if _gxp_config is None:
        return

    config = _gxp_config

    if not hasattr(config, "_gxp_test_results"):
        return

    status = _classify_report(report)
    if status is None:
        return

    test_id = report.nodeid
    requirement_ids = config._gxp_test_requirement_map.get(test_id, [])

    # Keep the worst status seen across this test's phases
    existing = config._gxp_test_records.get(test_id)
    if existing is None or _STATUS_RANK[status] < _STATUS_RANK[existing["status"]]:
        reason = getattr(report, "wasxfail", None) or _reason_from_report(report)
        config._gxp_test_records[test_id] = {
            "status": status,
            "reason": reason[:_MAX_REASON_LENGTH],
            "requirement_ids": list(requirement_ids),
            "risk_tier": getattr(config, "_gxp_test_risk", {}).get(test_id, ""),
        }

    status = config._gxp_test_records[test_id]["status"]
    config._gxp_test_results[test_id] = status

    # Update traceability matrix using marker-based mapping
    if hasattr(config, "_gxp_traceability"):
        for req_id in requirement_ids:
            config._gxp_traceability.update_test_status_by_requirement(req_id, status)


@pytest.fixture
def gxp_evidence(request):
    """
    Fixture to capture objective evidence during tests.

    Use this fixture to attach evidence (screenshots, directory listings,
    command output, or images) to your GxP validation tests.

    Example:
        @pytest.mark.gxp
        @pytest.mark.requirements(["FS-001"])
        def test_login(gxp_evidence, driver):
            # Capture a screenshot
            gxp_evidence.capture_screenshot(driver.get_screenshot_as_png(), "Login screen")

            # Capture directory listing
            gxp_evidence.capture_directory_listing("/app/config", "Config files")

            # Capture command output
            gxp_evidence.capture_command_output(result.stdout, "API response")

            # Add existing image
            gxp_evidence.add_image("chart.png", "Results chart")

    Note: Pillow is required for text-to-image conversion.
    Install with: pip install pytest-gxp[evidence]
    """
    if not request.config.getoption("--gxp", default=False):
        # Return a no-op collector if GxP mode is not enabled
        class NoOpCollector:
            def capture_screenshot(self, *args, **kwargs):
                pass

            def capture_directory_listing(self, *args, **kwargs):
                pass

            def capture_command_output(self, *args, **kwargs):
                pass

            def add_image(self, *args, **kwargs):
                pass

            def record_unscripted_session(self, *args, **kwargs):
                pass

        yield NoOpCollector()
        return

    if not hasattr(request.config, "_gxp_evidence_collector"):
        raise RuntimeError("GxP evidence collector not initialized")

    collector = request.config._gxp_evidence_collector

    # Get requirement IDs from marker
    marker = request.node.get_closest_marker("requirements")
    requirement_ids = []
    if marker and marker.args:
        req_arg = marker.args[0]
        if isinstance(req_arg, (list, tuple)):
            requirement_ids = list(req_arg)
        elif isinstance(req_arg, str):
            requirement_ids = [req_arg]

    # Set current test context
    collector.set_current_test(request.node.nodeid, requirement_ids)

    yield collector

    # Clear test context
    collector.clear_current_test()


def pytest_sessionfinish(session, exitstatus) -> None:
    """Generate reports after test session finishes."""
    if not session.config.getoption("--gxp"):
        return

    if not hasattr(session.config, "_gxp_specs"):
        return

    config = session.config
    gxp_config = getattr(config, "_gxp_config", GxPConfig())

    # Get all data
    specs = config._gxp_specs
    test_results = config._gxp_test_results
    test_requirement_map = getattr(config, "_gxp_test_requirement_map", {})
    all_requirements = getattr(config, "_gxp_all_requirements", [])

    # Build requirement-based results mapping
    # Map each requirement to its test result based on markers
    requirement_tests: Dict[str, List[str]] = {}
    for nodeid, req_ids in test_requirement_map.items():
        for req_id in req_ids:
            requirement_tests.setdefault(req_id, []).append(nodeid)

    test_records = getattr(config, "_gxp_test_records", {})
    requirement_results: Dict[str, str] = {
        req_id: _rollup_requirement_status(
            [test_results.get(nodeid, "NOT_EXECUTED") for nodeid in nodeids]
        )
        for req_id, nodeids in requirement_tests.items()
    }

    # Every matrix row now names one real test and carries that test's own status
    config._gxp_traceability.attach_tests(requirement_tests, test_records)

    # Check requirement coverage
    all_req_ids = {req.id for req in all_requirements}
    covered_req_ids = set(requirement_tests.keys())
    uncovered_req_ids = all_req_ids - covered_req_ids

    # Print coverage warnings
    if uncovered_req_ids:
        warnings.warn(
            f"GxP: {len(uncovered_req_ids)} requirement(s) have no test coverage: "
            f"{', '.join(sorted(uncovered_req_ids))}",
            stacklevel=2,
        )
        findings = getattr(config, "_gxp_findings", [])
        findings.extend(
            ValidationFinding(
                code="uncovered-requirement",
                severity="warning",
                message=f"Requirement {req_id} has no test coverage",
            )
            for req_id in sorted(uncovered_req_ids)
        )

    # Fail if strict coverage is enabled and there are uncovered requirements
    if gxp_config.strict_coverage and uncovered_req_ids:
        session.exitstatus = 1
        print(
            f"\nGxP STRICT COVERAGE FAILURE: {len(uncovered_req_ids)} requirement(s) "
            f"have no test coverage:\n  - " + "\n  - ".join(sorted(uncovered_req_ids))
        )

    # Generate reports
    if hasattr(config, "_gxp_test_cases"):
        test_cases = config._gxp_test_cases
    else:
        test_cases = []

    # Map test results to test case IDs using marker-based approach
    mapped_results: Dict[str, str] = {}
    for test_case in test_cases:
        for req_id in test_case.requirements:
            if req_id in requirement_results:
                mapped_results[test_case.id] = requirement_results[req_id]
                break

    report_path = config._gxp_report_files / "csv_validation_report.json"
    markdown_report_path = config._gxp_report_files / "csv_validation_report.md"

    # Create validation metadata
    from .markdown_format import ApprovalSignature, QualificationType, ValidationMetadata

    qual_type_map = {
        "IQ": QualificationType.IQ,
        "OQ": QualificationType.OQ,
        "PQ": QualificationType.PQ,
    }
    qual_type = qual_type_map.get(gxp_config.qualification_type, QualificationType.OQ)

    today = utc_today()
    validation_metadata = ValidationMetadata(
        qualification_type=qual_type,
        software_name=gxp_config.project_name or "Application",
        software_version=gxp_config.software_version or "1.0.0",
        project_name=gxp_config.project_name or "GxP Validation Project",
        validation_date=today,
        tester=ApprovalSignature(
            name=gxp_config.tester_name or "",
            role="Tester",
            date=gxp_config.tester_date or today,
        )
        if gxp_config.tester_name
        else None,
        reviewer=ApprovalSignature(
            name=gxp_config.reviewer_name or "",
            role="Reviewer",
            date=gxp_config.reviewer_date or today,
        )
        if gxp_config.reviewer_name
        else None,
        approver=ApprovalSignature(
            name=gxp_config.approver_name or "",
            role="Approver",
            date=gxp_config.approver_date or today,
        )
        if gxp_config.approver_name
        else None,
    )

    # Parse output formats from the merged configuration
    output_formats = {fmt.strip().lower() for fmt in gxp_config.output_formats.split(",")}
    source_provenance = getattr(config, "_gxp_provenance", None)

    # Get evidence items from collector
    evidence_items: List[EvidenceItem] = []
    if hasattr(config, "_gxp_evidence_collector"):
        evidence_collector = config._gxp_evidence_collector
        evidence_items = evidence_collector.get_all_evidence()
        # Write evidence manifest (always JSON)
        if evidence_items:
            evidence_collector.write_manifest()

    # High-risk requirements need objective evidence, non-passing tests need a deviation
    findings: List[ValidationFinding] = getattr(config, "_gxp_findings", [])
    deviations = getattr(config, "_gxp_deviations", {})
    findings.extend(_check_risk_evidence(requirement_tests, test_records, evidence_items))
    findings.extend(_check_deviation_refs(test_records, deviations))

    if gxp_config.strict:
        error_findings = [f for f in findings if f.severity == "error"]
        if error_findings:
            session.exitstatus = 1
            print(
                f"\nGxP STRICT FAILURE: {len(error_findings)} error-severity "
                "validation finding(s):\n  - "
                + "\n  - ".join(
                    f"{f.code} [{f.location or '-'}] {f.message}"
                    for f in sorted(error_findings, key=lambda f: (f.code, f.location))
                )
            )

    # Generate the report data (always needed for any output format)
    config._gxp_report.generate_report(
        test_cases,
        design_spec=specs.get(SpecType.DESIGN),
        functional_spec=specs.get(SpecType.FUNCTIONAL),
        user_spec=specs.get(SpecType.USER),
        installation_spec=specs.get(SpecType.INSTALLATION),
        traceability_matrix=config._gxp_traceability,
        test_results=mapped_results,
        output_path=report_path if "json" in output_formats else None,
        validation_metadata=validation_metadata,
        all_requirements=all_requirements,
        requirement_tests=requirement_tests,
        source_provenance=source_provenance,
        findings=findings,
        test_records=test_records,
        deviations=deviations,
    )

    # Generate validation reports in requested formats
    if "json" in output_formats:
        config._gxp_report.write_report(report_path)

    if "md" in output_formats:
        config._gxp_report.write_markdown_report(
            markdown_report_path, evidence_items=evidence_items
        )

    if "csv" in output_formats:
        csv_report_path = config._gxp_report_files / "csv_validation_report.csv"
        config._gxp_report.write_csv_report(csv_report_path)

    if "pdf" in output_formats:
        pdf_report_path = config._gxp_report_files / "csv_validation_report.pdf"
        try:
            config._gxp_report.write_pdf_report(pdf_report_path, evidence_items=evidence_items)
        except (ImportError, OSError) as e:
            # WeasyPrint raises OSError when its native libraries are missing; a broken
            # PDF backend must not cost us the remaining artefacts or the manifest.
            warnings.warn(f"PDF generation skipped: {e}", stacklevel=2)

    # Generate traceability matrix in requested formats
    project_name = gxp_config.project_name or "GxP Validation Project"
    if "csv" in output_formats:
        traceability_csv_path = config._gxp_report_files / "traceability_matrix.csv"
        config._gxp_traceability.write_csv(traceability_csv_path)

    if "json" in output_formats:
        traceability_json_path = config._gxp_report_files / "traceability_matrix.json"
        config._gxp_traceability.write_json(
            traceability_json_path, project_name, source_provenance=source_provenance
        )

    if "md" in output_formats:
        traceability_md_path = config._gxp_report_files / "traceability_matrix.md"
        config._gxp_traceability.write_markdown(
            traceability_md_path, project_name, source_provenance=source_provenance
        )

    # Generate requirement coverage report (always markdown for now)
    if "md" in output_formats:
        coverage_report_path = config._gxp_report_files / "requirement_coverage.md"
        _write_coverage_report(
            coverage_report_path,
            all_requirements,
            requirement_tests,
            requirement_results,
            test_results,
        )

    # Hash every artefact produced above; must stay the last output step
    write_artifact_manifest(config._gxp_report_files)


def _check_risk_evidence(
    requirement_tests: Dict[str, List[str]],
    test_records: Dict[str, Dict[str, Any]],
    evidence_items: List[EvidenceItem],
) -> List[ValidationFinding]:
    """A high-risk requirement must be backed by at least one objective evidence item."""
    with_evidence = {req_id for item in evidence_items for req_id in item.requirement_ids}

    findings = []
    for req_id in sorted(requirement_tests):
        tiers = [
            test_records.get(nodeid, {}).get("risk_tier", "")
            for nodeid in requirement_tests[req_id]
        ]
        if rollup_risk(tiers) == "high" and req_id not in with_evidence:
            findings.append(
                ValidationFinding(
                    code="high-risk-no-evidence",
                    severity="error",
                    message=f"High-risk requirement {req_id} has no objective evidence",
                    location=req_id,
                )
            )
    return findings


def _check_deviation_refs(
    test_records: Dict[str, Dict[str, Any]], deviations: Dict[str, str]
) -> List[ValidationFinding]:
    """Every non-passing test must carry a deviation reference."""
    findings = []
    for node_id in sorted(test_records):
        record = test_records[node_id]
        if record.get("status") in PASSING_OUTCOMES:
            continue
        if resolve_deviation_ref(node_id, list(record.get("requirement_ids", [])), deviations):
            continue
        findings.append(
            ValidationFinding(
                code="missing-deviation-ref",
                severity="error",
                message=(
                    f"Test outcome {record.get('status', 'NOT_EXECUTED')} has no "
                    "deviation reference"
                ),
                location=node_id,
            )
        )
    return findings


def _rollup_requirement_status(statuses: List[str]) -> str:
    """Roll several test outcomes up to the status of the requirement they verify."""
    if any(status in ("FAILED", "ERROR") for status in statuses):
        return "FAILED"
    if any(status in ("PASSED", "XPASS") for status in statuses):
        return "PASSED"
    if "SKIPPED" in statuses:
        return "SKIPPED"
    if "XFAIL" in statuses:
        return "XFAIL"
    return "NOT_EXECUTED"


def pytest_terminal_summary(terminalreporter, exitstatus, config: Config) -> None:
    """Print GxP validation findings at the end of the run, errors first."""
    if not config.getoption("--gxp", default=False):
        return

    findings = getattr(config, "_gxp_findings", [])
    if not findings:
        return

    terminalreporter.write_sep("=", "GxP validation findings")
    ordered = sorted(
        findings,
        key=lambda f: (0 if f.severity == "error" else 1, f.code, f.location, f.message),
    )
    for finding in ordered:
        terminalreporter.write_line(
            f"{finding.severity.upper()} {finding.code} "
            f"[{finding.location or '-'}] {finding.message}"
        )


def _write_coverage_report(
    output_path: Path,
    all_requirements: List,
    requirement_tests: Dict[str, List[str]],
    requirement_results: Dict[str, str],
    test_results: Dict[str, str],
) -> None:
    """Write requirement coverage report to file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Calculate metrics
    total_reqs = len(all_requirements)
    reqs_with_tests = len(requirement_tests)
    reqs_without_tests = total_reqs - reqs_with_tests
    coverage_rate = (reqs_with_tests / total_reqs * 100) if total_reqs > 0 else 0

    reqs_verified = sum(1 for status in requirement_results.values() if status == "PASSED")
    verification_rate = (reqs_verified / reqs_with_tests * 100) if reqs_with_tests > 0 else 0

    lines = [
        "# Requirement Coverage Report",
        "",
        f"**Generated:** {utc_now_iso()}",
        "",
        "## Summary",
        "",
        f"- **Total Requirements:** {total_reqs}",
        f"- **Requirements with Tests:** {reqs_with_tests}",
        f"- **Requirements without Tests:** {reqs_without_tests}",
        f"- **Requirement Coverage Rate:** {coverage_rate:.1f}%",
        "",
        f"- **Requirements Verified (passing tests):** {reqs_verified}",
        f"- **Verification Rate:** {verification_rate:.1f}%",
        "",
    ]

    # List uncovered requirements
    covered_ids = set(requirement_tests.keys())
    uncovered = [req for req in all_requirements if req.id not in covered_ids]

    if uncovered:
        lines.extend(
            [
                "## Requirements Without Test Coverage",
                "",
                "| Requirement ID | Title | Specification Type |",
                "|----------------|-------|-------------------|",
            ]
        )
        for req in uncovered:
            lines.append(f"| {req.id} | {req.title} | {req.spec_type.value} |")
        lines.append("")

    # List all requirements with their test status
    lines.extend(
        [
            "## All Requirements",
            "",
            "| Requirement ID | Title | Tests | Status |",
            "|----------------|-------|-------|--------|",
        ]
    )

    for req in all_requirements:
        tests = requirement_tests.get(req.id, [])
        test_count = len(tests)
        status = requirement_results.get(req.id, "No Tests")
        lines.append(f"| {req.id} | {req.title} | {test_count} | {status} |")

    lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def pytest_unconfigure(config: Config) -> None:
    """Clean up GxP plugin state."""
    global _gxp_config
    _gxp_config = None
