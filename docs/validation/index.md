# Validating pytest-gxp

!!! note "Template"
    Adopt this document under your own document control. Identifiers, roles,
    and references are placeholders. Nothing here is regulatory advice.

pytest-gxp generates the traceability matrix, evidence manifest, and validation
report that your organisation relies upon as GxP records. Under GAMP 5, a tool
that produces validation evidence must itself be shown fit for that purpose
before the records it produces can be relied upon.

This section provides a complete, executable tool-qualification package you can
adopt: a protocol, a work instruction, checklists and forms, and a risk-based
assurance strategy. The automated suite that implements the protocol ships with
the source distribution of every release.

## Why a user-side qualification is required

The question the qualification answers is deliberately narrow. It is not whether
pytest-gxp is well engineered; it is whether **the records it produces are
truthful**. A failing test must never surface as a pass. An uncovered
requirement must never surface as covered. Evidence must never be attributed to
a test that did not capture it.

You cannot discharge this obligation by citing a supplier assessment. pytest-gxp
is an open-source package you adopted; there is no supplier quality agreement,
no audited development process you have visibility into, and no supplier
commitment to your validation lifecycle. GAMP 5 fitness-for-purpose for a tool
in this position is established by the user, against a pinned version, before
use.

## Supplier and user roles

| Role | Held by | Obligation |
|---|---|---|
| Supplier | The package author, in a personal / open-source capacity | Versioned MIT-licensed releases on PyPI, release notes, public repository history |
| User | **Your organisation**, as the regulated party | This qualification, against a pinned version, before use |

The supplier obligation stops at publishing a versioned artifact. Everything
downstream of that — deciding which version to use, qualifying it, keeping the
qualification current, and dispositioning the records it produces — belongs to
your organisation. Record the two roles separately, and do not cite the
existence of the upstream project as supplier assurance.

!!! warning "Independence of review"
    The person who reviews the qualification execution must be someone other
    than the author of the pytest-gxp code. Where the tool author is a member of
    your organisation, the qualification is **self-attested** and an auditor
    will say so. Document the supplier and user roles separately, and arrange
    independent review by a person who did not author the tool. If you cannot,
    record the self-attestation explicitly as a limitation rather than leaving
    it to be discovered.

## Obtaining the qualification suite for a pinned version

The suite ships in the **source distribution**, under `tool_qualification/`. It
is deliberately excluded from the wheel, so `uv add pytest-gxp` does not
give you the suite — the qualification package is a release artifact you obtain
and retain deliberately.

```bash
# Option 1 — download the sdist for the exact version you are qualifying.
# uv has no `download` equivalent, so pip is used for this one step.
pip download --no-binary :all: --no-deps pytest-gxp==0.3.0 -d ./tq-download
tar xzf ./tq-download/pytest_gxp-0.3.0.tar.gz
cd pytest_gxp-0.3.0
ls tool_qualification/
```

```bash
# Option 2 — the tagged GitHub release tarball for the same version.
# Use the tag name shown on the release page for the version you are qualifying.
curl -L -o pytest_gxp-0.3.0.tar.gz \
  https://github.com/wshayes/pytest_gxp/archive/refs/tags/v0.3.0.tar.gz
tar xzf pytest_gxp-0.3.0.tar.gz
```

Retain the downloaded archive and its SHA-256 with the qualification record.
The suite's own commit and tag are captured automatically in
`tq_environment.json`.

## Running the suite

The qualification run must exercise the same installed artifact your projects
will use. Install from a built wheel or the sdist — **not** an editable or path
install — because one of the mandatory cases computes a content hash of the
installed distribution, and an editable install has no stable file inventory.

The suite ships a `justfile` that performs this whole procedure and renders the
signable report at the end:

```bash
cd tool_qualification
just          # list the recipes
just start    # fresh environment, pinned wheel, gate, report
```

See [`tool_qualification/README.md`](https://github.com/wshayes/pytest_gxp/blob/main/tool_qualification/README.md)
for the recipes. The equivalent commands, run by hand:

```bash
# Fresh, isolated environment
uv venv .tq && . .tq/bin/activate
uv pip install "pytest-gxp[pdf]==0.3.0"
uv pip freeze > tq_pip_freeze.txt

# Declare what is being qualified, and pin the timezone
export TZ=UTC
export TQ_PINNED_VERSION=0.3.0

pytest -c tool_qualification/pytest.ini tool_qualification/ \
       -m "not gap" -v --tb=short | tee tq_console.log
```

??? note "Alternative: pip"

    ```bash
    python -m venv .tq && . .tq/bin/activate
    pip install "pytest-gxp[pdf]==0.3.0"
    pip freeze > tq_pip_freeze.txt
    ```

`uv venv` + `uv pip install` is used rather than `uv sync`: the qualification
must run against the published wheel, and `uv sync` against a checkout installs
the project in editable mode, which makes the content-hash case (TQ-1.2) skip.
`uv pip freeze` emits the same requirements format as `pip freeze`, so
`tq_pip_freeze.txt` remains the dependency-closure record named on the forms.

`-c tool_qualification/pytest.ini` selects the suite's own configuration. This
both loads the `pytester` plugin the suite needs and isolates the run from any
project-level `addopts` — including a stray `--gxp` — that would otherwise
contaminate the qualification.

`TQ_PINNED_VERSION` declares the version under qualification. A qualification
run must state what it qualified; if the declared pin and the installed version
disagree, the first mandatory case fails.

`TZ=UTC` is set so that the timestamps in the records produced during the run
are unambiguous, and so the run is reproducible.

### Selecting by class

```bash
# The pass/fail gate — every case here must pass
pytest -c tool_qualification/pytest.ini tool_qualification/ -m "not gap"

# Mandatory cases only
pytest -c tool_qualification/pytest.ini tool_qualification/ -m mandatory

# Accepted-limitation cases; expected outcomes are recorded in the protocol §8
pytest -c tool_qualification/pytest.ini tool_qualification/ -m gap
```

## Records produced

| File | Purpose |
|---|---|
| `tq_evidence.jsonl` | One line per case: TQ ID, outcome, and the values actually observed. This is the objective evidence for the tool qualification. |
| `tq_environment.json` | Installed version, declared pin, Python / pytest versions, `TZ`, platform, suite commit and tag, dirty-tree flag |
| `tq_console.log` | Full execution record |
| `tq_pip_freeze.txt` | Complete dependency closure |
| `tq_report.md` / `tq_report.pdf` | The Tool Qualification Report rendered from the four records above, with the digest of each; the PDF is the copy that is signed |

The first four attach to the tool qualification report and to your tool
qualification checklist (FRM-CSA-03 in the [forms](forms.md) templates).

The report is written to be signed on its own, before any application
validation is run with the tool. It carries the intended use being qualified, a
register of intended-use requirements (`TQ-REQ-01` …) with a traceability matrix
to the cases that verify each, every case with its description and outcome, the
known limitations of the version, and the approval block.

That register — held in `tool_qualification/tq_requirements.py` — takes the place
of a Functional Specification for the tool. Specifying software you did not
author and then testing your own specification of it adds a document without
adding assurance; what the qualification needs is a statement of what must hold
for the records to be relied upon, and evidence that each such statement was
tested. Where your QMS requires a controlled requirements document for tools,
lift the statements into it verbatim; the identifiers are stable.

The report states the run's outcome as fact but leaves the **disposition**
blank: whether the version is qualified is the reviewer's judgement. It is
marked `PROVISIONAL — DRAFT RECORD. NOT FOR SIGNATURE.` whenever the run carries
a finding — a case that did not execute, a pin disagreement, a dirty working
tree, or a missing record.

A fresh `tq_evidence.jsonl` is written per run, so an abandoned run does not
silently merge into the record. Override the paths with `TQ_EVIDENCE_FILE` and
`TQ_ENVIRONMENT_FILE` if your record structure requires it.

## Reading the outcome

Cases carry one of two markers, and the two are dispositioned differently.

| Class | Marker | Meaning |
|---|---|---|
| **Mandatory** | `mandatory` | Must pass. Any failure means the version is **not qualified**. Do not use it, and review any record already produced with it. |
| **Gap** | `gap` | An accepted limitation whose expected outcome is recorded in the protocol §8, with a named compensating procedural control. A gap case that *changes state* is a signal to investigate and retire or retain the control by decision — not something to ignore. |

As of version 0.3.0 the gap set is empty — every case in the register is
mandatory, and the two remaining accepted limitations are documented facts rather
than failing cases. The `-m "not gap"` gate expression is retained regardless, so
that a future limitation cannot be introduced without the gate acknowledging it.
See the [protocol §8](tool-qualification-protocol.md#8-accepted-limitations-and-compensating-controls).

Four mandatory cases matter more than the rest, because they are what stands
between a green dashboard and a false record:

- **TQ-4.1** — a failing test must not be recorded as passed
- **TQ-4.3** — a requirement whose only test failed must not be counted as verified
- **TQ-4.5** — a test that errored in setup must not be recorded as passed
- **TQ-6.4** — evidence must be attributed to the test that captured it, verified by hash rather than by inspection

Failure of any of these results in immediate withdrawal of the version from
qualification use, and review of every record already produced with it.

## When to re-run

- Any pytest-gxp version change, before the next qualification run
- Any change to pytest itself, the Python runtime, or the PDF rendering dependency
- Periodically, at the interval stated in your validation plan
- After any defect is found in a generated record

## The rest of this section

| Page | Contents |
|---|---|
| [Tool Qualification Protocol](tool-qualification-protocol.md) | The protocol itself: scope, prerequisites, the full test case register, acceptance criteria, the accepted-limitation register, deliverables, approval |
| [Work Instruction](work-instruction.md) | How to plan, freeze, execute, review, and disposition a qualification run using the plugin |
| [Checklists and Forms](forms.md) | Pre-execution readiness, post-execution review, tool qualification, requirement risk classification, unscripted session record, change risk assessment |
| [Risk-Based Assurance](risk-based-assurance.md) | How to allocate assurance effort by risk tier, and the mechanisms in the plugin that enforce it |
