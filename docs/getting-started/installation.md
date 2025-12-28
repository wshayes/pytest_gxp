# Installation

## Requirements

- Python 3.8 or higher
- pytest 7.0.0 or higher

## Install from PyPI

```bash
pip install pytest-gxp
```

## Install with uv

```bash
uv add pytest-gxp
```

## Optional Dependencies

Install optional features as needed:

### Evidence Capture (text-to-image conversion)

```bash
pip install pytest-gxp[evidence]
```

### PDF Report Generation

```bash
pip install pytest-gxp[pdf]
```

### All Optional Dependencies

```bash
pip install pytest-gxp[all]
```

## Development Installation

For development, install with dev dependencies:

```bash
git clone https://github.com/wshayes/pytest_gxp.git
cd pytest_gxp
pip install -e ".[dev]"
```

Or with uv:

```bash
uv sync --dev
```

This will install:

- The plugin in editable mode
- Development dependencies (pytest, ruff, pre-commit, mkdocs)

## Verify Installation

Verify the plugin is installed correctly:

```bash
pytest --version
pytest --help | grep gxp
```

You should see the GxP options in the help output:

```
GxP CSV Validation:
  --gxp                 Enable GxP CSV validation mode
  --gxp-spec-files=GXP_SPEC_FILES
                        Path to GxP specification files directory
  --gxp-report-files=GXP_REPORT_FILES
                        Path to GxP report files directory
  --gxp-qualification-type={IQ,OQ,PQ}
                        Qualification type: IQ, OQ, or PQ
  ...
```
