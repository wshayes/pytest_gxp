# TQ-001 — pytest-gxp Tool Qualification Protocol

!!! note "Template"
    Adopt this document under your own document control. Identifiers, roles,
    and references are placeholders. Nothing here is regulatory advice.

| | |
|---|---|
| **Document type** | Tool Qualification Protocol |
| **Tool** | `pytest-gxp` (pytest plugin), version `<X.Y.Z>` |
| **GAMP 5 classification of the tool** | Software tool supporting validation activity. Classify per your own assessment: a tool adopted as an unmodified open-source package with no supplier quality agreement is normally treated as Category 5 for qualification purposes, because no supplier assurance can be credited. |
| **Related** | `<Validation Plan ID>` §6; `WI-CSA-01`; `FRM-CSA-03` |
| **Status** | DRAFT |

!!! info "Document identifiers"
    `TQ-001`, `WI-CSA-01`, `FRM-CSA-0x`, and `SOP-01` are placeholders for your
    document control system's identifiers. Rename them to match your QMS.

---

## 1. Purpose and rationale

pytest-gxp generates the traceability matrix, evidence manifest, and validation
report relied upon as GxP records. A tool that produces the evidence must itself
be shown fit for that purpose. This protocol establishes that fitness by
black-box testing against the tool's documented public interface.

The scope is deliberately narrow. The question is not whether pytest-gxp is well
engineered; it is whether **the records it produces are truthful**. Accordingly
the protocol is weighted toward negative controls: a non-passing test must
surface as non-passing, an uncovered requirement must surface as uncovered, and
evidence must not be cross-attributed. A qualification consisting of
positive-path checks would demonstrate nothing about record integrity.

## 2. Supplier and user roles

pytest-gxp is authored and published under an MIT licence on PyPI by its author,
in a personal / open-source capacity. The two roles are held separately and the
record shall reflect this:

| Role | Held by | Obligation |
|---|---|---|
| Supplier | Package author (personal / open-source capacity) | Versioned releases, release notes, public repository history |
| User | **The regulated organisation**, as the regulated party | This qualification, against a pinned version, before use |

The availability of the package, or of its public repository history, shall not
be cited as supplier assurance, and does not substitute for user-side
qualification.

Where the tool author is a member of your organisation, document the two roles
separately in this section and ensure the review required by §7 criterion 5 is
performed by a person who did not author the pytest-gxp code. Where that is not
possible, the qualification is self-attested; record that fact explicitly as a
limitation in §8 rather than leaving it to be found.

## 3. Scope

**In scope:** requirement parsing, traceability generation, test result
determination and reporting, coverage arithmetic, evidence capture and
attribution, report metadata and source provenance, output format consistency,
risk-tier handling and the evidence gate, deviation reference handling,
provisional-record marking, artifact hash manifest generation, signature-field
handling.

**Out of scope:** pytest core behaviour; the correctness of the application under
test; the rendering fidelity of the PDF library; performance.

## 4. Prerequisites

1. `TQ_PINNED_VERSION` set to the exact version under qualification.
2. The pinned version installed from a wheel or sdist — **not** an editable or
   path install, so that a content hash can be computed (TQ-1.2).
3. Isolated virtual environment. `TZ=UTC` set.
4. The qualification suite obtained from the source distribution or tagged
   release for the version under qualification; suite commit recorded in
   `tq_environment.json`.
5. Reviewer identified, independent of the pytest-gxp author.

## 5. Test case register

Every case is implemented as an automated test. Cases are either **Mandatory** —
must pass for the version to be used in qualification activity — or **Gap
assessment**, whose expected outcome is recorded in §8 and whose *change of
state* is the signal to investigate.

As of version 0.2.0 every case in the register is Mandatory. The gap-assessment
class is retained in the protocol and in the suite's marker set because the
class is a permanent feature of the method, not because it is currently
populated; see §8.

### 5.1 TQ-1 — Installation and integration integrity
`test_tq1_installation_integrity.py`

| ID | Acceptance criterion | Class |
|---|---|---|
| TQ-1.1 | Installed version equals the declared pin | Mandatory |
| TQ-1.2 | A content hash of the installed distribution is computed and recorded | Mandatory |
| TQ-1.3 | All CLI options referenced by WI-CSA-01 are registered | Mandatory |
| TQ-1.4 | `gxp` and `requirements` markers are registered | Mandatory |
| TQ-1.5 | Pass/fail outcomes and exit code are identical with and without `--gxp` | Mandatory |
| TQ-1.6 | A risk-tier marker (`gxp_risk`) is registered and its tier reaches the traceability matrix | Mandatory |
| TQ-1.7 | The `--gxp-strict` gate is effective in both directions: a high-risk requirement with no evidence causes a non-zero exit when strict is on, and exits zero when it is off | Mandatory |

### 5.2 TQ-2 — Specification parsing fidelity
`test_tq2_specification_parsing.py`

| ID | Acceptance criterion | Class |
|---|---|---|
| TQ-2.1 | Requirements from all four specification types appear in the records | Mandatory |
| TQ-2.2 | Parsed requirement count equals authored count; none dropped, none invented | Mandatory |
| TQ-2.3 | Each prefix is attributed to the correct specification type / phase | Mandatory |
| TQ-2.4 | Requirement title and expected result are preserved verbatim | Mandatory |
| TQ-2.5 | Metadata key/values, including `Traces-To`, are preserved | Mandatory |
| TQ-2.6 | A duplicated requirement ID is reported as a finding, not silently collapsed | Mandatory |
| TQ-2.7 | A malformed requirement heading is reported as a finding, not silently dropped | Mandatory |

### 5.3 TQ-3 — Traceability accuracy
`test_tq3_traceability_accuracy.py`

| ID | Acceptance criterion | Class |
|---|---|---|
| TQ-3.1 | A test is attributed to its own requirement and to no other | Mandatory |
| TQ-3.2 | A multi-requirement marker yields one entry per requirement | Mandatory |
| TQ-3.3 | All tests verifying a requirement are listed against it, by real node ID | Mandatory |
| TQ-3.4 | An untested requirement is named in the coverage report and reflected in the arithmetic | Mandatory |
| TQ-3.5 | A test citing a non-existent requirement ID is flagged as a finding | Mandatory |
| TQ-3.6 | Matrix and report agree on which requirements are tested | Mandatory |

### 5.4 TQ-4 — Result fidelity (critical negative controls)
`test_tq4_result_fidelity.py`

| ID | Acceptance criterion | Class |
|---|---|---|
| TQ-4.1 | A failing test is recorded as failed, never as passed | Mandatory |
| TQ-4.2 | A run containing a failure exits non-zero | Mandatory |
| TQ-4.3 | A requirement whose only test failed is not counted as verified | Mandatory |
| TQ-4.4 | A skipped test is recorded as skipped, with its reason preserved | Mandatory |
| TQ-4.5 | A test that errored in setup is not recorded as passed | Mandatory |
| TQ-4.6 | An expected failure is not recorded as an ordinary pass | Mandatory |
| TQ-4.7 | An unexpected pass is identifiable in the record | Mandatory |
| TQ-4.8 | Summary counts account for every failure, skip, and error | Mandatory |
| TQ-4.9 | A deviation reference supplied via `--gxp-deviations` appears verbatim against the non-passing case, and its absence raises a finding | Mandatory |
| TQ-4.10 | A report from a run containing failures is visibly marked PROVISIONAL, and a clean run is marked FINAL with no banner | Mandatory |
| TQ-4.11 | A test that errored in setup is recorded with outcome `ERROR` and counted in the error total | Mandatory |

> TQ-4.1, TQ-4.3, TQ-4.5, TQ-4.8, and TQ-4.11 are the cases that most directly
> protect record integrity. Failure of any of them shall result in immediate
> withdrawal of the version from qualification use, and review of any record
> already produced with it.

### 5.5 TQ-5 — Coverage arithmetic and format consistency
`test_tq5_coverage_and_formats.py`

| ID | Acceptance criterion | Class |
|---|---|---|
| TQ-5.1 | Reported test counts equal those executed | Mandatory |
| TQ-5.2 | Pass rate recomputes from the reported counts | Mandatory |
| TQ-5.3 | Coverage rate recomputes; uncovered requirement correctly excluded | Mandatory |
| TQ-5.4 | Verification count excludes failed and skipped tests; rate denominator determinable | Mandatory |
| TQ-5.5 | Every requested output format is generated | Mandatory |
| TQ-5.6 | Counts agree across CSV, JSON, and Markdown for the same run | Mandatory |
| TQ-5.7 | PDF renders with a valid header and a plausible size | Mandatory |

### 5.6 TQ-6 — Objective evidence integrity
`test_tq6_evidence_integrity.py`

| ID | Acceptance criterion | Class |
|---|---|---|
| TQ-6.1 | Manifest is generated and its declared count matches its entries | Mandatory |
| TQ-6.2 | Every referenced evidence file exists on disk | Mandatory |
| TQ-6.3 | Stored evidence is byte-identical to what was captured | Mandatory |
| TQ-6.4 | Evidence is attributed to the correct test and requirement (verified by hash) | Mandatory |
| TQ-6.5 | Evidence timestamps fall within the execution window | Mandatory |
| TQ-6.6 | Evidence is surfaced in the human-readable report | Mandatory |
| TQ-6.7 | A thumbnail does not replace or substitute for full-size evidence | Mandatory |
| TQ-6.8 | The high-risk evidence gate is computable from the generated records | Mandatory |
| TQ-6.9 | Each evidence manifest entry carries a `sha256` value matching the bytes actually stored | Mandatory |

### 5.7 TQ-7 — Report metadata, signature handling, provenance
`test_tq7_report_metadata.py`

| ID | Acceptance criterion | Class |
|---|---|---|
| TQ-7.1 | Qualification phase recorded matches the phase requested | Mandatory |
| TQ-7.2 | Supplied signatory names are recorded verbatim | Mandatory |
| TQ-7.3 | Signature fields accept any string without authentication — **positive finding of fact** | Mandatory |
| TQ-7.4 | No placeholder name appears where no signatory was supplied | Mandatory |
| TQ-7.5 | Report timestamps are parseable ISO 8601 | Mandatory |
| TQ-7.6 | Timestamps carry an explicit timezone designator and parse as timezone-aware | Mandatory |
| TQ-7.7 | The record identifies the source revision or tag executed | Mandatory |
| TQ-7.8 | Identical input produces reproducible output apart from volatile fields (JSON, CSV, and Markdown; see §8) | Mandatory |
| TQ-7.9 | The record identifies the system name and version qualified | Mandatory |

TQ-7.3 is deliberately written so that it **passes** when the field is
unauthenticated. Its purpose is to place on the record, as established fact, that
the signature block is a printed name field. This is the evidentiary basis for
the signature model in your validation plan (see
[Risk-Based Assurance](risk-based-assurance.md) §6.10). Should a future version
add authentication, this case will fail — which is the correct signal to revisit
the Part 11 position.

TQ-7.4 is the paired safeguard: an unauthenticated field that is also
*pre-populated with a plausible default* would place a fabricated attribution in
a signature block. That is not an acceptable limitation and is Mandatory.

## 6. Execution

```bash
python -m venv .tq && . .tq/bin/activate
pip install "pytest-gxp[pdf]==<X.Y.Z>"
pip freeze > tq_pip_freeze.txt

export TZ=UTC
export TQ_PINNED_VERSION=<X.Y.Z>

pytest -c tool_qualification/pytest.ini tool_qualification/ \
       -v --tb=short | tee tq_console.log
```

`-c tool_qualification/pytest.ini` selects the suite's own configuration. It
loads the `pytester` plugin the suite requires and isolates the run from any
project-level `addopts` — including a stray `--gxp` — that would otherwise
contaminate the qualification.

The pass/fail gate is the `-m "not gap"` selection:

```bash
pytest -c tool_qualification/pytest.ini tool_qualification/ -m "not gap"
```

Retain: `tq_console.log`, `tq_evidence.jsonl`, `tq_environment.json`,
`tq_pip_freeze.txt`.

## 7. Acceptance criteria

| # | Criterion |
|---|---|
| 1 | Every Mandatory case passes. |
| 2 | Every Gap case yields the outcome recorded in §8. A gap case that now passes is investigated, and the corresponding compensating control retired or retained by decision. |
| 3 | The installed version equals the declared pin, and its content hash is recorded in the tool register. |
| 4 | The environment record is complete. |
| 5 | Review completed by a person independent of the pytest-gxp author. |
| 6 | Each entry in the accepted-limitation register (§8) has a named compensating control. |
| 7 | FRM-CSA-03 completed and approved. |

Failure of any Mandatory case: the version is **not qualified**. Do not use it
for qualification activity; remain on the previously qualified version or
remediate the tool and re-execute this protocol in full.

## 8. Accepted limitations and compensating controls

To be completed at execution and carried forward in the tool register. Expected
state for version 0.2.0:

| Ref | Finding | Compensating control | Owner |
|---|---|---|---|
| TQ-7.3 | The signature block is an **unauthenticated printed-name field**. Any string supplied at the command line or in project configuration is recorded verbatim. This is not an electronic signature within the meaning of 21 CFR Part 11 Subpart C. | The generated report is treated as an unsigned draft record. Signature is applied by an external Part 11 signing process, bound to the `artifact_manifest.sha256` digest of the reviewed artifacts. Signatory name fields are not populated at generation time and are prohibited in committed project configuration. | QA |
| PDF-1 | The rendered PDF is **not byte-reproducible**: the PDF library embeds a creation timestamp. The determinism claim verified by TQ-7.8 therefore covers the JSON, CSV, and Markdown renderings only. | The PDF is treated as a rendering of the Markdown record, not as the record of authority. The signature binds to `artifact_manifest.sha256`, which covers every generated artifact including the PDF as produced, so the specific signed PDF is still fixed and verifiable. | System Owner |

Neither entry has a failing automated case. TQ-7.3 is a Mandatory case that
passes by design in order to place the limitation on the record as fact; PDF-1 is
a scope statement on TQ-7.8. The `gap` marker set is consequently empty for
version 0.2.0, and the gate expression `-m "not gap"` selects the whole suite.

Where the tool author is a member of your organisation and independent review
per §7 criterion 5 cannot be arranged, add a third row recording the
self-attestation, its rationale, and the compensating control you rely on
instead.

### Closed gaps

The following were open gaps in earlier versions, each carrying a compensating
procedural control. All are now closed in the tool, and the corresponding
procedural control may be retired by documented decision. Verify closure by
execution rather than by reading this table: the point of the register is that
state changes are investigated.

| Ref | Former finding | Retired compensating control | Status |
|---|---|---|---|
| TQ-1.6 | No risk-tier marker | Tier carried on FRM-CSA-04 only; evidence gate applied by an external post-run script | Closed in 0.2.0 — `@pytest.mark.gxp_risk(...)` and a `Risk Tier` matrix column |
| TQ-2.6 | Duplicate requirement IDs not detected | Manual uniqueness check on requirement IDs at protocol freeze | Closed in 0.2.0 — `duplicate-requirement-id` finding |
| TQ-2.7 | Malformed headings may be silently dropped | Authored-vs-parsed requirement count reconciliation | Closed in 0.2.0 — `malformed-requirement-heading` finding |
| TQ-3.5 | Orphan requirement references not flagged | Bidirectional reconciliation at review; pre-commit check of marker IDs against parsed spec IDs | Closed in 0.2.0 — `unknown-requirement-ref` finding |
| TQ-4.9 | No deviation reference field in the record | References recorded on the review form only; no signature routing while any reference is missing | Closed in 0.2.0 — `--gxp-deviations` and a `deviation_ref` field on every record entry |
| TQ-4.10 | Report not marked provisional on failure | Review precedes signature as the only barrier | Closed in 0.2.0 — `report_metadata.status` of `PROVISIONAL` / `FINAL` with an in-document banner |
| TQ-7.6 | Timestamps not timezone-qualified | `TZ=UTC` enforced in the execution environment; timezone recorded on FRM-CSA-01 | Closed in 0.2.0 — all emitted timestamps are UTC with an explicit designator |
| TQ-7.7 | No source provenance in the record | Tag and commit SHA recorded on the readiness checklist and reconciled at review | Closed in 0.2.0 — `source_provenance` in report metadata (commit, tag, dirty flag) |
| TQ-7.8 | Output not reproducible | Artifact hash manifest generated manually post-run, pre-review | Closed in 0.2.0 — deterministic ordering across JSON / CSV / Markdown, and `artifact_manifest.sha256` written by the tool |

Setting `TZ=UTC` and recording the tag and commit on the readiness checklist
remain good practice even though the tool no longer depends on them; retiring a
control is a decision to record, not an automatic consequence of the tool
improving.

## 9. Deliverables

1. This protocol, approved before execution.
2. Executed suite results: `tq_console.log`, `tq_evidence.jsonl`,
   `tq_environment.json`, `tq_pip_freeze.txt`.
3. Completed FRM-CSA-03.
4. Tool Qualification Report stating the disposition, the qualified version and
   content hash, and the accepted-limitation register with compensating controls.
5. Tool register entry.

## 10. Approval

| Role | Name | Signature | Date |
|---|---|---|---|
| Author | | | |
| Reviewer (independent of the pytest-gxp author) | | | |
| QA Approver | | | |
