# Reports API

The `CSVValidationReport` class generates CSV validation summary reports.

## CSVValidationReport

### Methods

#### `generate_report(test_cases, design_spec, functional_spec, user_spec, traceability_matrix, test_results, output_path, validation_metadata, all_requirements, requirement_tests) -> Dict`

Generate CSV validation summary report.

**Parameters**:

- `test_cases`: List of `TestCase` objects
- `design_spec`: Optional `Specification` object
- `functional_spec`: Optional `Specification` object
- `user_spec`: Optional `Specification` object
- `traceability_matrix`: Optional `TraceabilityMatrix` object
- `test_results`: Optional dictionary mapping test IDs to status
- `output_path`: Optional path for JSON output
- `validation_metadata`: Optional `ValidationMetadata` with qualification info and approvals
- `all_requirements`: Optional list of all requirements
- `requirement_tests`: Optional mapping of requirement IDs to test node IDs

**Returns**: Dictionary containing report data

#### `write_report(output_path) -> None`

Write report to JSON file.

**Parameters**:

- `output_path`: Path for JSON output

#### `write_markdown_report(output_path, evidence_items) -> None`

Write report in Markdown format with optional evidence.

**Parameters**:

- `output_path`: Path for Markdown output
- `evidence_items`: Optional list of `EvidenceItem` objects

#### `write_csv_report(output_path) -> None`

Write report in CSV format.

**Parameters**:

- `output_path`: Path for CSV output

#### `write_pdf_report(output_path, evidence_items) -> None`

Write report in PDF format with optional evidence.

**Parameters**:

- `output_path`: Path for PDF output
- `evidence_items`: Optional list of `EvidenceItem` objects

**Requires**: `pip install pytest-gxp[pdf]`

## Example

```python
from pathlib import Path
from pytest_gxp.report import CSVValidationReport
from pytest_gxp.markdown_format import ValidationMetadata, ApprovalSignature, QualificationType

# Create validation metadata
metadata = ValidationMetadata(
    qualification_type=QualificationType.OQ,
    software_name="My Application",
    software_version="1.0.0",
    project_name="My Project",
    validation_date="2024-01-01",
    tester=ApprovalSignature(name="John Doe", role="Tester", date="2024-01-01"),
    reviewer=ApprovalSignature(name="Jane Smith", role="Reviewer", date="2024-01-01"),
    approver=ApprovalSignature(name="Bob Johnson", role="Approver", date="2024-01-01"),
)

# Generate report
report = CSVValidationReport()
report_data = report.generate_report(
    test_cases,
    design_spec,
    functional_spec,
    user_spec,
    traceability_matrix,
    test_results,
    Path("csv_validation_report.json"),
    validation_metadata=metadata,
)

# Write in multiple formats
report.write_report(Path("csv_validation_report.json"))
report.write_markdown_report(Path("csv_validation_report.md"), evidence_items=evidence_items)
report.write_csv_report(Path("csv_validation_report.csv"))
report.write_pdf_report(Path("csv_validation_report.pdf"), evidence_items=evidence_items)
```
