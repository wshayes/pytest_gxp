# CSV Validation Report JSON Format

The CSV Validation Summary Report is generated in JSON format to support programmatic processing and integration with other systems.

## Format Overview

The report is a JSON object containing metadata, specification information, test summaries, coverage data, and detailed test case information.

## JSON Schema

### Root Object

```json
{
  "report_metadata": { ... },
  "specifications": { ... },
  "test_summary": { ... },
  "coverage": { ... },
  "test_cases": [ ... ]
}
```

### report_metadata

Contains report generation information.

```json
{
  "title": "CSV Validation Summary Report",
  "generated_date": "2024-01-15T10:30:00",
  "version": "1.0"
}
```

**Fields:**
- `title` (string): Report title
- `generated_date` (string): ISO 8601 formatted generation timestamp
- `version` (string): Report format version

### specifications

Information about all specification documents.

```json
{
  "design_spec": {
    "title": "Design Specification",
    "version": "1.0",
    "requirement_count": 3
  },
  "functional_spec": {
    "title": "Functional Specification",
    "version": "1.0",
    "requirement_count": 4
  },
  "user_spec": {
    "title": "User Specification",
    "version": "1.0",
    "requirement_count": 3
  }
}
```

**Fields:**
- `design_spec` (object): Design specification metadata
- `functional_spec` (object): Functional specification metadata
- `user_spec` (object): User specification metadata

Each spec object contains:
- `title` (string): Specification title
- `version` (string): Specification version
- `requirement_count` (integer): Number of requirements in specification

### test_summary

Summary statistics of test execution.

```json
{
  "total_test_cases": 7,
  "passed": 6,
  "failed": 0,
  "skipped": 0,
  "not_executed": 1,
  "pass_rate": 85.7
}
```

**Fields:**
- `total_test_cases` (integer): Total number of test cases
- `passed` (integer): Number of passed tests
- `failed` (integer): Number of failed tests
- `skipped` (integer): Number of skipped tests
- `not_executed` (integer): Number of tests not yet executed
- `pass_rate` (float): Percentage of passed tests (0-100)

### coverage

Requirement coverage information.

```json
{
  "total_requirements": 7,
  "covered_requirements": 6,
  "coverage_percentage": 85.7,
  "uncovered_requirements": ["FS-004"]
}
```

**Fields:**
- `total_requirements` (integer): Total number of requirements
- `covered_requirements` (integer): Number of requirements with passing tests
- `coverage_percentage` (float): Percentage of requirements covered (0-100)
- `uncovered_requirements` (array of strings): List of requirement IDs not covered

### test_cases

Array of test case objects with detailed information.

```json
[
  {
    "id": "TEST-FS-001",
    "title": "Test FS-001: User Login Functionality",
    "requirements": ["FS-001"],
    "status": "PASSED",
    "spec_type": "Functional"
  }
]
```

**Fields:**
- `id` (string): Test case identifier
- `title` (string): Test case title
- `requirements` (array of strings): List of requirement IDs this test covers
- `status` (string): Test execution status (PASSED, FAILED, SKIPPED, Not Executed)
- `spec_type` (string): Specification type (Design, Functional, User)

## Complete Example

See [examples/csv-validation-report-example.json](../examples/files/csv_validation_report.json) for a complete example.

## Usage

### Programmatic Access

```python
import json

with open('csv_validation_report.json') as f:
    report = json.load(f)
    
print(f"Pass rate: {report['test_summary']['pass_rate']}%")
print(f"Coverage: {report['coverage']['coverage_percentage']}%")
```

### Integration

The JSON format supports:
- Automated report processing
- Integration with CI/CD pipelines
- Dashboard visualization
- Compliance reporting systems
- Data analysis tools

### Validation

The JSON follows standard JSON schema and can be validated using JSON Schema validators.

## Status Values

Test case status values:
- **PASSED** - Test executed and passed
- **FAILED** - Test executed and failed
- **SKIPPED** - Test skipped (e.g., due to dependencies)
- **Not Executed** - Test defined but not yet executed

## Best Practices

1. **Version Control**: Track report versions for audit purposes
2. **Timestamps**: Use ISO 8601 format for dates
3. **Consistency**: Maintain consistent status values
4. **Completeness**: Ensure all test cases are included
5. **Accuracy**: Verify counts match actual test execution

## Related Formats

- [Traceability Matrix Format](traceability-format.md)
- [Markdown Report Format](reports.md)

