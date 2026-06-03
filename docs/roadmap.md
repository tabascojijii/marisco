# Roadmap

**Phase:** PM
**Date:** 2026-06-03
**Authority Sources:** `AGENTS.md`, `docs/requirements.md`, `docs/plan.md`, `docs/reference_standards.md`

## Purpose

This roadmap translates `docs/plan.md` into executable PM work items for the handler template workstream. It is subordinate to `docs/requirements.md` for acceptance thresholds and to `docs/reference_standards.md` for workflow behavior. It also applies the repository-local editing and notebook-first rules in `AGENTS.md`.

## Execution Constraints

- Treat `nbs/` as the primary implementation surface and treat generated `marisco/` modules as derived artifacts.
- Keep changes minimal and targeted to this workstream.
- Do not force refactoring of existing handler notebooks during template creation.
- Keep the post-commit flow lightweight: export, compile, and import-smoke only.
- Preserve CLI-first and explicit user-facing behavior rules if implementation later touches CLI surfaces.

## Roadmap-Phase Audit Boundary

- For roadmap-phase auditing, pass/fail must be decidable from the fixed documentation scope only: `AGENTS.md`, `docs/requirements.md`, `docs/plan.md`, `docs/reference_standards.md`, `docs/roadmap.md`, `docs/acceptance_matrix.md`, and `docs/traceability_map.md`.
- Implementation artifacts such as `nbs/handlers/handler_template.ipynb`, generated `.py`, `.git/hooks/post-commit`, `artifacts/*.json`, and any hook run log are future deliverable evidence for later phases and must not be required to decide roadmap-phase acceptance.
- This roadmap therefore separates:
  - roadmap-phase documentary evidence that proves sequencing, ownership, and standards alignment now
  - implementation-phase file evidence that proves deliverables exist later
- If a requirement cannot be traced to documentary evidence during roadmap audit, the repair target is the governance docs, not inferred implementation state.

## Roadmap Items

### RM-001 — Confirm Governance Inputs

Verify that `docs/requirements.md`, `docs/plan.md`, and `docs/reference_standards.md` remain mutually consistent before implementation begins. Confirm that the PM roadmap does not introduce new acceptance thresholds, new workflow states, or alternate evidence paths that conflict with the governing documents.

Maps to: `PLAN-007`
Roadmap-phase evidence: `docs/roadmap.md`, `docs/requirements.md`, `docs/plan.md`, `docs/reference_standards.md`

### RM-002 — Publish Traceability-Ready Roadmap

Create a roadmap structure that gives each implementation area an executable task owner, ordered step sequence, and explicit evidence destination. Ensure the roadmap contains the required self-check block and is specific enough for `docs/traceability_map.md` to reference concrete roadmap items.

Maps to: `PLAN-007`
Roadmap-phase evidence: `docs/roadmap.md`, `docs/traceability_map.md`

### RM-003 — Build The Template Notebook Skeleton

Implement the new handler template notebook at `nbs/handlers/handler_template.ipynb` using the 8 ordered baseline sections from `docs/requirements.md`. Include `default_exp`, correct `#| export` use where appropriate, and notes that the template is current-state descriptive rather than future-state prescriptive.

Maps to: `PLAN-001`
Roadmap-phase evidence: `docs/roadmap.md`, `docs/requirements.md`, `docs/plan.md`, `docs/traceability_map.md`
Later implementation evidence: `nbs/handlers/handler_template.ipynb`, generated `.py`

### RM-004 — Mark Variation And Reuse Zones

Annotate the template so reviewers can distinguish provider-specific logic, reusable callback-based logic, and likely future commonization candidates. Keep these labels descriptive only; they must not imply mandatory normalization or immediate migration.

Maps to: `PLAN-002`, `PLAN-008`
Roadmap-phase evidence: `docs/roadmap.md`, `docs/requirements.md`, `docs/traceability_map.md`
Later implementation evidence: `nbs/handlers/handler_template.ipynb`

### RM-005 — Preserve Literate Notebook Readability

Add adjacent prose to every baseline section so the notebook remains understandable as both implementation scaffold and documentation. Use the HELCOM notebook only as a read-only calibration reference and note any structural divergence in the template notes rather than rewriting existing handlers.

Maps to: `PLAN-003`, `PLAN-001`, `PLAN-008`
Roadmap-phase evidence: `docs/roadmap.md`, `docs/plan.md`, `docs/traceability_map.md`
Later implementation evidence: `nbs/handlers/handler_template.ipynb`

### RM-006 — Deliver Hook-Governed Lightweight Verification

Implement `.git/hooks/post-commit` as the single workflow authority for this workstream's post-commit checks. The hook must run notebook export, `python -m py_compile`, and lightweight import smoke checks, and it must exclude dataset downloads, remote API calls, full NetCDF runs, and regression suites.

Maps to: `PLAN-004`
Roadmap-phase evidence: `docs/roadmap.md`, `docs/requirements.md`, `docs/plan.md`, `docs/traceability_map.md`
Later implementation evidence: `.git/hooks/post-commit`

### RM-007 — Emit Required JSON Evidence Artifacts

Make the post-commit flow generate the three required JSON artifacts under `artifacts/` with one shared `execution_id` per hook invocation. Artifact generation is part of the deliverable, not an optional add-on.

Maps to: `PLAN-005`
Roadmap-phase evidence: `docs/roadmap.md`, `docs/plan.md`, `docs/reference_standards.md`, `docs/traceability_map.md`
Later implementation evidence: `artifacts/acceptance_gate_report.json`, `artifacts/md_json_completeness_report.json`, `artifacts/json_schema_validation_report.json`

### RM-008 — Enforce Python Baseline And Validation Order

Keep any new notebook-exported code and hook-supporting code compatible with Python `>=3.7`. Validate the smallest affected surface first, then run lightweight static or CLI-adjacent checks before any broader verification, consistent with `AGENTS.md`.

Maps to: `PLAN-006`
Roadmap-phase evidence: `docs/roadmap.md`, `AGENTS.md`, `docs/requirements.md`, `docs/traceability_map.md`
Later implementation evidence: `nbs/handlers/handler_template.ipynb`, `.git/hooks/post-commit`

## Milestones

### Milestone 1 — PM Governance Completion

1. Finalize this roadmap with executable roadmap items.
2. Update `docs/traceability_map.md` so every in-scope requirement points to one or more roadmap items.
3. Re-check that the roadmap stays subordinate to requirements, plan, and reference standards.

### Milestone 2 — Template Notebook Delivery

1. Create `nbs/handlers/handler_template.ipynb`.
2. Add all 8 baseline sections in the required order.
3. Add zone annotations and literate prose.
4. Keep existing handler notebooks unchanged.

### Milestone 3 — Post-Commit Verification Delivery

1. Create or revise `.git/hooks/post-commit`.
2. Implement export, compile, and import-smoke stages.
3. Generate the required JSON evidence artifacts with a shared `execution_id`.
4. Confirm the hook remains within the lightweight boundary.

### Milestone 4 — Acceptance Readiness

1. Confirm the template notebook is the file-backed evidence for template requirements.
2. Confirm the hook and generated artifacts are the file-backed evidence for verification requirements.
3. Confirm no roadmap step requires direct edits to autogenerated `.py` files as the only source of truth.

## Implementation Sequence

1. Complete RM-001 and RM-002 before implementation starts.
2. Execute RM-003, RM-004, and RM-005 together while building the notebook template.
3. Execute RM-006 and RM-007 together while building the hook-governed validation flow.
4. Execute RM-008 during both notebook and hook work, not as an afterthought.
5. Finish by checking evidence paths against `docs/traceability_map.md` and `docs/acceptance_matrix.md`.

## Evidence Expectations

| Roadmap Item | Roadmap-Phase Documentary Evidence | Later Implementation Evidence |
|---|---|---|
| RM-001 | `docs/roadmap.md`, `docs/requirements.md`, `docs/plan.md`, `docs/reference_standards.md` | not applicable |
| RM-002 | `docs/roadmap.md`, `docs/traceability_map.md` | not applicable |
| RM-003 | `docs/roadmap.md`, `docs/requirements.md`, `docs/plan.md`, `docs/traceability_map.md` | `nbs/handlers/handler_template.ipynb`, generated `.py` |
| RM-004 | `docs/roadmap.md`, `docs/requirements.md`, `docs/traceability_map.md` | `nbs/handlers/handler_template.ipynb` |
| RM-005 | `docs/roadmap.md`, `docs/plan.md`, `docs/traceability_map.md` | `nbs/handlers/handler_template.ipynb` |
| RM-006 | `docs/roadmap.md`, `docs/requirements.md`, `docs/plan.md`, `docs/traceability_map.md` | `.git/hooks/post-commit` |
| RM-007 | `docs/roadmap.md`, `docs/plan.md`, `docs/reference_standards.md`, `docs/traceability_map.md` | `artifacts/acceptance_gate_report.json`, `artifacts/md_json_completeness_report.json`, `artifacts/json_schema_validation_report.json` |
| RM-008 | `docs/roadmap.md`, `AGENTS.md`, `docs/requirements.md`, `docs/traceability_map.md` | `nbs/handlers/handler_template.ipynb`, `.git/hooks/post-commit` |

## Risks And Controls

- Risk: The roadmap drifts into new acceptance criteria.
  Control: RM-001 requires a direct consistency pass against `docs/requirements.md` and `docs/reference_standards.md`.
- Risk: The template becomes future-state architecture instead of current-state scaffolding.
  Control: RM-003 and RM-005 keep the baseline anchored to `docs/requirements.md` and the HELCOM read-only calibration reference.
- Risk: The hook becomes too heavy for normal development.
  Control: RM-006 constrains the sequence to the three required lightweight stages plus artifact emission.
- Risk: Traceability remains incomplete at the roadmap phase.
  Control: RM-002 requires explicit roadmap-item coverage in `docs/traceability_map.md`.

## Granularity Boundary

- This roadmap sequences work derived from `docs/requirements.md` and `docs/plan.md`.
- This roadmap may add execution order, task grouping, ownership, and self-check reminders.
- This roadmap must not introduce new acceptance thresholds or become the only source of detail needed for audit decisions.
- If a milestone reveals a missing contract boundary, the defect must be repaired upstream in `docs/requirements.md` or `docs/reference_standards.md`, not hidden in roadmap prose.

## Self-Check (Required)

- [x] `docs/requirements.md` remains the sole source of acceptance thresholds used by this roadmap.
- [x] `docs/plan.md` roadmap mappings use existing `PLAN-xxx` items only and do not redefine plan intent.
- [x] `docs/reference_standards.md` workflow authority, required markdown block, and evidence rules are reflected here.
- [x] Roadmap-phase acceptance is documented as decidable from the fixed documentation scope without requiring implementation artifacts.
- [x] `AGENTS.md` notebook-first, minimal-diff, and generated-artifact discipline are reflected here.
- [x] `docs/traceability_map.md` is updated so roadmap-phase traceability is not left as `TBD` where this roadmap defines the mapping.
