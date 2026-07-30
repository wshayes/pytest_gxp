"""Configuration management for pytest-gxp plugin."""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


@dataclass
class GxPConfig:
    """Configuration for pytest-gxp plugin."""

    enabled: bool = False
    spec_files: str = "gxp_spec_files"
    report_files: str = "gxp_report_files"
    qualification_type: str = "OQ"
    software_version: str = ""
    project_name: str = ""
    strict_coverage: bool = False
    strict: bool = False

    # Path to a JSON map of {nodeid-or-requirement-id: deviation ref}
    deviations: str = ""

    # Output/evidence fields
    output_formats: str = "csv,json,md,pdf"
    evidence_thumbnails: bool = True

    # Source provenance overrides (empty = derive from git)
    source_commit: str = ""
    source_tag: str = ""

    # Approval fields
    tester_name: str = ""
    tester_date: str = ""
    reviewer_name: str = ""
    reviewer_date: str = ""
    approver_name: str = ""
    approver_date: str = ""


# Fields whose ini values arrive as strings and must be coerced to bool
_BOOLEAN_FIELDS = frozenset({"strict_coverage", "strict", "evidence_thumbnails"})

# Fields only ever set by a ``store_true`` CLI option: a ``False`` from the CLI layer
# means "flag not passed", not an override of an ini/pyproject value.
_CLI_STORE_TRUE_FIELDS = frozenset({"strict_coverage", "strict"})


def load_config_from_pyproject(root_path: Path) -> Dict[str, Any]:
    """Load configuration from pyproject.toml.

    Args:
        root_path: The root directory containing pyproject.toml

    Returns:
        Dictionary of configuration values from [tool.pytest-gxp] section
    """
    pyproject_path = root_path / "pyproject.toml"
    if not pyproject_path.exists():
        return {}

    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        return data.get("tool", {}).get("pytest-gxp", {})
    except Exception:
        return {}


def load_config_from_ini(config) -> Dict[str, Any]:
    """Load configuration from pytest.ini or pyproject.toml [tool.pytest.ini_options].

    Args:
        config: pytest Config object

    Returns:
        Dictionary of configuration values from ini options
    """
    result = {}

    # Map ini option names to config keys
    ini_options = [
        ("gxp_spec_files", "spec_files"),
        ("gxp_report_files", "report_files"),
        ("gxp_qualification_type", "qualification_type"),
        ("gxp_software_version", "software_version"),
        ("gxp_project_name", "project_name"),
        ("gxp_strict_coverage", "strict_coverage"),
        ("gxp_strict", "strict"),
        ("gxp_deviations", "deviations"),
        ("gxp_output_formats", "output_formats"),
        ("gxp_evidence_thumbnails", "evidence_thumbnails"),
        ("gxp_source_commit", "source_commit"),
        ("gxp_source_tag", "source_tag"),
        ("gxp_tester_name", "tester_name"),
        ("gxp_tester_date", "tester_date"),
        ("gxp_reviewer_name", "reviewer_name"),
        ("gxp_reviewer_date", "reviewer_date"),
        ("gxp_approver_name", "approver_name"),
        ("gxp_approver_date", "approver_date"),
    ]

    for ini_name, config_key in ini_options:
        try:
            value = config.getini(ini_name)
            if value:
                if config_key in _BOOLEAN_FIELDS:
                    if isinstance(value, str):
                        result[config_key] = value.lower() in ("true", "1", "yes")
                    else:
                        result[config_key] = bool(value)
                else:
                    result[config_key] = value
        except (ValueError, KeyError):
            pass

    return result


def merge_config(
    cli_options: Dict[str, Any],
    pyproject_config: Dict[str, Any],
    ini_config: Dict[str, Any],
) -> GxPConfig:
    """Merge configuration from all sources.

    Priority (highest to lowest):
    1. CLI options
    2. pyproject.toml [tool.pytest-gxp]
    3. pytest.ini options
    4. Default values

    Args:
        cli_options: Options from command line
        pyproject_config: Options from pyproject.toml
        ini_config: Options from pytest.ini

    Returns:
        Merged GxPConfig instance
    """
    # Start with defaults
    config = GxPConfig()

    # Map pyproject.toml keys (with hyphens) to dataclass fields (with underscores)
    key_mapping = {
        "spec-files": "spec_files",
        "report-files": "report_files",
        "qualification-type": "qualification_type",
        "software-version": "software_version",
        "project-name": "project_name",
        "strict-coverage": "strict_coverage",
        "strict": "strict",
        "deviations": "deviations",
        "output-formats": "output_formats",
        "evidence-thumbnails": "evidence_thumbnails",
        "source-commit": "source_commit",
        "source-tag": "source_tag",
        "tester-name": "tester_name",
        "tester-date": "tester_date",
        "reviewer-name": "reviewer_name",
        "reviewer-date": "reviewer_date",
        "approver-name": "approver_name",
        "approver-date": "approver_date",
    }

    # Normalize pyproject config keys
    normalized_pyproject = {}
    for key, value in pyproject_config.items():
        normalized_key = key_mapping.get(key, key.replace("-", "_"))
        normalized_pyproject[normalized_key] = value

    # Apply ini config (lowest priority of the three)
    for key, value in ini_config.items():
        if hasattr(config, key) and value is not None and value != "":
            setattr(config, key, value)

    # Apply pyproject config (medium priority)
    for key, value in normalized_pyproject.items():
        if hasattr(config, key) and value is not None and value != "":
            setattr(config, key, value)

    # Apply CLI options (highest priority)
    for key, value in cli_options.items():
        if not hasattr(config, key) or value is None or value == "":
            continue
        if value is False and key in _CLI_STORE_TRUE_FIELDS:
            continue
        setattr(config, key, value)

    return config
