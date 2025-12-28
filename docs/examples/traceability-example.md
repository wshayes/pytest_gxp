# Traceability Matrix Examples

This page provides complete examples of traceability matrices in both CSV and Markdown formats.

## CSV Format Example

See the complete example file: [traceability_matrix.csv](files/traceability_matrix.csv)

```csv
Test Case ID,Test Case Title,Requirement ID,Requirement Title,Specification Type,User Requirement ID,Status
TEST-FS-001,Test FS-001: User Login Functionality,FS-001,User Login Functionality,Functional,US-001,Passed
TEST-FS-002,Test FS-002: Input Data Validation,FS-002,Input Data Validation,Functional,US-002,Passed
TEST-FS-003,Test FS-003: Audit Logging,FS-003,Audit Logging,Functional,US-003,Passed
```

## Markdown Format Example

See the complete example file: [traceability_matrix.md](files/traceability_matrix.md)

```markdown
# Traceability Matrix

**Project:** Example GxP Validation Project  
**Generated:** 2024-01-15  
**Version:** 1.0

## Traceability Data

| Test Case ID | Test Case Title | Requirement ID | Requirement Title | Specification Type | User Requirement ID | Status |
|--------------|----------------|----------------|-------------------|-------------------|---------------------|--------|
| TEST-FS-001 | Test FS-001: User Login Functionality | FS-001 | User Login Functionality | Functional | US-001 | Passed |
```

## Using the Examples

1. **CSV Format**: Open `traceability_matrix.csv` in Excel or any spreadsheet application
2. **Markdown Format**: View `traceability_matrix.md` in any Markdown viewer or text editor

## Generating Your Own

Run pytest with the GxP plugin to generate your own traceability matrix:

```bash
pytest --gxp --gxp-spec-files=examples/gxp_spec_files --gxp-report-files=examples/gxp_report_files
```

The traceability matrix will be generated in both formats in the specified report directory.

