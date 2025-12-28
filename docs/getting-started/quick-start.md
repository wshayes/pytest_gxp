# Quick Start

This guide will help you get started with Pytest GxP in minutes.

## Step 1: Create Specification Files

Create a directory for your GxP specifications:

```bash
mkdir gxp_spec_files
```

Create a functional specification file `gxp_spec_files/functional_specification.md`:

```markdown
# Functional Specification

## Version: 1.0

### FS-001: User Login

#### Description
The system shall allow users to log in using username and password.

1. Display login form
2. Validate credentials
3. Create session on success

Expected Result: User is authenticated and granted access.

#### Metadata
Priority: High
Category: Authentication
```

## Step 2: Write Tests with Markers

Create test files that link to your requirements using markers:

```python
# tests/test_login.py
import pytest

@pytest.mark.gxp
@pytest.mark.requirements(["FS-001"])
def test_user_login():
    """Test user login functionality."""
    # Your test implementation
    assert True
```

## Step 3: Run Tests

Run pytest with GxP mode:

```bash
pytest --gxp --gxp-spec-files=gxp_spec_files --gxp-report-files=gxp_report_files
```

## Step 4: Review Reports

After running tests, check the generated reports in `gxp_report_files/`:

### Traceability Matrix
- `traceability_matrix.csv` - CSV format
- `traceability_matrix.json` - JSON format
- `traceability_matrix.md` - Markdown format

### Validation Report
- `csv_validation_report.csv` - CSV format
- `csv_validation_report.json` - JSON format
- `csv_validation_report.md` - Markdown format
- `csv_validation_report.pdf` - PDF format (requires `pip install pytest-gxp[pdf]`)

### Coverage Report
- `requirement_coverage.md` - Coverage summary

## Adding Objective Evidence

Capture evidence during tests using the `gxp_evidence` fixture:

```python
@pytest.mark.gxp
@pytest.mark.requirements(["FS-001"])
def test_user_login(gxp_evidence):
    """Test user login with evidence capture."""
    # Capture command output
    import subprocess
    result = subprocess.run(["echo", "Login test"], capture_output=True, text=True)
    gxp_evidence.capture_command_output(result.stdout, "Login test output")

    assert True
```

Install evidence dependencies:

```bash
pip install pytest-gxp[evidence]
```

## Next Steps

- Learn about the [Specification Format](../user-guide/specification-format.md)
- See [Examples](../examples/overview.md) for complete examples
- Read the [Configuration Guide](configuration.md) for advanced setup
- Explore [Running Tests](../user-guide/running-tests.md) for evidence capture details
