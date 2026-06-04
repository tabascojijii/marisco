# Roadmap — Handler Template Workstream

**Phase:** PM  
**Date:** 2026-06-04  
**Governing Authority Sources:** `docs/requirements.md`, `docs/reference_standards.md`  
**Repository-Local Instructions Consulted:** `AGENTS.md`  
**Upstream Design Input:** `docs/plan.md`

## Purpose

This roadmap translates `docs/plan.md` into executable PM-phase work for the handler-template workstream without changing requirement meaning, authority boundaries, or acceptance thresholds.

This roadmap remains subordinate to the governing two-document contract formed by `docs/requirements.md` and `docs/reference_standards.md`. It sequences execution and documentary self-check work, but it does not define an independent gate algorithm or replace requirement-level acceptance detail.

## Execution Principles

- Execute against the current in-scope governing contract, not against hypothetical future rewrites.
- Keep the workstream notebook-first and `nbdev`-compatible.
- Keep generated `.py` files as derived output, not the canonical behavior-change surface.
- Keep supporting governance documents aligned in the same change set when they are in active scope, while preserving their subordinate role.
- Do not require git commit operations as part of roadmap completion.

## Roadmap Items

### RM-001 — Preserve Governing Contract Boundaries In Execution

Required execution outcomes:

- project-specific acceptance granularity for this workstream remains defined in `docs/requirements.md` and is not relocated into `docs/roadmap.md`, `docs/acceptance_matrix.md`, `docs/traceability_map.md`, the hook, or repository-local guidance
- roadmap execution does not leave unresolved contradiction-closing or auditability-closing requirement detail to downstream compensation; if the governing two-document contract has a missing boundary that would block scoped auditing, that upstream defect is closed in `docs/requirements.md` and `docs/reference_standards.md` before roadmap or supporting-governance text is used to mirror the repair
- when a revision set repairs a structural governance defect, roadmap execution consumes the repaired present-tense governing contract from `docs/requirements.md` and `docs/reference_standards.md` first rather than compensating for an upstream gap locally in downstream text
- repository-wide audit-depth rules, abstract-term handling, and documentary-phase audit-status semantics remain owned by `docs/reference_standards.md`
- execution work treats `docs/requirements.md` and `docs/reference_standards.md` as the only co-equal authority sources for requirements-, plan-, and roadmap-phase contract validity
- the machine-readable audit-status contract needed for requirements-, plan-, and roadmap-phase decisions remains decidable from `docs/requirements.md` and `docs/reference_standards.md` alone without requiring `docs/audit_contract.md`, `docs/acceptance_matrix.md`, `docs/traceability_map.md`, or roadmap prose as co-equal authority
- `docs/audit_contract.md` may restate or exemplify the audit-status contract, but roadmap execution keeps it subordinate and non-exclusive rather than treating it as a required co-equal authority source
- execution work uses `docs/plan.md` as upstream design input and keeps `docs/roadmap.md` subordinate to that governing contract
- roadmap execution does not make Architect-gate validity depend on supporting-governance completion; Architect-phase contract closure remains decidable from `docs/requirements.md`, `docs/reference_standards.md`, and `docs/plan.md`, while same-change-set support-document alignment remains downstream consistency work only
- roadmap sequencing and self-check text remain execution-facing only and do not become the sole source of acceptance detail that auditors need in order to judge this workstream
- roadmap execution does not introduce a new gate prerequisite, alternate decision algorithm, or substitute decision vocabulary
- roadmap execution keeps documentary-phase evidence paths inside the fixed documentation scope
- repository-local guidance such as `AGENTS.md` may be consulted for authoring discipline but must not become deciding documentary evidence for contract closure
- if supporting-governance documents are in active scope, they are aligned in the same change set for consistency only and do not become replacement authority
- roadmap completion remains decidable from present-tense in-scope documents rather than from speculative future upstream rewrites

### RM-002 — Keep Supporting Governance Documents Complete And Direct

Required execution outcomes:

- `docs/acceptance_matrix.md` represents every normative `REQ-...` identifier defined in `docs/requirements.md`
- for every normative `REQ-...` identifier, `docs/acceptance_matrix.md` states acceptance layer, criterion, roadmap-phase documentary evidence path, later implementation evidence path or `not applicable`, roadmap threshold, and later implementation threshold or `not applicable`
- each `docs/acceptance_matrix.md` row carries those required fields in the row text itself rather than relying on section defaults, neighboring rows, or surrounding prose
- `docs/traceability_map.md` traces each normative `REQ-...` identifier from `docs/requirements.md` through `docs/plan.md` and this roadmap to documentary and later implementation evidence paths
- any requirement-to-plan mapping used by supporting governance documents cites only `PLAN-...` items whose stated outcomes directly satisfy the referenced requirement, and no supporting document replaces a requirement threshold with topic-adjacent plan prose
- every requirement-to-plan and requirement-to-roadmap citation in supporting governance documents points only to `PLAN-...` and `RM-...` items whose stated outcomes directly satisfy the cited requirement
- every citation for a `REQ-AC-...` identifier points only to `PLAN-...` and `RM-...` items that directly state the cited acceptance outcome itself
- supporting-governance text does not use generic governance language, nearby context, or cross-item inference to make an otherwise incomplete mapping appear valid
- supporting-governance documents remain subordinate operationalization surfaces and do not add new authority sources or gate rules

### RM-003 — Deliver The Template Notebook Definition

Required execution outcomes:

- an explicit handler template notebook is delivered under `nbs/handlers/`
- until `docs/requirements.md` resolves the open filename decision, roadmap execution refers to the deliverable generically as a handler template notebook under `nbs/handlers/` rather than pre-deciding a filename
- the template notebook preserves the Handler Template Baseline in the required order: title and purpose, configuration and input source notes, `load_data`, transformation pipeline, metadata construction via `get_attrs` or an equivalently named metadata section, `encode`, verification or smoke-check cells, and notes marking provider-specific logic, reusable logic, and known pain points
- the template follows repository `nbdev` conventions, including `default_exp` and exported cells where appropriate
- satisfying this roadmap item does not depend on direct edits to generated Python files
- the template remains current-state descriptive rather than future-state prescriptive
- later implementation evidence for `REQ-AC-TEMPLATE-EXISTS`, `REQ-AC-TEMPLATE-BASELINE`, and `REQ-AC-TEMPLATE-NBDEV` is recorded in `artifacts/acceptance_gate_report.json`, naming the canonical notebook target under `nbs/handlers/`, confirming notebook existence, confirming ordered baseline coverage, and recording export plus import-smoke outcomes against derived module targets

### RM-004 — Mark Variation Zones And Preserve Flexibility

Required execution outcomes:

- the template clearly marks provider-specific logic, reusable callback-based logic, and likely future commonization candidates
- the template explicitly identifies which baseline sections are expected to vary by provider
- sections that vary by provider are explicitly labeled as provider-specific rather than as required refactoring targets
- the template preserves the current need to absorb imperfect external data and does not imply immediate normalization of all provider differences
- roadmap execution does not force immediate refactoring of existing handlers into a shared pipeline
- commonization markers are recorded as discussion inputs for later work rather than as mandates for the template-creation phase
- later implementation evidence for `REQ-AC-TEMPLATE-ZONES`, `REQ-AC-PRESERVE-FLEXIBILITY`, `REQ-PRESERVE-FLEXIBILITY`, `REQ-DIFFERENCE-VISIBILITY`, `REQ-AVOID-PREMATURE-COMMONIZATION`, and `REQ-AC-NO-REFACTOR` is recorded in `artifacts/acceptance_gate_report.json` against the canonical notebook target

### RM-005 — Provide Author Guidance And Maintain Readability

Required execution outcomes:

- roadmap execution provides guidance for how maintainers start a new handler notebook from the template
- guidance tells maintainers to preserve notebook-first authoring and not make generated-file-only behavior changes
- guidance keeps prose explanation adjacent to code across the template baseline sections so the notebook remains readable as both implementation and documentation
- guidance avoids unexplained generated-code patterns in the template scaffold
- roadmap execution keeps the template understandable to maintainers using the repository’s literate-programming notebook style
- roadmap execution does not require immediate migration of existing handlers
- later implementation evidence for `REQ-READABILITY`, `REQ-AC-READABILITY`, and `REQ-AC-NO-REFACTOR` is recorded in `artifacts/acceptance_gate_report.json` against the canonical notebook target

### RM-006 — Define The Hook-Governed Lightweight Verification Path

Required execution outcomes:

- the governing orchestration surface for post-commit verification is `.git/hooks/post-commit`
- helper scripts called by the hook remain subordinate implementation details and do not become alternative sources of workflow authority
- the documented minimum post-commit verification sequence contains every required stage: notebook export or equivalent regeneration, `python -m py_compile` on touched generated modules or the relevant generated module set, and lightweight import smoke checks for affected modules
- the documented post-commit path remains limited to those lightweight stages and excludes heavyweight execution, including full provider dataset downloads, remote API calls, full NetCDF production runs, and full regression suites
- the documented verification design directly states stage-to-failure coverage: export or regeneration catches broken notebook export structure, `python -m py_compile` catches syntax errors in generated modules, and import smoke checks catch obvious import-time breakage in touched code paths
- the post-commit path remains practical for normal development and does not require external-network or full-dataset execution
- later implementation evidence for `REQ-POST-COMMIT-AUTHORITY`, `REQ-POST-COMMIT-SEQUENCE`, `REQ-POST-COMMIT-LIGHTWEIGHT-BOUNDARY`, `REQ-LOW-FRICTION-VALIDATION`, `REQ-CHECK-EXPORT`, `REQ-CHECK-COMPILE`, `REQ-CHECK-COVERAGE`, `REQ-AC-POST-COMMIT-SEQUENCE`, and `REQ-AC-POST-COMMIT-BOUNDARY` is recorded in `artifacts/acceptance_gate_report.json`, naming the canonical hook target and the result of each required lightweight stage

### RM-007 — Preserve Validation And Compatibility Guardrails

Required execution outcomes:

- any verification helper code or workflow change introduced by this workstream targets Python `>=3.7`
- roadmap execution uses the workstream-specific lightweight validation baseline instead of inventing an unnecessary `pytest tests/` gate when no dedicated `tests/` target is intentionally introduced
- if additional executable implementation artifacts are intentionally introduced later under `src/`, `tests/`, or `artifacts/`, supplementary validation may be added without replacing the required lightweight sequence
- roadmap execution preserves the plan’s guardrail that no step in this phase requires git commit operations

## Execution Sequence

### Phase 1 — Governance Alignment

1. apply `RM-001` so the governing authority boundary and documentary evidence boundary remain explicit
2. apply `RM-002` so supporting-governance documents stay complete, direct, and subordinate

### Phase 2 — Template Definition

1. apply `RM-003` to define the template notebook deliverable and its ordered baseline
2. apply `RM-004` to mark provider-specific and reusable zones without forcing refactor
3. apply `RM-005` to attach maintainer guidance and literate-notebook readability expectations

### Phase 3 — Verification Definition

1. apply `RM-006` to define the hook-governed lightweight verification sequence and its coverage claims
2. apply `RM-007` to keep Python and validation guardrails intact

## Evidence Boundaries

- roadmap-phase documentary evidence remains inside `docs/requirements.md`, `docs/reference_standards.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/acceptance_matrix.md`, and `docs/traceability_map.md` when those supporting-governance documents are in active scope
- repository-local instruction files remain consulted guidance only and are excluded from deciding documentary evidence paths
- later implementation evidence for notebook and hook outcomes outside `src/`, `tests/`, or `artifacts/` remains auditable from `artifacts/acceptance_gate_report.json`, which must name the canonical notebook or hook path being checked

## Non-Goals

- no immediate refactoring of existing handlers into a shared execution framework
- no direct generated `.py`-only behavior changes
- no heavyweight post-commit runtime execution
- no git commit operations

## Self-Check (Required)

- [x] `docs/roadmap.md` treats `docs/requirements.md` and `docs/reference_standards.md` as the only co-equal authority sources and keeps `docs/plan.md` as upstream design input only.
- [x] `RM-001` directly states the contradiction-closing upstream-repair rule, two-document audit-contract decidability rule, `docs/audit_contract.md` subordinate status, Architect-gate decidability boundary, and roadmap-subordination rule that supporting-governance traces cite it for.
- [x] `RM-002` directly states the plan-mapping directness rule and the roadmap-mapping directness rule so supporting-governance citations do not need cross-item inference.
- [x] Template deliverable text stays aligned with `docs/requirements.md` on notebook-first authoring, `nbs/handlers/` placement, ordered baseline sections, and open filename status.
- [x] Post-commit verification text stays aligned with `docs/requirements.md` and `docs/plan.md` on hook governance, required lightweight stages, heavyweight exclusions, and stage-to-failure coverage.
- [x] Supporting-governance alignment remains subordinate to the two-document governing contract and does not redefine authority boundaries.
- [x] Repository-local guidance from `AGENTS.md` is acknowledged as consulted discipline only and is not used as deciding documentary evidence.
