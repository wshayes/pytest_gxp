# pytest-gxp Tool Qualification Suite (TQ-001)

Automated implementation of the TQ-001 protocol. This suite tests **pytest-gxp
itself**, not any application. It exists because pytest-gxp generates GxP
records, and a tool that generates the evidence must be shown fit for that
purpose.

This is a template. Adopt it under your own document control and record its
execution against your own qualification forms.

## Design

**Black-box, against the documented public surface only.** No private API of
pytest-gxp is imported. Everything the suite knows about flag names, artefact
filenames, marker names, and the report structure lives in `tq_config.py`. If a
future version renames something, one file changes.

**Subprocess execution.** Runs are executed via pytest's `pytester` subprocess
runner so the real command-line path is exercised, including session-finish
report generation.

**Artefacts located by glob.** `tq_helpers.find_artefact` searches recursively
beneath the run directory and reports what *was* produced when something is
missing, so the report directory does not need to be hard-coded.

**Structure-tolerant accessors.** `deep_get` finds a field by name at any depth
in the report JSON, so a nesting change surfaces as one clear failure rather
than dozens of `KeyError`s.

**Both registers are checked.** The report keeps a per-requirement register
(`test_cases`, one entry per requirement, carrying the rolled-up status of the
tests citing it) and an executed-test register (`test_execution`, one entry per
real pytest node). Counts are asserted against both, because a discrepancy
between them is invisible from either alone.

**Weighted toward negative controls.** The failure mode that would most damage a
qualification record is a non-passing test surfacing as a pass. Most of TQ-4 and
much of TQ-6 arrange for failures, skips, errors, and byte-distinct evidence
images, then check the record tells the truth.

## Files

| File | Contents |
|---|---|
| `justfile` | Run recipes: `just` lists them, `just start` executes the qualification |
| `tq_requirements.py` | **The intended-use requirements** and the case that verifies each; the report's RTM is built from it |
| `tq_report.py` | Renders the Tool Qualification Report (Markdown + PDF) from the records; does not import pytest_gxp |
| `tq_config.py` | **Edit this first.** Pinned version, flag names, artefact filenames, matrix columns, tolerances |
| `tq_helpers.py` | Specification authoring, run helpers, artefact location, PNG generation, hashing |
| `conftest.py` | Environment capture, per-case evidence recording |
| `pytest.ini` | Marker declarations and `-p pytester`; also isolates the run from project-level pytest configuration |
| `test_tq1_installation_integrity.py` | TQ-1.1 – 1.7 |
| `test_tq2_specification_parsing.py` | TQ-2.1 – 2.7 |
| `test_tq3_traceability_accuracy.py` | TQ-3.1 – 3.6 |
| `test_tq4_result_fidelity.py` | TQ-4.1 – 4.11 — the critical negative controls |
| `test_tq5_coverage_and_formats.py` | TQ-5.1 – 5.7 |
| `test_tq6_evidence_integrity.py` | TQ-6.1 – 6.10 |
| `test_tq7_report_metadata.py` | TQ-7.1 – 7.9 |

## Before first use

1. **Set the pin.** `TQ_PINNED_VERSION` (or `tq_config.PINNED_VERSION`) must name
   the exact version being qualified. TQ-1.1 fails if the installed version
   differs, which prevents an accidental qualification of the wrong build.

2. **Verify the config against the installed package.** Run the suite once in
   exploratory mode, correct any flag name or filename that does not match, and
   record the corrections on your configuration form. Doing this *before* the
   formal run is part of the procedure, not a workaround.

3. **Install from a wheel or sdist, not editable.** TQ-1.2 computes a content
   hash of the installed distribution. An editable install has no stable file
   inventory, so the case skips with an explanatory reason rather than reporting
   a false pass.

4. **Fix the timezone.** Run with `TZ=UTC` so timestamps in the record are
   unambiguous and comparable between runs.

## Execution

The suite ships with a `justfile` ([just](https://just.systems)). From this
directory:

```bash
just          # list the available recipes
just start    # run the qualification
```

`just start` performs the whole documented procedure:

1. Resolves the version to qualify — the recipe argument if given, otherwise
   `TQ_PINNED_VERSION`, otherwise `tq_config.PINNED_VERSION`.
2. Creates a fresh `.tq` virtual environment at the distribution root.
3. Installs `pytest-gxp[pdf]` at that version, from `dist/` if a matching wheel
   has been built there and from PyPI otherwise. Never editable — TQ-1.2 cannot
   content-hash an editable install. Qualifying the locally built wheel is what
   the publish workflow gates a release on.
4. Writes the dependency closure to `tq_pip_freeze.txt`.
5. Runs the pass/fail gate (`-m "not gap"`) with `TZ=UTC`, teeing the run to
   `tq_console.log`.
6. Renders the Tool Qualification Report — `tq_report.md` and `tq_report.pdf`
   for signature. A failed run is reported too, marked provisional.

Recipes run from the distribution root — the parent of this directory — so the
records land beside `dist/`, exactly as in the manual procedure below. The
recipe exits non-zero if any case fails, so it can be used as a release gate.

```bash
just start 0.3.0          # qualify a specific version
just report               # re-render the report from the last run's records
just check                # exploratory run against the active environment
just check -m mandatory   # arguments are passed through to pytest
just clean                # remove .tq and the records of the last run
```

`just check` is the exploratory run named in **Before first use** step 2. It
uses whatever pytest-gxp is already installed, which in a development checkout
is an editable install — so TQ-1.2 skips, and the run is a configuration check
rather than a qualification. It writes `tq_evidence.jsonl` and
`tq_environment.json` but not `tq_console.log` or `tq_pip_freeze.txt`: an
exploratory run is not a formal record.

`just clean` deletes the records of the last run. Do not run it before they are
filed.

On macOS the recipes set `DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib` when it
exists, because Homebrew's pango and cairo are not on the dynamic loader's
default path. Without it WeasyPrint cannot load, TQ-5.7 does not execute, and
the report PDF cannot be rendered. The path used is written into
`tq_console.log`, so the record states the loader configuration it ran under.

### The report

`just report` renders the report from the records of the last run. It is also
run automatically at the end of `just start`, so a run always leaves a signable
document behind.

| Section | Contents |
|---|---|
| 1. Summary | Qualified artefact, declared pin, requirements verified, case counts, gate result |
| 2. Intended use | What the tool is relied upon for, and the requirement register that follows from it |
| 3. Qualification environment | Verbatim `tq_environment.json` |
| 4. Findings | Failures, cases that did not execute and why, unverified requirements, pin disagreements, a dirty working tree, register drift, missing records |
| 5. Requirements traceability matrix | Each requirement, its risk, its cases, and whether it is verified |
| 6. Case register | Every case with its description, the requirements it verifies, class, and outcome |
| 7. Records attached | Each record with its size and SHA-256, which is what the signature binds to |
| 8. Known limitations | Established facts about the version that need a procedural control |
| 9. Disposition | **Left blank.** Stated by the reviewer |
| 10. Approval | Tester / Reviewer / Approver, printed name, signature, date — all blank |

The report is intended to be signed on its own, before an application validation
is run with the tool. That is why the intended use, the requirements, the case
descriptions, and the limitations are inside it rather than cited from elsewhere:
a signatory should not need the protocol and the suite source open beside them.

The report is marked `PROVISIONAL — DRAFT RECORD. NOT FOR SIGNATURE.` whenever
there is at least one finding, so a run that skipped a mandatory case or ran
from a dirty tree cannot be signed by inattention.

### Requirements, not a functional specification

`tq_requirements.py` holds a register of **intended-use requirements**
(`TQ-REQ-01` …): what must hold for the records this tool produces to be relied
upon. Each names the cases that verify it and a risk rating, and the report
builds its traceability matrix from that mapping.

This is deliberately not a Functional Specification of pytest-gxp. Writing a
specification for software you did not author, then testing your own
specification of it, adds a document to maintain without adding assurance — the
qualification question is whether the tool's records are truthful in your
intended use, not whether the tool matches a spec you wrote for it. Where a QMS
requires a controlled requirements document for tools, lift these statements
into it verbatim: the identifiers are stable and the report cites them.

A case that executes but is registered against no requirement raises a finding,
and `tests/test_tq_report.py` fails if the register and the suite disagree — so
the register cannot quietly fall behind the cases.

Two deliberate omissions. The renderer (`tq_report.py`) does not import
pytest_gxp: the record of a tool's fitness should not be produced by the tool
under qualification, and an auditor will ask. And it never fills in the
disposition — the outcome of the run is a fact and is stated as one, but whether
the version is qualified is a judgement that belongs to the named reviewer.

### Manual equivalent

```bash
uv venv .tq && . .tq/bin/activate
uv pip install "pytest-gxp[pdf]==<X.Y.Z>"
uv pip freeze > tq_pip_freeze.txt

export TZ=UTC TQ_PINNED_VERSION=<X.Y.Z>
pytest -c tool_qualification/pytest.ini tool_qualification/ -v --tb=short | tee tq_console.log
```

The venv must be fresh and the install must come from a built wheel — not
`uv sync` against this repository, which installs the project in editable mode
and makes TQ-1.2 skip.

<details>
<summary>Alternative: pip</summary>

```bash
python -m venv .tq && . .tq/bin/activate
pip install "pytest-gxp[pdf]==<X.Y.Z>"
pip freeze > tq_pip_freeze.txt
```
</details>

`-c tool_qualification/pytest.ini` selects the suite's own configuration, which
prevents any project-level `addopts` (including a stray `--gxp`) from
contaminating the qualification run.

### Selecting by class

```bash
pytest -c tool_qualification/pytest.ini tool_qualification/ -m mandatory    # must all pass
pytest -c tool_qualification/pytest.ini tool_qualification/ -m gap          # expected outcomes per TQ-001 section 5
pytest -c tool_qualification/pytest.ini tool_qualification/ -m "not gap"    # the pass/fail gate
```

Every case is currently mandatory; the `gap` marker and the `-m "not gap"` gate
expression are retained so a future accepted limitation can be recorded without
changing the procedure.

## Interpreting results

| Class | Meaning |
|---|---|
| **Mandatory** | Must pass. Any failure means the version is **not qualified**. Do not use it, and review any record already produced with it. |
| **Gap** | Expected to fail on the version under test. Each has a compensating procedural control recorded in TQ-001 section 8. A gap case that *starts* passing is a signal to investigate and retire the control — not something to ignore. |

Four cases matter more than the rest, because they are what stands between a
green dashboard and a false record:

- **TQ-4.1** a failing test must not be recorded as passed
- **TQ-4.3** a requirement whose only test failed must not be counted as verified
- **TQ-4.5** a test that errored in setup must not be recorded as passed
- **TQ-6.4** evidence must be attributed to the test that captured it (verified by hash, not inspection)

A case that skips is neither a pass nor a failure. Two cases skip on an
environment that cannot support them — TQ-1.2 under an editable install and
TQ-5.7 with no PDF renderer available — and both state the reason in the record.
A formal qualification run must be performed in an environment where neither
skips.

## Records produced

| File | Purpose |
|---|---|
| `tq_evidence.jsonl` | One line per case: TQ ID, outcome, and the values actually observed. This is the objective evidence for the tool qualification. |
| `tq_environment.json` | Installed version, declared pin, Python/pytest versions, platform, timezone, suite commit and tag, dirty-tree flag |
| `tq_console.log` | Full execution record |
| `tq_pip_freeze.txt` | Complete dependency closure |
| `tq_report.md` / `tq_report.pdf` | The Tool Qualification Report; the PDF is the copy that is signed |

The first four attach to the report and are bound to the signature by the
digests printed in it.

The suite writes a fresh `tq_evidence.jsonl` per run, so an abandoned run does
not silently merge into the record. Override the paths with `TQ_EVIDENCE_FILE`
and `TQ_ENVIRONMENT_FILE`.

## When to re-run

- Any pytest-gxp version change — before the next qualification run
- Any change to pytest itself, the Python runtime, or the PDF rendering dependency
- Periodically, per the interval in your validation plan
- After any defect is found in a generated record

## Note on independence

The reviewer of this suite's execution should be someone other than the author of
the pytest-gxp code. Where those are the same person, the tool qualification is
self-attested and an auditor will say so. This is why the supplier and user roles
are documented separately in TQ-001 section 2.
