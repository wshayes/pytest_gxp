"""
Helpers for the TQ-001 qualification suite.

Design notes
------------
* All checks are black-box, against the documented public surface: CLI flags,
  generated filenames, and the documented JSON structure. No private API of
  pytest_gxp is imported. This keeps the qualification valid across refactors
  and means the suite tests what a user actually depends on.
* Runs are executed as subprocesses so the real command-line path is exercised,
  including session-finish report generation, rather than an in-process
  approximation of it.
* Artefacts are located by recursive glob, so the plugin's default output
  directory does not need to be known.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import struct
import zlib
from pathlib import Path
from typing import Any, Iterable

import tq_config as cfg

# ---------------------------------------------------------------------------
# Specification authoring
# ---------------------------------------------------------------------------


class Requirement:
    """A single requirement to be written into a Markdown specification."""

    def __init__(
        self,
        req_id: str,
        title: str,
        description: str = "The system shall perform the stated function.",
        details: Iterable[str] = (),
        expected: str = "The stated function is performed without error.",
        metadata: dict[str, str] | None = None,
    ) -> None:
        self.req_id = req_id
        self.title = title
        self.description = description
        self.details = list(details)
        self.expected = expected
        self.metadata = metadata or {}

    def render(self) -> str:
        lines = [f"### {self.req_id}: {self.title}", "", "#### Description", self.description, ""]
        for n, detail in enumerate(self.details, start=1):
            lines.append(f"{n}. {detail}")
        if self.details:
            lines.append("")
        lines.append(f"Expected Result: {self.expected}")
        lines.append("")
        if self.metadata:
            lines.append("#### Metadata")
            for key, value in self.metadata.items():
                lines.append(f"{key}: {value}")
            lines.append("")
        return "\n".join(lines)

    def text_hash(self) -> str:
        """Requirement-Hash per Validation Plan Section 6.9."""
        return hashlib.sha256(self.render().encode("utf-8")).hexdigest()[:16]


def write_spec(
    pytester,
    kind: str,
    requirements: Iterable[Requirement],
    title: str | None = None,
    version: str = "1.0",
) -> Path:
    """Write a Markdown specification of the given kind into the run directory.

    kind: one of 'installation', 'design', 'functional', 'user'.
    """
    stem = cfg.SPEC_FILES[kind]
    heading = title or f"{kind.capitalize()} Specification"
    body = [f"# {heading}", "", f"## Version: {version}", ""]
    for req in requirements:
        body.append(req.render())
    return _write_spec_file(pytester, stem, "\n".join(body))


def write_raw_spec(pytester, kind: str, content: str) -> Path:
    """Write specification content verbatim, for malformed-input testing."""
    return _write_spec_file(pytester, cfg.SPEC_FILES[kind], content)


def _write_spec_file(pytester, stem: str, content: str) -> Path:
    # Specifications are only discovered beneath the configured spec directory;
    # a file written at the run root is never parsed, so the whole suite would
    # silently observe an empty specification set.
    path = Path(pytester.path) / cfg.SPEC_DIR / f"{stem}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------


def run_gxp(pytester, *extra_args: str, formats: str = "csv,json,md"):
    """Execute a GxP-mode run as a subprocess and return the RunResult.

    PDF is excluded by default because rendering is slow and depends on optional
    packages; TQ-5.7 requests it explicitly.
    """
    args = [cfg.FLAG_ENABLE, f"{cfg.FLAG_OUTPUT_FORMATS}={formats}", *extra_args]
    return pytester.runpytest_subprocess(*args)


def run_plain(pytester, *extra_args: str):
    """Execute without GxP mode, for baseline comparison (TQ-1.5)."""
    return pytester.runpytest_subprocess(*extra_args)


# ---------------------------------------------------------------------------
# Artefact location and loading
# ---------------------------------------------------------------------------


class ArtefactNotFound(AssertionError):
    pass


def find_artefact(root: Path, filename: str) -> Path:
    """Locate a generated artefact anywhere beneath root.

    Raises ArtefactNotFound with a directory listing, so a failure reports what
    *was* produced rather than only what was missing.
    """
    matches = sorted(p for p in Path(root).rglob(filename) if p.is_file())
    if not matches:
        produced = sorted(
            str(p.relative_to(root))
            for p in Path(root).rglob("*")
            if p.is_file() and p.suffix in {".json", ".csv", ".md", ".pdf"}
        )
        raise ArtefactNotFound(
            f"Expected artefact {filename!r} was not generated.\n"
            f"Artefacts found beneath {root}:\n  "
            + ("\n  ".join(produced) if produced else "(none)")
        )
    if len(matches) > 1:
        # Ambiguity is itself a finding: a qualification run must produce one
        # authoritative copy of each record.
        raise AssertionError(
            f"Multiple copies of {filename!r} generated: "
            + ", ".join(str(m.relative_to(root)) for m in matches)
        )
    return matches[0]


def artefact_exists(root: Path, filename: str) -> bool:
    return any(Path(root).rglob(filename))


def load_json(root: Path, filename: str) -> dict[str, Any]:
    return json.loads(find_artefact(root, filename).read_text(encoding="utf-8"))


def load_report(root: Path) -> dict[str, Any]:
    return load_json(root, cfg.ARTEFACT_REPORT_JSON)


def load_manifest(root: Path) -> dict[str, Any]:
    return load_json(root, cfg.ARTEFACT_EVIDENCE_MANIFEST)


def load_csv_rows(root: Path, filename: str) -> list[dict[str, str]]:
    text = find_artefact(root, filename).read_text(encoding="utf-8")
    return list(csv.DictReader(io.StringIO(text)))


def read_text_artefact(root: Path, filename: str) -> str:
    return find_artefact(root, filename).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Structure-tolerant accessors
#
# The report JSON is nested and its exact key names may vary between versions.
# These accessors search for the values by key name at any depth, so that a
# structural change surfaces as a single clear failure here rather than as
# dozens of KeyErrors across the suite.
# ---------------------------------------------------------------------------


def deep_get(obj: Any, key: str, default: Any = None) -> Any:
    """Return the first value found for `key` at any depth, else `default`."""
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for value in obj.values():
            found = deep_get(value, key, _SENTINEL)
            if found is not _SENTINEL:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = deep_get(item, key, _SENTINEL)
            if found is not _SENTINEL:
                return found
    return default


_SENTINEL = object()


def require(obj: Any, key: str) -> Any:
    value = deep_get(obj, key, _SENTINEL)
    if value is _SENTINEL:
        raise AssertionError(
            f"Report does not contain a {key!r} field at any depth. "
            "Either the record is incomplete or the documented report "
            "structure has changed; record the finding on FRM-CSA-03."
        )
    return value


def test_cases(report: dict[str, Any]) -> list[dict[str, Any]]:
    cases = deep_get(report, "test_cases", [])
    if not isinstance(cases, list):
        raise AssertionError("'test_cases' in the report is not a list.")
    return cases


def case_field(case: dict[str, Any], *candidates: str) -> Any:
    """Fetch the first present key from a set of plausible field names."""
    for name in candidates:
        if name in case:
            return case[name]
    return deep_get(case, candidates[0])


def status_of(case: dict[str, Any]) -> str:
    value = case_field(case, "status", "result", "outcome") or ""
    return str(value).strip().upper()


def requirements_of(case: dict[str, Any]) -> list[str]:
    value = case_field(case, "requirement_ids", "requirements", "requirement_id")
    if value is None:
        return []
    if isinstance(value, str):
        return [r.strip() for r in value.replace(";", ",").split(",") if r.strip()]
    return [str(v).strip() for v in value]


def case_name(case: dict[str, Any]) -> str:
    return str(
        case_field(case, "test_id", "test_case_id", "node_id", "id", "name", "test_name") or ""
    )


def executed_tests(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the record of tests that actually ran, keyed by real pytest node id.

    Distinct from `test_cases`, which is one synthetic entry per requirement.
    Result fidelity is asserted against this register.
    """
    executed = deep_get(report, "test_execution", _SENTINEL)
    if executed is _SENTINEL:
        raise AssertionError(
            "The report has no 'test_execution' list, so it does not name the "
            "tests that were actually run. Requirement-level entries alone "
            "cannot evidence which test produced which outcome."
        )
    if not isinstance(executed, list):
        raise AssertionError("'test_execution' in the report is not a list.")
    return executed


def executed_by_node(report: dict[str, Any], fragment: str) -> dict[str, Any]:
    """Return the single executed-test record whose node id contains `fragment`."""
    matches = [e for e in executed_tests(report) if fragment in str(e.get("node_id", ""))]
    if len(matches) != 1:
        raise AssertionError(
            f"Expected exactly one executed test matching {fragment!r}, found "
            f"{len(matches)}: {[e.get('node_id') for e in executed_tests(report)]}"
        )
    return matches[0]


def findings(report: dict[str, Any], code: str | None = None) -> list[dict[str, Any]]:
    """Return the report's validation findings, optionally filtered by code."""
    items = deep_get(report, "findings", [])
    if not isinstance(items, list):
        raise AssertionError("'findings' in the report is not a list.")
    return [f for f in items if code is None or f.get("code") == code]


def matrix_rows(root: Path) -> list[dict[str, str]]:
    """Return the traceability matrix CSV as a list of rows."""
    return load_csv_rows(root, cfg.ARTEFACT_MATRIX_CSV)


def matrix_pairs(root: Path) -> set[tuple[str, str]]:
    """Return {(requirement_id, test identifier)} from the traceability CSV.

    The real pytest node id is preferred: it is the identifier a reviewer can
    trace back to an executed test. The synthetic per-requirement case id is
    only used where no node id column exists.
    """
    pairs: set[tuple[str, str]] = set()
    for row in matrix_rows(root):
        req = (row.get(cfg.MATRIX_REQ_COLUMN) or row.get("requirement_id") or "").strip()
        test = (
            row.get(cfg.MATRIX_NODE_COLUMN)
            or row.get(cfg.MATRIX_CASE_COLUMN)
            or row.get("test_case_id")
            or ""
        ).strip()
        if req:
            pairs.add((req, test))
    return pairs


def load_hash_manifest(root: Path) -> dict[str, str]:
    """Parse artifact_manifest.sha256 into {relative path: digest}.

    Format is sha256sum-compatible: '<hex>  <path>', '#' comments ignored.
    """
    text = read_text_artefact(root, cfg.ARTEFACT_HASH_MANIFEST)
    entries: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        digest, _, name = line.partition("  ")
        if not name.strip():
            raise AssertionError(f"Hash manifest line is not sha256sum-formatted: {line!r}")
        entries[name.strip()] = digest.strip()
    return entries


# ---------------------------------------------------------------------------
# Binary evidence fixtures
# ---------------------------------------------------------------------------


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def make_png(width: int = 96, height: int = 64, rgb: tuple[int, int, int] = (180, 40, 40)) -> bytes:
    """Build a valid solid-colour PNG without requiring an imaging library.

    Distinct colours give byte-distinct images, which is what the evidence
    cross-attribution checks rely on.
    """
    raw = b"".join(b"\x00" + bytes(rgb) * width for _ in range(height))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", zlib.compress(raw, 9))
        + _png_chunk(b"IEND", b"")
    )


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pdf_backend_reason() -> str | None:
    """Return why PDF rendering is unavailable in this environment, else None.

    WeasyPrint imports cleanly without its native libraries (pango, cairo,
    gobject) and only fails when a document is rendered. TQ-5.7 must not report
    a missing renderer as a tool defect, so the renderer is probed directly.
    """
    try:
        import weasyprint
    except Exception as exc:  # noqa: BLE001 - any import problem is the reason
        return f"WeasyPrint is not importable: {exc}"
    try:
        weasyprint.HTML(string="<p>probe</p>").write_pdf()
    except Exception as exc:  # noqa: BLE001 - typically a missing native library
        return f"WeasyPrint cannot render: {exc}"
    return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()
