# Plan — Handler Template Workstream

**Phase:** Architect  
**Date:** 2026-06-03  
**Authority Sources:** `AGENTS.md`, `docs/requirements.md`, `docs/reference_standards.md`  
**Informative Audit Input:** `docs/audit_report.md`

## Purpose

This plan defines the Architect response for the handler-template workstream. It first closes the governing contract between `docs/requirements.md` and `docs/reference_standards.md`, then translates that contract into an implementation-ready design for the actual workstream deliverables:

- an explicit handler template notebook under `nbs/handlers/`
- a checklist or equivalent guidance that separates provider-specific sections from reusable sections
- a hook-governed lightweight post-commit verification flow
- usage documentation that explains how the template should be used before any commonization effort

`docs/audit_report.md` is treated as a diagnostic input to this revision, not as a governing authority source.

## Architectural Response To The Audit

The current audit identifies four failure modes that this plan must eliminate:

1. plan-phase acceptance drifted into required supporting documents as if they were governing authority
2. the plan emphasized governance repair but under-specified the real workstream deliverables
3. the plan elevated `docs/audit_report.md` into an authority source
4. the plan replaced the source-of-truth rule `every normative REQ-...` with a brittle fixed-count threshold

The design response is:

- keep the governing contract in `docs/requirements.md` and `docs/reference_standards.md`
- treat `docs/acceptance_matrix.md` and `docs/traceability_map.md` as required supporting documents that must align to that contract without replacing it
- structure the plan around the substantive handler-template deliverables, with governance repair only as enabling work
- express coverage in terms of all currently normative requirement identifiers defined in `docs/requirements.md`, never a copied count

## Design Principles

### DP-1 — Governing Authority Stays Upstream

Acceptance meaning and audit-contract meaning remain owned by `docs/requirements.md` and `docs/reference_standards.md`. This plan may explain how those requirements will be satisfied, but it must not tighten, relax, or replace them.

### DP-2 — Supporting Governance Documents Stay Subordinate

`docs/acceptance_matrix.md` and `docs/traceability_map.md` are required and must be kept internally consistent with this plan, but they operationalize and trace the governing contract rather than define it.

### DP-3 — Deliverables Come Before Commonization

The first deliverable is a current-state explicit template. It must document the existing handler shape clearly enough to support later commonization discussions, without forcing immediate refactoring.

### DP-4 — Notebook-First Execution

The implementation path must remain notebook-first. The canonical behavioral changes live in notebook sources, with generated Python treated as derived output.

### DP-5 — Lightweight Verification Boundary

Post-commit verification for this workstream exists to catch export, syntax, and import-time breakage quickly. It does not expand into dataset downloads, remote API usage, full NetCDF runs, or broad regression execution.

## Plan Items

### PLAN-001 — Close The Governing Contract

Revise `docs/requirements.md` and `docs/reference_standards.md` so they explicitly close the authority boundary that the audit found ambiguous.

Required outcomes:

- the two-document governance set is explicit and self-sufficient for requirements-, plan-, and roadmap-phase contract interpretation
- `docs/acceptance_matrix.md` and `docs/traceability_map.md` are explicitly defined as required supporting governance documents
- supporting governance documents are stated to be subordinate operationalization surfaces, not replacement authority sources
- plan-phase and roadmap-phase documentary acceptance remains decidable without importing out-of-scope authority

### PLAN-002 — Define The Handler Template Architecture

Specify the architecture of the explicit handler template notebook so PM and Implementer work from a concrete current-state target.

Required outcomes:

- the template target is an `nbs/handlers/` notebook, not a generated `.py` file
- the template preserves the ordered Handler Template Baseline from `docs/requirements.md`
- the template is explicitly current-state descriptive
- the template identifies where provider-specific logic is expected to vary

### PLAN-003 — Define Zone Guidance And Usage Documentation

Architect the guidance surfaces that accompany the template so reviewers can distinguish stable reusable structure from provider-specific variance.

Required outcomes:

- the template or its paired usage guidance identifies provider-specific zones
- the template or its paired usage guidance identifies reusable callback-oriented zones
- likely future commonization candidates are marked as discussion inputs, not refactoring mandates
- maintainers are told how to use the template before any broad handler migration begins

### PLAN-004 — Define Hook-Governed Lightweight Verification

Architect the post-commit verification flow required by this workstream.

Required outcomes:

- `.git/hooks/post-commit` remains the governing orchestration surface
- the documented minimum sequence is export/regeneration, `python -m py_compile`, and lightweight import smoke checks
- heavyweight categories excluded by `REQ-POST-COMMIT-LIGHTWEIGHT-BOUNDARY` remain excluded
- the validation design stays compatible with the repository's practical validation order in `AGENTS.md`

### PLAN-005 — Align Required Supporting Governance Documents

Revise `docs/acceptance_matrix.md` and `docs/traceability_map.md` so they faithfully operationalize the repaired contract and this plan.

Required outcomes:

- every normative `REQ-...` identifier currently defined in `docs/requirements.md` is represented without fixed-count duplication
- no matrix or traceability row implies that required supporting documents outrank the governing contract
- roadmap-phase documentary evidence stays inside the declared documentation scope
- later implementation evidence remains tracked separately for downstream phases

### PLAN-006 — Preserve Implementation Guardrails

Carry the workstream's substantive boundaries intact into downstream planning.

Required outcomes:

- no plan item forces immediate refactoring of existing handlers
- no plan item authorizes direct generated-code edits as the canonical behavior change
- Python `>=3.7` compatibility remains the baseline for any new supporting code
- success criteria continue to point at the actual deliverables: template notebook, zone guidance, hook-governed lightweight verification, and usage documentation

## Deliverable Architecture

### Deliverable Group A — Template Assets

- explicit handler template notebook under `nbs/handlers/`
- baseline sections in required order
- prose and code layout consistent with literate notebook use

### Deliverable Group B — Guidance Assets

- provider-specific versus reusable zone markers
- notes on likely commonization candidates
- usage guidance for authors adopting the template

### Deliverable Group C — Verification Assets

- hook-governed post-commit sequence definition
- export, compile, and import-smoke stages only
- explicit heavyweight exclusions

### Deliverable Group D — Governance Support Assets

- acceptance matrix aligned to every normative requirement
- traceability map aligned from requirements through plan and roadmap to evidence

## Requirement-to-Plan Mapping

| Plan Item | Primary Requirements Served |
|---|---|
| PLAN-001 | `REQ-GRAN-REQS-SCOPE`, `REQ-GRAN-REQS-COMPLETE`, `REQ-GRAN-CONTRACT-DECIDABLE`, `REQ-GRAN-CONTRACT-SUBORD`, `REQ-GRAN-SUPPORTING-DOCS-ROLE` |
| PLAN-002 | `REQ-NB-TEMPLATE`, `REQ-CURRENT-STATE-FIDELITY`, `REQ-NBDEV-COMPAT`, `REQ-AC-TEMPLATE-EXISTS`, `REQ-AC-TEMPLATE-BASELINE`, `REQ-AC-TEMPLATE-NBDEV` |
| PLAN-003 | `REQ-DIFFERENCE-VISIBILITY`, `REQ-PRESERVE-FLEXIBILITY`, `REQ-AVOID-PREMATURE-COMMONIZATION`, `REQ-READABILITY`, `REQ-AC-TEMPLATE-ZONES`, `REQ-AC-PRESERVE-FLEXIBILITY`, `REQ-AC-READABILITY` |
| PLAN-004 | `REQ-GRAN-HOOK`, `REQ-POST-COMMIT-AUTHORITY`, `REQ-POST-COMMIT-SEQUENCE`, `REQ-POST-COMMIT-LIGHTWEIGHT-BOUNDARY`, `REQ-LOW-FRICTION-VALIDATION`, `REQ-CHECK-EXPORT`, `REQ-CHECK-COMPILE`, `REQ-CHECK-COVERAGE`, `REQ-AC-POST-COMMIT-SEQUENCE`, `REQ-AC-POST-COMMIT-BOUNDARY` |
| PLAN-005 | `REQ-GRAN-CHECKS`, `REQ-GRAN-ROADMAP` |
| PLAN-006 | `REQ-GRAN-PLAN`, `REQ-PYTHON-BASELINE`, `REQ-AC-NO-REFACTOR` |

## Phase Breakdown

### Phase 1 — Contract Repair

| Step | Action | Plan Item |
|---|---|---|
| A1 | tighten the authority boundary in `docs/requirements.md` | PLAN-001 |
| A2 | tighten the authority boundary in `docs/reference_standards.md` | PLAN-001 |
| A3 | realign `docs/acceptance_matrix.md` to the repaired contract | PLAN-005 |
| A4 | realign `docs/traceability_map.md` to the repaired contract | PLAN-005 |

### Phase 2 — Deliverable Architecture

| Step | Action | Plan Item |
|---|---|---|
| B1 | define the notebook-first template target and baseline sections | PLAN-002 |
| B2 | define provider-specific, reusable, and commonization-candidate zones | PLAN-003 |
| B3 | define usage guidance expectations for template authors | PLAN-003 |
| B4 | define the lightweight hook-governed verification sequence | PLAN-004 |

### Phase 3 — Downstream Guardrails

| Step | Action | Plan Item |
|---|---|---|
| C1 | confirm no plan item forces immediate handler migration | PLAN-006 |
| C2 | confirm no plan item treats generated Python as canonical | PLAN-006 |
| C3 | confirm verification and support code remain within Python `>=3.7` | PLAN-006 |

## Architect Gate Criteria

The Architect gate is satisfied only if all of the following are true:

- `docs/plan.md` is subordinate to `docs/requirements.md` and `docs/reference_standards.md`
- the plan no longer treats `docs/audit_report.md` as an authority source
- the plan describes how the actual workstream deliverables will be produced
- the plan does not use copied fixed-count coverage thresholds
- the required supporting governance documents are aligned in the same change set without being elevated above the governing contract

## Non-Goals

This plan does not:

- claim that the template notebook already exists
- claim that `.git/hooks/post-commit` is already implemented
- require git commit operations
- force migration of existing handlers into a shared pipeline during this phase
- change the repository's notebook-first source-of-truth model

## Audit Closure Intent

This revision addresses the audit findings by:

- removing out-of-scope gate dependence from the plan's governing authority
- restoring deliverable-centered planning
- demoting `docs/audit_report.md` to informative input
- replacing fixed-count language with source-of-truth coverage language tied to all normative `REQ-...` identifiers currently defined in `docs/requirements.md`
