# CSV Validation Report JSON Format

The CSV Validation Summary Report is generated in JSON format to support programmatic processing and integration with other systems.

## Format Overview

The report is a JSON object containing metadata, specification information, test summaries, coverage data, and detailed test case information.

## JSON Schema

### Root Object

```json
{
  "report_metadata": { ... },
  "validation_info": { ... },
  "approvals": { ... },
  "specifications": { ... },
  "test_execution_summary": { ... },
  "requirement_coverage": { ... },
  "test_summary": { ... },
  "coverage": { ... },
  "test_cases": [ ... ],
  "test_execution": [ ... ],
  "findings": [ ... ]
}
```

`test_summary` and `coverage` are retained from 0.1.x for backwards compatibility;
`test_execution_summary` and `requirement_coverage` are the current equivalents.

### report_metadata

Contains report generation information, the identity of the generating tool, the
revision of the system under validation, and the record's own status.

```json
{
  "title": "OQ Report",
  "qualification_type": "OQ",
  "generated_date": "2026-07-29T14:22:05Z",
  "version": "1.0",
  "status": "PROVISIONAL",
  "provisional_reasons": [
    "1 test(s) failed or errored",
    "1 error-severity validation finding(s)"
  ],
  "generator": { "name": "pytest-gxp", "version": "0.3.0" },
  "findings_summary": { "errors": 1, "warnings": 2 },
  "source_provenance": {
    "source": "git",
    "git_commit": "9f1c0d3e8ab24f7c1d05e6b2f8a3907c4d5e6f70",
    "git_tag": "v2.4.0",
    "git_dirty": false
  }
}
```

**Fields:**
- `title` (string): Report title, derived from the qualification type
- `qualification_type` (string): `IQ`, `OQ`, or `PQ`
- `generated_date` (string): Generation timestamp, UTC ISO 8601 with a `Z` designator
- `version` (string): Report format version
- `status` (string): `FINAL` or `PROVISIONAL`
- `provisional_reasons` (array of strings): Why the record is provisional; empty when `FINAL`
- `generator` (object): `name` and `version` of the tool that produced the record
- `findings_summary` (object): Counts of `errors` and `warnings` in `findings`
- `source_provenance` (object): Revision of the system under validation

`source_provenance` fields:
- `source` (string): `git` when detected from a repository, `config` when supplied
  via `--gxp-source-commit` / `--gxp-source-tag`, `unavailable` when neither
- `git_commit` (string or null): Full commit SHA
- `git_tag` (string or null): Exact-match tag
- `git_dirty` (boolean or null): Whether the working tree had uncommitted changes

Values are never fabricated: outside a git checkout, with no override supplied,
all three are `null` and `source` is `unavailable`.

### validation_info

What was validated.

```json
{
  "software_name": "My Application",
  "software_version": "1.0.0",
  "project_name": "My Application",
  "validation_date": "2026-07-29"
}
```

### approvals

Approval signature blocks, one per role, `null` when no name was configured.

```json
{
  "tester": {
    "name": "John Doe",
    "role": "Tester",
    "date": "2026-07-29",
    "signature": "________________________"
  },
  "reviewer": { ... },
  "approver": null
}
```

!!! warning "Not an electronic signature"
    The `signature` field is an unauthenticated placeholder. Names are recorded
    verbatim from configuration; nothing is authenticated. Apply signatures with an
    external process bound to `artifact_manifest.sha256`. See
    [Validation](../validation/index.md).

### specifications

Information about all specification documents.

```json
{
  "design_spec": {
    "title": "Design Specification",
    "version": "1.0",
    "requirement_count": 3
  },
  "functional_spec": {
    "title": "Functional Specification",
    "version": "1.0",
    "requirement_count": 4
  },
  "user_spec": {
    "title": "User Specification",
    "version": "1.0",
    "requirement_count": 3
  },
  "installation_spec": {
    "title": "Installation Specification",
    "version": "1.0",
    "requirement_count": 5
  }
}
```

**Fields:**
- `design_spec` (object): Design specification metadata
- `functional_spec` (object): Functional specification metadata
- `user_spec` (object): User specification metadata
- `installation_spec` (object): Installation specification metadata

Each spec object contains:
- `title` (string): Specification title
- `version` (string): Specification version
- `requirement_count` (integer): Number of requirements in specification

### test_execution_summary

Summary statistics of test execution.

```json
{
  "total_tests": 7,
  "executed_tests": 6,
  "passed_tests": 6,
  "failed_tests": 0,
  "skipped_tests": 0,
  "error_tests": 0,
  "not_executed_tests": 1,
  "test_pass_rate": 100.0,
  "test_execution_rate": 85.7
}
```

**Fields:**
- `total_tests` (integer): Total number of test cases
- `executed_tests` (integer): Passed plus failed
- `passed_tests`, `failed_tests`, `skipped_tests`, `not_executed_tests` (integer): Counts by status
- `error_tests` (integer): Tests that errored in setup or teardown, counted over the execution register
- `test_pass_rate` (float): Passed as a percentage of executed (0-100)
- `test_execution_rate` (float): Executed as a percentage of total (0-100)

### test_summary

The 0.1.x-compatible view of the same counts, with `errors` added.

```json
{
  "total_test_cases": 7,
  "passed": 6,
  "failed": 0,
  "skipped": 0,
  "errors": 0,
  "not_executed": 1,
  "pass_rate": 100.0
}
```

### requirement_coverage

Requirement coverage metrics.

```json
{
  "total_requirements": 7,
  "requirements_with_tests": 6,
  "requirements_without_tests": 1,
  "coverage_rate": 85.7,
  "requirements_verified": 6,
  "verification_rate": 100.0
}
```

**Fields:**
- `total_requirements` (integer): Total number of requirements across all specifications
- `requirements_with_tests` (integer): Requirements cited by at least one test
- `requirements_without_tests` (integer): Requirements with no test
- `coverage_rate` (float): Requirements with tests, as a percentage of total (0-100)
- `requirements_verified` (integer): Requirements whose tests passed
- `verification_rate` (float): Verified as a percentage of covered (0-100)

### coverage

The traceability matrix's own coverage report, retained for backwards
compatibility. It contains the same metrics as `requirement_coverage` under legacy
names (`covered_requirements`, `coverage_percentage`) plus the detail lists
`uncovered_requirements` and `unverified_requirements` (arrays of requirement IDs).

### test_cases

Array of test cases derived from requirements.

```json
[
  {
    "id": "TEST-FS-001",
    "title": "Test FS-001: User Login Functionality",
    "requirements": ["FS-001"],
    "status": "PASSED",
    "spec_type": "Functional",
    "expected_result": "The user reaches the dashboard and a session is created",
    "metadata": { "spec_type": "Functional", "Priority": "High" },
    "risk_tier": "high",
    "deviation_ref": null
  }
]
```

**Fields:**
- `id` (string): Test case identifier, derived from the requirement ID
- `title` (string): Test case title
- `requirements` (array of strings): Requirement IDs this test case covers
- `status` (string): Rolled-up status of the tests citing those requirements
- `spec_type` (string): Specification type (Installation, Design, Functional, User)
- `expected_result` (string): Expected result carried from the requirement
- `metadata` (object): Requirement metadata carried from the specification
- `risk_tier` (string): Highest `gxp_risk` tier among the citing tests; empty when none is marked
- `deviation_ref` (string or null): Deviation reference; always present, `null` when none

### test_execution

Array of the real pytest tests that ran, sorted by node ID. This is the register
that names actual test identities; `test_cases` describes the requirement-derived
cases.

```json
[
  {
    "node_id": "tests/test_login.py::test_session_timeout",
    "outcome": "FAILED",
    "reason": "AssertionError: session still active after 900s",
    "requirement_ids": ["FS-007"],
    "risk_tier": "high",
    "deviation_ref": "DEV-2026-014"
  }
]
```

**Fields:**
- `node_id` (string): pytest node ID
- `outcome` (string): `PASSED`, `FAILED`, `ERROR`, `SKIPPED`, `XFAIL`, `XPASS`, or `NOT_EXECUTED`
- `reason` (string): Skip reason or failure summary; empty for a plain pass
- `requirement_ids` (array of strings): Requirement IDs from the test's `requirements` marker
- `risk_tier` (string): Value of the test's `gxp_risk` marker; empty when unmarked
- `deviation_ref` (string or null): Deviation reference; always present, `null` when none

Every phase of a test is classified, so a test that errored in setup is recorded
as `ERROR` with its reason rather than as a silent non-result. Where phases
disagree, the worst outcome wins.

### findings

Array of defects the plugin found in the specifications, markers, or evidence,
sorted by code, location, and message.

```json
[
  {
    "code": "unknown-requirement-ref",
    "severity": "error",
    "message": "Test cites requirement FS-999, which is not defined in any specification",
    "location": "tests/test_login.py::test_user_login"
  }
]
```

**Fields:**
- `code` (string): Finding code — see [Reports](reports.md#validation-findings) for the full list
- `severity` (string): `error` or `warning`
- `message` (string): Human-readable description
- `location` (string): `file.md:line` for specification findings, a pytest node ID for test findings, empty when neither applies

Run with `--gxp-strict` to fail the run on any error-severity finding.

## Complete Example

See [examples/csv-validation-report-example.json](../examples/files/csv_validation_report.json) for a complete example.

## Usage

### Programmatic Access

```python
import json

with open('csv_validation_report.json') as f:
    report = json.load(f)

print(f"Pass rate: {report['test_execution_summary']['test_pass_rate']}%")
print(f"Coverage: {report['requirement_coverage']['coverage_rate']}%")
print(f"Status: {report['report_metadata']['status']}")

for finding in report["findings"]:
    if finding["severity"] == "error":
        print(f"{finding['code']} at {finding['location']}: {finding['message']}")
```

### Integration

The JSON format supports:
- Automated report processing
- Integration with CI/CD pipelines
- Dashboard visualization
- Compliance reporting systems
- Data analysis tools

### Validation

The JSON follows standard JSON schema and can be validated using JSON Schema validators.

## Status Values

Status values, worst first — this is also the order in which a test's phases and a
requirement's tests are merged:

- **ERROR** - Test errored in setup or teardown; its body may never have run
- **FAILED** - Test executed and failed
- **XFAIL** - Test was expected to fail and did
- **XPASS** - Test was expected to fail but passed
- **SKIPPED** - Test skipped (e.g., due to dependencies)
- **NOT_EXECUTED** - Test case defined but no test executed it
- **PASSED** - Test executed and passed

`test_cases[*].status` uses the rolled-up requirement status and renders the
no-test case as `Not Executed`; `test_execution[*].outcome` uses the values above
verbatim.

## Determinism

The JSON, CSV, and Markdown renderings are reproducible across runs over unchanged
inputs, apart from `report_metadata.generated_date`,
`validation_info.validation_date`, and evidence timestamps and filenames. Every
list is emitted in a defined order. The PDF is excluded — its renderer embeds a
creation timestamp.

`artifact_manifest.sha256` in the report directory carries a SHA-256 of every
generated artifact, including this JSON. See
[Reports](reports.md#artifact-manifest).

## Best Practices

1. **Read by name**: Address fields by key, not position; the schema grows additively
2. **Timestamps**: All timestamps are UTC ISO 8601 with a `Z` designator
3. **Check status first**: A `PROVISIONAL` record is not fit for signature
4. **Check findings**: A green pass rate with error-severity findings is not a clean run
5. **Bind to the manifest**: Verify `artifact_manifest.sha256` before relying on a report

## Related Formats

- [Traceability Matrix Format](traceability-format.md)
- [Markdown Report Format](reports.md)

