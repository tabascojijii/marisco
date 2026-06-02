# Audit Contract

## Authority
- This document restates and exemplifies the machine-readable audit status contract governed by `docs/reference_standards.md`.
- For requirements-, plan-, and roadmap-phase auditing, `docs/reference_standards.md` is the authoritative scoped source for audit status contract rules.
- This document may provide supplemental structure guidance, examples, or implementation notes, but it must not be the sole source of contract authority for phases whose fixed audit scope does not include it.
- If this document and `docs/reference_standards.md` diverge, `docs/reference_standards.md` takes precedence unless `docs/requirements.md` defines a stricter project-specific rule.

## Output Files
- audit_status.txt
- audit_status.json
- docs/audit_report.md

## JSON Keys
- decision
- reason_codes
- owner
- next_gate
- checks[]

## checks[] Keys
- id
- pass
- evidence_path
- metric_value
- threshold

## Contract Rules
- `decision` must be one of the values allowed by `docs/requirements.md`.
- `reason_codes` must be a list, even when empty.
- `checks[]` entries must use `REQ-...` ids.
- `AUDIT_PASS_*` decisions cannot include failed checks.
- `REJECT_*` decisions must include at least one reason code.

## Phase Usage
- During requirements-, plan-, and roadmap-phase auditing, this document is supplementary and must remain consistent with the scoped contract defined in `docs/reference_standards.md`.
- During implementation-phase auditing or tooling integration, this document may be used as a consolidated restatement of the same contract, but it does not override `docs/reference_standards.md`.

## Granularity Contract Boundary
- This document defines machine-readable audit output requirements only.
- This document does not define project-specific acceptance thresholds, execution sequencing, or requirement-detail policy.
- When a finding concerns missing specificity, `audit_status.json` should reference the relevant `REQ-...` check id and evidence path, while the governing policy remains in `docs/requirements.md` or `docs/reference_standards.md`.
