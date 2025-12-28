"""Example test file demonstrating GxP plugin usage."""

import subprocess
import sys
from pathlib import Path

import pytest


# ============================================================================
# OQ Tests - Operational Qualification (Functional Specification)
# ============================================================================


@pytest.mark.gxp
@pytest.mark.requirements(["FS-001"])
def test_user_login_functionality():
    """Test FS-001: User Login Functionality

    This test verifies that users can successfully log in to the system.

    Requirements: FS-001
    """
    # Step 1: Display a login form with username and password fields
    login_form_displayed = True  # Simulated

    # Step 2: Validate user credentials when login is submitted
    credentials_valid = True  # Simulated

    # Step 3: Create a secure session upon successful authentication
    session_created = True  # Simulated

    # Expected: User is successfully authenticated and granted access to the system
    assert login_form_displayed
    assert credentials_valid
    assert session_created


@pytest.mark.gxp
@pytest.mark.requirements(["FS-002"])
def test_input_data_validation():
    """Test FS-002: Input Data Validation

    This test verifies that all user input is properly validated.

    Requirements: FS-002
    """
    # Step 1: Validate email format for email fields
    valid_email = "test@example.com"
    assert "@" in valid_email

    # Step 2: Validate numeric ranges for numeric inputs
    age = 25
    assert 0 <= age <= 150

    # Expected: All invalid input is rejected with clear error messages
    assert True


# ============================================================================
# IQ Tests - Installation Qualification (Installation Specification)
# ============================================================================


@pytest.mark.gxp
@pytest.mark.requirements(["IS-001"])
def test_python_version_requirement(gxp_evidence):
    """Test IS-001: System Requirements Verification - Python Version

    Verifies that the installed Python version meets minimum requirements.

    Requirements: IS-001
    """
    # Check Python version is 3.8 or higher
    version_info = sys.version_info
    assert version_info.major >= 3, "Python 3.x required"
    assert version_info.minor >= 8, f"Python 3.8+ required, found 3.{version_info.minor}"

    # Capture Python version as objective evidence
    version_output = f"Python {version_info.major}.{version_info.minor}.{version_info.micro}"
    gxp_evidence.capture_command_output(version_output, "Python version verification")


@pytest.mark.gxp
@pytest.mark.requirements(["IS-001"])
def test_required_packages_installed(gxp_evidence):
    """Test IS-001: System Requirements Verification - Required Packages

    Verifies that required packages are installed.

    Requirements: IS-001
    """
    # Check that pytest is available
    import pytest as pt

    assert pt is not None

    # Check that the gxp plugin is available
    import pytest_gxp

    assert pytest_gxp is not None

    # Capture installed package versions as objective evidence
    packages_info = f"pytest version: {pt.__version__}\npytest-gxp version: {pytest_gxp.__version__}"
    gxp_evidence.capture_command_output(packages_info, "Required packages verification")


@pytest.mark.gxp
@pytest.mark.requirements(["IS-002"])
def test_plugin_entry_point():
    """Test IS-002: Application Installation - Plugin Entry Point

    Verifies that the plugin is properly registered.

    Requirements: IS-002
    """
    from importlib.metadata import entry_points

    # Get pytest11 entry points (pytest plugin entry points)
    eps = entry_points()
    if hasattr(eps, "select"):
        # Python 3.10+
        pytest_plugins = eps.select(group="pytest11")
    else:
        # Python 3.9
        pytest_plugins = eps.get("pytest11", [])

    plugin_names = [ep.name for ep in pytest_plugins]
    assert "gxp" in plugin_names, "gxp plugin not found in pytest11 entry points"


@pytest.mark.gxp
@pytest.mark.requirements(["IS-003"])
def test_plugin_imports(gxp_evidence):
    """Test IS-003: Configuration Verification - Module Imports

    Verifies that all plugin modules can be imported.

    Requirements: IS-003
    """
    # Test all major module imports
    from pytest_gxp import evidence, generator, parser, plugin, report, traceability

    assert parser is not None
    assert generator is not None
    assert traceability is not None
    assert report is not None
    assert plugin is not None
    assert evidence is not None

    # Capture directory listing of specification files as objective evidence
    spec_files_dir = Path(__file__).parent / "gxp_spec_files"
    if spec_files_dir.exists():
        gxp_evidence.capture_directory_listing(str(spec_files_dir), "Specification files directory")


@pytest.mark.gxp
@pytest.mark.requirements(["IS-003"])
def test_specification_parser_initialization(gxp_evidence):
    """Test IS-003: Configuration Verification - Parser Initialization

    Verifies that the specification parser can be initialized.

    Requirements: IS-003
    """
    from pytest_gxp.parser import SpecificationParser

    parser = SpecificationParser()
    assert parser is not None
    assert hasattr(parser, "parse_file")
    assert hasattr(parser, "parse_directory")

    # Capture directory listing of report files as objective evidence
    report_files_dir = Path(__file__).parent / "gxp_report_files"
    if report_files_dir.exists():
        gxp_evidence.capture_directory_listing(str(report_files_dir), "Report files directory")
