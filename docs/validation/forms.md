# Checklists and Forms

!!! note "Template"
    Adopt this document under your own document control. Identifiers, roles,
    and references are placeholders. Nothing here is regulatory advice.

Companion forms to the [work instruction](work-instruction.md) and the
[risk-based assurance strategy](risk-based-assurance.md). Each form is intended
to become a controlled form template in your QMS.

!!! info "Document identifiers"
    `FRM-CSA-01` … `FRM-CSA-06`, `WI-CSA-01`, `TQ-001`, and `SOP-01` are
    placeholders for your document control system's identifiers. Rename them to
    match your QMS, and keep the cross-references consistent when you do.

Response convention throughout: **Y** (satisfied) / **N** (not satisfied) /
**N/A** (not applicable, with rationale). Any **N** blocks progression until
resolved or a documented exception is approved by QA.

Risk tiers below use the three tiers defined in the
[risk-based assurance strategy](risk-based-assurance.md#64-process-risk-tiers):
Tier 1 (high), Tier 2 (medium), Tier 3 (not high). These correspond to the
`@pytest.mark.gxp_risk("high" | "medium" | "not-high")` marker values.

---

## FRM-CSA-01 — Pre-Execution Readiness Checklist

Completed by System Owner; approved by QA **before** execution.

| Field | Entry |
|---|---|
| System / version | |
| Qualification phase | IQ / OQ / PQ |
| Protocol tag | |
| Commit SHA (full) | |
| Scheduled execution date | |

### A. Documentation readiness

| # | Check | Y/N/NA | Evidence / comment |
|---|---|---|---|
| A1 | Validation Plan approved and current, including the risk-based assurance strategy | | |
| A2 | URS approved as a controlled document | | |
| A3 | Derived specifications complete for this phase | | |
| A4 | Every requirement has an explicit expected result | | |
| A5 | Every requirement carries a `Traces-To:` value resolving to an approved URS requirement | | |
| A6 | Every requirement carries a `Requirement-Hash` matching its current text | | |
| A7 | FRM-CSA-04 tier classification approved by QA for every requirement in scope | | |
| A8 | Prior phase closed (OQ not commenced before IQ disposition, etc.) or concurrent execution justified | | |

### B. Protocol freeze

| # | Check | Y/N/NA | Evidence / comment |
|---|---|---|---|
| B1 | All specification and test changes merged to the release branch | | |
| B2 | Working tree clean; no uncommitted changes | | |
| B3 | Annotated tag created and pushed | | |
| B4 | `git describe --exact-match --tags` returns the approved tag | | |
| B5 | Protocol package assembled (specs, tests, FRM-CSA-04, tag/SHA record) | | |
| B6 | QA approval of protocol package recorded, dated **before** execution date | | |

### C. Test design

| # | Check | Y/N/NA | Evidence / comment |
|---|---|---|---|
| C1 | Every requirement in scope has ≥1 linked test via `@pytest.mark.requirements` | | |
| C2 | Every test's `gxp_risk` marker matches its FRM-CSA-04 tier | | |
| C3 | Every Tier 1 test captures objective evidence via `gxp_evidence` | | |
| C4 | Every Tier 1 requirement has ≥1 negative / boundary / error-path case | | |
| C5 | No test references a requirement ID absent from the specifications | | |
| C6 | Data integrity requirements (audit trail, access control, immutability) have dedicated tests | | |
| C7 | Tier 1 executor or reviewer identified and independent of the developer of the function under test | | |

### D. Tool readiness

| # | Check | Y/N/NA | Evidence / comment |
|---|---|---|---|
| D1 | `pytest-gxp` version pinned exactly (`==`) in the lock file | | |
| D2 | That version qualified under TQ-001 and the qualification is current | | |
| D3 | Installed version and distribution SHA-256 recorded below | | |
| D4 | Python version, pytest version, and OS/image digest recorded below | | |
| D5 | PDF rendering dependencies installed and functional | | |
| D6 | `--gxp-strict` will be passed at execution, so the high-risk evidence gate is armed | | |

```
pytest-gxp version : ______________  dist SHA-256: ______________________________
pytest version     : ______________  Python: ____________  OS/image digest: ______
```

### E. Environment

| # | Check | Y/N/NA | Evidence / comment |
|---|---|---|---|
| E1 | Environment matches that required by the Validation Plan for this phase | | |
| E2 | For IQ / PQ: execution is against the **production** deployment | | |
| E3 | For OQ in staging: environment equivalence rationale approved and evidence attached | | |
| E4 | Container image digest / package manifest hash recorded | | |
| E5 | IaC revision recorded | | |
| E6 | Application, database, and schema versions recorded | | |
| E7 | Clock synchronised to a documented time source; timezone explicit | | |
| E8 | Test data prepared; source and any de-identification documented | | |
| E9 | Access controls in the target environment configured as intended (not relaxed for testing) | | |

### F. Credited development testing (complete only if crediting)

| # | Check | Y/N/NA | Evidence / comment |
|---|---|---|---|
| F1 | SDLC / configuration-management procedure documented and in force | | |
| F2 | Protected branches technically enforced on the release branch | | |
| F3 | Code review evidenced per merge by a non-author reviewer | | |
| F4 | CI logs and coverage output retained for the required period | | |
| F5 | Test code under the same change control as application code | | |
| F6 | Specific credited test identifiers named in the traceability matrix (not cited in aggregate) | | |
| F7 | No Tier 1 requirement is being credited to development testing | | |

**Sign-off**

| Role | Name | Signature | Date |
|---|---|---|---|
| System Owner (prepared) | | | |
| QA (approved to execute) | | | |

---

## FRM-CSA-02 — Post-Execution Report Review Checklist

Completed by the independent reviewer; approved by QA.

| Field | Entry |
|---|---|
| Protocol tag / SHA | |
| Execution date and time (with timezone) | |
| Executed by | |
| Exit code | |
| Report metadata status | ☐ FINAL ☐ PROVISIONAL |
| Report artifact SHA-256 (from `artifact_manifest.sha256`) | |

### A. Execution integrity

| # | Check | Y/N/NA | Comment |
|---|---|---|---|
| A1 | Execution performed against the approved tag; report source provenance shows the expected commit and tag, and a clean tree | | |
| A2 | Installed tool version matches the TQ-qualified pinned version, per report metadata `generator` | | |
| A3 | Environment identifiers in the report match FRM-CSA-01 Section E | | |
| A4 | Complete console log retained | | |
| A5 | All execution attempts against this tag are accounted for, including abandoned runs and re-runs to supply deviation references | | |
| A6 | `artifact_manifest.sha256` verified pre-review and every hash reproduces | | |
| A7 | Signatory name fields were **not** populated at generation time | | |
| A8 | Report timestamps carry an explicit timezone designator | | |
| A9 | `findings_summary` reviewed; every error and warning finding assessed and dispositioned | | |

### B. Result fidelity

| # | Check | Y/N/NA | Comment |
|---|---|---|---|
| B1 | Total / passed / failed / skipped / errored counts independently reconciled against the test execution register | | |
| B2 | Reported pass rate arithmetically consistent | | |
| B3 | Reported coverage and verification rates arithmetically consistent | | |
| B4 | Counts consistent across CSV, JSON, Markdown, and PDF renderings of the same run | | |
| B5 | No requirement reported as verified where its verifying test failed, errored, or was skipped | | |
| B6 | No test that errored is reported as passed | | |
| B7 | Any result achieved only on repeat execution is recorded, with both outcomes | | |

### C. Traceability

| # | Check | Y/N/NA | Comment |
|---|---|---|---|
| C1 | Every requirement in scope appears in the matrix | | |
| C2 | No requirement appears in the uncovered list, or each is justified and reclassified | | |
| C3 | No test cites a requirement ID absent from the specifications (no `unknown-requirement-ref` finding) | | |
| C4 | Requirement hashes in the matrix match the tagged specification text | | |
| C5 | Requirement-to-phase mapping correct (`IS-`→IQ, `DS-`/`FS-`→OQ, `US-`→PQ) | | |
| C6 | Matrix `Risk Tier` values match FRM-CSA-04 for every requirement | | |

### D. Evidence

| # | Check | Y/N/NA | Comment |
|---|---|---|---|
| D1 | Every Tier 1 requirement has ≥1 evidence artifact | | |
| D2 | Each evidence file referenced in the manifest exists on disk | | |
| D3 | Each manifest entry's `sha256` matches the stored file | | |
| D4 | Evidence is attributed to the correct test and requirement | | |
| D5 | **Evidence substantiates the pass determination** — reviewer inspected the artifact, not only the result | | |
| D6 | Evidence timestamps fall within the execution window | | |
| D7 | Thumbnails are derived images, not substituted for full-size evidence | | |
| D8 | Evidence contains no unnecessary personal or patient-identifying data | | |

### E. Discrepancies

| # | Check | Y/N/NA | Comment |
|---|---|---|---|
| E1 | Every FAILED result carries a `deviation_ref` in the record, matching the raised deviation | | |
| E2 | Every SKIPPED / NOT_EXECUTED result has a recorded justification; the preserved skip reason is consistent with it | | |
| E3 | Every ERROR has a discrepancy record; affected requirements not treated as verified | | |
| E4 | Retests, where performed, reference the original record and were executed under the approved tag or an approved amendment | | |
| E5 | No Tier 1 deviation remains open | | |
| E6 | Report metadata status is `FINAL`; no `PROVISIONAL` banner present | | |

### F. Disposition

| Disposition | ☐ Qualified ☐ Qualified with conditions ☐ Not qualified |
|---|---|
| Conditions and closure dates | |
| Rationale | |

| Role | Name | Signature | Date |
|---|---|---|---|
| Independent Reviewer | | | |
| QA (disposition) | | | |

---

## FRM-CSA-03 — pytest-gxp Tool Qualification Checklist

Completed on initial qualification and on every version change. Supports
[TQ-001](tool-qualification-protocol.md).

| Field | Entry |
|---|---|
| Currently qualified version | |
| Candidate version | |
| Distribution filename | |
| Distribution SHA-256 | |
| Python / pytest versions used for qualification | |
| Reason for re-qualification | ☐ initial ☐ version change ☐ dependency change ☐ periodic ☐ defect response |

### A. Change review

| # | Check | Y/N/NA | Comment |
|---|---|---|---|
| A1 | Release notes and commit range reviewed between qualified and candidate versions | | |
| A2 | Changes affecting **requirement parsing** identified and assessed | | |
| A3 | Changes affecting **result determination** identified and assessed | | |
| A4 | Changes affecting **coverage arithmetic** identified and assessed | | |
| A5 | Changes affecting **evidence handling** identified and assessed | | |
| A6 | Changes affecting **report rendering or metadata** identified and assessed | | |
| A7 | Transitive dependency changes reviewed | | |
| A8 | Supplier-side records available (repository history, CI results, release process) | | |

### B. Automated suite execution

| # | Check | Y/N/NA | Comment |
|---|---|---|---|
| B1 | Qualification suite obtained from the sdist or tagged release for the candidate version | | |
| B2 | Candidate installed from a wheel or sdist, **not** editable, in an isolated environment | | |
| B3 | `TQ_PINNED_VERSION` and `TZ=UTC` set; suite executed per TQ-001 §6 | | |
| B4 | All **mandatory** test cases (TQ-1.x through TQ-7.x) passed | | |
| B5 | Each **gap-assessment** case yielded its documented expected outcome | | |
| B6 | Any gap-assessment case that changed state investigated and documented | | |
| B7 | `tq_console.log`, `tq_evidence.jsonl`, `tq_environment.json`, and `tq_pip_freeze.txt` retained | | |

### C. Independence of the qualification

| # | Check | Y/N/NA | Comment |
|---|---|---|---|
| C1 | Qualification suite execution reviewed by a person other than the author of the pytest-gxp code | | |
| C2 | Supplier role (package author) and user role (this organisation's qualification) documented as distinct | | |
| C3 | Where C1 cannot be satisfied, the self-attestation is recorded as a limitation with a stated compensating control | | |
| C4 | Negative controls confirmed present: failing test surfaces as FAILED; errored test surfaces as ERROR; uncovered requirement surfaces as uncovered; evidence cross-attribution detected | | |

### D. Outcome

| # | Item | Entry |
|---|---|---|
| D1 | Disposition | ☐ Qualified for use ☐ Not qualified |
| D2 | Accepted limitations carried forward (list each finding and its compensating procedural control) | |
| D3 | Procedural controls retired because the corresponding gap is now closed in the tool (list, with the decision reference) | |
| D4 | Tool register updated with version and hash | |
| D5 | Project lock file pin updated under change control | |

| Role | Name | Signature | Date |
|---|---|---|---|
| Performed by | | | |
| Reviewed by (independent) | | | |
| QA approved | | | |

---

## FRM-CSA-04 — Requirement Risk Classification Worksheet

One row per requirement. Approved by QA before protocol freeze. Maintain as CSV
alongside the specifications, so that classifications can be reconciled against
the `Risk Tier` column of the generated traceability matrix at review.

**Column definitions**

| Column | Content |
|---|---|
| `requirement_id` | e.g. `FS-014` |
| `requirement_title` | From the specification heading |
| `traces_to` | URS requirement ID |
| `gxp_critical` | Y/N — Q1 per the risk-based assurance strategy |
| `q1_rationale` | Why failure could / could not compromise safety, quality, or record integrity |
| `impact` | Direct / Indirect / N/A — Q2 per the risk-based assurance strategy |
| `compensating_control` | **Required if Indirect.** Name the specific detection control. "User would notice" is not acceptable. |
| `detectable_before_reliance` | Y/N — would failure be detected before the record is relied on or product released? |
| `risk_tier` | 1 / 2 / 3 |
| `gxp_risk_marker` | `high` / `medium` / `not-high` — the marker value that must appear on the verifying test |
| `assurance_method` | Scripted+evidence / Scripted automated / Unscripted / Credited dev testing |
| `credited_test_ids` | Required if `assurance_method` = Credited dev testing |
| `negative_testing_required` | Y/N |
| `downgrade_rationale` | Required if the tier was reduced from the default assignment |
| `classified_by` / `date` | |
| `qa_approved_by` / `date` | |

**Worked examples**

| requirement_id | gxp_critical | impact | compensating_control | risk_tier | gxp_risk_marker | assurance_method |
|---|---|---|---|---|---|---|
| `FS-014` Released batch record fields immutable | Y | Direct | — | 1 | `high` | Scripted + evidence |
| `FS-021` Audit trail captures user, timestamp, old and new value | Y | Direct | — | 1 | `high` | Scripted + evidence |
| `FS-032` Batch report totals recalculated from source on render | Y | Indirect | Independent recalculation by QA reviewer against source data before release, per `<SOP>` | 2 | `medium` | Scripted automated |
| `FS-047` Result table sortable by column | N | N/A | — | 3 | `not-high` | Unscripted |
| `IS-003` Application deployed at pinned version with expected file inventory | Y | Direct | — | 1 | `high` | Scripted + evidence |

**Classification integrity rules**

1. Where the tier is contested, assign the higher tier.
2. A downgrade from Tier 1 to Tier 2 requires a named compensating control
   **and** documented QA concurrence.
3. `detectable_before_reliance` = N forces Tier 1 regardless of `impact`.
4. Reclassification after execution has begun requires a protocol amendment.
5. The `gxp_risk_marker` column and the marker on the verifying test are
   reconciled at FRM-CSA-02 C6 against the matrix `Risk Tier` column. A
   worksheet tier that does not reach the record is not an enforced tier.

---

## FRM-CSA-05 — Unscripted Test Session Record

For Tier 3 assurance, and for supplementary exploratory testing at any tier. One
record per session. The session charter is approved before the session begins.

!!! tip "Recording the session as evidence"
    The fields below can be captured as an evidence artifact inside the run
    rather than transcribed by hand afterwards. The `gxp_evidence` fixture
    provides:

    ```python
    @pytest.mark.gxp
    @pytest.mark.gxp_risk("not-high")
    @pytest.mark.requirements(["US-012"])
    def test_result_table_exploratory_session(gxp_evidence):
        gxp_evidence.record_unscripted_session(
            charter="Explore result table sorting and filtering; a problem is "
                    "any ordering that misrepresents the underlying data.",
            tester="A. Tester, QA Analyst",
            duration_minutes=45,
            observations=[
                "Sorted by batch number ascending and descending; order matched source query.",
                "Filtered to a single site; row count reconciled against the database.",
                "Sorted an empty result set; no error, empty table rendered.",
            ],
            defects=["DEF-2026-031: column header tooltip truncated at narrow widths"],
        )
    ```

    The session record is written as an evidence entry in the manifest with UTC
    timestamps, attributed to the test that recorded it, and appears in the
    human-readable report as a labelled list. Use it so the session record is
    part of the same record set — and the same hash manifest — as the rest of the
    run. Complete the form below for the fields the API does not carry
    (charter approval, sign-off, tier reclassification assessment), and cross-
    reference the evidence entry ID.

| Field | Entry |
|---|---|
| Session ID | |
| Evidence entry ID (from the manifest) | |
| System / version / environment | |
| Requirements or functional area in scope | |
| Risk tier of items in scope | |
| **Charter** — what is being explored, and what would constitute a problem | |
| Charter approved by / date | |
| Tester (name, role) | |
| Start / end time (with timezone) | |
| Duration (active testing) | |

**Session log** — record what was actually done, not what was intended. These
rows correspond to the `observations` list.

| # | Area explored | Action taken | Observation | Assessment |
|---|---|---|---|---|
| 1 | | | | OK / Anomaly / Defect |
| 2 | | | | |

**Findings** — these rows correspond to the `defects` list.

| # | Description | Severity | Defect / discrepancy ref | Requirement affected | Tier reclassification needed? |
|---|---|---|---|---|---|
| | | | | | |

**Session conclusion**

| Field | Entry |
|---|---|
| Coverage achieved against charter | Full / Partial (state gaps) |
| Areas deliberately not explored, and why | |
| Any finding indicating a requirement is under-classified | |
| Evidence attached (screenshots, notes, exports) | |
| Conclusion for the requirements in scope | Acceptable / Not acceptable / Further testing required |

| Role | Name | Signature | Date |
|---|---|---|---|
| Tester | | | |
| Reviewed by | | | |

> A session record showing only "explored the module, no issues found" does not
> constitute assurance evidence. The log must show what was actually exercised.

---

## FRM-CSA-06 — Change Risk Assessment

Completed for every change to the system after initial qualification.

| Field | Entry |
|---|---|
| Change ID / change control ref | |
| Description of change | |
| Requestor / date | |
| Category | ☐ application code ☐ configuration ☐ infrastructure / dependency ☐ specification ☐ `pytest-gxp` version ☐ data model |

### A. Impact assessment

| # | Question | Y/N | Detail |
|---|---|---|---|
| A1 | Does the change introduce a new requirement? | | |
| A2 | Does it alter the behaviour verified by any existing requirement? | | |
| A3 | Does it affect any **Tier 1** requirement? | | |
| A4 | Does it affect audit trail, access control, electronic signature, or record retention behaviour? | | |
| A5 | Does it affect a calculation, algorithm, or decision rule relied upon for a GxP outcome? | | |
| A6 | Does it alter the runtime, container base image, or any pinned dependency? | | |
| A7 | Does it invalidate the OQ environment equivalence rationale? | | |
| A8 | Does any existing tier classification require revision? | | |
| A9 | Requirements affected (list IDs and tiers) | | |

### B. Routing determination

| Condition | Route | Selected |
|---|---|---|
| A3 = Y, or A1 = Y introducing a Tier 1 requirement, or A4 = Y, or A5 = Y | Protocol amendment; re-execute affected Tier 1 tests plus full regression; partial revalidation report | ☐ |
| A2 = Y affecting Tier 2 only | Full automated regression pass plus this assessment, under change control; no revalidation report | ☐ |
| Tier 3 only, or no requirement impact | Standard change control; retain regression pass as evidence | ☐ |
| A6 = Y | Re-execute IQ tests plus full regression; reassess environment equivalence | ☐ |
| `pytest-gxp` version change | Re-qualify per TQ-001 and FRM-CSA-03 before the next qualification run | ☐ |

> A regression pass alone is never sufficient where the change introduces or
> alters a Tier 1 requirement.

### C. Execution and closure

| # | Item | Entry |
|---|---|---|
| C1 | Regression run tag / SHA | |
| C2 | Regression outcome (counts, any non-passing result and its record) | |
| C3 | Tier 1 tests re-executed (IDs) | |
| C4 | Specifications and FRM-CSA-04 updated | |
| C5 | Validated state maintained? | Y / N |

| Role | Name | Signature | Date |
|---|---|---|---|
| Assessed by | | | |
| QA approved | | | |
