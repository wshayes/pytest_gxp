# Parser API

The `SpecificationParser` class parses Markdown specification files.

## SpecificationParser

### Methods

#### `parse_file(file_path: Path) -> Specification`

Parse a single specification file.

**Parameters**:
- `file_path`: Path to the Markdown specification file

**Returns**: `Specification` object

#### `parse_directory(directory: Path) -> Dict[SpecType, Specification]`

Parse all specification files in a directory.

**Parameters**:
- `directory`: Path to directory containing specification files

**Returns**: Dictionary mapping specification types to `Specification` objects

## Example

```python
from pathlib import Path
from pytest_gxp.parser import SpecificationParser

parser = SpecificationParser()
spec = parser.parse_file(Path("functional_specification.md"))
```

