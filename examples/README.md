# GxP Plugin Examples

This directory contains example GxP specifications to demonstrate the pytest-gxp plugin functionality.

## Directory Structure

```
examples/
├── gxp_spec_files/
│   ├── installation_specification.md
│   ├── design_specification.md
│   ├── functional_specification.md
│   └── user_specification.md
├── gxp_report_files/
│   └── ... (generated reports)
├── test_example.py
├── pytest.ini
└── README.md
```

## Specification Files

### Installation Specification (`installation_specification.md`)
Contains installation requirements (IS-001, IS-002, IS-003) that define how the system should be installed and configured. Used for IQ (Installation Qualification).

### Design Specification (`design_specification.md`)
Contains high-level design requirements (DS-001, DS-002, DS-003) that define the architectural and design aspects of the system. Used for OQ (Operational Qualification).

### Functional Specification (`functional_specification.md`)
Contains detailed functional requirements (FS-001, FS-002, FS-003, FS-004) that define how the system should behave from a functional perspective. Used for OQ (Operational Qualification).

### User Specification (`user_specification.md`)
Contains user requirements (US-001, US-002, US-003) that define what users need from the system. Used for PQ (Performance Qualification).

## Running the Examples

### Quick Start (Using pytest.ini)

The examples include a `pytest.ini` file with all configuration pre-set, including approval signatures:

```bash
cd examples
uv run pytest --gxp
```

This will use the configuration from `pytest.ini` which includes:
- Project name and version
- Specification and report file paths
- Tester, Reviewer, and Approver signatures
- All output formats (CSV, JSON, Markdown, PDF)

### Using CLI Options

You can also specify all options via command line:

```bash
cd examples
uv run pytest --gxp \
    --gxp-spec-files=gxp_spec_files \
    --gxp-report-files=gxp_report_files \
    --gxp-project-name="Example Application" \
    --gxp-software-version="1.0.0" \
    --gxp-tester="John Smith" \
    --gxp-reviewer="Jane Doe" \
    --gxp-approver="Robert Johnson"
```

### Using pip

1. Install the plugin:
   ```bash
   pip install -e ..
   ```

2. Run pytest with GxP mode:
   ```bash
   cd examples
   pytest --gxp
   ```

### Running with Qualification Type

For IQ (Installation Qualification):
```bash
uv run pytest --gxp \
    --gxp-qualification-type=IQ \
    --gxp-spec-files=gxp_spec_files \
    --gxp-report-files=gxp_report_files
```

For OQ (Operational Qualification):
```bash
uv run pytest --gxp \
    --gxp-qualification-type=OQ \
    --gxp-spec-files=gxp_spec_files \
    --gxp-report-files=gxp_report_files
```

## Generated Reports

After running, check the `gxp_report_files/` directory:

- `traceability_matrix.csv` - CSV traceability matrix
- `traceability_matrix.json` - JSON traceability matrix
- `traceability_matrix.md` - Markdown traceability matrix
- `csv_validation_report.csv` - CSV validation report
- `csv_validation_report.json` - JSON validation report
- `csv_validation_report.md` - Markdown validation report with approval signatures
- `csv_validation_report.pdf` - PDF validation report (requires `pip install pytest-gxp[pdf]`)
- `requirement_coverage.md` - Requirement coverage summary
- `evidence_manifest.json` - Evidence metadata
- `evidence/` - Directory containing captured evidence images

## Specification Format

Each specification file follows this format:

```markdown
# Specification Title

## Version: X.Y

### FS-001: Requirement Title

#### Description
Detailed description of the requirement.

1. First requirement detail
2. Second requirement detail
...

Expected Result: What should happen when this requirement is met.

#### Metadata
Priority: High/Medium/Low
Category: Category Name
Owner: Owner Name
```

## Requirement ID Format

| Specification Type | ID Format | Qualification Phase |
|-------------------|-----------|---------------------|
| Installation | `IS-XXX` | IQ |
| Design | `DS-XXX` | OQ |
| Functional | `FS-XXX` | OQ |
| User | `US-XXX` | PQ |
