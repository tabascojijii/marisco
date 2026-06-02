# Audit Examples

## PASS Example
- Decision: AUDIT_PASS_PLAN
- Reason-Codes: []
- Owner: Architect
- Next-Gate: FLOW_ADVANCE

## REJECT Example
- Decision: REJECT_TO_PM
- Reason-Code: PM_OPEN_ITEMS_MISSING
- Owner: PM
- Next-Gate: PM_REWORK

## ESCALATION Example
- Decision: ESCALATION
- Reason-Code: REQ_CONTRACT_INVALID
- Owner: Architect
- Next-Gate: ESCALATION_REVIEW
