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

```bash
python -m venv .tq && . .tq/bin/activate
pip install "pytest-gxp[pdf]==<X.Y.Z>"
pip freeze > tq_pip_freeze.txt

export TZ=UTC TQ_PINNED_VERSION=<X.Y.Z>
pytest -c tool_qualification/pytest.ini tool_qualification/ -v --tb=short | tee tq_console.log
```

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

All four attach to the qualification report.

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
