"""
TQ-001 configuration — the single place to adjust for your environment.

Everything the qualification suite knows about pytest_gxp's public surface is
declared here, so that a change in flag names or output paths requires one edit
rather than a suite-wide sweep. Values below were taken from the published
pytest_gxp documentation; verify each against the pinned version before the
first qualification run and record any correction on FRM-CSA-03.
"""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# Pinned version under qualification
# ---------------------------------------------------------------------------
# The exact version being qualified. TQ-1.1 fails if the installed version
# differs, which prevents an accidental qualification of the wrong build.
# Override per environment with TQ_PINNED_VERSION; CI sets it from the version
# actually installed from the built wheel.
PINNED_VERSION: str | None = os.environ.get("TQ_PINNED_VERSION") or "0.3.0"

DISTRIBUTION_NAME = "pytest-gxp"
IMPORT_NAME = "pytest_gxp"

# ---------------------------------------------------------------------------
# Command-line interface
# ---------------------------------------------------------------------------
FLAG_ENABLE = "--gxp"
FLAG_SPEC_FILES = "--gxp-spec-files"
FLAG_OUTPUT_FORMATS = "--gxp-output-formats"
FLAG_QUALIFICATION_TYPE = "--gxp-qualification-type"
FLAG_TESTER = "--gxp-tester"
FLAG_REVIEWER = "--gxp-reviewer"
FLAG_APPROVER = "--gxp-approver"
FLAG_NO_THUMBNAILS = "--no-gxp-evidence-thumbnails"
FLAG_STRICT = "--gxp-strict"
FLAG_STRICT_COVERAGE = "--gxp-strict-coverage"
FLAG_DEVIATIONS = "--gxp-deviations"
FLAG_SOURCE_COMMIT = "--gxp-source-commit"
FLAG_SOURCE_TAG = "--gxp-source-tag"

# ---------------------------------------------------------------------------
# Default input and output directories
# ---------------------------------------------------------------------------
# Specifications are only parsed from this directory, so the suite must author
# them there rather than at the run root.
SPEC_DIR = "gxp_spec_files"
REPORT_DIR = "gxp_report_files"

# ---------------------------------------------------------------------------
# Markers and fixtures
# ---------------------------------------------------------------------------
MARKER_GXP = "gxp"
MARKER_REQUIREMENTS = "requirements"
MARKER_RISK = "gxp_risk"
EVIDENCE_FIXTURE = "gxp_evidence"

# ---------------------------------------------------------------------------
# Generated artefacts
# ---------------------------------------------------------------------------
# Located by recursive glob beneath the run directory, so the plugin's default
# output directory does not need to be known or hard-coded.
ARTEFACT_REPORT_JSON = "csv_validation_report.json"
ARTEFACT_REPORT_CSV = "csv_validation_report.csv"
ARTEFACT_REPORT_MD = "csv_validation_report.md"
ARTEFACT_REPORT_PDF = "csv_validation_report.pdf"
ARTEFACT_MATRIX_JSON = "traceability_matrix.json"
ARTEFACT_MATRIX_CSV = "traceability_matrix.csv"
ARTEFACT_MATRIX_MD = "traceability_matrix.md"
ARTEFACT_COVERAGE_MD = "requirement_coverage.md"
ARTEFACT_EVIDENCE_MANIFEST = "evidence_manifest.json"
ARTEFACT_HASH_MANIFEST = "artifact_manifest.sha256"

# ---------------------------------------------------------------------------
# Traceability matrix columns
# ---------------------------------------------------------------------------
MATRIX_REQ_COLUMN = "Requirement ID"
MATRIX_CASE_COLUMN = "Test Case ID"
MATRIX_NODE_COLUMN = "Test Node ID"
MATRIX_RISK_COLUMN = "Risk Tier"
MATRIX_STATUS_COLUMN = "Status"

# ---------------------------------------------------------------------------
# Record status marking
# ---------------------------------------------------------------------------
# Text the tool places on a report that must not be signed as it stands.
PROVISIONAL_BANNER = "**PROVISIONAL — DRAFT RECORD. NOT FOR SIGNATURE.**"

# ---------------------------------------------------------------------------
# Specification file naming
# ---------------------------------------------------------------------------
# The plugin selects specification type by substring in the filename.
SPEC_FILES = {
    "installation": "installation_specification",
    "design": "design_specification",
    "functional": "functional_specification",
    "user": "user_specification",
}

# Requirement prefix -> expected qualification phase (VP Section 6.7).
PREFIX_TO_PHASE = {
    "IS": "IQ",
    "DS": "OQ",
    "FS": "OQ",
    "US": "PQ",
}

# ---------------------------------------------------------------------------
# Tolerances
# ---------------------------------------------------------------------------
# Rate fields are reported to one decimal place; allow only rounding error.
RATE_TOLERANCE = 0.06

# Minimum plausible size for a rendered PDF containing a signature block and a
# results table. A near-empty file indicates a silent rendering failure.
MIN_PDF_BYTES = 3_000
