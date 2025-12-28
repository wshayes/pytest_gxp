# Pytest GxP Plugin

Pytest plugin for GAMP5 GxP Computer System Validation (CSV) of custom applications. Provides requirement traceability, test coverage reporting, and validation reports for IQ/OQ/PQ qualification phases.

## Features

- Parse Markdown-based Installation, Design, Functional, and User Specifications
- Link pytest tests to requirements using markers
- Generate traceability matrices (CSV, JSON, and Markdown)
- Generate qualification reports (IQ/OQ/PQ) with approval signatures
- Capture objective evidence (screenshots, directory listings, command output)
- Requirement coverage checking with strict mode option
- Configuration via CLI, pyproject.toml, or pytest.ini

## Technical Stack

- Python 3.8+
- pytest 7.0+

## Installation

```bash
pip install pytest-gxp
```

```bash
uv add pytest-gxp
```

### Development Installation

For development, install with dev dependencies:

**Using pip:**
```bash
pip install -e ".[dev]"
```

**Using uv:**
```bash
uv sync --dev
```

This installs all development dependencies including:
- pytest and pytest-cov for testing
- ruff for linting and formatting
- pre-commit for git hooks
- mkdocs and mkdocs-material for documentation
- build and twine for packaging

### Pre-commit Hooks

This project uses pre-commit to ensure code quality. After installing dev dependencies, set up pre-commit hooks:

```bash
pre-commit install
```

The pre-commit hooks will:
- Format code using ruff
- Run linting checks with ruff
- Sort imports automatically

To manually run pre-commit on all files:

```bash
pre-commit run --all-files
```

### Documentation

This project includes documentation built with Material for MkDocs. The documentation is automatically deployed to GitHub Pages when changes are pushed to the main branch.

**Live Documentation**: [https://wshayes.github.io/pytest_gxp](https://wshayes.github.io/pytest_gxp)

#### Local Development

To build and serve the documentation locally:

```bash
mkdocs serve
```

Or using just:

```bash
just docs-serve
```

Visit `http://127.0.0.1:8000` to view the documentation.

To build static documentation:

```bash
mkdocs build
```

#### Deployment

Documentation is automatically deployed to GitHub Pages via GitHub Actions when:
- Changes are pushed to the `main` branch
- Files in `docs/`, `mkdocs.yml`, or the workflow file are modified

You can also manually trigger deployment from the GitHub Actions tab.

**Note**: On first setup, you need to enable GitHub Pages in your repository settings:
1. Go to Settings → Pages
2. Under "Source", select "GitHub Actions"
3. Save the settings

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed deployment instructions.

The documentation is located in the `docs/` directory and is **excluded from PyPI packages** - it's only included in the repository for hosting on GitHub Pages.

### Justfile Commands

This project uses [just](https://github.com/casey/just) for task management. Common commands:

```bash
just install          # Install in development mode
just test             # Run tests
just quality          # Format and lint code
just build            # Build the package
just publish          # Publish to PyPI
just docs-serve       # Serve documentation
```

Run `just` or `just --list` to see all available commands.

## Usage

### Basic Usage

Run pytest with GxP mode enabled:

```bash
pytest --gxp
```

### With Qualification Type and Approvals

```bash
pytest --gxp \
    --gxp-qualification-type=OQ \
    --gxp-software-version=1.0.0 \
    --gxp-project-name="My Application" \
    --gxp-tester="John Doe" \
    --gxp-reviewer="Jane Smith" \
    --gxp-approver="Bob Johnson"
```

### Custom Paths

Specify custom paths for specification files and report output:

```bash
pytest --gxp --gxp-spec-files=path/to/specs/ --gxp-report-files=path/to/reports/
```

### Strict Coverage Mode

Fail the test run if any requirements lack test coverage:

```bash
pytest --gxp --gxp-strict-coverage
```

### Example

See the `examples/` directory for a complete working example with sample specifications.

```bash
cd examples
pytest --gxp --gxp-spec-files=gxp_spec_files --gxp-report-files=gxp_report_files
```

## Configuration

### Command Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--gxp` | False | Enable GxP CSV validation mode |
| `--gxp-spec-files` | `gxp_spec_files` | Path to specification files directory |
| `--gxp-report-files` | `gxp_report_files` | Path to report output directory |
| `--gxp-qualification-type` | `OQ` | Qualification type: IQ, OQ, or PQ |
| `--gxp-software-version` | | Software version being validated |
| `--gxp-project-name` | | Project name for reports |
| `--gxp-tester` | | Tester name for approval signature |
| `--gxp-reviewer` | | Reviewer name for approval signature |
| `--gxp-approver` | | Approver name for approval signature |
| `--gxp-strict-coverage` | False | Fail if requirements lack test coverage |
| `--gxp-output-formats` | `csv,json,md,pdf` | Comma-separated output formats |
| `--gxp-evidence-thumbnails` | True | Generate thumbnail images for evidence |

### Configuration File (pyproject.toml)

```toml
[tool.pytest-gxp]
spec-files = "gxp_spec_files"
report-files = "gxp_report_files"
qualification-type = "OQ"
software-version = "1.0.0"
project-name = "My Application"
strict-coverage = false
tester-name = "John Doe"
reviewer-name = "Jane Smith"
approver-name = "Bob Johnson"
output-formats = "csv,json,md,pdf"
```

### Configuration File (pytest.ini)

```ini
[pytest]
gxp_spec_files = gxp_spec_files
gxp_report_files = gxp_report_files
gxp_qualification_type = OQ
gxp_software_version = 1.0.0
gxp_project_name = My Application
```

Configuration priority (highest to lowest):
1. CLI options
2. pyproject.toml `[tool.pytest-gxp]`
3. pytest.ini options
4. Default values

### Specification File Format

The plugin expects Markdown specification files with the following format:

```markdown
# Specification Title

## Version: 1.0

### FS-001: Requirement Title

#### Description
Detailed description of the requirement.

1. First requirement detail
2. Second requirement detail
...

Expected Result: What should happen when this requirement is met.

#### Metadata
Priority: High
Category: Category Name
Owner: Owner Name
```

### Specification File Naming

- Installation specifications: Files containing "installation" in the filename (e.g., `installation_specification.md`)
- Design specifications: Files containing "design" in the filename (e.g., `design_specification.md`)
- Functional specifications: Files containing "functional" in the filename (e.g., `functional_specification.md`)
- User specifications: Files containing "user" in the filename (e.g., `user_specification.md`)

### Requirement ID Format

| Specification Type | ID Format | Qualification Phase |
|-------------------|-----------|---------------------|
| Installation | `IS-XXX` (e.g., `IS-001`) | IQ |
| Design | `DS-XXX` (e.g., `DS-001`) | OQ |
| Functional | `FS-XXX` (e.g., `FS-001`) | OQ |
| User | `US-XXX` (e.g., `US-001`) | PQ |

## Generated Outputs

When running with `--gxp`, the plugin generates reports in all requested formats (CSV, JSON, Markdown, PDF by default):

### Traceability Matrix
Links test cases to requirements with auto-generated Test IDs (`TEST-FS-001`).
- `traceability_matrix.csv`
- `traceability_matrix.json`
- `traceability_matrix.md`

### Qualification Report
Validation summary with approval signatures, test results, and evidence.
- `csv_validation_report.csv`
- `csv_validation_report.json`
- `csv_validation_report.md`
- `csv_validation_report.pdf` (requires `pip install pytest-gxp[pdf]`)

### Requirement Coverage Report
Details which requirements have tests and their verification status.
- `requirement_coverage.md`

### Evidence (when captured)
Objective evidence with auto-generated IDs (`EV-0001`).
- `evidence/` - Evidence image files
- `evidence/thumbnails/` - Thumbnail images
- `evidence_manifest.json` - Evidence metadata

## Test Markers

The plugin provides pytest markers for GxP tests:

- `@pytest.mark.gxp`: Mark a test as a GxP validation test
- `@pytest.mark.requirements(["FS-001", "FS-002"])`: Associate test with requirement IDs

Example:

```python
import pytest

@pytest.mark.gxp
@pytest.mark.requirements(["FS-001"])
def test_user_login():
    """Test user login functionality."""
    # Test implementation
    pass

@pytest.mark.gxp
@pytest.mark.requirements(["FS-001", "FS-002"])
def test_login_with_validation():
    """Test login with input validation."""
    # This test covers multiple requirements
    pass
```

## Objective Evidence

The plugin supports capturing objective evidence during tests for GxP validation reports. Evidence types include screenshots, directory listings, command output, and arbitrary images.

### Installation

For evidence capture with text-to-image conversion:

```bash
pip install pytest-gxp[evidence]
```

Or install all optional dependencies:

```bash
pip install pytest-gxp[all]
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

    # Add existing image file
    gxp_evidence.add_image(
        "results/chart.png",
        "Test results chart"
    )
```

### Evidence Methods

| Method | Description |
|--------|-------------|
| `capture_screenshot(data, description)` | Capture screenshot (bytes, path, or base64) |
| `capture_directory_listing(path, description)` | Convert directory listing to image |
| `capture_command_output(text, description)` | Convert text output to image |
| `add_image(path, description)` | Add existing image file |

### Utility Functions

```python
from pytest_gxp.evidence import text_to_image, directory_listing_to_image

# Convert text to image
text_to_image("Hello World\nLine 2", "output.png")

# Convert directory to image
directory_listing_to_image("/app/logs", "logs.png")
```

## Metrics Terminology

The plugin reports two distinct types of metrics:

### Test Execution Metrics
- **Test Pass Rate**: Percentage of executed tests that passed (passed / (passed + failed))
- **Test Execution Rate**: Percentage of total tests that were executed

### Requirement Coverage Metrics
- **Requirement Coverage Rate**: Percentage of requirements that have at least one test
- **Requirement Verification Rate**: Percentage of covered requirements verified by passing tests

## Qualification Types (GAMP5)

| Phase | Description | Specifications Used |
|-------|-------------|---------------------|
| **IQ** | Installation Qualification - Verifies software is correctly installed | Installation Spec (IS) |
| **OQ** | Operational Qualification - Verifies software operates according to specifications | Design Spec (DS), Functional Spec (FS) |
| **PQ** | Performance Qualification - Verifies software meets user requirements | User Spec (US) |

For PQ/User Acceptance Testing, the plugin generates reports but actual testing is performed by end users.
