# Roadmap

**Phase:** PM  
**Date:** 2026-06-03  
**Governing Authority Sources:** `docs/requirements.md`, `docs/reference_standards.md`  
**Consulted Inputs:** `docs/plan.md`, `AGENTS.md`

## Purpose

This roadmap translates `docs/plan.md` into an implementation-ready PM sequence for the handler-template workstream.

For documentary-phase acceptance, this roadmap remains subordinate to the governing two-document contract formed by `docs/requirements.md` and `docs/reference_standards.md`. `AGENTS.md` is applied as repository-local execution guidance for notebook-first authoring, minimal diffs, and validation discipline, but it is not used here as a replacement authority source for gate semantics or contract closure.

## Authority Boundary

- `docs/requirements.md` defines delivery obligations, acceptance thresholds, and requirement identifiers.
- `docs/reference_standards.md` defines workflow behavior, role expectations, evidence rules, and required markdown blocks.
- `docs/plan.md` defines the Architect response that this roadmap sequences into executable work.
- `AGENTS.md` constrains how work should be carried out locally in this repository, especially notebook-first editing and lightweight validation order.
- This roadmap must not introduce new acceptance thresholds, new workflow states, alternate decision vocabularies, or extra documentary-phase gate prerequisites.

## Roadmap-Phase Evidence Boundary

- Roadmap-phase pass or fail must remain decidable from the fixed documentation scope declared by the governing contract.
- Documentary evidence in this phase therefore stays inside `docs/requirements.md`, `docs/reference_standards.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/acceptance_matrix.md`, and `docs/traceability_map.md`.
- `AGENTS.md` may be cited as consulted implementation guidance, but it is not a deciding evidence path for whether the governing contract is closed.
- Future implementation evidence such as `nbs/handlers/handler_template.ipynb`, generated modules, `.git/hooks/post-commit`, or hook-run artifacts belongs to later phases and must not be required to pass the roadmap phase.

## Execution Constraints

- Treat `nbs/` as the primary implementation surface.
- Treat generated `marisco/` modules as derived artifacts.
- Keep changes minimal and targeted to this workstream.
- Do not force migration or immediate refactoring of existing handlers.
- Keep post-commit verification limited to export or regeneration, compile, and import-smoke checks.
- Preserve Python `>=3.7` compatibility for any new verification-supporting code introduced by this workstream.
- Do not require git commit operations as part of roadmap execution.

## Roadmap Items

### RM-001 — Lock Governance Boundaries Before Execution

Confirm that roadmap execution stays subordinate to `docs/requirements.md` and `docs/reference_standards.md`, and that `docs/plan.md` is translated without changing requirement meaning.

Required outcomes:

- project-specific acceptance granularity remains owned by `docs/requirements.md`, and roadmap execution does not attempt to repair requirements-level completeness gaps locally
- repository-wide audit-depth rules, abstract-term handling, and documentary-phase audit-contract semantics remain owned by `docs/reference_standards.md`, with `docs/audit_contract.md` remaining subordinate
- no roadmap text becomes a replacement acceptance authority
- no roadmap item introduces a new gate rule or alternate pass/fail algorithm
- roadmap-phase evidence paths stay inside the declared documentation scope
- repository-local guidance remains consulted execution discipline only
- roadmap validity is judged from the current in-scope governing documents, plan, and roadmap text rather than from hypothetical future rewrites

Maps to: `PLAN-005`, `PLAN-006`  
Roadmap-phase evidence: `docs/requirements.md`, `docs/reference_standards.md`, `docs/plan.md`, `docs/roadmap.md`

### RM-002 — Align Supporting Governance Documents

Revise supporting-governance documents so they operationalize the current normative requirement set and this roadmap without changing the authority boundary.

Required outcomes:

- `docs/acceptance_matrix.md` continues to cover every normative `REQ-...` identifier
- for every normative `REQ-...` identifier, `docs/acceptance_matrix.md` states acceptance layer, criterion, roadmap-phase documentary evidence path, later implementation evidence path or `not applicable`, roadmap threshold, and later implementation threshold or `not applicable`
- `docs/traceability_map.md` maps every normative `REQ-...` identifier to source, plan, roadmap, and evidence paths
- every requirement-to-plan and requirement-to-roadmap citation in supporting documents remains semantically exact to the stated outcomes of the cited item
- roadmap references to supporting documents remain operational, not authority-transferring
- no supporting document introduces a new prerequisite absent from the governing contract

Maps to: `PLAN-005`  
Roadmap-phase evidence: `docs/acceptance_matrix.md`, `docs/traceability_map.md`, `docs/roadmap.md`

### RM-003 — Deliver The Template Notebook Target

Create the first explicit handler template notebook under `nbs/handlers/` as a current-state descriptive asset that preserves the Handler Template Baseline in the required order.

Required outcomes:

- the deliverable target is a notebook under `nbs/handlers/`
- the ordered baseline sections from `docs/requirements.md` are preserved
- `nbdev` conventions such as `default_exp` and appropriate exported cells are planned into the notebook structure
- generated `.py` files are not treated as the canonical behavior-change surface
- the notebook structure is planned to export through the current `nbdev` flow and remain importable after generation
- the planned structure avoids introducing a broken `default_exp`, invalid export cell, or circular import by default

Maps to: `PLAN-001`  
Roadmap-phase evidence: `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/traceability_map.md`  
Later implementation evidence: `nbs/handlers/handler_template.ipynb`, generated module under `marisco/handlers/`

### RM-004 — Mark Variation, Reuse, And Flexibility Zones

Define how the template will distinguish provider-specific logic, reusable callback-oriented logic, and future commonization candidates without turning those labels into immediate refactoring mandates.

Required outcomes:

- provider-specific sections are explicitly marked
- reusable sections are explicitly marked
- commonization candidates are labeled as discussion inputs only
- provider variation remains explicitly allowed rather than normalized away by roadmap language
- template usage remains flexible enough to absorb imperfect external provider data without forcing premature normalization

Maps to: `PLAN-002`, `PLAN-006`  
Roadmap-phase evidence: `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/traceability_map.md`  
Later implementation evidence: `nbs/handlers/handler_template.ipynb`

### RM-005 — Define Author Guidance And Readability Rules

Describe how maintainers should use the template as a literate notebook scaffold before any broader commonization effort begins.

Required outcomes:

- the roadmap preserves notebook-first authoring
- the roadmap preserves prose-adjacent-to-code readability expectations
- the roadmap explains that existing handlers are not forced to migrate in this phase
- usage guidance remains current-state and pragmatic rather than speculative

Maps to: `PLAN-003`, `PLAN-006`  
Roadmap-phase evidence: `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/traceability_map.md`  
Later implementation evidence: `nbs/handlers/handler_template.ipynb`

### RM-006 — Define Hook-Governed Lightweight Verification

Specify the minimum post-commit verification design for this workstream, keeping `.git/hooks/post-commit` as the orchestration surface and preserving the lightweight boundary.

Required outcomes:

- project-specific acceptance granularity remains owned by `docs/requirements.md`, and `.git/hooks/post-commit` is not treated as the source of that granularity policy
- `.git/hooks/post-commit` is the governing orchestration surface
- the documented sequence contains export or regeneration, `python -m py_compile`, and lightweight import smoke checks
- the documented post-commit path remains practical for normal development by staying limited to those lightweight stages and by excluding external-network and full-dataset execution from the post-commit path
- the roadmap directly states stage-to-failure coverage: export or regeneration catches broken notebook export structure, `python -m py_compile` catches syntax errors in generated modules, and import smoke checks catch obvious import-time breakage in touched code paths
- heavyweight execution remains explicitly excluded
- the verification path remains practical for normal development

Maps to: `PLAN-004`  
Roadmap-phase evidence: `docs/requirements.md`, `docs/reference_standards.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/traceability_map.md`  
Later implementation evidence: `.git/hooks/post-commit`, hook run log

### RM-007 — Preserve Validation And Compatibility Guardrails

Carry AGENTS-guided execution discipline into implementation planning without promoting repository-local guidance into documentary-phase authority.

Required outcomes:

- validation starts from the smallest affected surface first
- lightweight static validation is planned before broader verification
- Python `>=3.7` compatibility is preserved for any new verification-supporting code
- no roadmap step requires git commit operations

Maps to: `PLAN-004`, `PLAN-006`  
Roadmap-phase evidence: `docs/requirements.md`, `docs/reference_standards.md`, `docs/plan.md`, `docs/roadmap.md`  
Later implementation evidence: `nbs/handlers/handler_template.ipynb`, `.git/hooks/post-commit`

## Milestones

### Milestone 1 — Documentary Readiness

1. Complete `RM-001`.
2. Complete `RM-002`.
3. Confirm that roadmap-phase evidence remains documentary and in-scope.

### Milestone 2 — Template Definition Readiness

1. Complete `RM-003`.
2. Complete `RM-004`.
3. Complete `RM-005`.

### Milestone 3 — Verification Definition Readiness

1. Complete `RM-006`.
2. Complete `RM-007`.
3. Reconfirm that verification remains lightweight and hook-governed.

## Execution Order

1. Finish governance-boundary checks in `RM-001` before relying on roadmap text for downstream execution.
2. Finish support-document alignment in `RM-002` before declaring roadmap traceability complete.
3. Execute `RM-003`, `RM-004`, and `RM-005` together as the template-definition workstream.
4. Execute `RM-006` and `RM-007` together as the verification-definition workstream.
5. Close by rechecking `docs/acceptance_matrix.md` and `docs/traceability_map.md` against the final roadmap language.

## Evidence Expectations

| Roadmap Item | Roadmap-Phase Documentary Evidence | Later Implementation Evidence |
|---|---|---|
| `RM-001` | `docs/requirements.md`, `docs/reference_standards.md`, `docs/plan.md`, `docs/roadmap.md` | not applicable |
| `RM-002` | `docs/acceptance_matrix.md`, `docs/traceability_map.md`, `docs/roadmap.md` | not applicable |
| `RM-003` | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/traceability_map.md` | `nbs/handlers/handler_template.ipynb`, generated module under `marisco/handlers/` |
| `RM-004` | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/traceability_map.md` | `nbs/handlers/handler_template.ipynb` |
| `RM-005` | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/traceability_map.md` | `nbs/handlers/handler_template.ipynb` |
| `RM-006` | `docs/requirements.md`, `docs/reference_standards.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/traceability_map.md` | `.git/hooks/post-commit`, hook run log |
| `RM-007` | `docs/requirements.md`, `docs/reference_standards.md`, `docs/plan.md`, `docs/roadmap.md` | `nbs/handlers/handler_template.ipynb`, `.git/hooks/post-commit` |

## Risks And Controls

- Risk: The roadmap drifts into gate-definition rather than execution sequencing.  
  Control: `RM-001` keeps authority in `docs/requirements.md` and `docs/reference_standards.md`.
- Risk: Supporting documents accidentally become replacement authority.  
  Control: `RM-002` limits them to operationalization and traceability.
- Risk: The template becomes speculative future architecture.  
  Control: `RM-003` and `RM-004` keep the template current-state descriptive.
- Risk: Verification grows too heavy for normal development.  
  Control: `RM-006` limits the sequence to the required lightweight stages.
- Risk: Local execution guidance gets written as gate-defining authority.  
  Control: `RM-007` keeps `AGENTS.md` as consulted discipline only.

## Granularity Boundary

- This roadmap owns task ordering, implementation grouping, readiness checks, and self-check sequencing.
- This roadmap does not own requirement thresholds, workflow state semantics, or documentary-phase contract validity rules.
- If a missing acceptance boundary is discovered, the repair point is upstream in `docs/requirements.md` or `docs/reference_standards.md`, not an ad hoc roadmap patch.

## Self-Check (Required)

- [x] `docs/requirements.md` remains the sole source of acceptance thresholds and requirement meaning used by this roadmap.
- [x] `docs/reference_standards.md` remains the sole source of workflow authority, evidence rules, and required roadmap markdown structure.
- [x] `docs/plan.md` is translated into `RM-...` items without redefining `PLAN-...` intent or introducing alternate gate logic.
- [x] `AGENTS.md` is reflected as repository-local execution guidance only and is not used as the deciding documentary-phase evidence path.
- [x] Roadmap-phase evidence paths stay inside the declared documentation scope for plan and roadmap auditing.
- [x] `docs/acceptance_matrix.md` and `docs/traceability_map.md` remain subordinate operationalization documents rather than replacement authority sources.
