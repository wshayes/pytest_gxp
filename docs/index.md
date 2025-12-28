# Pytest GxP Plugin

Welcome to the Pytest GxP Plugin documentation!

Pytest GxP is a pytest plugin that supports **GAMP5 GxP product Computer System Validation (CSV)** validation of Custom Applications with Requirements, Tests, Traceability Matrices, and Validation Reports.

## Features

- **Markdown-based Specifications**: Define Installation, Design, Functional, and User specifications in Markdown
- **Marker-based Test Mapping**: Link tests to requirements using `@pytest.mark.requirements()`
- **Traceability Matrix**: Automatic generation linking tests to requirements (CSV, JSON, Markdown)
- **Validation Reports**: IQ/OQ/PQ qualification reports with approval signatures (CSV, JSON, Markdown, PDF)
- **Objective Evidence**: Capture screenshots, directory listings, and command output during tests
- **Requirement Coverage**: Track and enforce test coverage of requirements
- **Flexible Configuration**: CLI options, pyproject.toml, or pytest.ini
- **GAMP5 Compliant**: Follows GAMP5 guidelines for CSV validation

## Quick Start

```bash
# Install the plugin
pip install pytest-gxp

# Run with GxP mode
pytest --gxp
```

## Workflow

1. **Create Specifications**: Write Installation, Design, Functional, and User specifications in Markdown
2. **Write Tests**: Create pytest tests with `@pytest.mark.requirements()` markers
3. **Capture Evidence**: Use the `gxp_evidence` fixture to capture objective evidence
4. **Run Tests**: Execute `pytest --gxp` with configuration options
5. **Generate Reports**: Traceability matrices and validation reports are created automatically

## Qualification Phases

| Phase | Specification Type | ID Format | Description |
|-------|-------------------|-----------|-------------|
| IQ | Installation | `IS-XXX` | Verify software is correctly installed |
| OQ | Design, Functional | `DS-XXX`, `FS-XXX` | Verify software operates according to specs |
| PQ | User | `US-XXX` | Verify software meets user requirements |

## Example

```python
import pytest

@pytest.mark.gxp
@pytest.mark.requirements(["FS-001"])
def test_user_login(gxp_evidence, driver):
    """Test user login functionality."""
    # Capture evidence
    gxp_evidence.capture_screenshot(driver.get_screenshot_as_png(), "Login screen")

    # Test implementation
    driver.find_element("id", "username").send_keys("user")
    driver.find_element("id", "password").send_keys("pass")
    driver.find_element("id", "submit").click()

    assert driver.current_url.endswith("/dashboard")
```

## What is GxP CSV Validation?

GxP (Good Practice) refers to regulations and guidelines that apply to life sciences organizations. Computer System Validation (CSV) ensures that computer systems used in regulated environments are fit for their intended use and comply with regulatory requirements.

The GAMP5 (Good Automated Manufacturing Practice) framework provides guidance for CSV, including:

- Requirements specification (Design, Functional, User)
- Test planning and execution
- Traceability between requirements and tests
- Validation documentation and reports

## Generated Outputs

When running with `--gxp`, the plugin generates:

| Output | Formats | Description |
|--------|---------|-------------|
| Traceability Matrix | CSV, JSON, MD | Links tests to requirements |
| Validation Report | CSV, JSON, MD, PDF | IQ/OQ/PQ qualification report |
| Requirement Coverage | MD | Coverage analysis |
| Evidence Manifest | JSON | Evidence metadata |

## Documentation Structure

- **[Getting Started](getting-started/installation.md)**: Installation and basic setup
- **[Configuration](getting-started/configuration.md)**: CLI options and configuration files
- **[User Guide](user-guide/specification-format.md)**: How to use the plugin
- **[Examples](examples/overview.md)**: Example specifications and usage
- **[API Reference](api/parser.md)**: Detailed API documentation

## Contributing

We welcome contributions! See our [Contributing Guide](contributing.md) for details.

## License

This project is licensed under the MIT License.
