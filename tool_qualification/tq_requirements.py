"""TQ-001 intended-use requirements and their trace to the test case register.

A tool qualification is only as good as the answer to "how do you know these
tests cover what you rely on the tool for?". This module is that answer: a
register of the properties the regulated user depends on, each traced to the
qualification cases that exercise it, so the report can carry a requirements
traceability matrix rather than an unjustified list of 57 tests.

It is deliberately *not* a Functional Specification of pytest-gxp. Specifying a
tool you did not write, and then testing your own specification of it, adds a
document to maintain without adding assurance. What a qualification needs is a
statement of **intended use** — what the tool must be true of for the records it
produces to be relied upon — and evidence that each such statement was tested.
That is what is registered here. Where a QMS requires a controlled requirements
document for tools, lift these statements into it verbatim; the identifiers are
stable and the report cites them.

Risk is stated per requirement and drives nothing automatically: it is recorded
so that a reviewer can see the depth of testing was allocated deliberately, and
so that a High requirement left unverified is visible as a finding rather than
as a number in a coverage percentage.

Editing rules:
  * Every case in the suite must appear against exactly one requirement. The
    report raises a finding for any case it saw execute that is not registered
    here, so the register cannot silently fall behind the suite.
  * Adding a case means adding its ID here in the same change.
"""

from __future__ import annotations

INTENDED_USE = (
    "pytest-gxp is used as the tool that generates the traceability matrix, "
    "evidence manifest, coverage arithmetic, and qualification report relied upon "
    "as GxP records for application validation. The qualification establishes that "
    "the records this tool produces are truthful: that a non-passing test cannot "
    "surface as a pass, that an uncovered requirement cannot surface as covered, "
    "and that evidence cannot be attributed to a test that did not capture it. "
    "It does not establish that the tool is well engineered, nor anything about "
    "the application under test."
)

# id -> statement, risk, and the qualification cases that exercise it.
REQUIREMENTS: dict[str, dict] = {
    "TQ-REQ-01": {
        "statement": (
            "The qualified artefact shall be identifiable: the installed version "
            "matches the declared pin and its content is fixed by a hash."
        ),
        "risk": "High",
        "cases": ("TQ-1.1", "TQ-1.2"),
    },
    "TQ-REQ-02": {
        "statement": (
            "The command-line options and markers the work instruction depends on "
            "shall be present as documented."
        ),
        "risk": "Medium",
        "cases": ("TQ-1.3", "TQ-1.4"),
    },
    "TQ-REQ-03": {
        "statement": (
            "Enabling GxP mode shall not alter the pass/fail outcome of any test, "
            "so the record describes the same run that would have occurred without it."
        ),
        "risk": "High",
        "cases": ("TQ-1.5",),
    },
    "TQ-REQ-04": {
        "statement": (
            "Requirements shall be parsed from the specifications completely and "
            "verbatim: none dropped, none invented, attributed to the correct "
            "specification type, with title, expected result, and metadata preserved."
        ),
        "risk": "High",
        "cases": ("TQ-2.1", "TQ-2.2", "TQ-2.3", "TQ-2.4", "TQ-2.5"),
    },
    "TQ-REQ-05": {
        "statement": (
            "A defective specification shall raise a located finding rather than be "
            "silently accepted, for both duplicated IDs and malformed headings."
        ),
        "risk": "High",
        "cases": ("TQ-2.6", "TQ-2.7"),
    },
    "TQ-REQ-06": {
        "statement": (
            "Each test shall be traced to exactly the requirements it cites — all of "
            "them, and no others — consistently between the matrix and the report."
        ),
        "risk": "High",
        "cases": ("TQ-3.1", "TQ-3.2", "TQ-3.3", "TQ-3.6"),
    },
    "TQ-REQ-07": {
        "statement": (
            "Gaps shall surface: a requirement with no test is reported as uncovered, "
            "and a test citing an unknown requirement ID is reported as a finding."
        ),
        "risk": "High",
        "cases": ("TQ-3.4", "TQ-3.5"),
    },
    "TQ-REQ-08": {
        "statement": (
            "Every non-passing outcome shall be recorded as such — failure, skip with "
            "its reason, setup error, expected failure, and unexpected pass — and all "
            "shall be accounted for in the summary."
        ),
        "risk": "High",
        "cases": ("TQ-4.1", "TQ-4.4", "TQ-4.5", "TQ-4.6", "TQ-4.7", "TQ-4.8", "TQ-4.11"),
    },
    "TQ-REQ-09": {
        "statement": (
            "Coverage and verification arithmetic shall recompute from the reported "
            "counts, and a requirement shall count as verified only where its tests passed."
        ),
        "risk": "High",
        "cases": ("TQ-4.3", "TQ-5.1", "TQ-5.2", "TQ-5.3", "TQ-5.4"),
    },
    "TQ-REQ-10": {
        "statement": (
            "The status of a run shall be unmistakable: a run containing a failure "
            "exits non-zero, deviation references are carried into the record, and a "
            "record from an unclean run is marked provisional."
        ),
        "risk": "High",
        "cases": ("TQ-4.2", "TQ-4.9", "TQ-4.10"),
    },
    "TQ-REQ-11": {
        "statement": (
            "Every requested output format shall be produced, and all renderings of "
            "one run shall describe the same results."
        ),
        "risk": "Medium",
        "cases": ("TQ-5.5", "TQ-5.6", "TQ-5.7"),
    },
    "TQ-REQ-12": {
        "statement": (
            "Objective evidence shall be complete, unaltered, correctly attributed to "
            "the capturing test, hashed, contemporaneous with the run, and surfaced in "
            "the report a reviewer reads."
        ),
        "risk": "High",
        "cases": (
            "TQ-6.1",
            "TQ-6.2",
            "TQ-6.3",
            "TQ-6.4",
            "TQ-6.5",
            "TQ-6.6",
            "TQ-6.7",
            "TQ-6.9",
        ),
    },
    "TQ-REQ-13": {
        "statement": (
            "The risk-based evidence gate shall be effective: the risk tier reaches the "
            "matrix, a high-risk requirement without a capture of system state fails "
            "under strict mode, and a session record alone does not satisfy the gate."
        ),
        "risk": "High",
        "cases": ("TQ-1.6", "TQ-1.7", "TQ-6.8", "TQ-6.10"),
    },
    "TQ-REQ-14": {
        "statement": (
            "The record shall identify what it describes: qualification phase, system "
            "and version, source revision, and unambiguous timezone-aware timestamps; "
            "and identical input shall produce identical records but for timestamps."
        ),
        "risk": "High",
        "cases": ("TQ-7.1", "TQ-7.5", "TQ-7.6", "TQ-7.7", "TQ-7.8", "TQ-7.9"),
    },
    "TQ-REQ-15": {
        "statement": (
            "Signature attribution shall be truthful: signatory fields carry exactly "
            "the strings supplied, no placeholder name appears where none was supplied, "
            "and the unauthenticated nature of the field is on record."
        ),
        "risk": "High",
        "cases": ("TQ-7.2", "TQ-7.3", "TQ-7.4"),
    },
}

# Facts about the qualified version that a signatory must see, because they
# constrain how the records may be used. Kept in step with protocol §8.
LIMITATIONS = (
    "The rendered PDF is not byte-reproducible: the rendering library embeds a "
    "creation timestamp. The determinism established by TQ-7.8 covers the JSON, "
    "CSV, and Markdown renderings. The PDF is treated as a rendering of the record "
    "rather than the record of authority, and the specific PDF signed is fixed by "
    "its digest in the artifact hash manifest.",
    "Signature fields are printed-name fields and are not authenticated by the "
    "tool (TQ-7.3). Attribution of a signature to a person is a procedural control "
    "of the adopting organisation, not a tool control.",
)


def case_to_requirements() -> dict[str, list[str]]:
    """Invert the register: TQ case ID -> the requirements it verifies."""
    mapping: dict[str, list[str]] = {}
    for req_id, req in REQUIREMENTS.items():
        for case_id in req["cases"]:
            mapping.setdefault(case_id, []).append(req_id)
    return mapping


def registered_cases() -> set[str]:
    return set(case_to_requirements())
