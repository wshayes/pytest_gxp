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
- `Specification Type`: Installation, Design, Functional, or User
- `User Requirement ID`: Related user requirement (if applicable)
- `Test Node ID`: The pytest node ID of the test that verified the requirement
- `Risk Tier`: Risk tier declared by the test's `gxp_risk` marker (empty when unmarked)
- `Status`: Execution status of that test (PASSED, FAILED, ERROR, SKIPPED, XFAIL, XPASS, `Not Executed`)

The matrix emits **one row per executed test**: a requirement verified by three
tests produces three rows, each naming its own test and carrying that test's own
status. A requirement with no test keeps a single row with an empty `Test Node ID`
and status `Not Executed`.

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
| JSON | `csv_validation_report.json` | Full report with metadata, findings, and execution register |
| Markdown | `csv_validation_report.md` | Human-readable with evidence |
| PDF | `csv_validation_report.pdf` | Print-ready with evidence |

The CSV rendering carries the test case rows only — `Test Case ID`, `Title`,
`Requirements`, `Specification Type`, `Status`, `Deviation Ref` — with no metadata
or provenance. Read the JSON when you need the full record.

### JSON Structure

```json
{
  "report_metadata": {
    "title": "OQ Report",
    "qualification_type": "OQ",
    "generated_date": "2026-07-29T14:22:05Z",
    "version": "1.0",
    "status": "PROVISIONAL",
    "provisional_reasons": [
      "1 test(s) failed or errored",
      "1 non-passing test(s) without a deviation reference"
    ],
    "generator": { "name": "pytest-gxp", "version": "0.3.0" },
    "findings_summary": { "errors": 1, "warnings": 2 },
    "source_provenance": {
      "source": "git",
      "git_commit": "9f1c0d3e8ab24f7c1d05e6b2f8a3907c4d5e6f70",
      "git_tag": "v2.4.0",
      "git_dirty": false
    }
  },
  "validation_info": {
    "software_name": "My Application",
    "software_version": "1.0.0",
    "project_name": "My Application",
    "validation_date": "2026-07-29"
  },
  "approvals": {
    "tester": { "name": "John Doe", "role": "Tester", "date": "2026-07-29", "signature": "________" },
    "reviewer": { "name": "Jane Smith", "role": "Reviewer", "date": "2026-07-29", "signature": "________" },
    "approver": null
  },
  "specifications": {
    "design_spec": { "title": "...", "version": "1.0", "requirement_count": 3 },
    "functional_spec": { ... },
    "user_spec": { ... },
    "installation_spec": { ... }
  },
  "test_execution_summary": {
    "total_tests": 10,
    "executed_tests": 9,
    "passed_tests": 8,
    "failed_tests": 1,
    "skipped_tests": 0,
    "error_tests": 0,
    "not_executed_tests": 1,
    "test_pass_rate": 88.9,
    "test_execution_rate": 90.0
  },
  "requirement_coverage": { ... },
  "test_summary": {
    "total_test_cases": 10,
    "passed": 8,
    "failed": 1,
    "skipped": 0,
    "errors": 0,
    "not_executed": 1,
    "pass_rate": 88.9
  },
  "coverage": { ... },
  "test_cases": [ ... ],
  "test_execution": [ ... ],
  "findings": [ ... ]
}
```

`validation_info` and `approvals` are separate top-level sections; there is no
combined `validation_metadata` object. `test_summary` and `coverage` are retained
for backwards compatibility with 0.1.x consumers — `test_execution_summary` and
`requirement_coverage` are the current equivalents.

See [CSV Report Format](csv-report-format.md) for a field-by-field reference.

### Report Status

`report_metadata.status` is either `FINAL` or `PROVISIONAL`, with
`provisional_reasons` listing why. A report is provisional when the run contained
failed or errored tests, non-passing tests without a deviation reference, or any
error-severity finding.

**Non-passing** means an outcome of `FAILED`, `ERROR`, `XPASS`, or `NOT_EXECUTED`.
`PASSED`, `SKIPPED`, and `XFAIL` are treated as passing outcomes: a skip and an
expected failure are documented results, so they need no deviation reference. An
unexpected pass (`XPASS`) does — the test's own expectation was wrong.

A provisional report is marked as such in the Markdown and PDF renderings: the
title carries a suffix and the document opens with a banner reading *PROVISIONAL —
DRAFT RECORD. NOT FOR SIGNATURE.* A clean run produces `FINAL` with no banner.
This makes an unreviewed record visibly unfit for signature rather than merely
incomplete.

### Validation Findings

The plugin reports defects in the specifications, markers, and evidence rather
than degrading silently. Findings appear as a top-level `findings` list, are
counted in `report_metadata.findings_summary`, are rendered as a `## Validation
Findings` table in the Markdown and PDF reports, and are printed in the pytest
terminal summary.

| Code | Severity | Raised when |
|------|----------|-------------|
| `duplicate-requirement-id` | error | The same requirement ID is defined more than once |
| `malformed-requirement-heading` | error | A heading looks like a requirement but does not parse, so it was not read |
| `unknown-requirement-ref` | error | A test's `requirements` marker cites an ID no specification defines |
| `uncovered-requirement` | warning | A requirement has no test citing it |
| `invalid-risk-tier` | warning | A `gxp_risk` marker value is not `high`, `medium`, or `not-high` |
| `high-risk-no-evidence` | error | A high-risk requirement was verified with no objective evidence |
| `high-risk-evidence-unscripted-only` | error | A high-risk requirement's only evidence is unscripted session records, which describe what a tester did rather than capture system state |
| `missing-deviation-ref` | error | A non-passing test has no deviation reference (see below) |
| `deviation-file-error` | warning | The `--gxp-deviations` file is missing or unreadable |

Each finding carries `code`, `severity`, `message`, and `location` — a
`file.md:line` reference for specification findings, a pytest node ID for test
findings. Run with [`--gxp-strict`](../getting-started/configuration.md#strict-mode)
to fail the run on any error-severity finding.

### Test Execution Register

`test_execution` names the real pytest tests, one entry per executed test:

```json
[
  {
    "node_id": "tests/test_login.py::test_session_timeout",
    "outcome": "FAILED",
    "reason": "AssertionError: session still active after 900s",
    "requirement_ids": ["FS-007"],
    "risk_tier": "high",
    "deviation_ref": "DEV-2026-014"
  }
]
```

`outcome` is one of `PASSED`, `FAILED`, `ERROR`, `SKIPPED`, `XFAIL`, `XPASS`, or
`NOT_EXECUTED`. Setup and teardown are classified too, so a test that never ran
its body is recorded as `ERROR` or `SKIPPED` with its reason, not as a silent
non-result. Where a test's phases disagree, the worst outcome wins.

`deviation_ref` is always present, and is `null` when no reference was supplied.

The Markdown and PDF renderings carry the same register as a
`| Node ID | Outcome | Requirements | Deviation Ref | Reason |` table. The
deviation cell shows the reference, an em-dash when a passing test has none to
give, or a literal **MISSING** when a non-passing test has none.

### Markdown Report Sections

1. **Validation Information**: Project, software version, generation timestamp, source revision
2. **Approvals**: Approval signature blocks
3. **Validation Findings**: Findings raised during the run (omitted when there are none)
4. **Specifications**: Overview of all specifications
5. **Test Execution Summary**: Test execution statistics
6. **Requirement Coverage Summary**: Requirement coverage metrics
7. **Test Cases**: Requirement-derived test cases with links to their evidence
8. **Test Execution**: The real pytest tests with their outcomes, deviation references, and reasons — an unexplained non-passing result renders as **MISSING** rather than as a blank cell
9. **Objective Evidence**: Evidence captured during tests

### Source Provenance

Every report and the traceability matrix JSON record the revision of the system
under validation:

| Field | Meaning |
|-------|---------|
| `source` | `git` (detected), `config` (supplied via CLI/config), or `unavailable` |
| `git_commit` | Full commit SHA, or `null` |
| `git_tag` | Exact-match tag, or `null` |
| `git_dirty` | `true` when the working tree had uncommitted changes |

Nothing is fabricated: outside a git checkout every value is `null` and `source`
is `unavailable`. Supply the revision with `--gxp-source-commit` /
`--gxp-source-tag` when running outside a checkout. Provenance is not written to
the CSV renderings, which carry test rows only.

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
| `evidence/` | Evidence image files and unscripted session records |
| `evidence/thumbnails/` | Thumbnail images (if enabled) |
| `evidence_manifest.json` | Evidence metadata, with a SHA-256 per item |

### Evidence Manifest Structure

```json
{
  "generated_at": "2026-07-29T12:00:00Z",
  "evidence_count": 3,
  "evidence": [
    {
      "id": "EV-0001",
      "type": "screenshot",
      "description": "Login screen displayed",
      "file_path": "evidence/screenshot_20260729_120000_a1b2c3d4.png",
      "sha256": "3b1a5f...c07d",
      "timestamp": "2026-07-29T12:00:00Z",
      "test_id": "tests/test_login.py::test_user_login",
      "requirement_ids": ["FS-001"],
      "thumbnail_path": "evidence/thumbnails/thumb_screenshot_20260729_120000_a1b2c3d4.png",
      "metadata": {}
    }
  ]
}
```

Each entry carries the `sha256` of its evidence file, so evidence attribution can
be verified by hash rather than by inspection — the file named against a test is
demonstrably the file that test captured.

### Unscripted Session Evidence

Exploratory and other unscripted testing is recorded as evidence in its own right,
as a JSON side-car rather than an image (so it needs no Pillow):

```python
@pytest.mark.gxp
@pytest.mark.gxp_risk("not-high")
@pytest.mark.requirements(["US-004"])
def test_report_export_exploration(gxp_evidence):
    gxp_evidence.record_unscripted_session(
        charter="Explore report export across formats and locales",
        tester="John Doe",
        duration_minutes=45,
        observations=[
            "CSV export opens correctly in Excel with UTF-8 characters intact",
            "PDF export honours the configured page size",
        ],
        defects=["Export button remains enabled during export"],
    )
```

`defects` is optional. Sessions appear under the `unscripted_session` evidence
type and render in the report as a labelled bullet list rather than an inline
image. See the unscripted session record form
(FRM-CSA-05) in [Checklists and Forms](../validation/forms.md).

### Evidence in Reports

Evidence is included in both Markdown and PDF reports. Each test with evidence shows:

- Evidence ID (auto-generated, e.g., `EV-0001`)
- Type (screenshot, directory_listing, command_output, image, unscripted_session)
- Description
- Timestamp
- The image inline, or the session details for an unscripted session

### Capturing Evidence

See [Running Tests](running-tests.md#capturing-objective-evidence) for details on using the `gxp_evidence` fixture.

## Artifact Manifest

**File**: `artifact_manifest.sha256`

A SHA-256 digest of every other file in the report directory, written last in the
session so that it covers all of them. The format is `sha256sum`-compatible —
`<hex>  <relative-path>`, sorted by path — behind a short comment header naming
the generating tool and version.

Verify a report directory by stripping the comment lines and handing the rest to
your platform's checker:

```bash
cd gxp_report_files
grep -v '^#' artifact_manifest.sha256 | sha256sum -c -     # Linux
grep -v '^#' artifact_manifest.sha256 | shasum -a 256 -c -  # macOS
```

The manifest is what an external signing process should bind to: it fixes the
exact bytes of the reviewed artifacts, including the PDF as produced.

## Reproducibility

Two runs over unchanged specifications and unchanged test outcomes produce
identical JSON, CSV, and Markdown artifacts apart from the recorded timestamps
(`generated_date`, `validation_date`, and evidence timestamps and filenames).
Specification files are parsed in sorted order, specifications are iterated in a
fixed type order, and every emitted list — evidence, findings, test execution
records, matrix rows — is sorted.

The **PDF is excluded** from this claim: the renderer embeds its own creation
timestamp, so the PDF is not byte-reproducible. Treat the PDF as a rendering of
the Markdown record rather than the record of authority, and bind signatures to
`artifact_manifest.sha256`.

All timestamps are UTC ISO 8601 with a `Z` designator (`2026-07-29T14:22:05Z`).

## PDF Generation

### Prerequisites

Install PDF conversion dependencies:

```bash
uv add --dev "pytest-gxp[pdf]"
```

Or install all optional dependencies:

```bash
uv add --dev "pytest-gxp[all]"
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
2. Traceability matrix expanded to one row per executed test
3. Coverage calculated from requirement-test mapping
4. Findings collected and the report status determined (`FINAL` or `PROVISIONAL`)
5. Evidence manifest written
6. Reports generated in requested formats
7. `artifact_manifest.sha256` written last, covering every artifact above

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
