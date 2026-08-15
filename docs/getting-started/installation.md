# Installation

## Requirements

- Python 3.8 or higher
- pytest 7.0.0 or higher

## Add to your project

```bash
uv add --dev pytest-gxp
```

This records the dependency in your `pyproject.toml` and pins it in `uv.lock`:

```toml
[dependency-groups]
dev = [
    "pytest-gxp>=0.2.0",
]
```

For a validated system, pin the exact version you qualified (`pytest-gxp==0.2.0`)
and commit `uv.lock` — the lockfile is the reproducible dependency closure your
qualification record refers to.

??? note "Alternative: pip"

    ```bash
    pip install pytest-gxp
    ```

## Optional Dependencies

Install optional features as needed:

### Evidence Capture (text-to-image conversion)

```bash
uv add --dev "pytest-gxp[evidence]"
```

### PDF Report Generation

```bash
uv add --dev "pytest-gxp[pdf]"
```

### All Optional Dependencies

```bash
uv add --dev "pytest-gxp[all]"
```

??? note "Alternative: pip"

    ```bash
    pip install "pytest-gxp[evidence]"
    pip install "pytest-gxp[pdf]"
    pip install "pytest-gxp[all]"
    ```

## Development Installation

For development, install with dev dependencies:

```bash
git clone https://github.com/wshayes/pytest_gxp.git
cd pytest_gxp
uv sync --dev
```

This will install:

- The plugin in editable mode
- Development dependencies (pytest, ruff, pre-commit, mkdocs)

Prefix commands with `uv run` to use the project environment, e.g. `uv run pytest`.

??? note "Alternative: pip"

    ```bash
    pip install -e ".[dev]"
    ```

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
