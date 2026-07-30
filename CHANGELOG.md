# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-07-29

This release makes the generated artifacts fit to be relied upon as GxP records:
every record names the real pytest tests, states the source revision it was
produced from, reports its own defects as findings, and is hashed. It also ships
the tool-qualification package that lets you establish fitness for purpose of the
tool itself.

### Added

- **Source provenance.** `report_metadata.source_provenance` and the traceability
  matrix JSON metadata record `source`, `git_commit`, `git_tag` and `git_dirty`
  for the system under validation, detected from git once per session. Nothing is
  fabricated: outside a repository the source is reported as `unavailable` with
  null values. New `--gxp-source-commit` / `--gxp-source-tag` options (plus
  `gxp_source_commit` / `gxp_source_tag` ini keys and `source-commit` /
  `source-tag` in `pyproject.toml`) supply the revision when the run is not
  inside a git checkout.
- **Generator identification.** `report_metadata.generator` records the tool name
  and version that produced the record.
- **Validation findings.** The plugin now reports its own defects instead of
  silently degrading. Findings carry a `code`, `severity`, `message` and
  `location`, appear as a top-level `findings` list plus a
  `report_metadata.findings_summary` count in the JSON report, as a
  `## Validation Findings` table in the Markdown and PDF reports, and as a
  terminal summary section. Codes: `duplicate-requirement-id`,
  `malformed-requirement-heading`, `unknown-requirement-ref`,
  `uncovered-requirement`, `invalid-risk-tier`, `high-risk-no-evidence`,
  `missing-deviation-ref`, `deviation-file-error`.
- **Real test identities.** A top-level `test_execution` register lists every
  executed test by `node_id` with its `outcome`, `reason`, `requirement_ids`,
  `risk_tier` and `deviation_ref`. Outcomes now distinguish `ERROR`, `XFAIL` and
  `XPASS` alongside `PASSED` / `FAILED` / `SKIPPED` / `NOT_EXECUTED`, and skip and
  error reasons are recorded rather than discarded.
- **Risk tiers.** `@pytest.mark.gxp_risk("high" | "medium" | "not-high")`
  classifies a test's requirement risk. The tier appears as a `Risk Tier` column
  in the traceability matrix and on each `test_execution` entry. A requirement
  takes the highest tier among the tests that cite it. An unrecognised value
  raises an `invalid-risk-tier` finding and is treated as unset.
- **Strict gate.** `--gxp-strict` (ini `gxp_strict`, `pyproject.toml` `strict`)
  fails the run on any error-severity finding — including a high-risk requirement
  verified with no objective evidence, which raises `high-risk-no-evidence`. Off
  by default, so enabling the plugin cannot change a run's pass/fail outcome.
- **Deviation references.** `--gxp-deviations=deviations.json` supplies a JSON map
  of pytest node ID or requirement ID to a deviation reference (node ID wins).
  The reference is carried verbatim as `deviation_ref` on every `test_execution`
  and `test_cases` entry. Every non-passing test without a reference raises a
  `missing-deviation-ref` finding.
- **Provisional status.** `report_metadata.status` is `PROVISIONAL` or `FINAL`,
  with `provisional_reasons` listing why. A provisional report carries a
  *PROVISIONAL — DRAFT RECORD. NOT FOR SIGNATURE.* banner in the Markdown and PDF
  renderings; a clean run is `FINAL` with no banner.
- **Artifact manifest.** `artifact_manifest.sha256` is written last in the
  session, covering every other generated artifact. It is `sha256sum`-compatible,
  so `sha256sum -c` / `shasum -a 256 -c` verifies it once the leading comment
  lines are stripped.
- **Evidence hashes.** Each `evidence_manifest.json` entry carries the `sha256` of
  its evidence file, so evidence attribution can be verified by hash rather than
  by inspection.
- **Unscripted session evidence.** `gxp_evidence.record_unscripted_session(charter,
  tester, duration_minutes, observations, defects=None)` records an exploratory or
  unscripted testing session as a JSON side-car — no Pillow required — under the
  new `unscripted_session` evidence type.
- **Expected results and metadata in the record.** `test_cases` entries now carry
  `expected_result`, the requirement's `metadata`, `risk_tier` and
  `deviation_ref`.
- **User requirements reach the outputs.** `US-*` requirements now appear in the
  traceability matrix and validation report, not only in the coverage report.
- **Error counts.** `test_summary.errors` and
  `test_execution_summary.error_tests`.
- **Deterministic output.** The JSON, CSV and Markdown artifacts are reproducible
  across runs apart from the recorded timestamps: specification files are parsed
  in sorted order, specifications iterated in a fixed type order, and every
  emitted list sorted. The PDF is excluded — the renderer embeds its own creation
  timestamp.
- **Tool-qualification suite.** A black-box qualification suite ships in the
  source distribution under `tool_qualification/`, deliberately excluded from the
  wheel. Run it with
  `pytest -c tool_qualification/pytest.ini tool_qualification/ -m "not gap"`.
- **Validation documentation.** A new [Validation](docs/validation/index.md)
  documentation section: tool-qualification protocol, work instruction,
  checklists and forms, and a risk-based assurance strategy, all as templates to
  adopt under your own document control.
- **CI.** Unit tests on Python 3.9 / 3.11 / 3.13 with ruff lint and format checks,
  plus a tool-qualification gate that installs from the built wheel.

### Changed

- **Timestamps are UTC ISO 8601 with a `Z` designator** throughout the reports,
  matrices, evidence manifest and coverage report. Previously they were naive
  local times with no zone information.
- **Traceability matrix schema.** The matrix now emits **one row per executed
  test** rather than one row per requirement: each row names the test in a new
  `Test Node ID` column and carries that test's own `Status`, plus the new `Risk
  Tier` column. A requirement with no test keeps a single row with an empty node
  ID and status `Not Executed`. **This is a breaking change for consumers that
  read the matrix CSV by column position** — read by header name instead.
- `requires-python` is now `>=3.9`; Python 3.8 is no longer supported.
- `setup.py` was deleted; `pyproject.toml` is the sole packaging declaration and
  the sole source of the version, which `pytest_gxp.__version__` now reads via
  `importlib.metadata`.
- The Markdown and PDF reports are rendered from a single shared builder, so the
  two can no longer drift apart.

### Fixed

- Configuration merge no longer discards ini and `pyproject.toml` boolean values.
  A `store_true` CLI flag that was not passed arrives as `False`, and that `False`
  was overriding a `true` set in configuration — meaning `gxp_strict_coverage`
  from `pytest.ini` could never take effect.
- `gxp_output_formats` and `gxp_evidence_thumbnails` were registered as ini
  options but read from the command line only. Both are now honoured from
  `pytest.ini` and `pyproject.toml`.
- Specification files are parsed in sorted order. Previously the directory glob
  was filesystem-ordered, so requirement ordering in the generated artifacts
  varied between machines and runs.
- A broken PDF backend no longer costs the remaining artifacts. WeasyPrint raises
  `OSError` when its native libraries are missing, which was not caught; the
  failure is now warned about and the run continues through the remaining formats
  to the manifest.

## [0.1.0] - 2025-12-28

Initial release.
