# Pytest GxP Plugin

Pytest plugin for GAMP5 GxP Computer System Validation (CSV) of custom applications. Provides requirement traceability, test coverage reporting, and validation reports for IQ/OQ/PQ qualification phases.

Release notes are in [CHANGELOG.md](CHANGELOG.md).

## Features

- Parse Markdown-based Installation, Design, Functional, and User Specifications
- Link pytest tests to requirements using markers
- Generate traceability matrices (CSV, JSON, and Markdown), one row per executed test
- Generate qualification reports (IQ/OQ/PQ) with approval signatures
- Capture objective evidence (screenshots, directory listings, command output, unscripted sessions)
- Report defects in specifications and markers as validation findings, with a strict gate
- Record source provenance (commit, tag, dirty state) in every generated record
- Classify requirement risk and gate high-risk requirements on objective evidence
- Attach deviation references to non-passing results, and mark unclean records `PROVISIONAL`
- Hash every generated artifact into `artifact_manifest.sha256`
- Requirement coverage checking with strict mode option
- Configuration via CLI, pyproject.toml, or pytest.ini
- Ships a [tool-qualification suite](docs/validation/index.md) in the source distribution

## Technical Stack

- Python 3.9+
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

### Strict Mode

Fail the test run on any error-severity validation finding — a test citing a
requirement that does not exist, a duplicate requirement ID, a high-risk
requirement verified with no objective evidence, or a non-passing test with no
deviation reference:

```bash
pytest --gxp --gxp-strict
```

Off by default, so enabling the plugin never changes whether a run passes.

### Source Provenance

The revision of the system under validation is detected from git and recorded in
every report. Outside a git checkout, supply it explicitly:

```bash
pytest --gxp --gxp-source-commit=9f1c0d3e8a... --gxp-source-tag=v2.4.0
```

Nothing is fabricated: with neither git nor an override, the provenance is recorded
as `unavailable`.

### Deviation References

Supply deviation references for investigated failures as data, so controlled test
files need no editing:

```bash
pytest --gxp --gxp-deviations=deviations.json
```

```json
{
  "tests/test_login.py::test_session_timeout": "DEV-2026-014",
  "FS-007": "DEV-2026-015"
}
```

Keys are pytest node IDs or requirement IDs; a node ID wins for the same test. Any
non-passing test with no reference raises a `missing-deviation-ref` finding.

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
| `--gxp-strict` | False | Fail on any error-severity validation finding |
| `--gxp-deviations` | | Path to a JSON file mapping tests or requirements to deviation references |
| `--gxp-source-commit` | | Commit of the validated system (overrides git detection) |
| `--gxp-source-tag` | | Tag of the validated system (overrides git detection) |
| `--gxp-output-formats` | `csv,json,md,pdf` | Comma-separated output formats |
| `--gxp-evidence-thumbnails` | True | Generate thumbnail images for evidence |
| `--no-gxp-evidence-thumbnails` | | Disable thumbnail generation |

### Configuration File (pyproject.toml)

```toml
[tool.pytest-gxp]
spec-files = "gxp_spec_files"
report-files = "gxp_report_files"
qualification-type = "OQ"
software-version = "1.0.0"
project-name = "My Application"
strict-coverage = false
strict = false
tester-name = "John Doe"
reviewer-name = "Jane Smith"
approver-name = "Bob Johnson"
output-formats = "csv,json,md,pdf"
deviations = "deviations.json"
```

### Configuration File (pytest.ini)

```ini
[pytest]
gxp_spec_files = gxp_spec_files
gxp_report_files = gxp_report_files
gxp_qualification_type = OQ
gxp_software_version = 1.0.0
gxp_project_name = My Application
gxp_strict = false
gxp_deviations = deviations.json
gxp_source_commit =
gxp_source_tag =
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
One row per executed test, naming the real pytest node ID alongside the
requirement-derived Test ID (`TEST-FS-001`), its risk tier, and its own status.
- `traceability_matrix.csv`
- `traceability_matrix.json`
- `traceability_matrix.md`

### Qualification Report
Validation summary with approval signatures, findings, the test execution
register, and evidence. Marked `PROVISIONAL` when the run was not clean.
- `csv_validation_report.csv`
- `csv_validation_report.json`
- `csv_validation_report.md`
- `csv_validation_report.pdf` (requires `pip install pytest-gxp[pdf]`)

### Requirement Coverage Report
Details which requirements have tests and their verification status.
- `requirement_coverage.md`

### Evidence (when captured)
Objective evidence with auto-generated IDs (`EV-0001`), each hashed in the manifest.
- `evidence/` - Evidence image files and unscripted session records
- `evidence/thumbnails/` - Thumbnail images
- `evidence_manifest.json` - Evidence metadata with a SHA-256 per item

### Artifact Manifest
A `sha256sum`-compatible digest of every artifact above, written last in the
session so it covers all of them.
- `artifact_manifest.sha256`

```bash
cd gxp_report_files
grep -v '^#' artifact_manifest.sha256 | sha256sum -c -
```

The JSON, CSV, and Markdown outputs are reproducible across runs over unchanged
inputs, apart from the recorded timestamps. The PDF is not — its renderer embeds a
creation timestamp — so bind signatures to `artifact_manifest.sha256`. All
timestamps are UTC ISO 8601 with a `Z` designator.

## Test Markers

The plugin provides pytest markers for GxP tests:

- `@pytest.mark.gxp`: Mark a test as a GxP validation test
- `@pytest.mark.requirements(["FS-001", "FS-002"])`: Associate test with requirement IDs
- `@pytest.mark.gxp_risk("high")`: Declare the risk tier of the requirement being verified (`high`, `medium`, or `not-high`)

Example:

```python
import pytest

@pytest.mark.gxp
@pytest.mark.gxp_risk("high")
@pytest.mark.requirements(["FS-001"])
def test_user_login(gxp_evidence):
    """Test user login functionality."""
    # A high-risk requirement needs objective evidence under --gxp-strict
    pass

@pytest.mark.gxp
@pytest.mark.gxp_risk("medium")
@pytest.mark.requirements(["FS-001", "FS-002"])
def test_login_with_validation():
    """Test login with input validation."""
    # This test covers multiple requirements
    pass
```

A requirement takes the highest tier among the tests citing it, and the tier
appears in the traceability matrix and the execution register. An unrecognised
tier raises an `invalid-risk-tier` finding and is treated as unset.

## Validation Findings

The plugin reports defects in your specifications, markers, and evidence rather
than degrading silently. Findings are printed in the terminal summary, listed in
the JSON report, and tabulated in the Markdown and PDF reports.

| Code | Severity |
|------|----------|
| `duplicate-requirement-id` | error |
| `malformed-requirement-heading` | error |
| `unknown-requirement-ref` | error |
| `high-risk-no-evidence` | error |
| `missing-deviation-ref` | error |
| `uncovered-requirement` | warning |
| `invalid-risk-tier` | warning |
| `deviation-file-error` | warning |

`--gxp-strict` fails the run on any error-severity finding. See the
[Reports guide](docs/user-guide/reports.md#validation-findings) for what each code
means.

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
| `record_unscripted_session(charter, tester, duration_minutes, observations, defects=None)` | Record an unscripted or exploratory session as a JSON side-car (no Pillow needed) |

### Unscripted Sessions

Exploratory testing is recorded as evidence in its own right:

```python
@pytest.mark.gxp
@pytest.mark.gxp_risk("not-high")
@pytest.mark.requirements(["US-004"])
def test_report_export_exploration(gxp_evidence):
    gxp_evidence.record_unscripted_session(
        charter="Explore report export across formats and locales",
        tester="John Doe",
        duration_minutes=45,
        observations=["CSV export opens in Excel with UTF-8 characters intact"],
        defects=["Export button remains enabled during export"],
    )
```

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

## Validating this Tool (Tool Qualification)

pytest-gxp produces the traceability matrix, evidence manifest, and validation
report that your organisation relies upon as GxP records. Under GAMP 5, a tool that
produces validation evidence must itself be shown fit for that purpose. This plugin
supports your validation; establishing its fitness for your intended use is the
regulated user's responsibility, not something the package can assert on your
behalf.

An executable black-box qualification suite ships in the **source distribution**
under `tool_qualification/` — deliberately excluded from the wheel, so a
qualification package is an artifact you obtain and retain deliberately:

```bash
pip download --no-binary :all: --no-deps pytest-gxp==0.2.0 -d ./tq-download
tar xzf ./tq-download/pytest_gxp-0.2.0.tar.gz && cd pytest_gxp-0.2.0

TZ=UTC TQ_PINNED_VERSION=0.2.0 \
  pytest -c tool_qualification/pytest.ini tool_qualification/ -m "not gap" -v
```

The [Validation](docs/validation/index.md) documentation section provides the
supporting package as templates to adopt under your own document control: a tool
qualification protocol, a work instruction, checklists and forms, and a risk-based
assurance strategy.

## Releasing (Maintainers)

Releases are published to PyPI via [Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
(OpenID Connect) — no API tokens are stored anywhere. The
`.github/workflows/publish.yml` workflow builds the distributions, runs the
TQ-001 tool-qualification gate against the built wheel, and only then uploads.
An unqualified build never reaches PyPI, and the published artifact provably
comes from the tagged CI build rather than a maintainer's machine.

### One-time PyPI setup

1. On PyPI, go to **Your account → Publishing → Add a new pending publisher**
   (or, once the project exists, **Manage project → Publishing**) and register:

   | Field | Value |
   |-------|-------|
   | PyPI project name | `pytest-gxp` |
   | Owner | `wshayes` |
   | Repository name | `pytest_gxp` |
   | Workflow name | `publish.yml` |
   | Environment name | `pypi` |

2. On GitHub, create the matching environment: **Settings → Environments →
   New environment → `pypi`**. Optionally add required reviewers so every
   PyPI upload needs a manual approval click.

### Cutting a release

1. Bump `version` in `pyproject.toml` and add a `CHANGELOG.md` entry.
2. Commit, merge to `main`, and confirm CI (unit matrix + TQ-001 gate) is green.
3. Tag and publish the GitHub release:

   ```bash
   git tag -a vX.Y.Z -m "pytest-gxp X.Y.Z"
   git push origin vX.Y.Z
   gh release create vX.Y.Z --title "vX.Y.Z" --notes-file <notes>
   ```

4. The `Publish to PyPI` workflow triggers on the release, rebuilds from the
   tag, re-runs the qualification gate against the exact wheel being
   published, and uploads. (It can also be run manually from the Actions tab
   via *workflow_dispatch* — useful for publishing a release created before
   the workflow existed.)

Record the released artifact hashes (from the GitHub release page or
`shasum -a 256 dist/*`) in the release notes; user-side qualification pins
against them.

## Qualification Types (GAMP5)

| Phase | Description | Specifications Used |
|-------|-------------|---------------------|
| **IQ** | Installation Qualification - Verifies software is correctly installed | Installation Spec (IS) |
| **OQ** | Operational Qualification - Verifies software operates according to specifications | Design Spec (DS), Functional Spec (FS) |
| **PQ** | Performance Qualification - Verifies software meets user requirements | User Spec (US) |

For PQ/User Acceptance Testing, the plugin generates reports but actual testing is performed by end users.
