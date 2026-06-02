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
