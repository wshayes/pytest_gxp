# CLI Tools

pytest-gxp includes two command-line tools that are installed alongside the plugin to help manage GxP test development.

## gxp_test_stubs

Generate pytest test stubs for GxP specification requirements.

### Usage

```bash
gxp_test_stubs [OPTIONS]
```

### Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--spec-dir` | `-s` | `gxp_spec_files` | Directory containing specification files |
| `--output-dir` | `-o` | `tests` | Directory to write test stubs |
| `--test-dir` | `-t` | Same as output-dir | Directory to scan for existing tests |
| `--prefix` | `-p` | `test_gxp_` | Prefix for generated test files |
| `--force` | `-f` | False | Overwrite existing test stub files |
| `--dry-run` | `-n` | False | Show what would be generated without writing files |
| `--verbose` | `-v` | False | Enable verbose output |

### Examples

```bash
# Generate stubs for all specs in default locations
gxp_test_stubs

# Generate stubs from custom spec directory
gxp_test_stubs -s docs/specifications -o tests/gxp

# Preview what would be generated
gxp_test_stubs --dry-run --verbose

# Force overwrite existing stub files
gxp_test_stubs --force
```

### Generated Test Format

Each generated test stub includes:

- `@pytest.mark.gxp` marker
- `@pytest.mark.requirements([...])` marker linking to the requirement ID
- Docstring with requirement details
- Step comments extracted from requirement description
- `NotImplementedError` placeholder

Example generated stub:

```python
@pytest.mark.gxp
@pytest.mark.requirements(["FS-001"])
def test_fs_001():
    """Test FS-001: User Authentication

    The system shall authenticate users via username and password.

    Requirements: FS-001
    """
    # Step 1: User enters valid credentials
    # Step 2: System validates against database
    # Step 3: Session is created on success

    # TODO: Implement test for this requirement
    raise NotImplementedError("Test not yet implemented")
```

### Output Files

Test stubs are organized by specification type following the IQ, OQ, PQ qualification phases:

| Specification Type | Output File | Phase |
|-------------------|-------------|-------|
| Installation | `test_gxp_installation.py` | IQ |
| Design | `test_gxp_design.py` | OQ |
| Functional | `test_gxp_functional.py` | OQ |
| User | `test_gxp_user.py` | PQ |

---

## gxp_req_coverage

Check GxP requirement coverage and test identifier uniqueness.

### Usage

```bash
gxp_req_coverage [OPTIONS]
```

### Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--spec-dir` | `-s` | `gxp_spec_files` | Directory containing specification files |
| `--test-dir` | `-t` | `tests` | Directory containing test files |
| `--output` | `-o` | None | Write report to file (markdown format) |
| `--strict` | `-S` | False | Exit with error code if any issues found |
| `--verbose` | `-v` | False | Enable verbose output |
| `--json` | | False | Output results as JSON |

### Examples

```bash
# Basic coverage check
gxp_req_coverage

# Check with custom directories
gxp_req_coverage -s docs/specs -t tests/gxp

# Verbose output with details
gxp_req_coverage --verbose

# Generate markdown report
gxp_req_coverage -o coverage_report.md

# JSON output for CI/CD integration
gxp_req_coverage --json

# Strict mode (exit code 1 if issues found)
gxp_req_coverage --strict
```

### Checks Performed

1. **Duplicate Test Names**: Identifies test functions with the same name across different files
2. **Missing GxP Marker**: Tests with `@pytest.mark.requirements` but missing `@pytest.mark.gxp`
3. **Uncovered Requirements**: Requirements without any associated tests
4. **Stub-Only Requirements**: Requirements where all tests raise `NotImplementedError`
5. **Invalid Requirement IDs**: Tests referencing requirement IDs that don't exist in specifications

### Sample Output

```
============================================================
GxP Requirement Coverage Report
============================================================

Coverage Summary:
  Total Requirements:     13
  Fully Covered:          5 (38.5%)
  Stub Only:              2 (15.4%)
  No Tests:               6

Requirements Without Tests:
  - FS-003: Audit Logging
  - DS-001: User Authentication System

Requirements With Only Stub Tests:
  - FS-004: User Profile Management

Found 0 duplicate test name(s), 6 uncovered requirement(s), 2 stub-only requirement(s)
```

### JSON Output Format

```json
{
  "total_requirements": 13,
  "covered_requirements": 5,
  "uncovered_requirements": [
    {"id": "FS-003", "title": "Audit Logging"},
    {"id": "DS-001", "title": "User Authentication System"}
  ],
  "stub_only_requirements": [
    {"id": "FS-004", "title": "User Profile Management"}
  ],
  "duplicate_test_ids": {},
  "tests_without_gxp_marker": []
}
```

### CI/CD Integration

Use `--strict` mode in CI/CD pipelines to fail builds when coverage requirements aren't met:

```yaml
# GitHub Actions example
- name: Check GxP Coverage
  run: gxp_req_coverage --strict

# GitLab CI example
gxp_coverage:
  script:
    - gxp_req_coverage --strict --json > coverage.json
  artifacts:
    paths:
      - coverage.json
```

---

## Workflow Example

A typical workflow using both CLI tools:

```bash
# 1. Create specification files in gxp_spec_files/

# 2. Generate test stubs for all requirements
gxp_test_stubs --verbose

# 3. Implement the generated test stubs

# 4. Check coverage status
gxp_req_coverage --verbose

# 5. Run tests with GxP reporting
pytest --gxp
```
