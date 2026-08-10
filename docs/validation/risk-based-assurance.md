# Risk-Based Assurance Strategy

!!! note "Template"
    Adopt this document under your own document control. Identifiers, roles,
    and references are placeholders. Nothing here is regulatory advice.

**Intended placement:** Section 6 of your Validation Plan, `<VP-ID>` —
`<System Name>`
**GAMP 5 software category:** 5 (Custom / bespoke application)
**Status:** DRAFT — for insertion into the Validation Plan prior to approval

!!! info "Placeholders and identifiers"
    Placeholders are marked `<...>`. `FRM-CSA-0x`, `WI-CSA-01`, `TQ-001`, and
    `SOP-01` are placeholders for your document control system's identifiers —
    rename them to match your QMS. Section numbers are retained as `6.x` on the
    assumption this becomes Section 6 of your plan; renumber to suit. Verify the
    currency of every external reference in §6.2 before issue.

---

## 6.1 Purpose

This section defines how assurance effort is allocated across the requirements of
`<System Name>`. It establishes:

- the method for determining the GxP impact and process risk of each requirement;
- the assurance activity, evidence type, and independence requirement applicable
  to each risk tier;
- the conditions under which development testing may be credited as assurance
  evidence;
- the acceptance criteria for the qualification as a whole.

The intent is that assurance effort is **proportionate and documented**, not
uniform. Uniform effort is neither required nor desirable: it dilutes scrutiny of
the functions that matter.

## 6.2 Regulatory basis and standing of the CSA framework

| Reference | Standing for this validation |
|---|---|
| 21 CFR 211 subparts (cGMP for finished pharmaceuticals) | **Binding** where applicable to your products. |
| 21 CFR Part 11 — Electronic Records; Electronic Signatures | **Binding** where the system creates, modifies, maintains, or transmits electronic GxP records, or applies electronic signatures. |
| EU GMP Annex 11 — Computerised Systems | **Binding** for EU-facing activity. |
| ICH Q9(R1) — Quality Risk Management | Applied as the risk-assessment framework. |
| ISPE GAMP 5, 2nd Edition (2022) | Adopted as the lifecycle and categorisation framework. |
| FDA, *Computer Software Assurance for Production and Quality Management System Software* — cite the revision current at the date of approval | **Adopted voluntarily** as the critical-thinking framework for allocating assurance effort. |

**Applicability statement (retain in the approved plan, adapted to your
products).** The CSA guidance was issued by CDRH and CBER for medical device
production and quality system software, in consultation with CDER. It is not, on
its own terms, an applicable requirement for pharmaceutical products regulated
under 21 CFR 211. **The regulated organisation** adopts the CSA framework because
it represents current FDA thinking on risk-based software assurance and is
supported by ISPE and PDA consensus for GMP environments. Adoption of CSA does
**not** relax any Part 11 or Annex 11 control: audit trail, access control,
electronic signature, and record retention requirements apply in full and are
addressed in Section `<X>`.

**Scope limitation.** CSA reduces *testing and documentation effort where risk is
low*. It does not reduce effort where risk is high; for Tier 1 requirements
(§6.4) the rigour required by this plan is equal to or greater than that of
traditional scripted CSV.

## 6.3 GxP impact determination

Every requirement in the Installation, Design, Functional, and User
Specifications is assessed against two sequential questions. The determination
and its rationale are recorded on
**[FRM-CSA-04 Requirement Risk Classification Worksheet](forms.md#frm-csa-04-requirement-risk-classification-worksheet)**,
which is approved by QA prior to protocol freeze.

**Q1 — Is the function GxP-critical?**
Would credible failure or incorrect operation of this function have the potential
to compromise patient safety, product quality, or the integrity of a GxP record
or decision?

**Q2 — Is the impact direct or indirect?**

- **Direct** — the software itself performs, controls, calculates, or determines
  the GxP outcome, and there is no independent downstream control that would
  reliably detect the failure before the record is relied upon or the product is
  released.
- **Indirect** — the software supports a GxP activity, and a compensating
  detection control exists (independent human review, reconciliation against a
  second source, secondary calculation check, or downstream verification step).
  The compensating control **must be named** in the worksheet; "user would
  probably notice" is not a compensating control.

## 6.4 Process risk tiers

| Tier | Designation | `gxp_risk` marker | Assignment rule |
|---|---|---|---|
| **Tier 1** | High process risk | `high` | Q1 = Yes **and** Q2 = Direct. Also assigned, irrespective of Q2, where failure would be undetectable prior to reliance on the record or release of the product. |
| **Tier 2** | Medium process risk | `medium` | Q1 = Yes **and** Q2 = Indirect, with a named and effective compensating detection control. |
| **Tier 3** | Not high process risk | `not-high` | Q1 = No. Function is productivity, presentation, convenience, or otherwise non-GxP. |

Tier assignment is **per requirement**, not per system. A Category 5 application
will normally contain requirements in all three tiers, and it is expected that
the majority fall in Tiers 2 and 3.

**Escalation defaults.** Where the tier is contested or the compensating control
is arguable, the requirement is assigned to the **higher** tier. Downgrades from
Tier 1 to Tier 2 require documented QA concurrence and a stated rationale on
FRM-CSA-04.

**Tier in the record.** The tier travels with the test as
`@pytest.mark.gxp_risk("high" | "medium" | "not-high")` and appears as a
`Risk Tier` column in the generated traceability matrix. Where several tests cite
one requirement, the requirement takes the highest tier among them. An
unrecognised tier value produces a warning finding and is treated as unset rather
than silently defaulting — so a mis-typed marker is visible in the run output
instead of in the disposition. A tier that exists only on the worksheet and never
reaches the record is not an enforced tier.

## 6.5 Assurance activity matrix

| | **Tier 1 — High** | **Tier 2 — Medium** | **Tier 3 — Not high** |
|---|---|---|---|
| **Primary method** | Scripted testing, pre-approved at step level | Scripted automated testing (pass/fail) | Unscripted testing (exploratory / scenario / ad-hoc), **or** credited development testing per §6.6 |
| **Negative / boundary / error-handling testing** | Required; failure paths explicitly exercised | Required where the risk rationale identifies a credible failure mode | Not required |
| **Data integrity testing** (audit trail, access control, record immutability) | Required | Required where the requirement touches a GxP record | Not applicable |
| **Independence of execution** | Executor independent of the developer of the function under test | Automated execution in CI acceptable; results reviewed by a person independent of the developer | Developer may execute |
| **Pre-approval of the test** | Mandatory — test code frozen and approved at a tagged commit before execution (§6.8) | Mandatory — same tag | Not required; session charter approved before the session |
| **Objective evidence** | Captured per requirement: screenshot, command output, directory listing, or record extract, each timestamped and attributable | Result record in the traceability matrix; evidence at the executor's discretion | Aggregate session record on **FRM-CSA-05** |
| **pytest-gxp implementation** | `@pytest.mark.gxp`, `@pytest.mark.gxp_risk("high")`, `@pytest.mark.requirements([...])`, `gxp_evidence` capture mandatory | `@pytest.mark.gxp`, `@pytest.mark.gxp_risk("medium")`, `@pytest.mark.requirements([...])` | Excluded from the `--gxp` qualification run, or marked `gxp_risk("not-high")`; recorded via `gxp_evidence.record_unscripted_session(...)` on FRM-CSA-05, or cited as credited development testing |
| **Coverage acceptance criterion** | 100% of Tier 1 requirements verified by ≥1 passing scripted test with attached objective evidence | 100% of Tier 2 requirements verified by ≥1 passing test | ≥1 documented unscripted session, or a credited-testing citation, per functional area |
| **Handling of non-passing results** | Formal deviation record; QA approval required to close; retest under the original tag or an approved amendment | Discrepancy log entry with technical resolution and retest reference | Defect ticket; no deviation required unless reclassification results |

**Enforcement.** The Tier 1 evidence requirement is enforced programmatically,
not by inspection. Running with `--gxp-strict`, a requirement at tier `high` with
no evidence entry naming it produces a `high-risk-no-evidence` error finding.
Because the gate would otherwise count entries without regard to what they
contain, a requirement whose *only* evidence entries are unscripted session
records produces a second error finding,
`high-risk-evidence-unscripted-only`: a session record states what a tester did,
not what the system did, and cannot discharge the Tier 1 evidence requirement
alone. A session record captured *alongside* a state capture is unaffected, since
supplementary exploratory testing is permitted at any tier.

Both are error severity, and any error-severity finding sets a non-zero exit
status. The qualification run therefore fails rather than reporting a Tier 1
requirement as verified on the strength of a green assertion alone, or on the
strength of a narrative substituted for a capture. See
[WI-CSA-01 §5.4](work-instruction.md#54-execute-the-qualification-run).

`--gxp-strict` is off by default, so that enabling the plugin cannot change the
pass/fail outcome of an ordinary development run. Arming it is a step in the
qualification procedure, and its presence is confirmed on
[FRM-CSA-01 D6](forms.md#frm-csa-01-pre-execution-readiness-checklist).

## 6.6 Crediting development testing as assurance evidence

Development testing (unit, integration, and contract tests executed in CI) may be
cited as assurance evidence for **Tier 2 and Tier 3 requirements only**. It shall
**not** be credited for any Tier 1 requirement.

Crediting is permitted only where **all** of the following prerequisites are
demonstrably in place and are cited in the Validation Summary Report:

1. A documented and effective SDLC / configuration-management procedure
   (`<SOP-ID>`) governs the codebase.
2. Source code and test code are held in version control with protected
   branches; direct commits to the release branch are prevented by technical
   control.
3. Code review is evidenced per merge, by a reviewer other than the author, and
   the review record is retained.
4. CI execution logs, including test results and coverage output, are retained
   for the record-retention period defined in Section `<X>`.
5. The test code itself is under the same change control as the application code.
6. The specific test identifiers being credited are named in the traceability
   matrix, not cited in the aggregate. The matrix records real pytest node IDs in
   its `Test Node ID` column, which is what makes a per-test citation possible.

Where any prerequisite is not met, the affected requirements revert to the
scripted testing route for their tier.

## 6.7 Qualification environments

| Phase | Requirement prefix | Execution environment | Basis |
|---|---|---|---|
| IQ | `IS-` | **Production deployment.** No substitution permitted. | Installation evidence must describe the installed instance actually in use. |
| OQ | `DS-`, `FS-` | Production-equivalent staging environment | Permitted only with an approved environment equivalence rationale (§6.7.1) |
| PQ | `US-` | **Production deployment**, with production or production-representative data and the intended user population | Performance in intended use cannot be demonstrated elsewhere. |

### 6.7.1 Environment equivalence rationale

Where OQ is executed in staging, the following shall be documented and verified,
and the verification evidence retained with the OQ record:

- identical container image digest, or identical package manifest with pinned
  versions and matching hashes;
- infrastructure provisioned from the same infrastructure-as-code definition at
  the same revision;
- identical application configuration, other than endpoints, secrets, and
  dataset;
- documented enumeration of every difference, with an impact assessment for each.

Any difference assessed as capable of affecting a Tier 1 requirement invalidates
the equivalence rationale for that requirement, which shall then be executed in
production.

## 6.8 Protocol pre-approval and execution integrity

Because the test suite *is* the protocol, protocol pre-approval is implemented as
follows. The full procedure is in [WI-CSA-01](work-instruction.md).

1. Specification files and test code are frozen at a specific commit and
   annotated tag (e.g. `OQ-1.0.0`).
2. The tagged content is reviewed and **approved as the executable protocol**
   before any qualification execution.
3. Execution is performed against the tag. The commit SHA, tag, and dirty-tree
   flag are captured automatically in the report's `source_provenance` metadata,
   alongside the generator name and version; environment identifiers are recorded
   on FRM-CSA-01. Where git is unavailable, the provenance block records
   `unavailable` rather than a fabricated value, and `--gxp-source-commit` /
   `--gxp-source-tag` may be supplied explicitly.
4. Any change to specifications or test code after approval requires an approved
   protocol amendment and re-tagging. Re-execution against an untagged or
   modified working tree is not a valid qualification run — and a dirty tree is
   visible in the record.

This control exists to prevent tests being authored or adjusted after results are
observed. Absence of it is the most predictable audit finding against an
automated qualification approach.

## 6.9 Specification and controlled-document boundary

| Artifact | Control status | Custodian |
|---|---|---|
| User Requirements Specification | **Controlled document** in the QMS under SOP-01; approved and signed | QA |
| Installation / Design / Functional Specifications (`.md` in the repository) | **Derived specifications** under configuration management; each requirement carries a `Traces-To:` field citing the URS requirement | System owner |
| Test code | Under configuration management; frozen at tag per §6.8 | System owner |
| Traceability matrix, validation report, evidence manifest, `artifact_manifest.sha256` | **GxP records**, generated; controlled on issue per §6.10 | QA |

Derived specifications are frozen by tag at §6.8, and the approval binds to the
**full commit SHA** that tag resolves to rather than to the tag name. A subsequent
edit to requirement text produces a different commit, so it cannot reach an
execution citing the approved SHA — a silent edit is detectable rather than
passing unnoticed, and the same control covers the test code and fixtures.

Duplicate and malformed requirement IDs are reported as findings rather than
silently collapsed or dropped, so the denominator of the coverage arithmetic
cannot be distorted without the run saying so.

## 6.10 Records, approval, and signature

pytest-gxp produces the report **unsigned**. The signatory name fields available
at the command line and in project configuration produce printed name blocks;
these are **not** electronic signatures within the meaning of 21 CFR Part 11
Subpart C and shall not be represented as such. This is established as fact by
[TQ-001 case TQ-7.3](tool-qualification-protocol.md#57-tq-7-report-metadata-signature-handling-provenance).

Accordingly:

1. Signatory names shall **not** be stored in committed project configuration.
   Storing them there would permit any person with repository write access to
   attribute an approval, defeating attributability.
2. The generated report shall be treated as an **unsigned draft record** on
   generation. Where the run contains non-passing results without deviation
   references, or any error-severity finding, the report is marked `PROVISIONAL`
   and carries a banner reading *PROVISIONAL — DRAFT RECORD. NOT FOR SIGNATURE.*
   Such a report shall not be routed for signature.
3. A SHA-256 manifest of all generated artifacts, `artifact_manifest.sha256`, is
   produced by the tool at the end of the run and accompanies the report. It is
   `sha256sum`-compatible and shall be verified before review.
4. Signature shall be applied by the approved electronic signature process
   (`<signing system>`, validated under `<VAL-ID>`), binding the signature to the
   artifact hash manifest. Wet-ink signature of the rendered PDF is an acceptable
   alternative.
5. Signed records are filed in `<controlled repository>` per SOP-01 with the
   retention period defined in Section `<X>`.

**Reproducibility scope.** The JSON, CSV, and Markdown renderings are
deterministic: two runs over identical inputs differ only in the volatile
generation and validation timestamps and in evidence timestamps and filenames.
The PDF is **not** byte-reproducible, because the rendering library embeds a
creation timestamp. The PDF is therefore treated as a rendering rather than the
record of authority; the specific PDF produced is nonetheless fixed by its digest
in the hash manifest, which is what the signature binds to.

## 6.11 Discrepancy and deviation management

| Result | Required action |
|---|---|
| PASSED | None. |
| FAILED — Tier 1 | Deviation record raised before disposition. Root cause, impact on other requirements, correction, and retest reference documented. QA approval required to close. |
| FAILED — Tier 2 | Discrepancy log entry: cause, resolution, retest reference. Technical closure; QA notification. |
| SKIPPED / NOT_EXECUTED | Justification recorded against the specific requirement. An unjustified skip is a data integrity finding, not a neutral outcome. |
| ERROR (infrastructure, fixture, or environment) | Recorded as a discrepancy. The affected requirement is **not** treated as verified. |
| Passed only on repeat execution | Both the failure and the pass recorded. Intermittent behaviour on a Tier 1 requirement requires root cause investigation before disposition. |

Every result carries its own outcome in the report's test execution register —
`PASSED`, `FAILED`, `ERROR`, `SKIPPED` with its reason, `XFAIL`, `XPASS`, or
`NOT_EXECUTED` — so the table above can be applied per test rather than inferred
from a summary count.

Deviation and discrepancy references are assigned after investigation and
supplied to the tool as data, via `--gxp-deviations=deviations.json` mapping a
node ID or requirement ID to its reference. They enter the record by re-running
against the approved tag; the generated report is never edited. Every non-passing
result lacking a reference produces a `missing-deviation-ref` error finding.

No final report shall be issued for signature while any non-passing result lacks
a cited deviation or discrepancy reference. This is enforced by the `PROVISIONAL`
marking described in §6.10.

## 6.12 Acceptance criteria for the qualification

The system is deemed qualified for its intended use when all of the following are
satisfied:

1. Every requirement in the approved specifications carries an approved tier
   classification on FRM-CSA-04.
2. Tier 1: 100% verified by passing scripted tests with attached objective
   evidence, executed against the approved tag in the environment required by
   §6.7, with `--gxp-strict` armed and the run exiting zero.
3. Tier 2: 100% verified by passing tests, or by credited development testing
   meeting every §6.6 prerequisite.
4. Tier 3: covered by a documented unscripted session or a credited-testing
   citation per functional area.
5. No open Tier 1 deviation; no open Tier 2 discrepancy without an approved
   interim control.
6. Traceability is complete in both directions — no untested requirement, and no
   test referencing a requirement that does not exist.
7. The report metadata status is `FINAL`, and no error-severity finding remains
   undispositioned.
8. The pytest-gxp version used is a version qualified under
   [TQ-001](tool-qualification-protocol.md), and the qualification remains
   current.
9. `artifact_manifest.sha256` is complete, every hash reproduces, and the signed
   report binds to it.
10. The Validation Summary Report is approved by the signatories named in Section
    `<X>`.

## 6.13 Maintaining the validated state

Assurance is a lifecycle activity. Changes are assessed on
**[FRM-CSA-06 Change Risk Assessment](forms.md#frm-csa-06-change-risk-assessment)**
and routed as follows:

| Change | Route |
|---|---|
| Change affecting a Tier 1 requirement, or introducing one | Protocol amendment; re-execute affected Tier 1 tests plus full regression; partial revalidation report |
| Change affecting Tier 2 requirements only | Full automated regression pass plus change risk assessment; recorded under change control; no revalidation report required |
| Tier 3 change, or change with no GxP requirement impact | Standard change control; regression pass retained as evidence |
| Infrastructure or dependency change (runtime, OS, container base, library) | Re-execute IQ tests plus full regression; assess against §6.7.1 |
| pytest-gxp version change | Re-qualify the tool per TQ-001 before the next qualification run |
| pytest, Python runtime, or PDF rendering dependency change | Re-qualify the tool per TQ-001; the qualification is of a version *in an environment*, not of a version alone |
| Periodic review (frequency: `<interval>`) | Pull the current coverage and regression reports; confirm tier classifications remain valid against the matrix `Risk Tier` column; confirm no accumulated undocumented change |

A regression pass alone is never sufficient where the change introduces or alters
a Tier 1 requirement.

## 6.14 Roles and responsibilities

| Role | Responsibility |
|---|---|
| System Owner | Requirements; tier classification proposal; test authorship; execution; discrepancy resolution |
| Independent Tester / Reviewer | Execution or review of Tier 1 tests independently of the developer of the function under test |
| QA | Approval of tier classifications; protocol approval; deviation approval; report approval; approval of any tier downgrade |
| IT / Platform | Environment provisioning and equivalence evidence; CI retention; access control |

---

## References

Confirm the current revision of each reference at the date of approval.

1. FDA, *Computer Software Assurance for Production and Quality Management
   System Software*.
2. FDA, *General Principles of Software Validation*, January 2002.
3. ISPE, *GAMP 5: A Risk-Based Approach to Compliant GxP Computerized Systems*,
   2nd Edition, 2022.
4. ICH Q9(R1), *Quality Risk Management*.
5. 21 CFR Part 11; 21 CFR Part 211.
6. EudraLex Volume 4, Annex 11, *Computerised Systems*.
7. [TQ-001](tool-qualification-protocol.md), *pytest-gxp Tool Qualification
   Protocol*.
8. [WI-CSA-01](work-instruction.md), *Execution of Automated Qualification
   Testing Using pytest-gxp*.
