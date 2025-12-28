# Traceability Matrix Format

The traceability matrix is a critical component of GxP CSV validation, demonstrating the relationship between requirements and test cases.

## Format Overview

The traceability matrix is generated in two formats:
- **CSV format** (`traceability_matrix.csv`) - For programmatic processing and spreadsheet applications
- **Markdown format** (`traceability_matrix.md`) - For human-readable documentation

## CSV Format Specification

### File Structure

The CSV file uses comma-separated values with the following columns:

| Column Name | Description | Example |
|------------|-------------|---------|
| Test Case ID | Unique identifier for the test case | TEST-FS-001 |
| Test Case Title | Descriptive title of the test case | Test FS-001: User Login Functionality |
| Requirement ID | The requirement identifier being tested | FS-001 |
| Requirement Title | Title of the requirement | User Login Functionality |
| Specification Type | Type of specification (Design, Functional, or User) | Functional |
| User Requirement ID | Related user requirement ID (if applicable) | US-001 |
| Status | Test execution status | Passed, Failed, Not Executed, Skipped |

### CSV Example

```csv
Test Case ID,Test Case Title,Requirement ID,Requirement Title,Specification Type,User Requirement ID,Status
TEST-FS-001,Test FS-001: User Login Functionality,FS-001,User Login Functionality,Functional,US-001,Passed
TEST-FS-002,Test FS-002: Input Data Validation,FS-002,Input Data Validation,Functional,US-002,Passed
```

### Status Values

- **Passed** - Test case executed and passed
- **Failed** - Test case executed and failed
- **Not Executed** - Test case defined but not yet executed
- **Skipped** - Test case skipped (e.g., due to missing dependencies)

## Markdown Format Specification

### Structure

The Markdown format includes:

1. **Header Section**
   - Project name
   - Generation date
   - Version information

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
**Generated:** 2024-01-15  
**Version:** 1.0

## Traceability Data

| Test Case ID | Test Case Title | Requirement ID | ... |
|--------------|----------------|----------------|-----|
| TEST-FS-001 | Test FS-001: User Login | FS-001 | ... |

## Coverage Summary

- **Total Requirements:** 7
- **Covered Requirements:** 6
- **Coverage Percentage:** 85.7%
```

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

The traceability matrix status is automatically updated when tests are executed with the `--gxp` flag. You can also manually update the CSV file if needed.

### Coverage Analysis

Use the coverage summary to:
- Identify untested requirements
- Track validation progress
- Generate compliance reports

## Best Practices

1. **Regular Updates**: Update the matrix after each test execution
2. **Status Accuracy**: Ensure test status accurately reflects execution results
3. **Requirement Mapping**: Verify all requirements have corresponding test cases
4. **User Requirements**: Map user requirements to functional/design requirements when applicable
5. **Documentation**: Keep notes section updated with relevant information

## Integration

The traceability matrix integrates with:
- CSV Validation Summary Report
- Test execution results
- Requirement specifications
- Compliance documentation

See the [Examples](../examples/traceability-example.md) section for complete examples.

