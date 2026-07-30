"""Pytest GxP Plugin - GAMP5 CSV Validation Support"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("pytest-gxp")
except PackageNotFoundError:  # pragma: no cover - package not installed
    __version__ = "0.0.0+unknown"
