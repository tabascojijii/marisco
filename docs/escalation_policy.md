# Escalation Policy

## Trigger
- Requirements contradiction
- Repeated reject loop
- Contract invalid JSON
- Missing or invalid `REQ_...` escalation reason code

## Action
- Set decision to ESCALATION
- Produce docs/escalation_report.md
- Route to `ESCALATION_REVIEW`

## Required Reason-Code Family
- Requirements-level escalation reasons must use the `REQ_` prefix.
