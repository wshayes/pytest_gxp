# Traceability Matrix Format

The traceability matrix is a critical component of GxP CSV validation, demonstrating the relationship between requirements and test cases.

## Format Overview

The traceability matrix is generated in three formats:
- **CSV format** (`traceability_matrix.csv`) - For programmatic processing and spreadsheet applications
- **JSON format** (`traceability_matrix.json`) - Matrix rows plus coverage metrics and source provenance
- **Markdown format** (`traceability_matrix.md`) - For human-readable documentation

## One Row Per Executed Test

!!! warning "Schema change in 0.2.0"
    The matrix emits **one row per executed test**, and carries two new columns
    (`Test Node ID` and `Risk Tier`). A requirement verified by three tests
    produces three rows. Consumers that read the CSV by column position must be
    updated to read by header name.

Each row names a real pytest test in `Test Node ID` and carries that test's own
status, so a requirement whose second test failed shows one passing row and one
failing row rather than a single rolled-up verdict. A requirement with no test
keeps a single row with an empty `Test Node ID` and status `Not Executed`.

## CSV Format Specification

### File Structure

The CSV file uses comma-separated values with the following columns:

| Column Name | Description | Example |
|------------|-------------|---------|
| Test Case ID | Requirement-derived test case identifier | TEST-FS-001 |
| Test Case Title | Descriptive title of the test case | Test FS-001: User Login Functionality |
| Requirement ID | The requirement identifier being tested | FS-001 |
| Requirement Title | Title of the requirement | User Login Functionality |
| Specification Type | Type of specification (Installation, Design, Functional, or User) | Functional |
| User Requirement ID | Related user requirement ID (if applicable) | US-001 |
| Test Node ID | pytest node ID of the test that verified the requirement | tests/test_login.py::test_user_login |
| Risk Tier | Risk tier from the test's `gxp_risk` marker | high, medium, not-high |
| Status | Execution status of that test | PASSED, FAILED, ERROR, SKIPPED, XFAIL, XPASS, Not Executed |

### CSV Example

```csv
Test Case ID,Test Case Title,Requirement ID,Requirement Title,Specification Type,User Requirement ID,Test Node ID,Risk Tier,Status
TEST-FS-001,Test FS-001: User Login Functionality,FS-001,User Login Functionality,Functional,US-001,tests/test_login.py::test_user_login,high,PASSED
TEST-FS-001,Test FS-001: User Login Functionality,FS-001,User Login Functionality,Functional,US-001,tests/test_login.py::test_login_locale,high,PASSED
TEST-FS-004,Test FS-004: Audit Trail,FS-004,Audit Trail,Functional,,,,Not Executed
```

### Status Values

Values are those of the underlying test, worst first:

- **ERROR** - Test errored in setup or teardown
- **FAILED** - Test executed and failed
- **XFAIL** - Test was expected to fail and did
- **XPASS** - Test was expected to fail but passed
- **SKIPPED** - Test skipped (e.g., due to missing dependencies)
- **PASSED** - Test executed and passed
- **Not Executed** - No test cites the requirement

### Risk Tier Values

The tier comes from `@pytest.mark.gxp_risk("high" | "medium" | "not-high")` on the
test named in the row, and is empty when the test carries no marker. A requirement
takes the highest tier among the tests citing it. With
[`--gxp-strict`](../getting-started/configuration.md#strict-mode), a `high` tier
requirement verified with no objective evidence fails the run. See
[Risk-Based Assurance](../validation/risk-based-assurance.md) for how to allocate
tiers.

## Markdown Format Specification

### Structure

The Markdown format includes:

1. **Header Section**
   - Project name
   - Generation date
   - Version information
   - Source revision of the system under validation

2. **Traceability Table**
   - Same columns as CSV format
   - Formatted as a Markdown table

3. **Coverage Summary**
   - Total requirements count
   - Covered requirements count
   - Coverage percentage
   - List of uncovered requirements

4. **Notes Section**
   - Additional information about the traceability matrix

### Markdown Example

```markdown
# Traceability Matrix

**Project:** Example Project
**Generated:** 2026-07-29
**Version:** 1.0
**Source Revision:** 9f1c0d3e8ab24f7c1d05e6b2f8a3907c4d5e6f70

## Traceability Data

| Test Case ID | Test Case Title | Requirement ID | ... | Test Node ID | Risk Tier | Status |
|--------------|----------------|----------------|-----|--------------|-----------|--------|
| TEST-FS-001 | Test FS-001: User Login | FS-001 | ... | tests/test_login.py::test_user_login | high | PASSED |

## Coverage Summary

- **Total Requirements:** 7
- **Covered Requirements:** 6
- **Coverage Percentage:** 85.7%
```

## JSON Format Specification

The JSON rendering carries the same rows plus coverage metrics and the source
revision of the system under validation:

```json
{
  "metadata": {
    "title": "Traceability Matrix",
    "project": "Example Project",
    "generated_date": "2026-07-29T14:22:05Z",
    "version": "1.0",
    "source_provenance": {
      "source": "git",
      "git_commit": "9f1c0d3e8ab24f7c1d05e6b2f8a3907c4d5e6f70",
      "git_tag": "v2.4.0",
      "git_dirty": false
    }
  },
  "coverage": { "total_requirements": 7, "requirements_with_tests": 6, "...": "..." },
  "matrix": [ { "Test Case ID": "TEST-FS-001", "...": "..." } ]
}
```

Provenance is recorded in the JSON metadata and in the Markdown header; the CSV
rendering carries matrix rows only. See
[Reports](reports.md#source-provenance) for the provenance fields.

## Usage

### Viewing the Matrix

**CSV Format:**
- Open in Excel, Google Sheets, or any spreadsheet application
- Import into database systems
- Process programmatically with scripts

**Markdown Format:**
- View in any Markdown viewer
- Include in documentation
- Convert to PDF or HTML

### Updating Status

The traceability matrix status is written from the actual test outcomes of the run that produced it. Regenerate it by re-running with `--gxp`; do not edit it by hand. An edited matrix is no longer the record of a run, and its hash in `artifact_manifest.sha256` will no longer reproduce.

### Coverage Analysis

Use the coverage summary to:
- Identify untested requirements
- Track validation progress
- Generate compliance reports

## Best Practices

1. **Regenerate, don't edit**: Produce a new matrix by re-running the tests
2. **Read by header**: Address CSV columns by name, since the schema grows
3. **Requirement Mapping**: Verify all requirements have corresponding test cases
4. **User Requirements**: Map user requirements to functional/design requirements when applicable
5. **Risk Tiers**: Keep `gxp_risk` markers aligned with your requirement risk classification

## Integration

The traceability matrix integrates with:
- CSV Validation Summary Report
- Test execution results
- Requirement specifications
- Compliance documentation

See the [Examples](../examples/traceability-example.md) section for complete examples.

