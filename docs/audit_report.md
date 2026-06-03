# Audit Report

## Summary
- decision: `REJECT_TO_ARCHITECT`
- owner: `Architect`
- next_gate: `ARCHITECT_REWORK`
- audited_scope:
  - `AGENTS.md`
  - `docs/requirements.md`
  - `docs/plan.md`
  - `docs/reference_standards.md`

## Audit Method
- Read the full contents of all fixed-scope files before deciding.
- Applied the required authority order:
  1. `docs/requirements.md`
  2. `docs/plan.md`
  3. `docs/reference_standards.md`
- Did not use repository-wide recursive discovery.
- Did not use out-of-scope files as decision evidence.

## Findings

### 1. Invalid requirement-to-plan mapping for `REQ-NBDEV-COMPAT` and `REQ-AC-TEMPLATE-NBDEV`
- Severity: `high`
- Reason code: `ARCH_PLAN_MAPPING_NBDEV_COMPAT_INEXACT`
- Requirement evidence:
  - `docs/requirements.md:94-97` requires exportability through the current `nbdev` flow, importability after generation, and no broken `default_exp`, invalid export cell, or circular import by default.
  - `docs/requirements.md:217` requires the template to participate in the `nbdev` export flow without breaking repository imports.
- Plan evidence:
  - `docs/plan.md:166` maps `PLAN-001` to `REQ-NBDEV-COMPAT` and `REQ-AC-TEMPLATE-NBDEV`.
  - `docs/plan.md:72-75` states only that the template is under `nbs/handlers/`, follows `nbdev` conventions, preserves the baseline, and is current-state descriptive.
- Standard evidence:
  - `docs/reference_standards.md:113` requires requirement-to-plan mappings to be semantically exact.
  - `docs/reference_standards.md:175` requires cited plan items to contain the relevant required outcome directly.
- Judgment:
  - `PLAN-001` does not directly state exportability, post-generation importability, or the no-circular-import / no-invalid-export-cell outcome.
  - The cited mapping therefore requires inferential repair from nearby material and is not semantically exact.

### 2. Invalid requirement-to-plan mapping for `REQ-PRESERVE-FLEXIBILITY`
- Severity: `high`
- Reason code: `ARCH_PLAN_MAPPING_PRESERVE_FLEXIBILITY_INEXACT`
- Requirement evidence:
  - `docs/requirements.md:122-124` requires that the template not imply immediate normalization of provider differences and that it support the current need to absorb imperfect external data.
- Plan evidence:
  - `docs/plan.md:167` maps `PLAN-002` to `REQ-PRESERVE-FLEXIBILITY`.
  - `docs/plan.md:83-86` says `PLAN-002` marks provider-specific sections, reusable sections, commonization candidates, and varying sections.
  - `docs/plan.md:94-97` says `PLAN-003` preserves flexibility for imperfect provider inputs, but `PLAN-003` is not the mapped item for `REQ-PRESERVE-FLEXIBILITY`.
- Standard evidence:
  - `docs/requirements.md:38` forbids convenience mappings based only on nearby topic overlap.
  - `docs/reference_standards.md:113` and `docs/reference_standards.md:175` require exact mappings to items that directly state the required outcome.
- Judgment:
  - The cited `PLAN-002` outcomes do not directly cover the imperfect-external-data flexibility requirement.
  - The requirement is only partially addressed by the mapped item, so the table entry is not exact.

### 3. Invalid requirement-to-plan mapping for `REQ-CONTRACT-CLOSURE-PRESENT-STATE`
- Severity: `high`
- Reason code: `ARCH_PLAN_MAPPING_PRESENT_STATE_INEXACT`
- Requirement evidence:
  - `docs/requirements.md:59` requires documentary-phase acceptance to be judged against the current contents of the fixed in-scope governing documents, not against prospective future rewrites proposed later.
- Plan evidence:
  - `docs/plan.md:171` maps `PLAN-006` to `REQ-CONTRACT-CLOSURE-PRESENT-STATE`.
  - `docs/plan.md:131-135` says `PLAN-006` keeps the plan subordinate to thresholds, avoids immediate refactoring, avoids generated-code canonicalization, ties success to actual deliverables, and does not require git commit operations.
  - `docs/plan.md:46` contains the present-tense rule in `DP-2`, but that sentence is outside the cited plan item.
- Standard evidence:
  - `docs/requirements.md:50` requires trace links to be semantically exact without inferential repair.
  - `docs/reference_standards.md:175` requires every cited plan item to itself contain the relevant required outcome.
- Judgment:
  - The cited `PLAN-006` text does not directly state the present-state rule.
  - The mapping depends on cross-item inference from `DP-2`, so it fails the exact-citation rule.

## Decision Basis
- `docs/plan.md` correctly declares the two-document authority boundary and keeps `AGENTS.md` as consulted guidance only.
- The rejection is based on in-scope semantic mapping defects inside the plan itself.
- Under `docs/reference_standards.md:138`, design and requirements-interpretation defects require `REJECT_TO_ARCHITECT`.

## Insufficient Evidence
- none

## Open-Items
- Revise the `Requirement-to-Plan Mapping` table so that each cited plan item directly states the mapped requirement outcome.
- Either move the missing outcomes into the cited `PLAN-...` items or change the mappings to cite the plan items that already state those outcomes.
- Re-run plan audit after the mapping table is semantically exact under `docs/requirements.md:38`, `docs/requirements.md:50`, `docs/reference_standards.md:113`, and `docs/reference_standards.md:175`.
