"""TQ-001 tool qualification report renderer.

Reads the records a qualification run produced (`tq_evidence.jsonl`,
`tq_environment.json`, and the files attached alongside them) and renders the
Tool Qualification Report — protocol §9 deliverable 4 — as Markdown and as a PDF
for signature.

This module deliberately does not import pytest_gxp. The record of a tool's
fitness for purpose should not be produced by the tool under qualification; an
auditor will ask, and "rendered by an independent script" is the answer that
survives the question. Only `markdown` and `weasyprint` are used, and only for
rendering.

The disposition is never filled in here. The run's outcome is a fact and is
stated as one; whether the version is qualified is a judgement, and it belongs
to the named reviewer, not to a script.

Run from the distribution root:

    python3 tool_qualification/tq_report.py

Paths follow the same environment overrides as the suite: TQ_EVIDENCE_FILE,
TQ_ENVIRONMENT_FILE, plus TQ_REPORT_FILE for the output (the PDF takes the same
stem). Exit code is 2 when the PDF could not be rendered.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import sys
from pathlib import Path

import tq_requirements as reqs

import tq_config as cfg

EVIDENCE_FILE = Path(os.environ.get("TQ_EVIDENCE_FILE", "tq_evidence.jsonl")).resolve()
ENVIRONMENT_FILE = Path(os.environ.get("TQ_ENVIRONMENT_FILE", "tq_environment.json")).resolve()
REPORT_FILE = Path(os.environ.get("TQ_REPORT_FILE", "tq_report.md")).resolve()
PDF_FILE = REPORT_FILE.with_suffix(".pdf")

# Attached to the report and bound to the signature by their digests.
ATTACHED_RECORDS = (
    "tq_evidence.jsonl",
    "tq_environment.json",
    "tq_console.log",
    "tq_pip_freeze.txt",
)

FREEZE_APPENDIX_LIMIT = 120


def _tq_key(tq_id: str) -> tuple:
    """Sort TQ-4.2 before TQ-4.10, which a plain string sort does not."""
    digits = tq_id.removeprefix("TQ-").split(".")
    return tuple(int(d) if d.isdigit() else 0 for d in digits)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def _load() -> tuple[list[dict], dict]:
    if not EVIDENCE_FILE.exists():
        sys.exit(
            f"No evidence record at {EVIDENCE_FILE}. Run the qualification first "
            "(`just start`); the report is rendered from its records."
        )
    cases = [
        json.loads(line) for line in EVIDENCE_FILE.read_text(encoding="utf-8").splitlines() if line
    ]
    env = (
        json.loads(ENVIRONMENT_FILE.read_text(encoding="utf-8"))
        if ENVIRONMENT_FILE.exists()
        else {}
    )
    return cases, env


def _requirement_status(by_id: dict[str, dict]) -> dict[str, dict]:
    """Verification state of each intended-use requirement, from the cases that ran.

    A requirement is verified only where every case registered against it
    executed and passed. Anything else is stated as not verified rather than
    averaged into a percentage.
    """
    status = {}
    for req_id, req in reqs.REQUIREMENTS.items():
        executed = [by_id[c] for c in req["cases"] if c in by_id]
        passed = [c for c in executed if c["outcome"] == "PASSED"]
        missing = [c for c in req["cases"] if c not in by_id]
        status[req_id] = {
            **req,
            "executed": len(executed),
            "passed": len(passed),
            "missing": missing,
            "verified": bool(req["cases"]) and len(passed) == len(req["cases"]),
        }
    return status


def _findings(cases: list[dict], env: dict) -> list[str]:
    """Everything that stands between this run and a signature."""
    findings = []
    for case in cases:
        gap = case.get("expected_to_fail")
        if case["outcome"] == "FAILED" and not gap:
            findings.append(
                f"**{case['tq_id']}** failed — {case['purpose']} The version is not qualified."
            )
        elif case["outcome"] == "PASSED" and gap:
            findings.append(
                f"**{case['tq_id']}** is registered as an accepted limitation but passed. "
                "Investigate, then retire or retain the compensating control by decision."
            )
        elif case["outcome"] == "SKIPPED":
            findings.append(
                f"**{case['tq_id']}** did not execute — {_skip_reason(case)} "
                "A formal qualification run must be performed in an environment where it executes."
            )

    declared, installed = (
        env.get("pinned_version_declared"),
        env.get("pytest_gxp_version_installed"),
    )
    if declared and installed and declared != installed:
        findings.append(
            f"The declared pin ({declared}) and the installed version ({installed}) disagree, "
            "so the record does not identify the qualified artefact."
        )
    if env.get("tq_suite_dirty"):
        findings.append(
            "The qualification suite was executed from a working tree with uncommitted changes "
            f"(commit {env.get('tq_suite_commit')}), so the executed suite is not "
            "identified by commit alone."
        )
    by_id = {c["tq_id"]: c for c in cases}
    for req_id, req in _requirement_status(by_id).items():
        if req["verified"]:
            continue
        if not req["executed"]:
            findings.append(
                f"**{req_id}** ({req['risk']} risk) has no executed case in this run, so the "
                "intended-use requirement is untested and the report cannot support a signature."
            )
        else:
            not_passed = [c for c in req["cases"] if c not in req["missing"]]
            findings.append(
                f"**{req_id}** ({req['risk']} risk) is not verified: "
                f"{req['passed']} of {len(req['cases'])} registered cases passed "
                f"({', '.join(not_passed)})."
            )

    unregistered = sorted(set(by_id) - reqs.registered_cases(), key=_tq_key)
    if unregistered:
        findings.append(
            f"Executed but not registered against any intended-use requirement: "
            f"{', '.join(unregistered)}. The requirements register in `tq_requirements.py` "
            "has fallen behind the suite."
        )

    for name in ATTACHED_RECORDS:
        if not Path(name).exists():
            findings.append(f"`{name}` was not produced, so the record package is incomplete.")
    return findings


def _skip_reason(case: dict) -> str:
    reason = case.get("skip_reason") or ""
    if not reason:
        observed = case.get("observations", {})
        reason = "; ".join(f"{k}: {v}" for k, v in observed.items()) or "no reason recorded."
    return reason.strip().replace("\n", " ")


def _table(header: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join(["---"] * len(header)) + "|"]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines)


def build_markdown(cases: list[dict], env: dict) -> str:
    findings = _findings(cases, env)
    by_id = {c["tq_id"]: c for c in cases}
    status = _requirement_status(by_id)
    case_reqs = reqs.case_to_requirements()
    counts = {
        outcome: sum(1 for c in cases if c["outcome"] == outcome)
        for outcome in ("PASSED", "FAILED", "SKIPPED")
    }
    verified = [r for r in status.values() if r["verified"]]
    version = env.get("pytest_gxp_version_installed") or cfg.PINNED_VERSION

    out = [f"# Tool Qualification Report — {cfg.DISTRIBUTION_NAME} {version}", ""]
    if findings:
        out += [cfg.PROVISIONAL_BANNER, ""]
    out += [
        "Protocol TQ-001. This report is rendered from the records of the qualification "
        "run identified below, which are attached and bound to it by digest. It is "
        "self-contained: the intended use qualified, the requirements traced to the "
        "cases that verify them, every case with its outcome, the known limitations, "
        "and the approval block are all present here.",
        "",
        "## 1. Summary",
        "",
        _table(
            ["Field", "Value"],
            [
                ["Qualified artefact", f"{cfg.DISTRIBUTION_NAME} {version}"],
                ["Declared pin", str(env.get("pinned_version_declared", "—"))],
                [
                    "Intended-use requirements verified",
                    f"{len(verified)} of {len(status)}",
                ],
                ["Cases executed", str(len(cases))],
                [
                    "Passed / Failed / Not executed",
                    f"{counts['PASSED']} / {counts['FAILED']} / {counts['SKIPPED']}",
                ],
                ["Gate result", "PASS" if not counts["FAILED"] else "**FAIL**"],
                ["Findings", str(len(findings)) if findings else "None"],
                ["Run captured (UTC)", str(env.get("captured_utc", "—"))],
                [
                    "Report rendered (UTC)",
                    dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                ],
            ],
        ),
        "",
        "## 2. Intended use",
        "",
        reqs.INTENDED_USE,
        "",
        "The requirements below state what must hold for records produced by this tool "
        "to be relied upon. They are requirements of the *intended use*, not a "
        "specification of the tool's internals: specifying software you did not write, "
        "then testing your own specification of it, adds a document without adding "
        "assurance. Section 5 traces each to the cases that verify it.",
        "",
        _table(
            ["ID", "Requirement", "Risk", "Cases"],
            [
                [req_id, req["statement"], req["risk"], str(len(req["cases"]))]
                for req_id, req in reqs.REQUIREMENTS.items()
            ],
        ),
        "",
        "## 3. Qualification environment",
        "",
        _table(["Field", "Value"], [[k, f"`{v}`"] for k, v in env.items()])
        if env
        else "No environment record was produced. The run cannot be attributed to an environment.",
        "",
        "## 4. Findings",
        "",
    ]
    out += [
        ("\n".join(f"{i}. {f}" for i, f in enumerate(findings, 1))) if findings else "No findings."
    ]
    out += [
        "",
        "## 5. Requirements traceability matrix",
        "",
        "A requirement is verified only where every case registered against it executed "
        "and passed. Anything short of that is stated as not verified.",
        "",
        _table(
            ["Requirement", "Risk", "Cases", "Passed", "Verified"],
            [
                [
                    req_id,
                    req["risk"],
                    ", ".join(req["cases"]),
                    f"{req['passed']} / {len(req['cases'])}",
                    "Yes" if req["verified"] else "**No**",
                ]
                for req_id, req in status.items()
            ],
        ),
        "",
        "## 6. Case register",
        "",
        "Each description is the stated purpose of the executed case, taken from the "
        "test itself rather than from a parallel document that could drift from it.",
        "",
        _table(
            ["TQ ID", "Description", "Verifies", "Class", "Outcome"],
            [
                [
                    c["tq_id"],
                    f"{c['purpose']}<br>`{c['test']}`",
                    ", ".join(case_reqs.get(c["tq_id"], ["**unregistered**"])),
                    "Gap" if c.get("expected_to_fail") else "Mandatory",
                    c["outcome"] if c["outcome"] != "SKIPPED" else "**NOT EXECUTED**",
                ]
                for c in sorted(cases, key=lambda c: _tq_key(c["tq_id"]))
            ],
        ),
        "",
        "## 7. Records attached",
        "",
        _table(
            ["File", "Bytes", "SHA-256"],
            [
                [f"`{name}`", f"{p.stat().st_size:,}", f"`{_sha256(p)}`"]
                if (p := Path(name)).exists()
                else [f"`{name}`", "—", "**not produced**"]
                for name in ATTACHED_RECORDS
            ],
        ),
        "",
        "The signature below binds to this report and, through the digests above, "
        "to the records it was rendered from.",
        "",
        "## 8. Known limitations of the qualified version",
        "",
        "Established facts about this version, carried here so that they are seen "
        "before signature rather than discovered after it. Each requires a procedural "
        "control in the adopting organisation.",
        "",
    ]
    out += ["\n".join(f"{i}. {lim}" for i, lim in enumerate(reqs.LIMITATIONS, 1))]
    out += [
        "",
        "## 9. Disposition",
        "",
        "Stated by the reviewer. A run in which every mandatory case passed is a "
        "necessary condition, not the decision itself.",
        "",
        _table(
            ["Field", "Entry"],
            [
                ["Disposition (Qualified / Qualified with limitations / Not qualified)", ""],
                ["Basis", ""],
                ["Additional limitations and compensating controls", ""],
                ["Valid for use until (review date or version change)", ""],
            ],
        ),
        "",
        "## 10. Approval",
        "",
        "By signing, the Reviewer and Approver attest that the qualification described "
        "in this report was executed as recorded, that the findings and limitations "
        "above were considered, and that the disposition in section 9 is theirs.",
        "",
        _table(
            ["Role", "Printed name", "Signature", "Date"],
            [[role, "", "", ""] for role in ("Tester", "Reviewer", "Approver")],
        ),
        "",
        "Signature fields are printed-name fields and are not authenticated by the tool "
        "(protocol §5, TQ-7.3). The reviewer must be a person other than the author of the "
        "pytest-gxp code; where they are not, record the self-attestation as a limitation.",
        "",
    ]

    not_passed = [c for c in cases if c["outcome"] != "PASSED"]
    if not_passed:
        out += ["## Appendix A — cases that did not pass", ""]
        for case in not_passed:
            out += [
                f"**{case['tq_id']} — {case['test']}** ({case['outcome']})",
                "",
                "> "
                + (
                    _skip_reason(case)
                    if case["outcome"] == "SKIPPED"
                    else case.get("failure_detail", "").strip()
                ),
                "",
                f"Observations: `{json.dumps(case.get('observations', {}))}`",
                "",
            ]

    freeze = Path("tq_pip_freeze.txt")
    if freeze.exists():
        lines = freeze.read_text(encoding="utf-8").splitlines()
        shown = lines[:FREEZE_APPENDIX_LIMIT]
        out += ["## Appendix B — dependency closure", "", "```", *shown]
        if len(lines) > len(shown):
            out += [f"... {len(lines) - len(shown)} further entries; see tq_pip_freeze.txt"]
        out += ["```", ""]

    return "\n".join(out)


CSS = """
@page {
  size: A4; margin: 18mm 16mm;
  @bottom-center { content: counter(page) " / " counter(pages); font: 9pt sans-serif; color: #555; }
}
body { font: 10pt/1.45 -apple-system, "Helvetica Neue", Arial, sans-serif; color: #111; }
h1 { font-size: 17pt; border-bottom: 2px solid #111; padding-bottom: 4pt; }
h2 { font-size: 12pt; margin-top: 16pt; border-bottom: 1px solid #bbb; padding-bottom: 2pt; }
/* The provisional banner, when present, is the paragraph straight after the title. */
h1 + p strong { display: block; border: 1.5pt solid #b00; color: #b00;
                padding: 5pt; text-align: center; letter-spacing: 0.4pt; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0; }
th, td { border: 1px solid #999; padding: 3pt 5pt; text-align: left; vertical-align: top; }
th { background: #eee; }
td:first-child { white-space: nowrap; }  /* keep TQ-REQ-03 on one line */
thead { display: table-header-group; }   /* repeat the header on every page */
tr { break-inside: avoid; }              /* never split a case across a page */
table:last-of-type td { height: 26pt; }  /* the approval block is signed by hand */
code { font-family: "SF Mono", Menlo, monospace; font-size: 8.5pt; word-break: break-all; }
pre { border: 1px solid #ccc; padding: 5pt; font-size: 8pt; white-space: pre-wrap; }
blockquote { margin: 4pt 0 4pt 8pt; padding-left: 8pt; border-left: 2px solid #999;
             color: #333; font-size: 9pt; }
"""


def render_pdf(markdown_text: str) -> bool:
    try:
        import markdown as md
        from weasyprint import CSS as WeasyCSS
        from weasyprint import HTML
    except Exception as exc:  # noqa: BLE001 - any import or native-library failure
        print(f"PDF not rendered: {exc}", file=sys.stderr)
        return False
    html = md.markdown(markdown_text, extensions=["tables", "fenced_code"])
    HTML(string=html).write_pdf(PDF_FILE, stylesheets=[WeasyCSS(string=CSS)])
    return True


def main() -> int:
    cases, env = _load()
    text = build_markdown(cases, env)
    REPORT_FILE.write_text(text, encoding="utf-8")
    print(f"Report   : {REPORT_FILE}")
    if not render_pdf(text):
        print(
            "The Markdown report was written but the PDF was not. Install the PDF "
            "renderer (`uv pip install weasyprint markdown` plus its native "
            "libraries) and re-run; the PDF is the artefact that carries the signature.",
            file=sys.stderr,
        )
        return 2
    print(f"Signable : {PDF_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
