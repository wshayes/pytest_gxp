# Configuration

pytest-gxp supports configuration through CLI options, `pyproject.toml`, and `pytest.ini`. Options are applied with the following priority (highest to lowest):

1. CLI options
2. `pyproject.toml` `[tool.pytest-gxp]`
3. `pytest.ini` options
4. Default values

## Command Line Options

### Core Options

| Option | Default | Description |
|--------|---------|-------------|
| `--gxp` | `False` | Enable GxP CSV validation mode |
| `--gxp-spec-files` | `gxp_spec_files` | Path to specification files directory |
| `--gxp-report-files` | `gxp_report_files` | Path to report output directory |
| `--gxp-output-formats` | `csv,json,md,pdf` | Comma-separated list of output formats |

### Qualification Options

| Option | Default | Description |
|--------|---------|-------------|
| `--gxp-qualification-type` | `OQ` | Qualification type: IQ, OQ, or PQ |
| `--gxp-software-version` | | Software version being validated |
| `--gxp-project-name` | | Project name for reports |

### Approval Signature Options

| Option | Default | Description |
|--------|---------|-------------|
| `--gxp-tester` | | Tester name for approval signature |
| `--gxp-reviewer` | | Reviewer name for approval signature |
| `--gxp-approver` | | Approver name for approval signature |

### Coverage Options

| Option | Default | Description |
|--------|---------|-------------|
| `--gxp-strict-coverage` | `False` | Fail if any requirements lack test coverage |

### Evidence Options

| Option | Default | Description |
|--------|---------|-------------|
| `--gxp-evidence-thumbnails` | `True` | Generate thumbnail images for evidence |
| `--no-gxp-evidence-thumbnails` | | Disable thumbnail generation |

## Basic Usage

```bash
# Enable GxP mode
pytest --gxp

# With custom paths
pytest --gxp --gxp-spec-files=path/to/specs --gxp-report-files=path/to/reports
```

## Full Example

```bash
pytest --gxp \
    --gxp-qualification-type=OQ \
    --gxp-software-version=1.0.0 \
    --gxp-project-name="My Application" \
    --gxp-tester="John Doe" \
    --gxp-reviewer="Jane Smith" \
    --gxp-approver="Bob Johnson" \
    --gxp-strict-coverage \
    --gxp-output-formats=csv,json,md,pdf
```

## pyproject.toml Configuration

Configure the plugin in your `pyproject.toml`:

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

## pytest.ini Configuration

Configure the plugin in `pytest.ini`:

```ini
[pytest]
gxp_spec_files = gxp_spec_files
gxp_report_files = gxp_report_files
gxp_qualification_type = OQ
gxp_software_version = 1.0.0
gxp_project_name = My Application
gxp_strict_coverage = false
gxp_tester_name = John Doe
gxp_reviewer_name = Jane Smith
gxp_approver_name = Bob Johnson
gxp_evidence_thumbnails = true
gxp_output_formats = csv,json,md,pdf
```

You can also add `--gxp` to default options:

```ini
[pytest]
addopts = --gxp --gxp-spec-files=specs --gxp-report-files=reports
```

## Output Formats

The `--gxp-output-formats` option accepts a comma-separated list of formats:

- `csv` - CSV files for spreadsheet applications
- `json` - JSON files for programmatic processing
- `md` - Markdown files for documentation
- `pdf` - PDF files for distribution (requires `pip install pytest-gxp[pdf]`)

By default, all formats are generated. To generate only specific formats:

```bash
# Generate only Markdown and PDF
pytest --gxp --gxp-output-formats=md,pdf

# Generate only CSV and JSON
pytest --gxp --gxp-output-formats=csv,json
```

## Strict Coverage Mode

When `--gxp-strict-coverage` is enabled, the test run will fail if any requirements in the specification files don't have corresponding tests:

```bash
pytest --gxp --gxp-strict-coverage
```

This ensures complete test coverage of all specified requirements.

## Pre-commit Hooks

If you're developing the plugin, set up pre-commit hooks:

```bash
pre-commit install
```

This ensures code quality and formatting before commits.
