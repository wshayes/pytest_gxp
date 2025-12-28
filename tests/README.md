# Test Suite

This directory contains comprehensive tests for the pytest-gxp plugin.

## Test Structure

- `conftest.py` - Pytest fixtures and configuration
- `test_parser.py` - Tests for the Markdown specification parser
- `test_generator.py` - Tests for test case generation
- `test_traceability.py` - Tests for traceability matrix generation
- `test_report.py` - Tests for CSV validation report generation
- `test_plugin.py` - Tests for pytest plugin hooks and integration

## Running Tests

### Run all tests
```bash
pytest tests/
```

### Run with coverage
```bash
pytest tests/ --cov=pytest_gxp --cov-report=html
```

### Run specific test file
```bash
pytest tests/test_parser.py
```

### Run specific test
```bash
pytest tests/test_parser.py::TestSpecificationParser::test_parse_file_design_spec
```

## Test Coverage

The test suite covers:
- ✅ Markdown parsing (design, functional, user specifications)
- ✅ Test case generation from specifications
- ✅ Traceability matrix generation
- ✅ CSV validation report generation
- ✅ Pytest plugin hooks and markers
- ✅ Edge cases and error handling

## Fixtures

Common fixtures are defined in `conftest.py`:
- `temp_dir` - Temporary directory for test files
- `sample_*_spec_content` - Sample markdown content
- `sample_*_spec_file` - Sample specification files
- `sample_requirement` - Sample requirement object
- `sample_specification` - Sample specification object
- `sample_test_case` - Sample test case object

## Notes

- Tests use temporary directories to avoid file system pollution
- All tests are designed to run independently
- Mock data is used where appropriate to isolate unit tests

