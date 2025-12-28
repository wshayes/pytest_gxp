# Reports

The Pytest GxP plugin generates several types of reports to support CSV validation documentation. By default, all output formats (CSV, JSON, Markdown, PDF) are generated.

## Output Formats

Control which formats are generated with `--gxp-output-formats`:

```bash
# Generate all formats (default)
pytest --gxp --gxp-output-formats=csv,json,md,pdf

# Generate only Markdown and PDF
pytest --gxp --gxp-output-formats=md,pdf

# Generate only CSV
pytest --gxp --gxp-output-formats=csv
```

## Traceability Matrix

The traceability matrix maps test cases to requirements across all specification types.

### Generated Files

| Format | File | Description |
|--------|------|-------------|
| CSV | `traceability_matrix.csv` | For spreadsheet applications |
| JSON | `traceability_matrix.json` | For programmatic processing |
| Markdown | `traceability_matrix.md` | For documentation |

### Columns

- `Test Case ID`: Auto-generated identifier (e.g., `TEST-FS-001`)
- `Test Case Title`: Descriptive title of the test
- `Requirement ID`: The requirement being tested
- `Requirement Title`: Title of the requirement
- `Specification Type`: Design, Functional, or User
- `User Requirement ID`: Related user requirement (if applicable)
- `Status`: Test execution status (PASSED, FAILED, NOT_EXECUTED)

### Usage

The traceability matrix demonstrates that:

- All requirements have corresponding test cases
- Test coverage is complete
- Requirements can be traced through the validation process

See [Traceability Format](traceability-format.md) for detailed format specifications.

## CSV Validation Report

Comprehensive validation report for IQ/OQ/PQ qualification.

### Generated Files

| Format | File | Description |
|--------|------|-------------|
| CSV | `csv_validation_report.csv` | Tabular test results |
| JSON | `csv_validation_report.json` | Full report with metadata |
| Markdown | `csv_validation_report.md` | Human-readable with evidence |
| PDF | `csv_validation_report.pdf` | Print-ready with evidence |

### JSON Structure

```json
{
  "report_metadata": {
    "title": "CSV Validation Summary Report",
    "generated_date": "2024-01-01T00:00:00",
    "version": "1.0"
  },
  "validation_metadata": {
    "qualification_type": "OQ",
    "software_name": "My Application",
    "software_version": "1.0.0",
    "validation_date": "2024-01-01",
    "tester": { "name": "John Doe", "role": "Tester", "date": "2024-01-01" },
    "reviewer": { "name": "Jane Smith", "role": "Reviewer", "date": "2024-01-01" },
    "approver": { "name": "Bob Johnson", "role": "Approver", "date": "2024-01-01" }
  },
  "specifications": {
    "design_spec": { ... },
    "functional_spec": { ... },
    "user_spec": { ... }
  },
  "test_summary": {
    "total_test_cases": 10,
    "passed": 8,
    "failed": 1,
    "skipped": 1,
    "pass_rate": 80.0
  },
  "coverage": {
    "total_requirements": 15,
    "requirements_with_tests": 12,
    "requirement_coverage_rate": 80.0,
    "requirements_verified": 10,
    "requirement_verification_rate": 83.3
  },
  "test_cases": [ ... ]
}
```

### Markdown Report Sections

1. **Validation Metadata**: Qualification type, software version, approval signatures
2. **Specifications**: Overview of all specifications
3. **Test Summary**: Test execution statistics
4. **Coverage**: Requirement coverage metrics
5. **Test Cases**: Detailed test case information
6. **Objective Evidence**: Evidence captured during tests

### Usage

The validation report is ideal for:

- IQ/OQ/PQ qualification documentation
- Review meetings
- Regulatory submissions
- Audit documentation

## Requirement Coverage Report

**File**: `requirement_coverage.md`

Detailed coverage analysis showing which requirements have tests and their verification status.

### Sections

- Summary metrics (total, covered, uncovered requirements)
- List of requirements without test coverage
- All requirements with their test count and status

## Objective Evidence

Evidence captured during test execution is stored and documented.

### Generated Files

| File/Directory | Description |
|----------------|-------------|
| `evidence/` | Evidence image files |
| `evidence/thumbnails/` | Thumbnail images (if enabled) |
| `evidence_manifest.json` | Evidence metadata |

### Evidence Manifest Structure

```json
{
  "generated_date": "2024-01-01T12:00:00",
  "evidence_count": 3,
  "evidence": [
    {
      "id": "EV-0001",
      "type": "screenshot",
      "description": "Login screen displayed",
      "file_path": "evidence/screenshot_20240101_120000_a1b2c3d4.png",
      "timestamp": "2024-01-01T12:00:00",
      "test_id": "tests/test_login.py::test_user_login",
      "requirement_ids": ["FS-001"],
      "thumbnail_path": "evidence/thumbnails/thumb_screenshot_20240101_120000_a1b2c3d4.png"
    }
  ]
}
```

### Evidence in Reports

Evidence is included in both Markdown and PDF reports. Each test with evidence shows:

- Evidence ID (auto-generated, e.g., `EV-0001`)
- Type (screenshot, directory_listing, command_output, image)
- Description
- Link to evidence file

### Capturing Evidence

See [Running Tests](running-tests.md#capturing-objective-evidence) for details on using the `gxp_evidence` fixture.

## PDF Generation

### Prerequisites

Install PDF conversion dependencies:

```bash
pip install pytest-gxp[pdf]
```

Or install all optional dependencies:

```bash
pip install pytest-gxp[all]
```

### PDF Features

The PDF report includes:

- Professional styling with headers and footers
- Approval signature blocks
- Tables with test results
- Embedded evidence images
- Page numbers and generation date
- Suitable for printing and distribution

### Generating PDF Only

```bash
pytest --gxp --gxp-output-formats=pdf
```

## Evidence Thumbnails

Thumbnails are generated by default for evidence images. Disable with:

```bash
pytest --gxp --no-gxp-evidence-thumbnails
```

Thumbnails appear in reports for quick visual reference while linking to full-size images.

## Report Generation Workflow

Reports are automatically generated after test execution when using `--gxp` mode:

1. Tests execute with evidence capture
2. Traceability matrix generated with test results
3. Coverage calculated from requirement-test mapping
4. Evidence manifest written
5. Reports generated in requested formats

## Customizing Reports

### Approval Signatures

Add approval signatures via CLI:

```bash
pytest --gxp \
    --gxp-tester="John Doe" \
    --gxp-reviewer="Jane Smith" \
    --gxp-approver="Bob Johnson"
```

Or via `pyproject.toml`:

```toml
[tool.pytest-gxp]
tester-name = "John Doe"
reviewer-name = "Jane Smith"
approver-name = "Bob Johnson"
```

### Qualification Type

Set the qualification type (IQ, OQ, or PQ):

```bash
pytest --gxp --gxp-qualification-type=OQ
```
