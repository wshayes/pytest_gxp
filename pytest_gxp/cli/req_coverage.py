"""Check requirement coverage and test identifier uniqueness.

This script analyzes test files and specifications to report on
requirement coverage and identify any issues with test organization.
"""

import ast
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import click

from pytest_gxp.markdown_format import Requirement, SpecType
from pytest_gxp.parser import SpecificationParser


@dataclass
class TestInfo:
    """Information about a test function."""

    file_path: str
    function_name: str
    line_number: int
    requirement_ids: List[str] = field(default_factory=list)
    is_stub: bool = False
    has_gxp_marker: bool = False


@dataclass
class CoverageResult:
    """Results of coverage analysis."""

    total_requirements: int = 0
    covered_requirements: int = 0
    uncovered_requirements: List[Requirement] = field(default_factory=list)
    stub_only_requirements: List[Tuple[Requirement, List[TestInfo]]] = field(
        default_factory=list
    )
    duplicate_test_ids: Dict[str, List[TestInfo]] = field(default_factory=dict)
    tests_without_gxp_marker: List[TestInfo] = field(default_factory=list)
    orphan_tests: List[TestInfo] = field(default_factory=list)


def is_test_stub(node: ast.FunctionDef) -> bool:
    """Check if a test function is a stub (not implemented)."""
    for child in ast.walk(node):
        # Check for NotImplementedError
        if isinstance(child, ast.Raise):
            if isinstance(child.exc, ast.Call):
                if isinstance(child.exc.func, ast.Name):
                    if child.exc.func.id == "NotImplementedError":
                        return True
        # Check for pytest.skip
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Attribute):
                if child.func.attr == "skip":
                    return True
        # Check for pass statement only
        if isinstance(child, ast.Pass):
            # Check if it's the only statement in the body (excluding docstring)
            body = [
                s for s in node.body
                if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))
            ]
            if len(body) == 1 and isinstance(body[0], ast.Pass):
                return True
    return False


def has_marker(decorators: List[ast.expr], marker_name: str) -> bool:
    """Check if a function has a specific pytest marker."""
    for dec in decorators:
        if isinstance(dec, ast.Call):
            if isinstance(dec.func, ast.Attribute):
                if dec.func.attr == marker_name:
                    return True
            elif isinstance(dec.func, ast.Name):
                if dec.func.id == marker_name:
                    return True
        elif isinstance(dec, ast.Attribute):
            if dec.attr == marker_name:
                return True
    return False


def extract_requirement_ids(decorators: List[ast.expr]) -> List[str]:
    """Extract requirement IDs from @pytest.mark.requirements decorator."""
    for dec in decorators:
        if isinstance(dec, ast.Call):
            if isinstance(dec.func, ast.Attribute):
                if dec.func.attr == "requirements":
                    if dec.args:
                        arg = dec.args[0]
                        if isinstance(arg, ast.List):
                            ids = []
                            for elt in arg.elts:
                                if isinstance(elt, ast.Constant):
                                    ids.append(elt.value)
                            return ids
    return []


def analyze_test_file(file_path: Path) -> List[TestInfo]:
    """Analyze a test file and extract test information."""
    tests: List[TestInfo] = []

    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content)
    except Exception as e:
        click.echo(f"Warning: Could not parse {file_path}: {e}", err=True)
        return tests

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.name.startswith("test_"):
                test_info = TestInfo(
                    file_path=str(file_path),
                    function_name=node.name,
                    line_number=node.lineno,
                    requirement_ids=extract_requirement_ids(node.decorator_list),
                    is_stub=is_test_stub(node),
                    has_gxp_marker=has_marker(node.decorator_list, "gxp"),
                )
                tests.append(test_info)

    return tests


def analyze_coverage(
    specs: Dict[SpecType, "Specification"],
    tests: List[TestInfo],
    all_requirement_ids: Set[str],
) -> CoverageResult:
    """Analyze requirement coverage."""
    result = CoverageResult()

    # Build mapping of requirement ID to tests
    req_to_tests: Dict[str, List[TestInfo]] = defaultdict(list)
    for test in tests:
        for req_id in test.requirement_ids:
            req_to_tests[req_id].append(test)

    # Check for duplicate test function names
    test_names: Dict[str, List[TestInfo]] = defaultdict(list)
    for test in tests:
        test_names[test.function_name].append(test)

    for name, test_list in test_names.items():
        if len(test_list) > 1:
            result.duplicate_test_ids[name] = test_list

    # Check for tests without gxp marker that have requirements
    for test in tests:
        if test.requirement_ids and not test.has_gxp_marker:
            result.tests_without_gxp_marker.append(test)

    # Check for orphan tests (have requirements that don't exist in specs)
    for test in tests:
        for req_id in test.requirement_ids:
            if req_id not in all_requirement_ids:
                result.orphan_tests.append(test)
                break

    # Analyze each requirement
    all_requirements: List[Requirement] = []
    for spec in specs.values():
        all_requirements.extend(spec.requirements)

    result.total_requirements = len(all_requirements)

    for req in all_requirements:
        tests_for_req = req_to_tests.get(req.id, [])

        if not tests_for_req:
            result.uncovered_requirements.append(req)
        else:
            # Check if all tests are stubs
            all_stubs = all(t.is_stub for t in tests_for_req)
            if all_stubs:
                result.stub_only_requirements.append((req, tests_for_req))
            else:
                result.covered_requirements += 1

    return result


def print_summary(result: CoverageResult, verbose: bool = False) -> None:
    """Print coverage summary."""
    click.echo()
    click.echo("=" * 60)
    click.echo("GxP Requirement Coverage Report")
    click.echo("=" * 60)

    # Coverage statistics
    covered = result.covered_requirements
    stub_only = len(result.stub_only_requirements)
    uncovered = len(result.uncovered_requirements)
    total = result.total_requirements

    coverage_pct = (covered / total * 100) if total > 0 else 0
    stub_pct = (stub_only / total * 100) if total > 0 else 0

    click.echo()
    click.echo("Coverage Summary:")
    click.echo(f"  Total Requirements:     {total}")
    click.echo(f"  Fully Covered:          {covered} ({coverage_pct:.1f}%)")
    click.echo(f"  Stub Only:              {stub_only} ({stub_pct:.1f}%)")
    click.echo(f"  No Tests:               {uncovered}")

    # Issues
    issues_found = False

    if result.duplicate_test_ids:
        issues_found = True
        click.echo()
        click.echo(click.style("Duplicate Test Names:", fg="red", bold=True))
        for name, tests in result.duplicate_test_ids.items():
            click.echo(f"  {name}:")
            for test in tests:
                click.echo(f"    - {test.file_path}:{test.line_number}")

    if result.tests_without_gxp_marker:
        issues_found = True
        click.echo()
        click.echo(click.style("Tests Missing @pytest.mark.gxp:", fg="yellow", bold=True))
        for test in result.tests_without_gxp_marker:
            click.echo(f"  - {test.file_path}:{test.line_number} {test.function_name}")

    if result.orphan_tests:
        issues_found = True
        click.echo()
        click.echo(click.style("Tests with Invalid Requirement IDs:", fg="yellow", bold=True))
        for test in result.orphan_tests:
            invalid_ids = [rid for rid in test.requirement_ids if rid not in all_requirement_ids]
            click.echo(
                f"  - {test.file_path}:{test.line_number} {test.function_name} "
                f"(invalid: {', '.join(test.requirement_ids)})"
            )

    # Uncovered requirements
    if result.uncovered_requirements:
        click.echo()
        click.echo(click.style("Requirements Without Tests:", fg="red", bold=True))
        for req in result.uncovered_requirements:
            click.echo(f"  - {req.id}: {req.title}")

    # Stub-only requirements
    if result.stub_only_requirements:
        click.echo()
        click.echo(click.style("Requirements With Only Stub Tests:", fg="yellow", bold=True))
        for req, tests in result.stub_only_requirements:
            test_locs = ", ".join(f"{t.file_path}:{t.line_number}" for t in tests)
            click.echo(f"  - {req.id}: {req.title}")
            if verbose:
                click.echo(f"      Stubs: {test_locs}")

    click.echo()
    if not issues_found and not result.uncovered_requirements and not result.stub_only_requirements:
        click.echo(click.style("All requirements have working tests!", fg="green", bold=True))
    else:
        click.echo(
            f"Found {len(result.duplicate_test_ids)} duplicate test name(s), "
            f"{len(result.uncovered_requirements)} uncovered requirement(s), "
            f"{len(result.stub_only_requirements)} stub-only requirement(s)"
        )


# Global variable to store all requirement IDs for orphan check
all_requirement_ids: Set[str] = set()


@click.command()
@click.option(
    '--spec-dir', '-s',
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default='gxp_spec_files',
    help='Directory containing specification files (default: gxp_spec_files)',
)
@click.option(
    '--test-dir', '-t',
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default='tests',
    help='Directory containing test files (default: tests)',
)
@click.option(
    '--output', '-o',
    type=click.Path(path_type=Path),
    default=None,
    help='Write report to file (markdown format)',
)
@click.option(
    '--strict', '-S',
    is_flag=True,
    default=False,
    help='Exit with error code if any issues found',
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    default=False,
    help='Enable verbose output',
)
@click.option(
    '--json',
    'json_output',
    is_flag=True,
    default=False,
    help='Output results as JSON',
)
def main(
    spec_dir: Path,
    test_dir: Path,
    output: Optional[Path],
    strict: bool,
    verbose: bool,
    json_output: bool,
):
    """Check GxP requirement coverage and test identifier uniqueness.

    This tool analyzes your test files and specification files to:

    \b
    1. Verify all test function names are unique
    2. Check that tests have @pytest.mark.gxp marker
    3. Identify requirements without any tests
    4. Identify requirements with only stub tests (NotImplementedError)
    5. Find tests referencing non-existent requirements

    Examples:

    \b
        # Basic coverage check
        gxp_req_coverage

    \b
        # Check with custom directories
        gxp_req_coverage -s docs/specs -t tests/gxp

    \b
        # Strict mode (exit code 1 if issues found)
        gxp_req_coverage --strict

    \b
        # Generate markdown report
        gxp_req_coverage -o coverage_report.md
    """
    global all_requirement_ids

    # Check directories exist
    if not spec_dir.exists():
        click.echo(f"Error: Specification directory not found: {spec_dir}", err=True)
        sys.exit(1)

    if not test_dir.exists():
        click.echo(f"Error: Test directory not found: {test_dir}", err=True)
        sys.exit(1)

    # Parse specifications
    parser = SpecificationParser()
    specs = parser.parse_directory(spec_dir)

    if not specs:
        click.echo(f"No specification files found in {spec_dir}", err=True)
        sys.exit(1)

    # Build set of all requirement IDs
    all_requirement_ids = set()
    for spec in specs.values():
        for req in spec.requirements:
            all_requirement_ids.add(req.id)

    if verbose:
        click.echo(f"Found {len(specs)} specification file(s)")
        click.echo(f"Found {len(all_requirement_ids)} requirement(s)")

    # Analyze test files
    all_tests: List[TestInfo] = []
    test_files = list(test_dir.glob("**/test_*.py"))

    if verbose:
        click.echo(f"Found {len(test_files)} test file(s)")

    for test_file in test_files:
        tests = analyze_test_file(test_file)
        all_tests.extend(tests)

    if verbose:
        click.echo(f"Found {len(all_tests)} test function(s)")

    # Analyze coverage
    result = analyze_coverage(specs, all_tests, all_requirement_ids)

    # Output results
    if json_output:
        import json
        output_data = {
            "total_requirements": result.total_requirements,
            "covered_requirements": result.covered_requirements,
            "uncovered_requirements": [
                {"id": r.id, "title": r.title} for r in result.uncovered_requirements
            ],
            "stub_only_requirements": [
                {"id": r.id, "title": r.title} for r, _ in result.stub_only_requirements
            ],
            "duplicate_test_ids": {
                name: [{"file": t.file_path, "line": t.line_number} for t in tests]
                for name, tests in result.duplicate_test_ids.items()
            },
            "tests_without_gxp_marker": [
                {"file": t.file_path, "line": t.line_number, "name": t.function_name}
                for t in result.tests_without_gxp_marker
            ],
        }
        click.echo(json.dumps(output_data, indent=2))
    else:
        print_summary(result, verbose)

    # Write to file if requested
    if output:
        write_markdown_report(output, result, specs)
        click.echo(f"Report written to: {output}")

    # Exit with error if strict mode and issues found
    if strict:
        has_issues = (
            result.duplicate_test_ids
            or result.uncovered_requirements
            or result.stub_only_requirements
            or result.tests_without_gxp_marker
        )
        if has_issues:
            sys.exit(1)


def write_markdown_report(
    output_path: Path,
    result: CoverageResult,
    specs: Dict[SpecType, "Specification"],
) -> None:
    """Write coverage report in markdown format."""
    from datetime import datetime

    lines = [
        "# GxP Requirement Coverage Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        "",
        f"- **Total Requirements:** {result.total_requirements}",
        f"- **Fully Covered:** {result.covered_requirements}",
        f"- **Stub Only:** {len(result.stub_only_requirements)}",
        f"- **No Tests:** {len(result.uncovered_requirements)}",
        "",
    ]

    coverage_pct = (
        result.covered_requirements / result.total_requirements * 100
        if result.total_requirements > 0
        else 0
    )
    lines.append(f"**Coverage Rate:** {coverage_pct:.1f}%")
    lines.append("")

    if result.duplicate_test_ids:
        lines.extend([
            "## Duplicate Test Names",
            "",
            "| Test Name | Locations |",
            "|-----------|-----------|",
        ])
        for name, tests in result.duplicate_test_ids.items():
            locs = ", ".join(f"{t.file_path}:{t.line_number}" for t in tests)
            lines.append(f"| {name} | {locs} |")
        lines.append("")

    if result.uncovered_requirements:
        lines.extend([
            "## Requirements Without Tests",
            "",
            "| Requirement ID | Title | Specification |",
            "|----------------|-------|---------------|",
        ])
        for req in result.uncovered_requirements:
            lines.append(f"| {req.id} | {req.title} | {req.spec_type.value} |")
        lines.append("")

    if result.stub_only_requirements:
        lines.extend([
            "## Requirements With Only Stub Tests",
            "",
            "| Requirement ID | Title | Stub Location |",
            "|----------------|-------|---------------|",
        ])
        for req, tests in result.stub_only_requirements:
            locs = ", ".join(f"{t.file_path}:{t.line_number}" for t in tests)
            lines.append(f"| {req.id} | {req.title} | {locs} |")
        lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == '__main__':
    main()
