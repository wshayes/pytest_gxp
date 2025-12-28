# Examples

This section provides complete examples of using the Pytest GxP plugin.

## Example Project Structure

```
project/
├── gxp_spec_files/
│   ├── design_specification.md
│   ├── functional_specification.md
│   ├── user_specification.md
│   └── installation_specification.md
├── tests/
│   └── test_example.py
└── pytest.ini
```

## Quick Example

See the `examples/` directory in the repository for a complete working example.

## Specification Examples

| Specification | ID Format | Qualification Phase |
|---------------|-----------|---------------------|
| [Design Specification](design-spec.md) | `DS-XXX` | OQ |
| [Functional Specification](functional-spec.md) | `FS-XXX` | OQ |
| [User Specification](user-spec.md) | `US-XXX` | PQ |
| [Installation Specification](installation-spec.md) | `IS-XXX` | IQ |

## Running the Examples

```bash
cd examples
pytest --gxp \
  --gxp-spec-files=gxp_spec_files \
  --gxp-report-files=gxp_report_files
```

## Next Steps

- Review the [Specification Format](../user-guide/specification-format.md)
- Learn about [Running Tests](../user-guide/running-tests.md)
- Understand [Reports](../user-guide/reports.md)

