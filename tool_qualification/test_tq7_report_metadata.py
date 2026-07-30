"""
TQ-7 — Report metadata, signature handling, provenance, and determinism.

These cases underpin the Part 11 position taken in Validation Plan Section 6.10.
The important negative result is TQ-7.3: it establishes that the signature block
is populated from whatever string is passed on the command line, with no
authentication, which is why the procedures prohibit populating it at generation
time and route the artefact through a separate signature process.
"""

from __future__ import annotations

import datetime as dt
import re
import subprocess

import pytest

import tq_config as cfg
import tq_helpers as h

SPEC = [
    h.Requirement("FS-001", "First requirement"),
    h.Requirement("FS-002", "Second requirement"),
]

SUITE = """\
import pytest

@pytest.mark.gxp
@pytest.mark.requirements(['FS-001'])
def test_a():
    assert True

@pytest.mark.gxp
@pytest.mark.requirements(['FS-002'])
def test_b():
    assert True
"""


def _build(pytester, *extra: str):
    h.write_spec(pytester, "functional", SPEC)
    (pytester.path / "test_suite.py").write_text(SUITE, encoding="utf-8")
    return h.run_gxp(pytester, *extra)


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-7.1")
def test_qualification_type_is_recorded_as_supplied(pytester, tq):
    """The qualification phase recorded matches the phase requested.

    A record labelled OQ that was executed as PQ, or vice versa, files evidence
    against the wrong phase.
    """
    _build(pytester, f"{cfg.FLAG_QUALIFICATION_TYPE}=PQ")
    report = h.load_report(pytester.path)
    recorded = str(h.deep_get(report, "qualification_type") or "")
    md = h.read_text_artefact(pytester.path, cfg.ARTEFACT_REPORT_MD)
    tq.observe(
        recorded_qualification_type=recorded,
        markdown_heading=md.splitlines()[0] if md else "",
    )
    assert recorded, "Report omits 'qualification_type'."
    # The tool records the phase in expanded form ("Performance Qualification").
    assert recorded.upper() in ("PQ", "PERFORMANCE QUALIFICATION"), (
        f"Requested qualification type PQ but the record states {recorded!r}."
    )
    for wrong in ("Installation Qualification", "Operational Qualification"):
        assert wrong.upper() not in recorded.upper(), (
            f"A PQ run is recorded as {recorded!r}, filing the evidence against "
            "the wrong qualification phase."
        )
        assert wrong not in md, f"The human-readable report of a PQ run names {wrong!r}."
    assert "Performance Qualification" in md, (
        "The qualification phase does not appear in the human-readable report, so "
        "a reader cannot tell which phase the evidence belongs to."
    )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-7.2")
def test_supplied_signatory_names_are_recorded_verbatim(pytester, tq):
    """Signatory name fields carry exactly the strings supplied — no substitution."""
    names = {
        cfg.FLAG_TESTER: "Aoife Nolan",
        cfg.FLAG_REVIEWER: "Rajesh Iyer",
        cfg.FLAG_APPROVER: "Marta Kowalczyk",
    }
    _build(pytester, *[f"{flag}={value}" for flag, value in names.items()])
    blob = h.find_artefact(pytester.path, cfg.ARTEFACT_REPORT_JSON).read_text(
        "utf-8"
    ) + h.read_text_artefact(pytester.path, cfg.ARTEFACT_REPORT_MD)
    missing = [v for v in names.values() if v not in blob]
    tq.observe(supplied=list(names.values()), missing_from_record=missing)
    assert not missing, f"Supplied signatory names absent from the record: {missing}"


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-7.3")
def test_signature_block_is_unauthenticated_and_accepts_any_string(pytester, tq):
    """The signature block is a printed name field, not an electronic signature.

    Establishes, as a positive finding of fact for the validation file, that any
    arbitrary string is accepted without authentication, identity check, or
    binding to a credential. This is the evidentiary basis for Validation Plan
    Section 6.10: the generated report is an unsigned draft record and the
    signatory fields shall not be populated at generation time.
    """
    fabricated = "Not A Real Person, PhD <injected@example.invalid>"
    _build(pytester, f"{cfg.FLAG_APPROVER}={fabricated}")
    blob = h.find_artefact(pytester.path, cfg.ARTEFACT_REPORT_JSON).read_text(
        "utf-8"
    ) + h.read_text_artefact(pytester.path, cfg.ARTEFACT_REPORT_MD)
    accepted = fabricated in blob or "Not A Real Person" in blob
    tq.observe(
        fabricated_value=fabricated,
        accepted_without_authentication=accepted,
        conclusion=(
            "Printed name field only. Not a 21 CFR Part 11 Subpart C electronic "
            "signature. Signature must be applied by the approved external "
            "process and bound to the artefact hash."
        ),
    )
    assert accepted, (
        "An arbitrary approver string was not reproduced in the record. If the "
        "tool now validates or authenticates this field, the Part 11 position in "
        "Validation Plan Section 6.10 should be re-examined and the finding updated."
    )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-7.4")
def test_signatory_fields_are_empty_when_not_supplied(pytester, tq):
    """No placeholder or default name appears where no signatory was supplied.

    A default such as "John Doe" appearing in a signature block would be a
    falsified record on its face.
    """
    _build(pytester)
    report_json = h.find_artefact(pytester.path, cfg.ARTEFACT_REPORT_JSON).read_text("utf-8")
    md = h.read_text_artefact(pytester.path, cfg.ARTEFACT_REPORT_MD)
    placeholders = ["John Doe", "Jane Smith", "Bob Johnson", "Test User", "TBD", "N/A Name"]
    found = [p for p in placeholders if p in report_json or p in md]
    tq.observe(placeholders_searched=placeholders, placeholders_found=found)
    assert not found, (
        f"Placeholder signatory name(s) {found} appear in a record where no "
        "signatory was supplied. Any such value in a signature block is a "
        "falsified attribution and this version must not be used."
    )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-7.5")
def test_report_timestamps_are_iso8601(pytester, tq):
    """Generation and validation timestamps are machine-parseable ISO 8601."""
    _build(pytester)
    report = h.load_report(pytester.path)
    generated = h.deep_get(report, "generated_date")
    tq.observe(generated_date=generated)
    assert generated, "Report omits 'generated_date'."
    try:
        parsed = dt.datetime.fromisoformat(str(generated))
    except ValueError:
        pytest.fail(f"generated_date {generated!r} is not parseable ISO 8601.")
    tq.observe(has_timezone=parsed.tzinfo is not None)


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-7.6")
def test_report_timestamps_carry_an_explicit_timezone(pytester, tq):
    """Timestamps carry a timezone designator and parse as timezone-aware.

    Annex 11 and ALCOA+ expect an unambiguous time reference. A naive local
    timestamp is ambiguous across daylight-saving transitions and across runners
    in different regions.
    """
    _build(pytester)
    report = h.load_report(pytester.path)
    generated = str(h.deep_get(report, "generated_date") or "")
    has_tz = bool(re.search(r"(Z|[+-]\d{2}:?\d{2})$", generated))
    parsed = None
    try:
        parsed = dt.datetime.fromisoformat(generated.replace("Z", "+00:00"))
    except ValueError:
        pass
    tq.observe(
        generated_date=generated,
        timezone_designator_present=has_tz,
        parsed_offset=str(parsed.utcoffset()) if parsed else None,
    )
    assert has_tz, (
        f"generated_date {generated!r} carries no timezone designator, so the "
        "time it states is ambiguous."
    )
    assert parsed is not None, f"generated_date {generated!r} is not parseable ISO 8601."
    assert parsed.tzinfo is not None and parsed.utcoffset() is not None, (
        f"generated_date {generated!r} does not parse to a timezone-aware instant."
    )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-7.7")
def test_report_records_source_provenance(pytester, tq):
    """The record identifies the source revision it was generated from.

    The report must itself evidence which approved protocol revision was
    executed, rather than relying on that link being reconstructed later.
    """
    # Supplied values take precedence and must be reproduced exactly as given.
    _build(
        pytester,
        f"{cfg.FLAG_SOURCE_COMMIT}=0123456789abcdef0123456789abcdef01234567",
        f"{cfg.FLAG_SOURCE_TAG}=OQ-1.0.0",
    )
    supplied = h.deep_get(h.load_report(pytester.path), "source_provenance")
    tq.observe(supplied_provenance=supplied)
    assert isinstance(supplied, dict), (
        "The report has no 'source_provenance' object, so it does not state which "
        f"revision produced it. Found: {supplied!r}."
    )
    assert supplied.get("git_commit") == "0123456789abcdef0123456789abcdef01234567", (
        f"The supplied source commit was not recorded verbatim: {supplied!r}."
    )
    assert supplied.get("git_tag") == "OQ-1.0.0", (
        f"The supplied source tag was not recorded verbatim: {supplied!r}."
    )

    # With nothing supplied, provenance is detected from the repository itself.
    subprocess.run(["git", "init", "-q"], cwd=pytester.path, check=True)
    subprocess.run(["git", "add", "-A"], cwd=pytester.path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=TQ",
            "-c",
            "user.email=tq@example.invalid",
            "commit",
            "-q",
            "-m",
            "protocol freeze",
        ],
        cwd=pytester.path,
        check=True,
    )
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=pytester.path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    h.run_gxp(pytester)
    detected = h.deep_get(h.load_report(pytester.path), "source_provenance")
    tq.observe(git_head=head, detected_provenance=detected)
    assert detected.get("git_commit") == head, (
        f"The record states commit {detected.get('git_commit')!r} but HEAD is "
        f"{head!r}. A wrong revision in the record breaks the link between the "
        "approved protocol and the executed run."
    )
    assert detected.get("source") == "git", (
        f"Provenance was detected but its source is recorded as {detected.get('source')!r}."
    )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-7.8")
def test_report_is_reproducible_and_artefacts_are_hashed(pytester, tq):
    """Two runs of identical input produce identical records but for timestamps.

    Reproducibility is what allows an unauthorised regeneration to be detected by
    comparison rather than only by trusting one artefact. The hash manifest is
    what a signature binds to, so its digests must verify.
    """
    _build(pytester)
    text_1 = h.find_artefact(pytester.path, cfg.ARTEFACT_REPORT_JSON).read_text("utf-8")

    # Remove generated artefacts and re-run identical input.
    for path in list(pytester.path.rglob(cfg.ARTEFACT_REPORT_JSON)):
        path.unlink()
    h.run_gxp(pytester)
    report_path = h.find_artefact(pytester.path, cfg.ARTEFACT_REPORT_JSON)
    text_2 = report_path.read_text("utf-8")

    volatile = re.compile(
        r'"(generated_date|validation_date|timestamp|generated_at|duration|duration_s'
        r'|start_time|end_time)"\s*:\s*("[^"]*"|[\d.]+)'
    )
    norm_1 = volatile.sub('"<volatile>": "<volatile>"', text_1)
    norm_2 = volatile.sub('"<volatile>": "<volatile>"', text_2)
    tq.observe(
        raw_identical=text_1 == text_2,
        normalised_identical=norm_1 == norm_2,
        normalised_hash_1=h.sha256_bytes(norm_1.encode())[:16],
        normalised_hash_2=h.sha256_bytes(norm_2.encode())[:16],
    )
    assert norm_1 == norm_2, (
        "Two runs of identical input produced records that differ after "
        "normalising known volatile fields. The record is not reproducible, so "
        "regeneration cannot be detected by hash comparison."
    )

    manifest = h.load_hash_manifest(pytester.path)
    report_dir = report_path.parent
    on_disk = {
        str(p.relative_to(report_dir).as_posix())
        for p in report_dir.rglob("*")
        if p.is_file() and p.name != cfg.ARTEFACT_HASH_MANIFEST
    }
    mismatched = {
        name: digest
        for name, digest in manifest.items()
        if h.sha256_file(report_dir / name) != digest
    }
    tq.observe(
        manifest_entries=sorted(manifest),
        files_on_disk=sorted(on_disk),
        sorted_order=list(manifest) == sorted(manifest),
        mismatched_digests=mismatched,
    )
    assert manifest, f"{cfg.ARTEFACT_HASH_MANIFEST} lists no artefacts."
    assert cfg.ARTEFACT_HASH_MANIFEST not in manifest, (
        "The hash manifest lists itself, which cannot be verified."
    )
    assert list(manifest) == sorted(manifest), (
        f"Manifest paths are not in sorted order, so two runs over the same "
        f"artefacts need not produce the same manifest: {list(manifest)}."
    )
    assert not mismatched, (
        "These manifest digests do not match the bytes on disk, so a signature "
        f"bound to the manifest would not bind to the artefacts: {mismatched}."
    )
    assert on_disk <= set(manifest), (
        "Artefacts were produced that the manifest does not cover, so they are "
        f"outside the signature's scope: {sorted(on_disk - set(manifest))}."
    )


@pytest.mark.mandatory
@pytest.mark.tq_id("TQ-7.9")
def test_software_name_and_version_are_carried_into_the_record(pytester, tq):
    """The record identifies the system and version under qualification.

    A qualification record that does not state what was qualified is not a
    qualification record.
    """
    _build(pytester)
    report = h.load_report(pytester.path)
    name = h.deep_get(report, "software_name")
    ver = h.deep_get(report, "software_version")
    tq.observe(software_name=name, software_version=ver)
    problems = []
    if not name:
        problems.append("software_name is absent or empty")
    if not ver:
        problems.append("software_version is absent or empty")
    assert not problems, (
        "; ".join(problems)
        + ". Supply these via configuration; if the tool provides no mechanism, "
        "record them on FRM-CSA-01 and state them on the report cover sheet."
    )
