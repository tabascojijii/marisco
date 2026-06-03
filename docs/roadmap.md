# Roadmap — Handler Template Workstream

**Phase:** PM  
**Date:** 2026-06-03  
**Governing Authority Sources:** `docs/requirements.md`, `docs/reference_standards.md`  
**Plan Source:** `docs/plan.md`  
**Consulted Local Guidance:** `AGENTS.md`

## Purpose

This roadmap translates `docs/plan.md` into executable PM-phase work for the handler-template workstream without changing the governing meaning owned by `docs/requirements.md` and `docs/reference_standards.md`.

This roadmap is subordinate to the governing two-document contract. It sequences execution, names documentary evidence paths, and defines self-checks, but it does not introduce an alternate gate algorithm, new authority source, or replacement decision vocabulary.

## Execution Rules

- The roadmap must keep roadmap-phase documentary evidence inside the declared documentation scope.
- `AGENTS.md` is consulted guidance for authoring discipline and notebook-first behavior only; it is not a co-equal authority source and it is not a required evidence source for contract closure.
- Supporting-governance updates may be executed in the same change set, but their completion does not redefine the governing authority boundary.
- No roadmap item requires git commit operations.

## Roadmap Items

### RM-001 — Preserve Governing Contract Boundaries In Execution

Required outcomes:

- execution remains governed by `docs/requirements.md` and `docs/reference_standards.md`
- project-specific acceptance granularity for this workstream remains defined by `docs/requirements.md`, and roadmap execution does not relocate that granularity into roadmap prose, supporting-governance documents, or hook implementation
- roadmap execution assumes the governing two-document contract is already complete enough for scoped auditing and does not paper over contradictory, undefined, or missing requirement boundaries with local roadmap inference
- repository-wide audit-depth rules, abstract-term handling, and documentary-phase semantic-exactness rules remain owned by `docs/reference_standards.md`
- the machine-readable audit-status contract for requirements-, plan-, and roadmap-phase auditing remains decidable from `docs/requirements.md` and `docs/reference_standards.md` alone
- no supporting-governance document, roadmap note, or consulted repository-local guidance becomes an extra authority source for deciding documentary-phase contract validity or audit-status semantics
- `docs/roadmap.md` does not become the sole source of acceptance detail needed for roadmap-phase auditing
- roadmap-phase documentary evidence paths stay inside `docs/requirements.md`, `docs/reference_standards.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/acceptance_matrix.md`, and `docs/traceability_map.md` as applicable
- supporting-governance documents remain subordinate operationalization surfaces and do not add new authority, new gate prerequisites, or replacement decision logic
- supporting-governance alignment may be executed in the same change set, but roadmap-phase gate validity does not depend on proving supporting-document completion first unless those documents are explicitly inside the active fixed audit scope
- roadmap execution is judged against the current in-scope governing documents and current `docs/plan.md`, not against hypothetical future rewrites
- `docs/plan.md` remains subordinate to requirement thresholds and this roadmap does not reinterpret those thresholds

### RM-002 — Align Supporting Governance Documents To Exact Downstream Outcomes

Required outcomes:

- `docs/traceability_map.md` traces every normative `REQ-...` identifier to `PLAN-...` and `RM-...` items whose text directly states the mapped outcome
- `docs/traceability_map.md` keeps roadmap-phase evidence paths inside the fixed documentation scope
- `docs/traceability_map.md` does not rely on milestone summaries, neighboring prose, or cross-item inference to make a mapping appear valid
- `docs/traceability_map.md` treats `REQ-AC-...` identifiers as normative and maps them only to roadmap items that state the acceptance outcome itself directly
- `docs/acceptance_matrix.md` contains one row for every normative `REQ-...` identifier currently defined in `docs/requirements.md`
- each `docs/acceptance_matrix.md` row carries its own acceptance layer, criterion, roadmap-phase documentary evidence path, later implementation evidence path or `not applicable`, roadmap threshold, and later implementation threshold or `not applicable`
- any roadmap item cited for matrix or traceability governance states the mapped completeness or directness outcome explicitly in that roadmap item itself
- `docs/acceptance_matrix.md` remains a subordinate operationalization surface rather than a replacement authority source
- neither supporting-governance document introduces a new gate prerequisite, new authority source, or substitute decision vocabulary

### RM-003 — Deliver The Explicit Notebook Template Baseline

Required outcomes:

- an explicit handler template notebook exists under `nbs/handlers/`
- the template follows repository `nbdev` conventions, including `default_exp` and exported cells where appropriate
- the template preserves the Handler Template Baseline in the required order: title and purpose, configuration and input source notes, `load_data`, transformation pipeline, metadata construction via `get_attrs` or equivalent metadata section, `encode`, verification or smoke-check cells, and notes marking provider-specific logic, reusable logic, and known pain points
- the template is current-state descriptive rather than future-state prescriptive
- the template is designed to export through the current `nbdev` flow and to remain importable after generation
- the template avoids introducing a broken `default_exp`, invalid export cell, or circular import by default

### RM-004 — Mark Variation Zones Without Forcing Refactor

Required outcomes:

- the template clearly distinguishes provider-specific logic, reusable callback-based logic, and likely future commonization candidates
- each section that varies by provider is explicitly marked as provider-specific rather than as a mandatory refactoring target
- the template preserves the project’s need to absorb imperfect external data
- the template does not imply that all provider differences must be normalized away immediately
- commonization discussion remains enabled without requiring immediate migration of existing handlers into a shared pipeline

### RM-005 — Preserve Notebook-First Readability And Non-Refactor Guardrails

Required outcomes:

- template usage guidance explains how maintainers start a new handler notebook from the template
- template usage guidance keeps prose explanation adjacent to code across the baseline sections in literate-programming style
- template usage guidance reinforces notebook-first authoring and forbids generated-file-only behavior changes
- no roadmap step requires immediate refactoring of existing handlers
- no roadmap step treats generated `.py` files as the canonical authoring surface

### RM-006 — Define The Hook-Governed Lightweight Verification Sequence

Required outcomes:

- the documented post-commit verification flow for this workstream is the sequence invoked by `.git/hooks/post-commit`
- the documented minimum sequence contains notebook export or equivalent regeneration, `python -m py_compile` on touched generated modules or relevant generated module set, and lightweight import smoke checks for affected modules
- the documented post-commit path is limited to those lightweight stages and excludes full provider dataset downloads, remote API calls, full NetCDF production runs, and full regression suites
- the documented post-commit path remains practical for normal development by staying limited to the lightweight stages above
- the documented verification design states failure-stage coverage directly: export or regeneration catches broken notebook export structure, `python -m py_compile` catches syntax errors in generated modules, and import smoke checks catch obvious import-time breakage in touched code paths
- the documented verification flow remains hook-governed even when helper scripts are used as subordinate implementation details

### RM-007 — Preserve Python Baseline Compatibility

Required outcomes:

- any verification step or supporting code introduced by this workstream targets Python `>=3.7`
- roadmap execution does not assume a stricter Python baseline unless that baseline is changed by an upstream authority document

## Execution Sequence

### Phase 1 — Governance Alignment

1. confirm the roadmap text stays subordinate to `docs/requirements.md` and `docs/reference_standards.md`
2. align `docs/traceability_map.md` so every `REQ-...` trace points only to `PLAN-...` and `RM-...` items that directly state the mapped outcome
3. confirm supporting-governance evidence paths remain inside the documentation scope used for roadmap-phase auditing

### Phase 2 — Template Delivery Definition

1. define the explicit template deliverable under `nbs/handlers/`
2. capture the ordered Handler Template Baseline in roadmap terms
3. capture `nbdev` exportability and importability expectations in roadmap terms

### Phase 3 — Authoring And Variation Guidance

1. define how the template marks provider-specific, reusable, and future-commonization zones
2. define notebook-first authoring guidance and literate readability expectations
3. confirm that no step requires immediate refactoring of existing handlers

### Phase 4 — Verification Definition

1. define the hook-governed post-commit sequence
2. define the lightweight boundary and explicit exclusions
3. define failure-stage coverage and Python compatibility expectations

## Evidence Paths

| Roadmap Item | Roadmap-Phase Evidence Path |
|---|---|
| RM-001 | `docs/requirements.md`, `docs/reference_standards.md`, `docs/plan.md`, `docs/roadmap.md` |
| RM-002 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/traceability_map.md` |
| RM-003 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md` |
| RM-004 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md` |
| RM-005 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md` |
| RM-006 | `docs/requirements.md`, `docs/reference_standards.md`, `docs/plan.md`, `docs/roadmap.md` |
| RM-007 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md` |

## Self-Check (Required)

- [x] `docs/roadmap.md` is explicitly aligned with `docs/requirements.md`, `docs/reference_standards.md`, and `docs/plan.md`, and it does not tighten, relax, or replace the governing thresholds or meanings they define.
- [x] `docs/roadmap.md` treats `docs/requirements.md` and `docs/reference_standards.md` as the governing authority sources and does not promote `AGENTS.md` into co-equal authority.
- [x] Every `RM-...` item states its mapped outcome directly enough to support semantic-exact traceability from `docs/traceability_map.md`.
- [x] The roadmap remains aligned with `docs/plan.md` plan intent and does not tighten, relax, or replace requirement thresholds.
- [x] The roadmap keeps roadmap-phase documentary evidence inside the declared documentation scope.
- [x] The roadmap includes the explicit template deliverable, variation-zone guidance, readability guidance, lightweight post-commit sequence, and Python baseline compatibility required by `docs/requirements.md`.
- [x] The roadmap states that no roadmap step requires git commit operations.

## Non-Goals

- This roadmap does not claim that the template notebook already exists.
- This roadmap does not claim that `.git/hooks/post-commit` is already implemented.
- This roadmap does not require immediate migration of existing handlers into a shared pipeline.
- This roadmap does not authorize generated `.py` files as the canonical behavior-change surface.
- This roadmap does not require git commit operations.
