# Pytest GxP Plugin - Justfile
# Run `just` to see all available commands

# Default recipe - show available commands
default:
    @just --list

# Install the package in development mode with all dev dependencies
install:
    pip install -e ".[dev]"

# Install pre-commit hooks
install-hooks:
    pre-commit install

# Run pre-commit on all files
lint:
    pre-commit run --all-files

# Format code with ruff
format:
    ruff format .

# Check code with ruff (linting)
check:
    ruff check .

# Fix auto-fixable linting issues
fix:
    ruff check --fix .

# Run all code quality checks (format + check)
quality: format check

# Run tests
test:
    pytest

# Run tests with verbose output
test-verbose:
    pytest -v

# Run tests with coverage
test-coverage:
    pytest --cov=pytest_gxp --cov-report=html --cov-report=term

# Run tests with GxP mode using examples
test-gxp:
    pytest --gxp --gxp-spec-files=examples/gxp_spec_files --gxp-report-files=examples/gxp_report_files

# Clean build artifacts
clean:
    rm -rf build/
    rm -rf dist/
    rm -rf *.egg-info
    rm -rf .pytest_cache
    rm -rf .ruff_cache
    rm -rf htmlcov/
    rm -rf .coverage
    rm -rf docs/site/
    find . -type d -name __pycache__ -exec rm -r {} +
    find . -type f -name "*.pyc" -delete

# Build the package
build:
    python -m build

# Build source distribution only
build-sdist:
    python -m build --sdist

# Build wheel only
build-wheel:
    python -m build --wheel

# Check the built package
check-package:
    twine check dist/*

# Upload to TestPyPI (for testing)
publish-test:
    python -m build
    twine upload --repository testpypi dist/*

# Upload to PyPI (production)
publish:
    python -m build
    twine upload dist/*

# Full release process: clean, build, check, and publish
release: clean build check-package
    @echo "Ready to publish. Run 'just publish' to upload to PyPI"

# Serve documentation locally
docs-serve:
    @if command -v uv > /dev/null 2>&1; then \
        uv pip install -e ".[dev]" --quiet > /dev/null 2>&1; \
        uv run python -m mkdocs serve --dev-addr=0.0.0.0:8089; \
    elif command -v mkdocs > /dev/null 2>&1; then \
        mkdocs serve; \
    else \
        echo "Error: mkdocs not found."; \
        echo "Install dev dependencies with:"; \
        echo "  uv pip install -e '.[dev]'" ; \
        echo "  or" ; \
        echo "  pip install -e '.[dev]'"; \
        exit 1; \
    fi

# Build documentation
docs-build:
    @if command -v uv > /dev/null 2>&1; then \
        uv pip install -e ".[dev]" --quiet > /dev/null 2>&1; \
        uv run python -m mkdocs build; \
    elif command -v mkdocs > /dev/null 2>&1; then \
        mkdocs build; \
    else \
        echo "Error: mkdocs not found."; \
        echo "Install dev dependencies with:"; \
        echo "  uv pip install -e '.[dev]'" ; \
        echo "  or" ; \
        echo "  pip install -e '.[dev]'"; \
        exit 1; \
    fi

# Clean and rebuild documentation
docs-clean:
    @if command -v uv > /dev/null 2>&1; then \
        uv pip install -e ".[dev]" --quiet > /dev/null 2>&1; \
        rm -rf docs/site/ && uv run python -m mkdocs build; \
    elif command -v mkdocs > /dev/null 2>&1; then \
        rm -rf docs/site/ && mkdocs build; \
    else \
        echo "Error: mkdocs not found."; \
        echo "Install dev dependencies with:"; \
        echo "  uv pip install -e '.[dev]'" ; \
        echo "  or" ; \
        echo "  pip install -e '.[dev]'"; \
        exit 1; \
    fi

# Deploy documentation to GitHub Pages (via GitHub Actions)
docs-deploy:
    @echo "Documentation will be deployed via GitHub Actions on push to main"
    @echo "To trigger manually, push changes or use GitHub Actions UI"

# Convert markdown reports to PDF (requires pdf dependencies)
docs-pdf:
    @if command -v uv > /dev/null 2>&1; then \
        uv pip install -e ".[pdf]" --quiet > /dev/null 2>&1; \
        echo "Converting markdown reports to PDF..."; \
        uv run python -c "from pathlib import Path; from pytest_gxp.report import CSVValidationReport; import json; r = CSVValidationReport(); f = Path('examples/gxp_report_files/csv_validation_report.json'); d = json.load(open(f)); r.report_data = d; r.write_pdf(Path('examples/gxp_report_files/csv_validation_report.pdf'))" && \
        echo "PDF generated: examples/gxp_report_files/csv_validation_report.pdf"; \
    else \
        echo "Error: uv not found. Install weasyprint and markdown:"; \
        echo "  pip install weasyprint markdown"; \
        exit 1; \
    fi

# Run all checks before committing (format, check, test)
pre-commit: quality test

# Show project information
info:
    @echo "Project: pytest-gxp"
    @grep -E "^version = " pyproject.toml | sed 's/version = /Version: /' | sed 's/"//g' || echo "Version: (check pyproject.toml)"
    @python --version
    @pytest --version 2>/dev/null || echo "pytest: not installed"
    @ruff --version 2>/dev/null || echo "ruff: not installed"

# Show help
help:
    @just --list

