# Contributing

Thank you for your interest in contributing to Pytest GxP!

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/pytest_gxp.git
   cd pytest_gxp
   ```
3. Install in development mode:
   ```bash
   uv sync --dev
   ```
   (Alternative without uv: `pip install -e ".[dev]"`)
4. Set up pre-commit hooks:
   ```bash
   uv run pre-commit install
   ```

## Code Style

This project uses:
- **Ruff** for linting and formatting
- **Pre-commit** hooks to enforce code quality

Before committing, ensure:
- Code is formatted: `uv run ruff format .`
- Linting passes: `uv run ruff check .`
- All tests pass: `uv run pytest`

## Documentation

Documentation is built with Material for MkDocs. To build locally:

```bash
uv run mkdocs serve
```

Then visit `http://127.0.0.1:8000` to view the documentation.

## Submitting Changes

1. Create a feature branch
2. Make your changes
3. Ensure tests pass and code is formatted
4. Submit a pull request

## Reporting Issues

Please use the GitHub issue tracker to report bugs or request features.

