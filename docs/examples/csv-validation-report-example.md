# CSV Validation Report JSON Example

This page provides a complete example of the CSV Validation Report in JSON format.

## Complete Example

See the complete example file: [csv_validation_report.json](files/csv_validation_report.json)

## Structure Overview

```json
{
  "report_metadata": {
    "title": "CSV Validation Summary Report",
    "generated_date": "2024-01-15T10:30:00",
    "version": "1.0"
  },
  "specifications": {
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
  },
  "test_summary": {
    "total_test_cases": 7,
    "passed": 6,
    "failed": 0,
    "skipped": 0,
    "not_executed": 1,
    "pass_rate": 85.7
  },
  "coverage": {
    "total_requirements": 7,
    "covered_requirements": 6,
    "coverage_percentage": 85.7,
    "uncovered_requirements": ["FS-004"]
  },
  "test_cases": [
    {
      "id": "TEST-FS-001",
      "title": "Test FS-001: User Login Functionality",
      "requirements": ["FS-001"],
      "status": "PASSED",
      "spec_type": "Functional"
    }
  ]
}
```

## Using the Example

1. **View the JSON**: Open `csv_validation_report.json` in any text editor or JSON viewer
2. **Validate**: Use a JSON validator to ensure the format is correct
3. **Process**: Use the JSON in your own scripts or tools

## Generating Your Own

Run pytest with the GxP plugin to generate your own validation report:

```bash
pytest --gxp --gxp-spec-files=examples/gxp_spec_files --gxp-report-files=examples/gxp_report_files
```

The validation report will be generated in JSON format in the specified report directory.

## Programmatic Access

```python
import json

# Load the report
with open('csv_validation_report.json') as f:
    report = json.load(f)

# Access test summary
print(f"Total tests: {report['test_summary']['total_test_cases']}")
print(f"Pass rate: {report['test_summary']['pass_rate']}%")

# Access coverage
print(f"Coverage: {report['coverage']['coverage_percentage']}%")
print(f"Uncovered: {report['coverage']['uncovered_requirements']}")

# Iterate test cases
for test_case in report['test_cases']:
    print(f"{test_case['id']}: {test_case['status']}")
```

