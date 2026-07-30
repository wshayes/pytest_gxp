"""
TQ-1 — Installation and integration integrity.

Establishes that the version under qualification is the version installed, that
it registers the interface the procedures depend on, and that merely enabling
the plugin does not change pass/fail determination.
"""

from __future__ import annotations

import hashlib
from importlib.metadata import PackageNotFoundError, distribution, version
from pathlib import Path

import pytest

import tq_config as cfg
import tq_helpers as h


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-1.1")
def test_installed_version_matches_pin(tq):
    """The installed pytest_gxp version is the version declared for qualification."""
    try:
        installed = version(cfg.DISTRIBUTION_NAME)
    except PackageNotFoundError:
        pytest.fail(
            f"{cfg.DISTRIBUTION_NAME} is not installed in the qualification "
            "environment. Install the pinned version before executing TQ-001."
        )
    tq.observe(installed_version=installed, declared_pin=cfg.PINNED_VERSION)
    if cfg.PINNED_VERSION is None:
        pytest.fail(
            "tq_config.PINNED_VERSION is not set. A qualification run must "
            "declare the exact version under test so the record identifies it "
            f"unambiguously. Installed version is {installed!r}."
        )
    assert installed == cfg.PINNED_VERSION, (
        f"Installed version {installed!r} does not match the declared pin "
        f"{cfg.PINNED_VERSION!r}. The qualification record would misidentify "
        "the qualified artefact."
    )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-1.2")
def test_distribution_content_hash_recorded(tq):
    """A content hash of the installed distribution is computed and recorded."""
    dist = distribution(cfg.DISTRIBUTION_NAME)
    # A PEP 660 editable install can expose only an import-finder shim, with no
    # package sources in its inventory and so nothing meaningful to hash. That is
    # an unqualifiable installation, not a tool defect, so say so plainly rather
    # than failing on an empty digest. A wheel or sdist install always has them.
    if not any(
        str(entry).startswith(f"{cfg.IMPORT_NAME}/") and str(entry).endswith(".py")
        for entry in (dist.files or [])
    ):
        tq.observe(install_exposes_sources=False)
        pytest.skip(
            "The installed distribution exposes no package sources to hash, so it "
            "cannot be content-identified. Install from a wheel or sdist for a "
            "qualification run; the CI tool-qualification job does exactly that."
        )
    files = sorted(dist.files or [], key=str)
    assert files, (
        "The installed distribution reports no file inventory, so its content "
        "cannot be hashed. Install from a wheel or sdist rather than by an "
        "editable or path-based install for qualification purposes."
    )
    digest = hashlib.sha256()
    counted = 0
    for entry in files:
        path = Path(dist.locate_file(entry))
        if path.is_file() and path.suffix == ".py":
            digest.update(str(entry).encode("utf-8"))
            digest.update(path.read_bytes())
            counted += 1
    content_hash = digest.hexdigest()
    tq.observe(
        python_files_hashed=counted,
        content_sha256=content_hash,
        install_location=str(Path(dist.locate_file("")).resolve()),
    )
    assert counted > 0, "No Python source files found in the installed distribution."
    # Record only. Compare against the value in the tool register on re-qualification.


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-1.3")
def test_gxp_options_are_registered(pytester, tq):
    """All command-line options relied upon by WI-CSA-01 are registered."""
    result = pytester.runpytest_subprocess("--help")
    text = "\n".join(result.outlines)
    expected = [
        cfg.FLAG_ENABLE,
        cfg.FLAG_SPEC_FILES,
        cfg.FLAG_OUTPUT_FORMATS,
        cfg.FLAG_QUALIFICATION_TYPE,
        cfg.FLAG_TESTER,
        cfg.FLAG_REVIEWER,
        cfg.FLAG_APPROVER,
        cfg.FLAG_STRICT,
        cfg.FLAG_STRICT_COVERAGE,
        cfg.FLAG_DEVIATIONS,
        cfg.FLAG_SOURCE_COMMIT,
        cfg.FLAG_SOURCE_TAG,
    ]
    missing = [flag for flag in expected if flag not in text]
    tq.observe(expected_flags=expected, missing_flags=missing)
    assert not missing, (
        f"Options absent from the plugin interface: {missing}. WI-CSA-01 "
        "references these; the procedure must be corrected or the version rejected."
    )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-1.4")
def test_required_markers_are_registered(pytester, tq):
    """The gxp and requirements markers are registered, so --strict-markers is usable."""
    result = pytester.runpytest_subprocess("--markers")
    text = "\n".join(result.outlines)
    present = {
        cfg.MARKER_GXP: f"{cfg.MARKER_GXP}" in text,
        cfg.MARKER_REQUIREMENTS: f"{cfg.MARKER_REQUIREMENTS}" in text,
    }
    tq.observe(markers_present=present)
    assert all(present.values()), (
        f"Markers not registered: {[k for k, v in present.items() if not v]}. "
        "Unregistered markers cannot be enforced with --strict-markers, so a "
        "typo in a requirement marker would silently orphan a test."
    )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-1.5")
def test_enabling_gxp_does_not_alter_pass_fail_determination(pytester, tq):
    """Pass/fail outcomes are identical with and without --gxp.

    A reporting plugin must not influence the results it reports.
    """
    h.write_spec(
        pytester,
        "functional",
        [
            h.Requirement("FS-001", "Passing behaviour"),
            h.Requirement("FS-002", "Failing behaviour"),
        ],
    )
    (pytester.path / "test_baseline.py").write_text(
        "import pytest\n"
        "\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['FS-001'])\n"
        "def test_passes():\n"
        "    assert True\n"
        "\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['FS-002'])\n"
        "def test_fails():\n"
        "    assert 1 == 2, 'deliberate failure for TQ-1.5'\n",
        encoding="utf-8",
    )

    plain = h.run_plain(pytester)
    gxp = h.run_gxp(pytester)

    plain_counts = plain.parseoutcomes()
    gxp_counts = gxp.parseoutcomes()
    tq.observe(
        plain_outcomes=plain_counts,
        gxp_outcomes=gxp_counts,
        plain_exit=plain.ret,
        gxp_exit=gxp.ret,
    )
    for key in ("passed", "failed"):
        assert plain_counts.get(key, 0) == gxp_counts.get(key, 0), (
            f"Count of {key!r} tests differs between a plain run "
            f"({plain_counts.get(key, 0)}) and a --gxp run "
            f"({gxp_counts.get(key, 0)}). The plugin is influencing outcomes."
        )
    assert plain.ret == gxp.ret, f"Exit code differs: plain={plain.ret}, gxp={gxp.ret}."


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-1.6")
def test_risk_tier_marker_is_registered_and_reaches_the_matrix(pytester, tq):
    """The risk-tier marker is registered and its value is carried into the matrix.

    Risk stratification is only a control if the assigned tier appears in the
    record; a marker the tool accepts but never reports cannot be reviewed.
    """
    # Registered without --gxp, so --strict-markers is usable on any run.
    markers = pytester.runpytest_subprocess("--markers")
    marker_text = "\n".join(markers.outlines)
    tq.observe(risk_marker=cfg.MARKER_RISK, registered_on_plain_run=cfg.MARKER_RISK in marker_text)
    assert cfg.MARKER_RISK in marker_text, (
        f"Marker {cfg.MARKER_RISK!r} is not registered on a plain run. An "
        "unregistered marker cannot be enforced with --strict-markers, so a "
        "mistyped risk tier would be silently ignored."
    )

    h.write_spec(
        pytester,
        "functional",
        [
            h.Requirement("FS-001", "High process risk requirement"),
            h.Requirement("FS-002", "Requirement with no tier assigned"),
        ],
    )
    (pytester.path / "test_risk.py").write_text(
        "import pytest\n"
        "\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['FS-001'])\n"
        f"@pytest.mark.{cfg.MARKER_RISK}('high')\n"
        "def test_high_risk():\n"
        "    assert True\n"
        "\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['FS-002'])\n"
        "def test_untiered():\n"
        "    assert True\n",
        encoding="utf-8",
    )
    h.run_gxp(pytester)

    tiers: dict[str, set[str]] = {}
    for row in h.matrix_rows(pytester.path):
        req = (row.get(cfg.MATRIX_REQ_COLUMN) or "").strip()
        if req:
            tiers.setdefault(req, set()).add((row.get(cfg.MATRIX_RISK_COLUMN) or "").strip())
    tq.observe(matrix_risk_tiers={k: sorted(v) for k, v in tiers.items()})

    assert cfg.MATRIX_RISK_COLUMN in (h.matrix_rows(pytester.path)[0] or {}), (
        f"The traceability matrix has no {cfg.MATRIX_RISK_COLUMN!r} column."
    )
    assert "high" in tiers.get("FS-001", set()), (
        f"FS-001 is marked {cfg.MARKER_RISK}('high') but the matrix records "
        f"{sorted(tiers.get('FS-001', set()))} in the {cfg.MATRIX_RISK_COLUMN!r} column."
    )
    assert "high" not in tiers.get("FS-002", set()), (
        "FS-002 has no risk marker but the matrix attributes a high tier to it. "
        "A tier applied to the wrong requirement would misdirect assurance effort."
    )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-1.7")
def test_strict_mode_gates_a_high_risk_requirement_without_evidence(pytester, tq):
    """A high-risk requirement with no objective evidence fails only under strict mode.

    This is the CSA evidence gate: under the Validation Plan a high process risk
    requirement needs captured evidence, not merely a green assertion. The gate
    must be opt-in, because enabling the plugin may not change pass/fail (TQ-1.5).
    """
    h.write_spec(pytester, "functional", [h.Requirement("FS-001", "High risk, unevidenced")])
    (pytester.path / "test_gate.py").write_text(
        "import pytest\n"
        "\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['FS-001'])\n"
        f"@pytest.mark.{cfg.MARKER_RISK}('high')\n"
        "def test_high_risk_without_evidence():\n"
        "    assert True\n",
        encoding="utf-8",
    )

    lenient = h.run_gxp(pytester)
    lenient_findings = h.findings(h.load_report(pytester.path), "high-risk-no-evidence")

    strict = h.run_gxp(pytester, cfg.FLAG_STRICT)
    strict_report = h.load_report(pytester.path)
    strict_findings = h.findings(strict_report, "high-risk-no-evidence")

    tq.observe(
        default_exit=lenient.ret,
        strict_exit=strict.ret,
        default_findings=lenient_findings,
        strict_findings=strict_findings,
        outcomes=strict.parseoutcomes(),
    )

    assert lenient.ret == 0, (
        f"A passing run exited {lenient.ret} without {cfg.FLAG_STRICT}. Enabling "
        "the plugin must not change pass/fail determination by default."
    )
    assert strict.ret != 0, (
        f"A high-risk requirement with no evidence exited {strict.ret} under "
        f"{cfg.FLAG_STRICT}. The evidence gate is not enforced, so the leaner "
        "assurance tiers cannot be claimed."
    )
    assert [f["location"] for f in strict_findings] == ["FS-001"], (
        f"Expected one 'high-risk-no-evidence' finding located at FS-001, got {strict_findings}."
    )
    assert all(f["severity"] == "error" for f in strict_findings), (
        f"The evidence-gate finding is not error severity: {strict_findings}."
    )
