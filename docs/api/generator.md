# Generator API

The `TestCaseGenerator` class generates test cases from specifications.

## TestCaseGenerator

### Methods

#### `generate_test_cases(design_spec, functional_spec) -> List[TestCase]`

Generate test cases from design and functional specifications.

**Parameters**:
- `design_spec`: Optional `Specification` object
- `functional_spec`: Optional `Specification` object

**Returns**: List of `TestCase` objects

#### `generate_pytest_code(test_cases, output_path) -> None`

Generate pytest test code from test cases.

**Parameters**:
- `test_cases`: List of `TestCase` objects
- `output_path`: Path where test code should be written

## Example

```python
from pathlib import Path
from pytest_gxp.generator import TestCaseGenerator
from pytest_gxp.parser import SpecificationParser

parser = SpecificationParser()
generator = TestCaseGenerator(parser)

specs = parser.parse_directory(Path("gxp_spec_files"))
test_cases = generator.generate_test_cases(
    specs.get(SpecType.DESIGN),
    specs.get(SpecType.FUNCTIONAL)
)
```

