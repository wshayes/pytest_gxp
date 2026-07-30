"""
TQ-6 — Objective evidence integrity.

For a Tier 1 requirement, the captured evidence *is* the assurance. If evidence
is altered in transit, attributed to the wrong test, or referenced but absent,
then the reviewer performing FRM-CSA-02 Section D is inspecting the wrong thing.

Two byte-distinct images are used throughout so that cross-attribution is
detectable by hash rather than by inspection.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

import tq_config as cfg
import tq_helpers as h

# Byte-distinct evidence images.
IMAGE_A = h.make_png(96, 64, (200, 30, 30))
IMAGE_B = h.make_png(96, 64, (30, 30, 200))
HASH_A = h.sha256_bytes(IMAGE_A)
HASH_B = h.sha256_bytes(IMAGE_B)


def _build_evidence_suite(pytester, *, thumbnails: bool = True):
    """Two tests, each capturing one distinct image against its own requirement."""
    h.write_spec(
        pytester,
        "functional",
        [
            h.Requirement("FS-001", "Requirement evidenced by image A"),
            h.Requirement("FS-002", "Requirement evidenced by image B"),
        ],
    )
    (pytester.path / "image_a.png").write_bytes(IMAGE_A)
    (pytester.path / "image_b.png").write_bytes(IMAGE_B)
    (pytester.path / "test_evidence.py").write_text(
        "import pathlib\n"
        "import pytest\n"
        "\n"
        "HERE = pathlib.Path(__file__).parent\n"
        "\n"
        f"@pytest.mark.{cfg.MARKER_GXP}\n"
        "@pytest.mark.requirements(['FS-001'])\n"
        f"def test_captures_image_a({cfg.EVIDENCE_FIXTURE}):\n"
        "    data = (HERE / 'image_a.png').read_bytes()\n"
        f"    {cfg.EVIDENCE_FIXTURE}.capture_screenshot(data, 'Evidence A for FS-001')\n"
        "    assert True\n"
        "\n"
        f"@pytest.mark.{cfg.MARKER_GXP}\n"
        "@pytest.mark.requirements(['FS-002'])\n"
        f"def test_captures_image_b({cfg.EVIDENCE_FIXTURE}):\n"
        "    data = (HERE / 'image_b.png').read_bytes()\n"
        f"    {cfg.EVIDENCE_FIXTURE}.capture_screenshot(data, 'Evidence B for FS-002')\n"
        "    assert True\n",
        encoding="utf-8",
    )
    extra = [] if thumbnails else [cfg.FLAG_NO_THUMBNAILS]
    started = dt.datetime.now(dt.timezone.utc)
    result = h.run_gxp(pytester, *extra)
    finished = dt.datetime.now(dt.timezone.utc)
    return result, started, finished


def _entries(pytester) -> list[dict]:
    manifest = h.load_manifest(pytester.path)
    entries = manifest.get("evidence")
    assert isinstance(entries, list), "Evidence manifest has no 'evidence' list."
    return entries


def _resolve(pytester, rel_path: str) -> Path:
    """Resolve a manifest path, which may be relative to the manifest or the run root."""
    manifest_dir = h.find_artefact(pytester.path, cfg.ARTEFACT_EVIDENCE_MANIFEST).parent
    for base in (manifest_dir, Path(pytester.path)):
        candidate = base / rel_path
        if candidate.is_file():
            return candidate
    matches = list(Path(pytester.path).rglob(Path(rel_path).name))
    if matches:
        return matches[0]
    raise AssertionError(
        f"Evidence file {rel_path!r} referenced in the manifest does not exist on "
        "disk. The record cites evidence that cannot be produced on request."
    )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-6.1")
def test_evidence_manifest_is_generated_and_self_consistent(pytester, tq):
    """The manifest is produced and its count matches the number of entries."""
    _build_evidence_suite(pytester)
    manifest = h.load_manifest(pytester.path)
    entries = _entries(pytester)
    declared = manifest.get("evidence_count")
    tq.observe(
        declared_count=declared,
        actual_entries=len(entries),
        entry_ids=[e.get("id") for e in entries],
    )
    assert len(entries) == 2, (
        f"Two evidence artefacts were captured but the manifest lists "
        f"{len(entries)}. Evidence loss is silent."
    )
    assert declared is not None, "Manifest omits 'evidence_count'."
    assert int(declared) == len(entries), (
        f"Manifest declares {declared} evidence items but lists {len(entries)}."
    )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-6.2")
def test_every_referenced_evidence_file_exists(pytester, tq):
    """Each file path in the manifest resolves to a file on disk."""
    _build_evidence_suite(pytester)
    resolved = {}
    for entry in _entries(pytester):
        rel = entry.get("file_path")
        assert rel, f"Manifest entry {entry.get('id')} has no file_path."
        resolved[entry["id"]] = str(_resolve(pytester, rel))
    tq.observe(resolved_paths=resolved)
    assert len(resolved) == 2


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-6.3")
def test_evidence_bytes_are_preserved_unaltered(pytester, tq):
    """Stored evidence is byte-identical to what the test captured.

    Silent re-encoding, resizing, or compression of evidence would mean the
    signed record does not contain what the system actually displayed.
    """
    _build_evidence_suite(pytester)
    observed = {}
    for entry in _entries(pytester):
        path = _resolve(pytester, entry["file_path"])
        observed[entry["id"]] = {
            "description": entry.get("description"),
            "stored_sha256": h.sha256_file(path),
            "stored_bytes": path.stat().st_size,
        }
    stored_hashes = {v["stored_sha256"] for v in observed.values()}
    tq.observe(
        source_hash_a=HASH_A,
        source_hash_b=HASH_B,
        stored=observed,
    )
    assert HASH_A in stored_hashes, (
        "The bytes captured for FS-001 are not present unaltered in the stored "
        f"evidence. Source SHA-256 {HASH_A[:16]}…; stored hashes "
        f"{[hh[:16] for hh in stored_hashes]}."
    )
    assert HASH_B in stored_hashes, (
        "The bytes captured for FS-002 are not present unaltered in the stored evidence."
    )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-6.4")
def test_evidence_is_attributed_to_the_correct_test_and_requirement(pytester, tq):
    """Evidence captured by one test is not attributed to another.

    Cross-attribution is the evidence failure most likely to survive review,
    because both artefacts exist and both look plausible.
    """
    _build_evidence_suite(pytester)
    mapping = {}
    for entry in _entries(pytester):
        path = _resolve(pytester, entry["file_path"])
        mapping[h.sha256_file(path)] = {
            "test_id": entry.get("test_id", ""),
            "requirement_ids": entry.get("requirement_ids", []),
            "description": entry.get("description", ""),
        }
    tq.observe(hash_to_attribution={k[:16]: v for k, v in mapping.items()})

    assert HASH_A in mapping and HASH_B in mapping, (
        "Could not locate both captured images in the manifest by hash; "
        "attribution cannot be verified."
    )
    a, b = mapping[HASH_A], mapping[HASH_B]
    assert "test_captures_image_a" in a["test_id"], (
        f"Image A is attributed to test {a['test_id']!r}."
    )
    assert "test_captures_image_b" in b["test_id"], (
        f"Image B is attributed to test {b['test_id']!r}."
    )
    assert a["requirement_ids"] == ["FS-001"], (
        f"Image A is attributed to requirements {a['requirement_ids']}, expected ['FS-001']."
    )
    assert b["requirement_ids"] == ["FS-002"], (
        f"Image B is attributed to requirements {b['requirement_ids']}, expected ['FS-002']."
    )
    assert "FS-001" in a["description"] and "FS-002" in b["description"], (
        "Evidence descriptions do not match their requirements; the captured "
        "description was not preserved."
    )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-6.5")
def test_evidence_timestamps_fall_within_the_execution_window(pytester, tq):
    """Evidence timestamps are contemporaneous with the run.

    Required for ALCOA+ contemporaneity; a timestamp outside the window would
    indicate a cached or reused artefact.
    """
    _, started, finished = _build_evidence_suite(pytester)
    margin = dt.timedelta(minutes=5)
    observations = []
    problems = []
    for entry in _entries(pytester):
        raw = entry.get("timestamp")
        observations.append({"id": entry.get("id"), "timestamp": raw})
        if not raw:
            problems.append(f"{entry.get('id')}: no timestamp recorded")
            continue
        try:
            parsed = dt.datetime.fromisoformat(str(raw))
        except ValueError:
            problems.append(f"{entry.get('id')}: timestamp {raw!r} is not ISO 8601")
            continue
        if parsed.tzinfo is None:
            # Naive timestamp: compare against naive local bounds and record the
            # absence of a timezone as a separate finding (see TQ-7.5).
            lo = started.astimezone().replace(tzinfo=None) - margin
            hi = finished.astimezone().replace(tzinfo=None) + margin
        else:
            lo, hi = started - margin, finished + margin
        if not (lo <= parsed <= hi):
            problems.append(f"{entry.get('id')}: timestamp {raw} outside the window {lo} – {hi}")
    tq.observe(
        window_start_utc=started.isoformat(),
        window_end_utc=finished.isoformat(),
        evidence_timestamps=observations,
        problems=problems,
    )
    assert not problems, "Evidence timestamp findings: " + "; ".join(problems)


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-6.6")
def test_evidence_appears_in_the_human_readable_report(pytester, tq):
    """Captured evidence is surfaced in the report a reviewer actually reads."""
    _build_evidence_suite(pytester)
    md = h.read_text_artefact(pytester.path, cfg.ARTEFACT_REPORT_MD)
    ids = [e.get("id", "") for e in _entries(pytester)]
    descriptions_present = "Evidence A for FS-001" in md and "Evidence B for FS-002" in md
    ids_present = [i for i in ids if i and i in md]
    tq.observe(descriptions_present=descriptions_present, evidence_ids_in_report=ids_present)
    assert descriptions_present, (
        "Evidence descriptions do not appear in the Markdown report. A reviewer "
        "cannot tell from the report which evidence supports which determination."
    )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-6.7")
def test_thumbnail_does_not_replace_full_size_evidence(pytester, tq):
    """Where thumbnails are generated, the full-size artefact remains the record."""
    _build_evidence_suite(pytester, thumbnails=True)
    findings = []
    observations = []
    for entry in _entries(pytester):
        full = _resolve(pytester, entry["file_path"])
        full_hash = h.sha256_file(full)
        thumb_rel = entry.get("thumbnail_path")
        record = {
            "id": entry.get("id"),
            "full_bytes": full.stat().st_size,
            "full_sha256": full_hash[:16],
            "thumbnail_path": thumb_rel,
        }
        if thumb_rel:
            thumb = _resolve(pytester, thumb_rel)
            record["thumbnail_bytes"] = thumb.stat().st_size
            record["thumbnail_sha256"] = h.sha256_file(thumb)[:16]
            if h.sha256_file(thumb) == full_hash and Path(thumb) != Path(full):
                findings.append(f"{entry.get('id')}: thumbnail is a byte copy, not a derivation")
            if Path(thumb).resolve() == Path(full).resolve():
                findings.append(
                    f"{entry.get('id')}: thumbnail_path and file_path resolve to the "
                    "same file; the full-size evidence has been replaced"
                )
        if full_hash not in {HASH_A, HASH_B}:
            findings.append(
                f"{entry.get('id')}: the file recorded as full-size evidence does "
                "not match either captured image"
            )
        observations.append(record)
    tq.observe(evidence=observations, findings=findings)
    assert not findings, "Thumbnail handling findings: " + "; ".join(findings)


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-6.8")
def test_tier1_evidence_gate_can_be_applied_from_the_generated_records(pytester, tq):
    """The generated records contain what the Tier 1 evidence gate needs.

    WI-CSA-01 Section 5.4.6 fails a run where a Tier 1 requirement has no
    evidence. This case demonstrates that the join between requirement ID and
    evidence presence is computable from the manifest alone.
    """
    h.write_spec(
        pytester,
        "functional",
        [
            h.Requirement("FS-001", "Tier 1, evidenced", metadata={"Risk-Tier": "1"}),
            h.Requirement("FS-002", "Tier 1, NOT evidenced", metadata={"Risk-Tier": "1"}),
        ],
    )
    (pytester.path / "image_a.png").write_bytes(IMAGE_A)
    (pytester.path / "test_gate.py").write_text(
        "import pathlib\n"
        "import pytest\n"
        "\n"
        "HERE = pathlib.Path(__file__).parent\n"
        "\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['FS-001'])\n"
        "def test_evidenced(gxp_evidence):\n"
        "    gxp_evidence.capture_screenshot((HERE / 'image_a.png').read_bytes(), 'FS-001 state')\n"
        "    assert True\n"
        "\n"
        "@pytest.mark.gxp\n"
        "@pytest.mark.requirements(['FS-002'])\n"
        "def test_not_evidenced():\n"
        "    assert True\n",
        encoding="utf-8",
    )
    h.run_gxp(pytester)

    evidenced: set[str] = set()
    for entry in _entries(pytester):
        evidenced.update(entry.get("requirement_ids", []))
    tier1 = {"FS-001", "FS-002"}
    unevidenced = sorted(tier1 - evidenced)
    tq.observe(evidenced_requirements=sorted(evidenced), tier1_without_evidence=unevidenced)

    assert "FS-001" in evidenced, (
        "A requirement whose test captured evidence is not associated with any "
        "manifest entry, so the gate cannot be implemented."
    )
    assert unevidenced == ["FS-002"], (
        f"The gate computation produced {unevidenced}; expected exactly ['FS-002'], "
        "the Tier 1 requirement whose test captured no evidence. If this is "
        "empty, a green assertion with no evidence would pass the gate."
    )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-6.9")
def test_every_manifest_entry_carries_a_verifying_hash(pytester, tq):
    """Each manifest entry records the SHA-256 of the evidence file it names.

    The hash is what lets a reviewer establish, at any later date, that the
    evidence file on disk is the one the run captured. An entry without one, or
    with a hash of different bytes, cannot support that.
    """
    _build_evidence_suite(pytester)
    entries = _entries(pytester)
    observations = []
    problems = []
    for entry in entries:
        path = _resolve(pytester, entry["file_path"])
        actual = h.sha256_file(path)
        declared = entry.get("sha256")
        observations.append(
            {
                "id": entry.get("id"),
                "file_path": entry.get("file_path"),
                "declared_sha256": declared,
                "actual_sha256": actual,
            }
        )
        if not declared:
            problems.append(f"{entry.get('id')}: no sha256 recorded")
        elif declared != actual:
            problems.append(
                f"{entry.get('id')}: manifest declares {declared[:16]}… but the "
                f"stored file hashes to {actual[:16]}…"
            )
    tq.observe(entries=observations, problems=problems)
    assert entries, "The evidence manifest lists no entries."
    assert not problems, "Evidence hash findings: " + "; ".join(problems)
    # The two captured images are byte-distinct, so their hashes must differ.
    declared = [e["declared_sha256"] for e in observations]
    assert len(set(declared)) == len(declared), (
        f"Two byte-distinct evidence files were recorded with the same hash: {declared}."
    )
    assert set(declared) == {HASH_A, HASH_B}, (
        "The recorded hashes are not those of the captured images. The manifest "
        f"declares {[d[:16] for d in declared]}; the captures were "
        f"{[HASH_A[:16], HASH_B[:16]]}."
    )
