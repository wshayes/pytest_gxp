# Traceability API

The `TraceabilityMatrix` class generates traceability matrices.

## TraceabilityMatrix

### Methods

#### `generate_matrix(test_cases, design_spec, functional_spec, user_spec, output_path) -> List[Dict]`

Generate traceability matrix linking test cases to requirements.

**Parameters**:
- `test_cases`: List of `TestCase` objects
- `design_spec`: Optional `Specification` object
- `functional_spec`: Optional `Specification` object
- `user_spec`: Optional `Specification` object
- `output_path`: Optional path for CSV output

**Returns**: List of dictionaries representing matrix rows

#### `write_csv(output_path) -> None`

Write traceability matrix to CSV file.

**Parameters**:
- `output_path`: Path for CSV output

#### `update_test_status(test_case_id, status) -> None`

Update the status of a test case in the matrix.

**Parameters**:
- `test_case_id`: Test case identifier
- `status`: Test status (e.g., "Passed", "Failed")

#### `get_coverage_report() -> Dict`

Generate coverage report from traceability matrix.

**Returns**: Dictionary with coverage statistics

## Example

```python
from pytest_gxp.traceability import TraceabilityMatrix

matrix = TraceabilityMatrix()
matrix_data = matrix.generate_matrix(
    test_cases,
    design_spec,
    functional_spec,
    user_spec,
    Path("traceability_matrix.csv")
)
```

