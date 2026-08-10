# WI-CSA-01 — Execution of Automated Qualification Testing Using pytest-gxp

!!! note "Template"
    Adopt this document under your own document control. Identifiers, roles,
    and references are placeholders. Nothing here is regulatory advice.

| | |
|---|---|
| **Document type** | Work Instruction |
| **Parent SOP** | `<SOP-ID>` Computer System Validation / Software Assurance |
| **Related** | Validation Plan §6 ([Risk-Based Assurance](risk-based-assurance.md)); [TQ-001](tool-qualification-protocol.md) (Tool Qualification); `SOP-01` (Document Control) |
| **Status** | DRAFT |

!!! info "Document identifiers"
    `WI-CSA-01`, `TQ-001`, `FRM-CSA-0x`, `SOP-01`, and `<SOP-ID>` are
    placeholders for your document control system's identifiers. Rename them to
    match your QMS.

---

## 1. Purpose

To define the procedure for planning, freezing, executing, reviewing, and
dispositioning automated qualification testing performed with the pytest-gxp
plugin, such that the resulting traceability matrix, evidence manifest, and
validation report constitute defensible GxP records.

## 2. Scope

Applies to all IQ, OQ, and PQ activity for GAMP 5 Category 4 and Category 5
systems where pytest-gxp is used to generate qualification records. Does not
apply to development testing performed outside a qualification run, which is
governed by `<SDLC SOP-ID>`.

## 3. Responsibilities

| Role | Responsibility |
|---|---|
| System Owner | Sections 5.1–5.5, 5.7 |
| Independent Tester/Reviewer | Section 5.5 (high-risk execution or review) |
| QA | Sections 5.2 (approval), 5.6, 5.8 |
| IT / Platform | Section 5.3 |

## 4. Prerequisites

The following shall be confirmed before any qualification execution. Recorded on
**FRM-CSA-01 Pre-Execution Readiness Checklist**.

1. Validation Plan approved, including the risk-based assurance strategy.
2. URS approved as a controlled document.
3. Derived IS/DS/FS/US specifications complete, each requirement carrying
   `Traces-To:`.
4. FRM-CSA-04 tier classification approved by QA for every requirement.
5. pytest-gxp version pinned, and that version qualified and current under
   TQ-001.
6. Target environment prepared and, for OQ in staging, environment equivalence
   evidence available.
7. SDLC prerequisites confirmed if development testing is to be credited.

## 5. Procedure

### 5.1 Author specifications and tests

1. Author each derived specification as Markdown using the prefix required by
   the qualification phase: `IS-` (IQ), `DS-` and `FS-` (OQ), `US-` (PQ). One
   requirement per heading.
2. For every requirement, include the description, the numbered requirement
   detail, and an explicit expected result. A requirement without a stated
   expected result cannot be objectively verified and shall be revised.
3. Include in the metadata block:

   ```
   #### Metadata
   Traces-To: URS-014
   Risk-Tier: 1
   Priority: High
   Owner: <name>
   ```

4. Author the verifying test(s). Apply, as a minimum:

   ```python
   @pytest.mark.gxp
   @pytest.mark.gxp_risk("high")          # high | medium | not-high — must match FRM-CSA-04
   @pytest.mark.requirements(["FS-014"])
   def test_batch_number_is_immutable_after_release(gxp_evidence, app):
       """FS-014: released batch record fields cannot be modified."""
       ...
   ```

   The `gxp_risk` tier reaches the traceability matrix as a `Risk Tier` column
   and drives the evidence gate in 5.4. An unrecognised tier value is reported
   as a warning finding and treated as unset — it does not silently become
   high-risk, so a typo in the marker is visible in the run output rather than
   in the disposition.

5. For every high-risk test, capture objective evidence via the `gxp_evidence`
   fixture. Evidence shall show the actual system state or output relied upon
   for the pass determination — not a log line asserting success.
6. For every high-risk test, include at least one negative or boundary case
   exercising the failure path.
7. No per-requirement content hash is recorded. The commit SHA captured at the
   protocol freeze (5.2.3) covers every byte of every specification and test file
   atomically, which is what binds the approval to the executed content.

### 5.2 Freeze and pre-approve the protocol

> The test suite is the protocol. Approval must precede execution.

1. Merge all specification and test changes to the release branch through normal
   review.
2. Verify the working tree is clean and no uncommitted changes exist. The report
   records a dirty-tree flag in its source provenance, so executing against a
   modified tree is visible in the record — but it is still not a valid
   qualification run.
3. Create a signed annotated tag naming the qualification phase and version, and
   record the **full commit SHA** it resolves to:

   ```bash
   git tag -s OQ-1.0.0 -m "OQ protocol for <System> v1.4.2 — frozen for execution"
   git push origin OQ-1.0.0
   git rev-parse OQ-1.0.0^{commit}     # record this value on the approval record
   ```

   The commit SHA is the identity of the frozen protocol. Record the SHA and not
   the tag name alone: a tag is a movable reference, so an approval citing only
   `OQ-1.0.0` binds to whatever that tag points at when it is later read, not to
   what was approved. Where the hosting platform supports it, protect the
   qualification tags against update and deletion.

   A subsequent edit to any requirement text produces a different commit, so it
   cannot reach an execution that cites the approved SHA. This is what makes a
   silent edit detectable, and it covers the test code and fixtures as well as the
   specification text.

4. Verify the tag before relying on it:

   ```bash
   git tag -v OQ-1.0.0                 # signature valid, expected signer
   git status --porcelain              # empty
   ```

   Where no commit-signing infrastructure is in place, use `git tag -a` and omit
   the `git tag -v` check. The commit SHA still provides the binding between the
   approval and the executed content; the signature adds attribution of *who*
   created the freeze, which is worth having but is not what makes the freeze
   effective.

5. Produce the protocol package for approval: the tagged specification files,
   the tagged test files, FRM-CSA-04, and the tag/SHA record.
6. Obtain QA approval of the protocol package. **Do not execute before approval
   is recorded.**
7. If a defect in the protocol is discovered after approval, raise a protocol
   amendment, obtain approval, re-tag (e.g. `OQ-1.0.1`), and restart from 5.3.
   Do not execute against a modified working tree.

### 5.3 Prepare and record the environment

1. Provision or confirm the target environment per the Validation Plan.
2. Record: environment identifier, container image digest or package manifest
   hash, IaC revision, application version, database version and schema
   revision, hostname, and time source.
3. Confirm system clock synchronisation to a documented time source. Report
   timestamps are emitted in UTC with an explicit designator; `TZ=UTC` in the
   execution environment remains good practice for the surrounding console log
   and shell tooling.
4. For OQ in staging, attach the environment equivalence evidence required by
   the Validation Plan.
5. Record all of the above on FRM-CSA-01.

### 5.4 Execute the qualification run

1. Check out the approved tag into a clean working directory. Confirm
   `git describe --exact-match --tags` returns the approved tag, **and** that
   `git rev-parse HEAD` matches the full commit SHA recorded on the approval
   record at 5.2.3. The tag name alone is not sufficient: a tag can be moved
   between approval and execution, and only the SHA comparison detects it.
2. Install the pinned, TQ-qualified pytest-gxp version and record the installed
   version and distribution hash.
3. Execute, supplying the qualification type and leaving signatory fields empty:

   ```bash
   pytest --gxp \
       --gxp-qualification-type=OQ \
       --gxp-output-formats=csv,json,md,pdf \
       --gxp-strict \
       -m "gxp" \
       --junitxml=junit.xml \
       | tee execution_console.log
   ```

4. **Do not** pass `--gxp-tester`, `--gxp-reviewer`, or `--gxp-approver`, and do
   not populate these in `pyproject.toml`. Signature is applied per 5.7.
   Populating names at generation time produces a printed name block that is not
   an electronic signature and undermines attributability.
5. Retain the complete console log, the JUnit XML, and the exit code as part of
   the record.
6. The high-risk evidence gate is applied by the plugin, not by an external
   script. With `--gxp-strict`, any requirement whose risk tier is `high` and
   which has no associated entry in the evidence manifest produces a
   `high-risk-no-evidence` error finding; one whose only entries are unscripted
   session records produces a `high-risk-evidence-unscripted-only` error finding,
   because a session record describes the tester's activity rather than capturing
   system state. Any error-severity finding sets a non-zero exit status. A
   qualification run is therefore executed with `--gxp-strict` on, and a zero exit
   is itself part of the evidence that the gate was satisfied.

   Verify the gate was armed rather than assuming it: the run output lists the
   findings section, and the report metadata carries a `findings_summary` with
   error and warning counts.

   !!! warning "Retired step"
       Earlier revisions of this instruction applied the evidence gate with an
       external post-run script reading the report and evidence manifest against
       an exported classification worksheet. That step is retired: the tier now
       travels with the test as a marker and the gate is enforced in-process. Do
       not maintain both — a second, divergent implementation of the gate is a
       finding in itself.

7. **Retired.** Earlier revisions required a manual `find | xargs sha256sum` step
   immediately after the run to produce the artifact hash manifest. pytest-gxp
   now writes `artifact_manifest.sha256` itself, last in the session, covering
   every generated artifact in the report directory and excluding only the
   manifest. It is `sha256sum`-compatible and can be verified in place:

   ```bash
   ( cd gxp_report_files && grep -v '^#' artifact_manifest.sha256 | shasum -a 256 -c - )
   ```

   Perform that verification before any file is moved or opened for editing, and
   retain its output. Nothing is to be generated by hand.

8. Do not re-run to obtain a more favourable result. Every execution attempt
   against the approved tag is part of the record. If a run is abandoned for
   environmental reasons, record the abandonment and the reason.

### 5.5 Independent execution or review of high-risk tests

1. High-risk tests shall be executed by, or their results reviewed by, a person
   independent of the developer of the function under test.
2. The reviewer shall inspect the captured objective evidence for each
   high-risk requirement and confirm it substantiates the pass determination. A
   green result with evidence that does not show the asserted state is not
   verified.
3. Record the reviewer, date, and outcome on FRM-CSA-02.

### 5.6 Review results and raise discrepancies

Performed against **FRM-CSA-02 Post-Execution Report Review Checklist**.

1. Reconcile the reported counts independently: total tests, passed, failed,
   skipped, errored, and requirement coverage. Confirm the reported rates are
   arithmetically consistent with the underlying test execution register, and
   consistent across the CSV, JSON, Markdown, and PDF renderings of the same
   run.
2. Reconcile the traceability matrix in both directions: no requirement without
   a test; no test citing a requirement absent from the specifications. An
   `unknown-requirement-ref` finding in the run output indicates the latter.
3. For every non-passing result, raise the record required by the Validation
   Plan and record its identifier — then supply it to the tool per 5.6.1 below.
4. For every skipped or not-executed test, record the justification against the
   requirement. The skip reason is preserved in the `test_execution` register; an
   unjustified skip shall be treated as a data integrity finding.
5. Confirm no requirement is reported as verified where its verifying test
   errored. Errors are recorded with outcome `ERROR` and counted separately from
   failures.
6. Confirm the report metadata carries the tag, commit SHA, environment
   identifiers, tool version, and timezone-qualified timestamps.
7. Confirm the artifact hash manifest is complete and each hash reproduces (see
   5.4.7).

#### 5.6.1 Supplying deviation references

Deviation and discrepancy references are assigned after investigation, which is
after the run. They are supplied to the tool as data rather than by editing
controlled test files:

```json
{
  "tests/test_batch.py::test_release_locks_fields": "DEV-2026-014",
  "FS-032": "DISC-2026-007"
}
```

```bash
pytest --gxp --gxp-deviations=deviations.json ...
```

Keys are either a pytest node ID or a requirement ID; a node ID takes precedence
over a requirement ID matching the same result. The `deviation_ref` field is
always present on every entry in the test execution register and the test case
register, and is null where no reference applies.

The references enter the record by **re-running against the approved tag**, not
by editing the generated report. An edited report is not a record. A re-run for
this purpose is an execution attempt and is accounted for under 5.4.8.

A report containing non-passing results with no deviation reference is marked
`PROVISIONAL` and carries a banner reading *PROVISIONAL — DRAFT RECORD. NOT FOR
SIGNATURE.* Such a report **shall not be routed for signature** under 5.7. Each
missing reference also produces a `missing-deviation-ref` error finding, so a
provisional report cannot be mistaken for a clean one.

A run with no non-passing results and no error findings is marked `FINAL` with no
banner.

### 5.7 Route for signature

1. Treat the generated report as an **unsigned draft record**. Confirm its
   metadata status is `FINAL`, not `PROVISIONAL`.
2. Assemble the record package: report (PDF), traceability matrix, evidence
   manifest and evidence files, console log, JUnit XML,
   `artifact_manifest.sha256`, FRM-CSA-01, FRM-CSA-02, FRM-CSA-04, environment
   record, and any deviation or discrepancy references.
3. Route through the approved electronic signature process, binding the
   signature to `artifact_manifest.sha256`, or apply wet-ink signature to the
   rendered PDF. Signatories are those named in the Validation Plan.
4. File the signed package in `<controlled repository>` per SOP-01, with the
   retention period defined in the Validation Plan.

### 5.8 Disposition

QA dispositions the run as one of:

| Disposition | Basis |
|---|---|
| **Qualified** | All Validation Plan acceptance criteria met |
| **Qualified with conditions** | Acceptance criteria met for high-risk requirements; open medium-risk discrepancies carry approved interim controls; conditions and their closure dates stated |
| **Not qualified** | Any high-risk acceptance criterion unmet, or traceability incomplete, or tool qualification not current |

## 6. Procedure — Tool re-qualification on pytest-gxp version change

Recorded on **FRM-CSA-03 Tool Qualification Checklist**.

1. Review the release notes and commit history between the currently qualified
   version and the candidate version. Record any change affecting requirement
   parsing, result determination, coverage arithmetic, evidence handling, or
   report rendering.
2. Obtain the qualification suite for the candidate version and install the
   candidate in an isolated environment from a wheel or sdist. Record version,
   distribution filename, and SHA-256 of the distribution artifact. See
   [Validating pytest-gxp](index.md) for the download and execution commands.
3. Execute the TQ-001 automated qualification suite against the candidate
   version.
4. Confirm all mandatory test cases pass. Confirm each gap-assessment case
   yields its expected outcome; a gap-assessment case that changes state is
   investigated and the tool qualification report updated.
5. Where a mandatory case fails, the candidate version shall not be used for
   qualification activity. Raise a defect against pytest-gxp and either remain
   on the qualified version or remediate and re-test.
6. Issue or amend the TQ-001 report, obtain approval, and record the newly
   qualified version and its hash in the tool register.
7. Update the pinned version in the project's dependency lock file under change
   control. The pin shall be exact (`==`), never a range.

## 7. Records generated

| Record | Retention |
|---|---|
| FRM-CSA-01 Pre-Execution Readiness Checklist | Per VP |
| FRM-CSA-02 Post-Execution Report Review Checklist | Per VP |
| FRM-CSA-03 Tool Qualification Checklist | Per VP |
| FRM-CSA-04 Requirement Risk Classification Worksheet | Per VP |
| FRM-CSA-05 Unscripted Test Session Record | Per VP |
| FRM-CSA-06 Change Risk Assessment | Per VP |
| Traceability matrix, validation report, evidence manifest, evidence files | Per VP |
| Execution console log, JUnit XML, `artifact_manifest.sha256` | Per VP |
| Deviation reference input file (`deviations.json`) | Per VP |
| Protocol tag and commit SHA record | Life of system |

## 8. Common failure modes and their controls

| Failure mode | Control |
|---|---|
| Tests adjusted after results observed | Tag-based protocol pre-approval (5.2); `git describe --exact-match` gate (5.4.1); dirty-tree flag in report source provenance |
| Approver name attributed by anyone with repository access | Signatory fields prohibited in committed configuration (5.4.4) |
| Requirement text edited after approval | Approval binds to the full commit SHA, not the tag name (5.2.3); an edit produces a different commit, and the executed SHA is checked against the approved one (5.4.1) |
| Duplicate or malformed requirement IDs distorting the denominator | `duplicate-requirement-id` and `malformed-requirement-heading` findings surfaced in the run output and report |
| Silent skip inflating apparent coverage | Skip reason preserved in the test execution register; unjustified skip is a finding (5.6.4) |
| Errored test counted as unverified-but-unnoticed | Errors recorded as `ERROR` and counted separately (5.6.5) |
| High-risk requirement verified by a green assertion with no evidence | In-process evidence gate: `--gxp-strict` plus `gxp_risk("high")` (5.4.6) |
| Unscripted session record substituted for objective evidence at Tier 1 | `high-risk-evidence-unscripted-only` finding; the gate distinguishes evidence type, not merely presence (5.4.6) |
| Non-passing result routed for signature without a deviation reference | `missing-deviation-ref` finding and `PROVISIONAL` report status (5.6.1) |
| IQ evidence taken from CI container rather than production | Environment table, no substitution for IQ (Validation Plan) |
| Report re-generated after review, changing content | `artifact_manifest.sha256` written by the tool at session end, verified pre-review, and bound to the signature (5.4.7, 5.7.3) |
| Tool defect silently corrupting records | TQ-001 negative controls, re-run on every version change (§6) |
