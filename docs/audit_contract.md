# Audit Contract

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

## Granularity Contract Boundary
- This document defines machine-readable audit output requirements only.
- This document does not define project-specific acceptance thresholds, execution sequencing, or requirement-detail policy.
- When a finding concerns missing specificity, `audit_status.json` should reference the relevant `REQ-...` check id and evidence path, while the governing policy remains in `docs/requirements.md` or `docs/reference_standards.md`.
