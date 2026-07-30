"""Tests for configuration loading and three-source merging."""

from pytest_gxp.config import GxPConfig, load_config_from_ini, merge_config


class FakeIniConfig:
    """Minimal stand-in for the pytest Config object's ini lookups."""

    def __init__(self, values):
        self._values = values

    def getini(self, name):
        if name not in self._values:
            raise ValueError(f"unknown ini option: {name}")
        return self._values[name]


def cli_defaults(**overrides):
    """CLI option dict as plugin.pytest_configure builds it when no flags are passed."""
    options = {
        "enabled": True,
        "spec_files": None,
        "report_files": None,
        "qualification_type": None,
        "software_version": None,
        "project_name": None,
        "strict_coverage": False,  # store_true default
        "strict": False,  # store_true default
        "deviations": None,
        "output_formats": None,
        "evidence_thumbnails": None,
        "source_commit": None,
        "source_tag": None,
        "tester_name": None,
        "reviewer_name": None,
        "approver_name": None,
    }
    options.update(overrides)
    return options


def test_ini_strict_coverage_survives_cli_defaults():
    """An ini-enabled strict coverage flag must not be clobbered by the CLI default."""
    ini = load_config_from_ini(FakeIniConfig({"gxp_strict_coverage": "true"}))
    assert ini["strict_coverage"] is True

    config = merge_config(cli_defaults(), {}, ini)
    assert config.strict_coverage is True


def test_cli_flag_still_enables_strict_coverage():
    config = merge_config(cli_defaults(strict_coverage=True), {}, {})
    assert config.strict_coverage is True


def test_strict_and_deviations_load_from_all_sources():
    """The strict gate and the deviation map follow the same three-source merge."""
    ini = load_config_from_ini(
        FakeIniConfig({"gxp_strict": "true", "gxp_deviations": "ini-deviations.json"})
    )
    assert ini == {"strict": True, "deviations": "ini-deviations.json"}

    # An unset CLI store_true must not clobber the ini value
    config = merge_config(cli_defaults(), {}, ini)
    assert config.strict is True
    assert config.deviations == "ini-deviations.json"

    assert merge_config(cli_defaults(strict=True), {}, {}).strict is True
    assert merge_config(cli_defaults(), {}, {}).strict is False

    config = merge_config(
        cli_defaults(deviations="cli.json"), {"deviations": "pyproject.json"}, ini
    )
    assert config.deviations == "cli.json"


def test_ini_output_formats_and_thumbnails_are_honoured():
    ini = load_config_from_ini(
        FakeIniConfig(
            {
                "gxp_output_formats": "json,md",
                "gxp_evidence_thumbnails": "false",
            }
        )
    )
    assert ini == {"output_formats": "json,md", "evidence_thumbnails": False}

    config = merge_config(cli_defaults(), {}, ini)
    assert config.output_formats == "json,md"
    assert config.evidence_thumbnails is False


def test_thumbnails_default_to_enabled():
    assert merge_config(cli_defaults(), {}, {}).evidence_thumbnails is True
    assert GxPConfig().output_formats == "csv,json,md,pdf"


def test_cli_no_thumbnails_flag_overrides_ini():
    ini = {"evidence_thumbnails": True}
    config = merge_config(cli_defaults(evidence_thumbnails=False), {}, ini)
    assert config.evidence_thumbnails is False


def test_precedence_cli_over_pyproject_over_ini():
    ini = {"software_version": "ini-version", "project_name": "ini-project"}
    pyproject = {"software-version": "pyproject-version"}

    # ini only
    assert merge_config(cli_defaults(), {}, ini).software_version == "ini-version"

    # pyproject beats ini
    config = merge_config(cli_defaults(), pyproject, ini)
    assert config.software_version == "pyproject-version"
    assert config.project_name == "ini-project"

    # CLI beats both
    config = merge_config(cli_defaults(software_version="cli-version"), pyproject, ini)
    assert config.software_version == "cli-version"


def test_source_provenance_overrides_load_from_all_sources():
    ini = load_config_from_ini(
        FakeIniConfig({"gxp_source_commit": "abc123", "gxp_source_tag": "v1.2.3"})
    )
    config = merge_config(cli_defaults(), {}, ini)
    assert (config.source_commit, config.source_tag) == ("abc123", "v1.2.3")

    config = merge_config(cli_defaults(source_commit="def456"), {"source-tag": "v9.9.9"}, ini)
    assert (config.source_commit, config.source_tag) == ("def456", "v9.9.9")
