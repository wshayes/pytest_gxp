# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

pytest-gxp is a Pytest plugin for GAMP5 GxP Computer System Validation (CSV). It parses Markdown-based specifications (Installation, Design, Functional, User), links tests to requirements via markers, generates traceability matrices, and produces IQ/OQ/PQ qualification reports with approval signatures.

## Common Commands

```bash
# Install for development
pip install -e ".[dev]"
# or with uv
uv sync --dev

# Run all tests
pytest
just test

# Run single test file
pytest tests/test_parser.py

# Run single test
pytest tests/test_parser.py::test_parse_design_spec

# Run tests with coverage
just test-coverage

# Run tests in GxP mode with example specs
just test-gxp

# Lint and format
just lint                    # Run pre-commit hooks on all files
just format                  # Format with ruff
just check                   # Lint check only
just fix                     # Auto-fix linting issues

# Build package
just build

# Serve documentation locally
just docs-serve
```

## Architecture

### Data Flow
```
Markdown Specs → Parser → Specification Objects → Generator → Test Cases
                                                      ↓
                              Test Markers → Requirement Mapping → Reports
                                                      ↓
                                           TraceabilityMatrix → Coverage Reports
```

### Core Modules (in `pytest_gxp/`)

- **plugin.py**: Pytest hooks - CLI options, marker-based test-to-requirement mapping, `gxp_evidence` fixture, report generation
- **config.py**: Configuration loading from CLI, pyproject.toml, pytest.ini with priority merging
- **parser.py**: `SpecificationParser` - Parses Markdown specs, extracts requirements using regex
- **markdown_format.py**: Data classes (`Requirement`, `TestCase`, `Specification`, `ValidationMetadata`, `ApprovalSignature`, `EvidenceItem`), enums (`SpecType`, `QualificationType`, `EvidenceType`)
- **generator.py**: `TestCaseGenerator` - Converts requirements to TestCase metadata objects
- **traceability.py**: `TraceabilityMatrix` - Links tests to requirements, dual coverage metrics
- **report.py**: `CSVValidationReport` - Generates IQ/OQ/PQ reports with approvals and evidence in JSON/Markdown/PDF
- **evidence.py**: `EvidenceCollector` - Captures screenshots, directory listings, command output as objective evidence; utility functions `text_to_image()`, `directory_listing_to_image()`

### Key Features

**Marker-Based Test Mapping**: Tests link to requirements via `@pytest.mark.requirements(["FS-001"])` marker, not naming conventions.

**Dual Coverage Metrics**:
- Test Pass Rate: passed / (passed + failed)
- Requirement Coverage Rate: requirements with tests / total requirements

**IQ/OQ/PQ Support**: Qualification type with approval signatures (Tester, Reviewer, Approver).

**Objective Evidence**: Capture screenshots, directory listings, command output as images for validation reports. Use `gxp_evidence` fixture in tests.

**Configuration Priority**: CLI > pyproject.toml > pytest.ini > defaults

### Plugin Entry Point

Registered as `gxp` via `pytest11` in setup.py. Usage:
```bash
pytest --gxp \
    --gxp-spec-files=<path> \
    --gxp-report-files=<path> \
    --gxp-qualification-type=OQ \
    --gxp-software-version=1.0.0 \
    --gxp-tester="Name" \
    --gxp-strict-coverage
```

### Test Markers
```python
@pytest.mark.gxp                              # Mark as GxP validation test
@pytest.mark.requirements(["FS-001", "DS-002"])  # Associate with requirement IDs
```

### Configuration (pyproject.toml)
```toml
[tool.pytest-gxp]
spec-files = "gxp_spec_files"
report-files = "gxp_report_files"
qualification-type = "OQ"
software-version = "1.0.0"
project-name = "My Application"
strict-coverage = false
tester-name = "John Doe"
reviewer-name = "Jane Smith"
approver-name = "Bob Johnson"
```

## Code Style

- **Formatter/Linter**: Ruff (line length 100, Python 3.8+ target)
- **Rules**: E, W, F, I (isort), B, C4, UP
- **Quotes**: Double quotes, 4-space indent
- **Pre-commit**: Auto-runs ruff format and lint on commit
