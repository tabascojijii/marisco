# Roadmap — Handler Template Workstream

**Phase:** PM  
**Date:** 2026-06-04  
**Governing Authority Sources:** `docs/requirements.md`, `docs/reference_standards.md`  
**Plan Source:** `docs/plan.md`  
**Repository-Local Guidance Consulted:** `AGENTS.md`

## Purpose

This roadmap translates `docs/plan.md` into executable PM sequencing for the handler-template workstream without changing requirement meaning, gate semantics, or authority boundaries. `docs/requirements.md` and `docs/reference_standards.md` remain the governing contract. `AGENTS.md` is consulted guidance only.

## Execution Rules

- Keep roadmap-phase evidence inside the fixed documentation scope.
- Keep `docs/acceptance_matrix.md` and `docs/traceability_map.md` subordinate to the governing two-document contract.
- Do not require repository-wide discovery to judge roadmap completeness.
- Do not require git commit operations in this phase.
- Preserve notebook-first execution and treat generated `.py` files as derived artifacts.

## Roadmap Items

### RM-001 — Lock Governance Boundaries Before Delivery Detailing

Required outcomes:

- roadmap text keeps `docs/requirements.md` and `docs/reference_standards.md` as the only governing authority sources for contract validity, gate semantics, and audit-status interpretation
- roadmap text treats `docs/plan.md`, `docs/roadmap.md`, `docs/acceptance_matrix.md`, and `docs/traceability_map.md` as subordinate execution or operationalization surfaces rather than replacement authority
- roadmap text keeps documentary-phase acceptance decidable from the current in-scope governing documents rather than from prospective future rewrites
- roadmap text preserves the rule that supporting-governance alignment may happen in the same change set without becoming prerequisite replacement authority
- roadmap text preserves the rule that roadmap sequencing must not become the sole source of acceptance detail auditors need to judge this workstream
- roadmap text preserves the rule that no roadmap item may rely on topic adjacency or neighboring prose to satisfy a traced requirement

### RM-002 — Align Supporting Governance Documents To Direct-Mapping Rules

Required outcomes:

- `docs/acceptance_matrix.md` remains the operational source for acceptance layer, criterion, documentary evidence path, later implementation evidence path, roadmap threshold, and later implementation threshold for every normative `REQ-...` identifier
- each supporting-governance row or trace entry cited by this workstream must carry its own required fields rather than borrowing missing content from neighboring rows, defaults, or surrounding prose
- `docs/traceability_map.md` traces every normative `REQ-...` identifier to plan and roadmap items whose own text directly states the mapped outcome
- when a traced identifier is a `REQ-AC-...` requirement, the cited roadmap item directly states the acceptance outcome itself rather than only a related deliverable class, location, or preparatory step
- repository-local instruction files such as `AGENTS.md` may be cited only as consulted guidance and must not appear as deciding evidence paths for contract closure

### RM-003 — Deliver The Explicit Handler Template Notebook

Required outcomes:

- an explicit handler template notebook is created under `nbs/handlers/`
- the roadmap keeps the final template filename open until `docs/requirements.md` resolves that open decision, so roadmap and trace text refer generically to a handler template notebook under `nbs/handlers/`
- the template notebook follows repository `nbdev` conventions, including `default_exp` and exported cells where appropriate
- the template notebook preserves the ordered Handler Template Baseline defined in `docs/requirements.md`: title and purpose, configuration and input source notes, `load_data`, transformation pipeline, metadata construction via `get_attrs` or equivalent metadata section, `encode`, verification or smoke-check cells, and notes marking provider-specific logic, reusable logic, and known pain points
- the template notebook is current-state descriptive rather than future-state prescriptive
- satisfying this roadmap item must not depend on direct edits to generated Python files
- the documented outcome for this roadmap item is that the template can participate in the current `nbdev` export flow without introducing a broken `default_exp`, invalid export cell, or circular import by default

### RM-004 — Mark Variation Zones Without Forcing Commonization

Required outcomes:

- the template notebook clearly marks provider-specific logic, reusable callback-oriented logic, and likely future commonization candidates
- every section expected to vary by provider is explicitly marked as provider-specific rather than as a mandatory refactoring target
- roadmap guidance preserves the current need to absorb imperfect external data and does not require immediate normalization of provider differences
- roadmap execution for this phase does not require refactoring existing handlers into a shared pipeline
- commonization notes produced in this phase are discussion inputs only and do not become migration mandates

### RM-005 — Add Author Guidance That Preserves Literate Readability

Required outcomes:

- roadmap deliverables include usage guidance explaining how maintainers start a new handler notebook from the template
- the guidance explains how to keep prose explanation adjacent to code across the baseline sections so the literate-programming style remains readable
- the guidance reinforces notebook-first authoring and forbids generated-file-only behavior changes
- roadmap execution in this phase does not require broad migration of existing handlers to the new template
- the readability guidance is explicit enough to support `REQ-AC-READABILITY` without requiring inference from surrounding roadmap prose

### RM-006 — Define The Hook-Governed Lightweight Verification Path

Required outcomes:

- the documented post-commit verification flow for this workstream is the sequence invoked by `.git/hooks/post-commit`
- any helper script called by the hook is described as a subordinate implementation detail rather than an alternative workflow authority source
- the documented minimum post-commit sequence explicitly contains notebook export or equivalent regeneration, `python -m py_compile` on touched generated modules or the relevant generated module set, and lightweight import smoke checks for affected modules
- the documented post-commit path is explicitly limited to those lightweight stages and explicitly excludes full provider dataset downloads, remote API calls, full NetCDF production runs, and full regression suites
- the documented post-commit path is stated to remain practical for normal development by staying within that lightweight boundary
- the documented verification coverage explicitly states that export or regeneration catches broken notebook export structure, `python -m py_compile` catches syntax errors in generated modules, and import smoke checks catch obvious import-time breakage in touched code paths
- roadmap text preserves the rule that this phase requires a documented sequence, not proof of heavyweight runtime execution

### RM-007 — Preserve Baseline Compatibility And Phase Guardrails

Required outcomes:

- any verification helper or supporting code introduced by this workstream is specified to target Python `>=3.7`
- roadmap execution preserves notebook-first authoring, derived generated files, and minimal-scope edits
- roadmap execution does not add a phase-local PASS or REJECT algorithm beyond the governing contract
- roadmap execution does not require git commit operations

## Execution Sequence

### Phase 1 — Governance Alignment

1. confirm roadmap wording stays subordinate to `docs/requirements.md` and `docs/reference_standards.md`
2. align `docs/traceability_map.md` so every `RM-...` citation points to a roadmap item whose text directly states the mapped outcome
3. leave supporting-governance documents operational and subordinate rather than authority-bearing

### Phase 2 — Template And Guidance Definition

1. define the explicit handler template notebook deliverable under `nbs/handlers/` without pre-deciding the filename
2. define baseline sections, provider-variance markers, reusable zones, and commonization-candidate notes
3. define author guidance that preserves literate readability and notebook-first authoring

### Phase 3 — Verification Definition

1. define the hook-governed post-commit sequence with export or regeneration, compile, and import-smoke stages
2. document heavyweight exclusions and low-friction expectations
3. keep the Python baseline and no-git-operation guardrails explicit

## Deliverable Evidence

- roadmap-phase documentary evidence: `docs/requirements.md`, `docs/reference_standards.md`, `docs/plan.md`, `docs/roadmap.md`, and where scoped, aligned supporting-governance documents
- later implementation evidence for the template deliverable: handler template notebook under `nbs/handlers/` and derived generated module under `marisco/handlers/`
- later implementation evidence for verification deliverables: `.git/hooks/post-commit` and any subordinate helper script or run log that the hook invokes

## Self-Check (Required)

- [x] roadmap text treats `docs/requirements.md` and `docs/reference_standards.md` as the only governing authority sources
- [x] roadmap items restate mapped outcomes directly instead of relying on neighboring prose or milestone summaries
- [x] roadmap preserves alignment with `docs/plan.md` without replacing plan or requirements semantics
- [x] roadmap keeps `docs/acceptance_matrix.md` and `docs/traceability_map.md` subordinate operationalization documents
- [x] roadmap keeps handler-template delivery notebook-first and avoids generated-file-only behavior changes
- [x] roadmap states the full lightweight post-commit sequence and its heavyweight exclusions explicitly
- [x] roadmap preserves the open template-filename decision by referring generically to a handler template notebook under `nbs/handlers/`
- [x] roadmap does not require git commit operations
