# Requirements

## Scope
- Define the canonical contract for plan, roadmap, and implementation audits.
- Treat this file as the source of truth when any document disagrees.

## Phase Contracts
- Requirements audit may output only `AUDIT_PASS_REQUIREMENTS` or `ESCALATION`.
- Plan audit may output only `AUDIT_PASS_PLAN` or `REJECT_TO_ARCHITECT`.
- Roadmap audit may output only `AUDIT_PASS_ROADMAP`, `REJECT_TO_PM`, or `REJECT_TO_ARCHITECT`.
- Implement audit may output only `AUDIT_PASS_IMPLEMENT`, `REJECT_TO_IMPLEMENT`, `REJECT_TO_ARCHITECT`, or `ESCALATION`.
- Any requirements-level contradiction must be escalated with a `REQ_` reason code.

## Audit Status JSON Contract
- Required top-level keys: `decision`, `reason_codes`, `owner`, `next_gate`, `checks`.
- `reason_codes` must be a list.
- `checks` must be a list of objects.
- Each `checks[]` object must contain `id`, `pass`, `evidence_path`, `metric_value`, and `threshold`.
- Every `checks[].id` must start with `REQ-`.
- If `decision` starts with `REJECT_`, `reason_codes` must contain at least one item.
- If `decision` starts with `AUDIT_PASS_`, `checks` must not contain `pass: false`.

## Allowed Values
- Allowed `next_gate` values: `FLOW_ADVANCE`, `ARCHITECT_REWORK`, `PM_REWORK`, `IMPLEMENT_REWORK`, `ESCALATION_REVIEW`.
- Owner values must match the receiving role for the decision: `Architect`, `PM`, or `Implementer`.

## Acceptance Layers
- Layer A: Document contract integrity. Required docs exist and contain the mandatory blocks needed by the hook.
- Layer B: Evidence integrity. Every requirement used for audit has a concrete evidence path and a measurable threshold.

## Naming Stage Rules
- Stage 1: Requirement IDs use `REQ-...` format.
- Stage 2: Reason codes use role prefixes such as `REQ_`, `ARCH_`, `PM_`, or `IMPLEMENT_`.

## Required Documents
- `docs/acceptance_matrix.md`
- `docs/check_catalog.md`
- `docs/audit_contract.md`
- `docs/escalation_policy.md`
- `docs/traceability_map.md`
- `docs/audit_examples.md`
- `docs/audit_report.md`
- `docs/escalation_report.md`

## Acceptance Criteria
- All required documents exist.
- `docs/roadmap.md` contains `## Self-Check (Required)` with at least one checked item.
- `docs/audit_report.md` contains a `## Open-Items` block.
- Architect escalation blocks, when present, must include `Decision: REJECT_TO_ARCHITECT`, an `ARCH_...` reason code, and `Required-Design-Changes: ...`.
- The audit status contract is respected without missing keys.

## Governance
- Follow `docs/reference_standards.md`.
- Do not redefine transition algorithms outside the hook.
