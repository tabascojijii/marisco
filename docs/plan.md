# Plan — Handler Template Workstream

**Phase:** Architect  
**Date:** 2026-06-03  
**Authority Sources:** `docs/requirements.md`, `docs/reference_standards.md`, `docs/audit_report.md`

## Purpose

This plan repairs the structural governance defects identified in `docs/audit_report.md` before any downstream implementation work proceeds. It defines Architect-owned plan items that:

- close the normative contract between `docs/requirements.md` and `docs/reference_standards.md`
- restore full normative coverage in `docs/acceptance_matrix.md`
- keep roadmap-phase auditing decidable from the fixed documentation scope alone
- preserve a clean boundary between documentary acceptance and later implementation evidence

This plan is subordinate to `docs/requirements.md` for acceptance meaning and to `docs/reference_standards.md` for workflow behavior.

## Audit-Driven Design Response

`docs/audit_report.md` identified three upstream defects that must be corrected at the Architect layer:

1. `docs/acceptance_matrix.md` did not cover every normative `REQ-...` identifier.
2. Roadmap-phase acceptance still depended on out-of-scope implementation evidence paths.
3. Artifact-failure rules were not phase-qualified inside the normative governance set.

The repair strategy in this plan is therefore contract-first:

- define phase-aware evidence ownership in the governing documents themselves
- require every normative requirement to have documentary evidence for roadmap-phase auditing
- treat implementation artifacts as later evidence, not as prerequisites for requirements-, plan-, or roadmap-phase PASS decisions

## Architectural Principles

### AP-1 — Two-Layer Evidence Model

Every normative requirement in this workstream must be expressible in two evidence layers:

- documentary evidence used during requirements-, plan-, and roadmap-phase auditing
- later implementation evidence used during implementation-phase auditing when concrete files, hook outputs, or generated artifacts exist

No roadmap-phase check may require reading files outside the fixed documentation scope.

### AP-2 — Normative Closure Lives Upstream

If a phase boundary, artifact rule, or acceptance threshold is ambiguous, the repair target is `docs/requirements.md` or `docs/reference_standards.md`, not downstream prose in `docs/plan.md` or `docs/roadmap.md`.

### AP-3 — Matrix Completeness Is Mandatory

`docs/acceptance_matrix.md` is not a partial convenience table. It is a normative operationalization surface and must cover every `REQ-...` identifier defined in `docs/requirements.md`.

### AP-4 — Traceability Must Preserve Phase Separation

`docs/traceability_map.md` must show, per requirement, which evidence is sufficient at roadmap phase and which evidence is expected later at implementation phase. That separation must be explicit, not inferred.

## Plan Items

### PLAN-001 — Close the Requirements Contract

Revise `docs/requirements.md` so the source-of-truth contract explicitly requires phase-aware operationalization in `docs/acceptance_matrix.md`.

Required outcomes:

- `REQ-GRAN-CHECKS` explicitly requires full normative coverage for every `REQ-...`
- the matrix contract explicitly includes:
  - layer
  - criterion
  - roadmap-phase documentary evidence path
  - later implementation evidence path or `not applicable`
  - roadmap threshold
  - later implementation threshold or `not applicable`
- the validation baseline explicitly states that requirements-, plan-, and roadmap-phase audits are judged from the fixed documentation scope only

Rationale:
This removes the prior defect where acceptance semantics depended on unstated phase interpretation.

### PLAN-002 — Close the Reference Standards Contract

Revise `docs/reference_standards.md` so artifact and evidence rules are phase-qualified inside the normative governance set.

Required outcomes:

- `Granularity Ownership Boundary` names the full phase-aware ownership of `docs/acceptance_matrix.md`
- `Evidence And Artifact Rules` states that absent later implementation artifacts are not documentary-phase failures by themselves
- implementation-phase artifact failure remains mandatory once those artifacts are in scope
- `Validation And Test Baseline` explicitly states that earlier documentary phases must be decidable from documentary evidence alone

Rationale:
This removes the ambiguity called out in the audit around `artifacts/*.json` and other future outputs.

### PLAN-003 — Rebuild the Acceptance Matrix as a Complete Normative Surface

Replace `docs/acceptance_matrix.md` with a fully covered, phase-aware matrix.

Required outcomes:

- every normative requirement in `docs/requirements.md` is listed exactly once
- the matrix covers all `33/33` currently normative requirements in scope
- each row contains:
  - layer
  - criterion
  - roadmap-phase documentary evidence path
  - later implementation evidence path
  - roadmap threshold
  - later implementation threshold
- roadmap-phase rows rely only on documentation-scope evidence paths

Rationale:
This resolves the audit finding that the matrix had incomplete coverage and mixed future evidence into documentary acceptance.

### PLAN-004 — Align the Traceability Map to the Two-Layer Evidence Model

Revise `docs/traceability_map.md` so every requirement maps to:

- an Architect plan item
- a PM roadmap item
- roadmap-phase documentary evidence
- later implementation evidence when applicable

Required outcomes:

- no requirement remains without a plan item
- roadmap-phase evidence stays within the fixed documentation scope
- later implementation evidence is preserved without being misclassified as roadmap-phase evidence

Rationale:
This ensures PM and Auditor work from the same phase boundaries without reconstructing intent.

### PLAN-005 — Recast the Plan as the Architectural Bridge, Not an Override

`docs/plan.md` itself must remain an implementation strategy document, not a place where acceptance meaning is invented or waived.

Required outcomes:

- plan items reference upstream requirements instead of replacing them
- this plan explicitly treats contract repairs as prerequisites for downstream implementation planning
- the plan preserves the original workstream intent:
  - explicit handler template notebook
  - current-state fidelity
  - lightweight hook-governed verification
  - no forced immediate commonization

Rationale:
This prevents the earlier failure mode where plan prose tried to explain away unresolved upstream ambiguity.

### PLAN-006 — Preserve Downstream Implementation Guardrails

After the documentary contract is repaired, downstream execution remains governed by the original workstream requirements.

Architectural guardrails to preserve:

- the template remains notebook-first under `nbs/handlers/`
- generated `.py` files remain derived artifacts
- post-commit verification remains hook-governed
- the lightweight verification boundary remains export / compile / import-smoke only
- provider-specific variation remains explicitly allowed
- existing handlers are not forced into immediate refactoring during this workstream

Rationale:
The governance repair must not accidentally mutate the substantive intent of the handler-template workstream.

## Requirement-to-Plan Mapping

| Plan Item | Primary Requirements Served |
|---|---|
| PLAN-001 | `REQ-GRAN-REQS-SCOPE`, `REQ-GRAN-REQS-COMPLETE`, `REQ-GRAN-CONTRACT-DECIDABLE`, `REQ-GRAN-CHECKS` |
| PLAN-002 | `REQ-GRAN-STANDARDS`, `REQ-GRAN-CONTRACT-DECIDABLE`, `REQ-GRAN-CONTRACT-SUBORD` |
| PLAN-003 | `REQ-GRAN-CHECKS` |
| PLAN-004 | `REQ-GRAN-ROADMAP`, `REQ-GRAN-CHECKS` |
| PLAN-005 | `REQ-GRAN-PLAN`, `REQ-GRAN-ROADMAP` |
| PLAN-006 | `REQ-NB-TEMPLATE`, `REQ-CURRENT-STATE-FIDELITY`, `REQ-DIFFERENCE-VISIBILITY`, `REQ-NBDEV-COMPAT`, `REQ-POST-COMMIT-AUTHORITY`, `REQ-POST-COMMIT-SEQUENCE`, `REQ-POST-COMMIT-LIGHTWEIGHT-BOUNDARY`, `REQ-PRESERVE-FLEXIBILITY`, `REQ-AVOID-PREMATURE-COMMONIZATION`, `REQ-READABILITY`, `REQ-LOW-FRICTION-VALIDATION`, `REQ-CHECK-EXPORT`, `REQ-CHECK-COMPILE`, `REQ-CHECK-COVERAGE`, `REQ-AC-*`, `REQ-PYTHON-BASELINE` |

## Phase Breakdown

### Phase 1 — Governance Repair

| Step | Action | Plan Item |
|---|---|---|
| A1 | Close `docs/requirements.md` phase-aware matrix contract | PLAN-001 |
| A2 | Close `docs/reference_standards.md` phase boundary and artifact rules | PLAN-002 |
| A3 | Replace `docs/acceptance_matrix.md` with complete normative coverage | PLAN-003 |
| A4 | Align `docs/traceability_map.md` with documentary-vs-implementation evidence separation | PLAN-004 |
| A5 | Rewrite `docs/plan.md` so it documents the repair architecture instead of compensating informally | PLAN-005 |

### Phase 2 — Downstream Planning Preservation

| Step | Action | Plan Item |
|---|---|---|
| B1 | Confirm the repaired documents do not alter notebook-first intent | PLAN-006 |
| B2 | Confirm the repaired documents do not force immediate handler refactoring | PLAN-006 |
| B3 | Confirm the repaired documents preserve hook-governed lightweight verification intent | PLAN-006 |

## Verification Strategy

### Documentary Verification

The repaired docset passes the Architect gate only if all of the following are true:

- `docs/requirements.md` and `docs/reference_standards.md` now close the phase boundary without relying on extra-scope interpretation
- `docs/acceptance_matrix.md` maps every normative requirement in scope
- roadmap-phase evidence paths point only to files in the fixed documentation scope
- later implementation evidence paths are still preserved for downstream phases
- `docs/traceability_map.md` agrees with the acceptance matrix on phase separation

### Residual Downstream Verification

This plan does not waive later implementation evidence. After roadmap phase:

- the template notebook will still need to exist under `nbs/handlers/`
- the generated module will still need to export and import cleanly
- `.git/hooks/post-commit` will still need to implement the required lightweight sequence
- required JSON artifacts will still need to satisfy the shared `execution_id` contract when implementation-phase evidence is in scope

## Non-Goals

This plan does not:

- create or edit the handler template notebook itself
- implement `.git/hooks/post-commit`
- require a git commit
- change the substantive acceptance intent of the workstream
- move implementation-phase evidence into roadmap-phase scope

## Audit Alignment

This revised plan resolves the three open items in `docs/audit_report.md` as follows:

- `OI-001` by requiring complete `33/33` normative coverage in `docs/acceptance_matrix.md`
- `OI-002` by enforcing documentary evidence paths for roadmap-phase acceptance
- `OI-003` by phase-qualifying artifact-failure rules inside `docs/reference_standards.md`

The plan therefore positions the docset for a clean Architect re-audit without shifting unresolved ambiguity downstream.
