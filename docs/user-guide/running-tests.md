# Running Tests

## Basic Usage

Run pytest with GxP mode enabled:

```bash
pytest --gxp
```

## With Custom Paths

Specify custom paths for specifications and reports:

```bash
pytest --gxp \
  --gxp-spec-files=path/to/specs \
  --gxp-report-files=path/to/reports
```

## With Qualification Type and Approvals

```bash
pytest --gxp \
    --gxp-qualification-type=OQ \
    --gxp-software-version=1.0.0 \
    --gxp-project-name="My Application" \
    --gxp-tester="John Doe" \
    --gxp-reviewer="Jane Smith" \
    --gxp-approver="Bob Johnson"
```

## Test Markers

The plugin provides markers for organizing GxP tests:

### `@pytest.mark.gxp`

Mark a test as a GxP validation test:

```python
@pytest.mark.gxp
def test_user_login():
    """Test user login functionality."""
    pass
```

### `@pytest.mark.requirements`

Associate a test with requirement IDs:

```python
@pytest.mark.gxp
@pytest.mark.requirements(["FS-001", "DS-001"])
def test_user_login():
    """Test user login functionality."""
    pass
```

## Capturing Objective Evidence

Use the `gxp_evidence` fixture to capture objective evidence during tests. Evidence is included in validation reports and provides documented proof of test execution.

### Installation

For evidence capture with text-to-image conversion:

```bash
pip install pytest-gxp[evidence]
```

### Using the Evidence Fixture

```python
import pytest

@pytest.mark.gxp
@pytest.mark.requirements(["FS-001"])
def test_application_login(gxp_evidence, driver):
    """Test login with evidence capture."""

    # Capture a screenshot (from Selenium, Playwright, etc.)
    gxp_evidence.capture_screenshot(
        driver.get_screenshot_as_png(),
        "Login screen displayed"
    )

    # Perform login
    driver.find_element("id", "username").send_keys("user")
    driver.find_element("id", "password").send_keys("pass")
    driver.find_element("id", "submit").click()

    # Capture another screenshot
    gxp_evidence.capture_screenshot(
        driver.get_screenshot_as_png(),
        "Login successful - dashboard displayed"
    )
```

### Evidence Methods

| Method | Description |
|--------|-------------|
| `capture_screenshot(data, description)` | Capture screenshot (bytes, path, or base64) |
| `capture_directory_listing(path, description)` | Convert directory listing to image |
| `capture_command_output(text, description)` | Convert text output to image |
| `add_image(path, description)` | Add existing image file |

### More Evidence Examples

```python
import subprocess

@pytest.mark.gxp
@pytest.mark.requirements(["FS-002"])
def test_config_files(gxp_evidence):
    """Test configuration file presence."""

    # Capture directory listing
    gxp_evidence.capture_directory_listing(
        "/app/config",
        "Configuration files present"
    )

    # Capture command output
    result = subprocess.run(["app", "--version"], capture_output=True, text=True)
    gxp_evidence.capture_command_output(
        result.stdout,
        "Application version",
        command="app --version"
    )

    # Add existing image
    gxp_evidence.add_image(
        "results/chart.png",
        "Test results chart"
    )
```

## Test Discovery

The plugin will:

1. Parse specification files from the specified directory
2. Generate test cases from requirements
3. Create traceability matrices
4. Track test execution results
5. Capture objective evidence
6. Generate validation reports

## Viewing Results

After running tests, check the generated reports in your report directory:

### Traceability Matrix
- `traceability_matrix.csv` - CSV format
- `traceability_matrix.json` - JSON format
- `traceability_matrix.md` - Markdown format

### Validation Report
- `csv_validation_report.csv` - CSV format
- `csv_validation_report.json` - JSON format
- `csv_validation_report.md` - Markdown format
- `csv_validation_report.pdf` - PDF format (requires `pip install pytest-gxp[pdf]`)

### Requirement Coverage
- `requirement_coverage.md` - Coverage summary

### Evidence
- `evidence/` - Evidence image files
- `evidence/thumbnails/` - Thumbnail images
- `evidence_manifest.json` - Evidence metadata

## Strict Coverage Mode

Fail the test run if any requirements lack test coverage:

```bash
pytest --gxp --gxp-strict-coverage
```

## Selecting Output Formats

By default, all formats (CSV, JSON, Markdown, PDF) are generated. Select specific formats:

```bash
# Generate only Markdown and PDF
pytest --gxp --gxp-output-formats=md,pdf

# Generate only CSV
pytest --gxp --gxp-output-formats=csv
```
