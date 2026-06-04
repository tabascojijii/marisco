# Plan Audit Report

Execution-ID: PLAN_AUDIT-20260604T151458Z-80186e
Phase: PLAN_AUDIT
Decision: REJECT_TO_ARCHITECT
Next-Gate: ARCHITECT_REWORK

## Scope

- Fixed audit scope completed in full before decision:
- `AGENTS.md`
- `docs/requirements.md`
- `docs/plan.md`
- `docs/reference_standards.md`

## Findings

1. `PLAN-005` overclaims `REQ-GRAN-CONTRACT-DECIDABLE`.
`docs/requirements.md:44` requires the governing machine-readable audit-status contract to be decidable from `docs/requirements.md` and `docs/reference_standards.md` alone. `docs/plan.md:232` maps `PLAN-005` to that requirement, but `PLAN-005` itself at `docs/plan.md:152-176` states ownership and subordination rules without directly stating that the machine-readable audit-status contract is fully decidable from the governing two-document contract alone. Under the directness rule in `docs/reference_standards.md:24-32` and `docs/reference_standards.md:126-130`, that blanket mapping is invalid.

2. `PLAN-005` overclaims `REQ-CONTRACT-CLOSURE-AUTHORITY`.
`docs/requirements.md:62` requires every rule needed to decide contract validity, authority boundaries, and allowed audit-status semantics to be stated in `docs/requirements.md` and `docs/reference_standards.md` without requiring supporting-governance documents, roadmap text, or repository-local instruction files as additional authority. `docs/plan.md:232` maps `PLAN-005` to that requirement, but `PLAN-005` at `docs/plan.md:152-176` does not directly state the full allowed-audit-status-semantics portion of that requirement or state that the governing two-document contract alone is sufficient for those semantics. Because the mapped fragment is not directly present in the cited item, the mapping fails the directness rule.

## Insufficient Evidence

- none

## Open-Items

- Revise `PLAN-005` so the item itself directly states that the machine-readable audit-status contract and allowed audit-status semantics for requirements-, plan-, and roadmap-phase auditing are decidable from `docs/requirements.md` and `docs/reference_standards.md` alone.
- Re-check the `PLAN-005` mapping row after the above text exists in the item itself, not only in surrounding narrative or inferred ownership language.

## Decision Basis

- `docs/reference_standards.md:24-32` requires direct statement in the cited document's own text.
- `docs/reference_standards.md:126-130` rejects downstream mappings that overclaim fragments not directly stated by the cited item.
- The detected defects are plan-design and mapping defects, so `REJECT_TO_ARCHITECT` is the allowed disposition under `docs/reference_standards.md:154-157`.
