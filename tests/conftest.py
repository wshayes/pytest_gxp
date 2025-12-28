"""Pytest configuration and fixtures."""

import tempfile
from pathlib import Path

import pytest

from pytest_gxp.markdown_format import Requirement, Specification, SpecType


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_design_spec_content():
    """Sample design specification markdown content."""
    return """# Design Specification

## Version: 1.0

### DS-001: User Authentication

#### Description
The system shall provide secure user authentication.

1. Validate credentials
2. Create secure session
3. Log authentication attempts

#### Metadata
Priority: High
Category: Security
"""


@pytest.fixture
def sample_functional_spec_content():
    """Sample functional specification markdown content."""
    return """# Functional Specification

## Version: 1.0

### FS-001: User Login

#### Description
The application shall allow users to log in.

1. Display login form
2. Validate credentials
3. Create session

Expected Result: User is authenticated successfully.

#### Metadata
Priority: High
Category: Authentication
"""


@pytest.fixture
def sample_user_spec_content():
    """Sample user specification markdown content."""
    return """# User Specification

## Version: 1.0

### US-001: Secure Access

#### Description
As a user, I need to securely access the system.

1. Log in with credentials
2. Receive feedback on failures

Expected Result: Users can securely access the system.

#### Metadata
Priority: High
Category: Security
"""


@pytest.fixture
def sample_design_spec_file(temp_dir, sample_design_spec_content):
    """Create a temporary design specification file."""
    file_path = temp_dir / "design_specification.md"
    file_path.write_text(sample_design_spec_content)
    return file_path


@pytest.fixture
def sample_functional_spec_file(temp_dir, sample_functional_spec_content):
    """Create a temporary functional specification file."""
    file_path = temp_dir / "functional_specification.md"
    file_path.write_text(sample_functional_spec_content)
    return file_path


@pytest.fixture
def sample_user_spec_file(temp_dir, sample_user_spec_content):
    """Create a temporary user specification file."""
    file_path = temp_dir / "user_specification.md"
    file_path.write_text(sample_user_spec_content)
    return file_path


@pytest.fixture
def sample_requirement():
    """Create a sample requirement object."""
    return Requirement(
        id="FS-001",
        title="User Login",
        description="The application shall allow users to log in.\n\n1. Display login form\n2. Validate credentials",
        spec_type=SpecType.FUNCTIONAL,
        metadata={"Priority": "High", "Category": "Authentication"},
    )


@pytest.fixture
def sample_specification(sample_requirement):
    """Create a sample specification object."""
    return Specification(
        spec_type=SpecType.FUNCTIONAL,
        title="Functional Specification",
        version="1.0",
        requirements=[sample_requirement],
    )


@pytest.fixture
def sample_test_case():
    """Create a sample test case object."""
    from pytest_gxp.markdown_format import TestCase

    return TestCase(
        id="TEST-FS-001",
        title="Test FS-001: User Login",
        description="The application shall allow users to log in.",
        requirements=["FS-001"],
        steps=["Display login form", "Validate credentials"],
        expected_result="User is authenticated successfully.",
        metadata={"spec_type": "Functional", "requirement_id": "FS-001"},
    )

