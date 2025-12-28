"""Pytest plugin hooks for GxP validation."""

import warnings
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pytest
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from _pytest.reports import TestReport

from .config import GxPConfig, load_config_from_ini, load_config_from_pyproject, merge_config
from .evidence import EvidenceCollector
from .generator import TestCaseGenerator
from .markdown_format import EvidenceItem, SpecType
from .parser import SpecificationParser
from .report import CSVValidationReport
from .traceability import TraceabilityMatrix

# Module-level reference to config for use in hooks
_gxp_config: Optional[Config] = None


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

    # Evidence options
    group.addoption(
        "--gxp-evidence-thumbnails",
        action="store_true",
        default=True,
        help="Generate thumbnail images for evidence (default: True)",
    )
    group.addoption(
        "--no-gxp-evidence-thumbnails",
        action="store_false",
        dest="gxp_evidence_thumbnails",
        help="Disable thumbnail generation for evidence",
    )

    # Output format options
    group.addoption(
        "--gxp-output-formats",
        action="store",
        default="csv,json,md,pdf",
        help="Comma-separated list of output formats: csv,json,md,pdf (default: all)",
    )

    # Add ini options for configuration file support
    parser.addini("gxp_spec_files", "Path to GxP specification files directory")
    parser.addini("gxp_report_files", "Path to GxP report files directory")
    parser.addini("gxp_qualification_type", "Qualification type (IQ, OQ, PQ)")
    parser.addini("gxp_software_version", "Software version being validated")
    parser.addini("gxp_project_name", "Project name for validation reports")
    parser.addini("gxp_strict_coverage", "Fail if requirements lack coverage (true/false)")
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

    # Initialize GxP components
    config._gxp_parser = SpecificationParser()
    config._gxp_generator = TestCaseGenerator(config._gxp_parser)
    config._gxp_traceability = TraceabilityMatrix()
    config._gxp_report = CSVValidationReport()
    config._gxp_test_results: Dict[str, str] = {}
    config._gxp_test_requirement_map: Dict[str, List[str]] = {}

    # Initialize evidence collector
    generate_thumbnails = config.getoption("gxp_evidence_thumbnails", True)
    config._gxp_evidence_collector = EvidenceCollector(
        config._gxp_report_files,
        generate_thumbnails=generate_thumbnails,
    )


def pytest_collection_modifyitems(config: Config, items: List) -> None:
    """Modify collected test items for GxP validation."""
    if not config.getoption("--gxp"):
        return

    # Check if plugin was configured
    if not hasattr(config, "_gxp_parser"):
        return

    # Build test-to-requirement mapping from markers
    test_requirement_map: Dict[str, List[str]] = {}
    for item in items:
        marker = item.get_closest_marker("requirements")
        if marker and marker.args:
            requirement_ids = marker.args[0]
            if isinstance(requirement_ids, (list, tuple)):
                test_requirement_map[item.nodeid] = list(requirement_ids)
            elif isinstance(requirement_ids, str):
                test_requirement_map[item.nodeid] = [requirement_ids]
    config._gxp_test_requirement_map = test_requirement_map

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

    # Generate test cases from specifications
    design_spec = config._gxp_specs.get(SpecType.DESIGN)
    functional_spec = config._gxp_specs.get(SpecType.FUNCTIONAL)
    installation_spec = config._gxp_specs.get(SpecType.INSTALLATION)

    if design_spec or functional_spec or installation_spec:
        test_cases = config._gxp_generator.generate_test_cases(
            design_spec, functional_spec, installation_spec
        )
        config._gxp_test_cases = test_cases

        # Generate traceability matrix data (outputs written at session finish)
        user_spec = config._gxp_specs.get(SpecType.USER)
        config._gxp_traceability.generate_matrix(
            test_cases,
            design_spec,
            functional_spec,
            user_spec,
            installation_spec=installation_spec,
        )
    else:
        config._gxp_test_cases = []

    # Collect all requirements for coverage checking
    all_requirements = []
    for spec in config._gxp_specs.values():
        all_requirements.extend(spec.requirements)
    config._gxp_all_requirements = all_requirements


def pytest_runtest_setup(item) -> None:
    """Setup before running a test."""
    if not item.config.getoption("--gxp"):
        return

    # Mark test with GxP marker if not already marked
    if not item.get_closest_marker("gxp"):
        item.add_marker(pytest.mark.gxp())


def pytest_runtest_logreport(report: TestReport) -> None:
    """Log test report for GxP validation."""
    global _gxp_config

    # Use module-level config reference
    if _gxp_config is None:
        return

    config = _gxp_config

    if not hasattr(config, "_gxp_test_results"):
        return

    if report.when == "call":
        test_id = report.nodeid
        status = report.outcome.upper()

        # Store test result
        config._gxp_test_results[test_id] = status

        # Update traceability matrix using marker-based mapping
        has_traceability = hasattr(config, "_gxp_traceability")
        has_req_map = hasattr(config, "_gxp_test_requirement_map")
        if has_traceability and has_req_map:
            requirement_ids = config._gxp_test_requirement_map.get(test_id, [])
            for req_id in requirement_ids:
                # Update status for each requirement covered by this test
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
    requirement_results: Dict[str, str] = {}
    requirement_tests: Dict[str, List[str]] = {}

    for nodeid, req_ids in test_requirement_map.items():
        test_status = test_results.get(nodeid, "NOT_EXECUTED")
        for req_id in req_ids:
            if req_id not in requirement_tests:
                requirement_tests[req_id] = []
            requirement_tests[req_id].append(nodeid)

            # A requirement is considered PASSED only if all its tests pass
            # If any test fails, the requirement is FAILED
            current_status = requirement_results.get(req_id)
            if current_status is None:
                requirement_results[req_id] = test_status
            elif test_status == "FAILED":
                requirement_results[req_id] = "FAILED"
            elif test_status == "PASSED" and current_status != "FAILED":
                requirement_results[req_id] = "PASSED"

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

    today = datetime.now().strftime("%Y-%m-%d")
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
        ) if gxp_config.tester_name else None,
        reviewer=ApprovalSignature(
            name=gxp_config.reviewer_name or "",
            role="Reviewer",
            date=gxp_config.reviewer_date or today,
        ) if gxp_config.reviewer_name else None,
        approver=ApprovalSignature(
            name=gxp_config.approver_name or "",
            role="Approver",
            date=gxp_config.approver_date or today,
        ) if gxp_config.approver_name else None,
    )

    # Parse output formats
    output_formats_str = config.getoption("--gxp-output-formats", "csv,json,md,pdf")
    output_formats = {fmt.strip().lower() for fmt in output_formats_str.split(",")}

    # Get evidence items from collector
    evidence_items: List[EvidenceItem] = []
    if hasattr(config, "_gxp_evidence_collector"):
        evidence_collector = config._gxp_evidence_collector
        evidence_items = evidence_collector.get_all_evidence()
        # Write evidence manifest (always JSON)
        if evidence_items:
            evidence_collector.write_manifest()

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
        except ImportError as e:
            warnings.warn(f"PDF generation skipped: {e}", stacklevel=2)

    # Generate traceability matrix in requested formats
    project_name = gxp_config.project_name or "GxP Validation Project"
    if "csv" in output_formats:
        traceability_csv_path = config._gxp_report_files / "traceability_matrix.csv"
        config._gxp_traceability.write_csv(traceability_csv_path)

    if "json" in output_formats:
        traceability_json_path = config._gxp_report_files / "traceability_matrix.json"
        config._gxp_traceability.write_json(traceability_json_path, project_name)

    if "md" in output_formats:
        traceability_md_path = config._gxp_report_files / "traceability_matrix.md"
        config._gxp_traceability.write_markdown(traceability_md_path, project_name)

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
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
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
        lines.extend([
            "## Requirements Without Test Coverage",
            "",
            "| Requirement ID | Title | Specification Type |",
            "|----------------|-------|-------------------|",
        ])
        for req in uncovered:
            lines.append(f"| {req.id} | {req.title} | {req.spec_type.value} |")
        lines.append("")

    # List all requirements with their test status
    lines.extend([
        "## All Requirements",
        "",
        "| Requirement ID | Title | Tests | Status |",
        "|----------------|-------|-------|--------|",
    ])

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
