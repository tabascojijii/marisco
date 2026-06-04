# Plan — Handler Template Workstream

**Phase:** Architect  
**Date:** 2026-06-04  
**Governing Authority Sources:** `docs/requirements.md`, `docs/reference_standards.md`  
**Repository-Local Instructions Consulted:** `AGENTS.md`  
**Informative Audit Input:** `docs/audit_report.md`

## Purpose

This plan defines the Architect response for the handler-template workstream under the currently active two-document governing contract: `docs/requirements.md` and `docs/reference_standards.md`.

The plan is limited to designing how the workstream will satisfy that contract. It does not create an alternate gate model, it does not depend on prospective upstream rewrites for its own validity, and it does not promote supporting-governance documents or repository-local instruction files into co-equal authority.

This revision assumes and reflects the repair order now made explicit in the governing contract: structural governance defects are closed in `docs/requirements.md` and `docs/reference_standards.md` first, then propagated into this plan and the subordinate supporting-governance documents in the same change set.

This plan is valid evidence only for requirement fragments stated directly in its own text. It does not rely on `docs/traceability_map.md`, `docs/acceptance_matrix.md`, or neighboring plan items to supply missing requirement meaning.

The workstream deliverables remain:

- an explicit handler template notebook under `nbs/handlers/`
- guidance that distinguishes provider-specific structure from reusable structure
- a hook-governed lightweight post-commit verification flow
- artifact-backed implementation audit evidence under `artifacts/acceptance_gate_report.json` for acceptance points whose canonical implementation surfaces live in `nbs/handlers/` or `.git/hooks/post-commit`
- supporting-governance documents that operationalize, but do not replace, the governing contract

## Architectural Response To The Audit

This revision is structured to prevent the defect classes that previously made this workstream hard to audit within a fixed documentation scope:

1. requirement-to-plan mappings cited plan items whose stated outcomes did not actually satisfy the referenced requirements
2. traceability links propagated those mismatches into supporting governance documents
3. supporting-document alignment risked being read as a plan-validity prerequisite instead of same-change-set consistency work

The current scoped audit input in `docs/audit_report.md` records no remaining findings against this repaired contract shape. Accordingly, this plan revision preserves the same authority boundary and same-change-set alignment model rather than introducing new plan-local gate logic or compensating requirements.

The plan responds by:

- consuming the repaired present-tense governing contract from `docs/requirements.md` and `docs/reference_standards.md` first, rather than trying to close contract gaps locally in plan prose
- treating `docs/requirements.md` and `docs/reference_standards.md` as already-authoritative current-state inputs
- keeping Architect-gate decidability inside `docs/requirements.md`, `docs/reference_standards.md`, and `docs/plan.md`
- treating `docs/acceptance_matrix.md` and `docs/traceability_map.md` as required subordinate operationalization documents
- keeping `AGENTS.md` as consulted local guidance only
- treating `docs/audit_report.md` as informative audit input that can point to structural defects but cannot itself close those defects
- expressing support-document alignment as same-change-set consistency work rather than as a plan-validity prerequisite or replacement authority source

## Design Principles

### DP-0 — Repair Order Is Upstream First

When a revision set addresses structural governance defects, the repair sequence is: governing contract first, then plan and roadmap alignment, then supporting-governance alignment. Downstream exactness must inherit repaired upstream semantics rather than substituting for them.

### DP-1 — Governing Authority Stays Upstream

Requirements meaning, authority boundaries, and documentary-phase gate semantics remain owned by `docs/requirements.md` and `docs/reference_standards.md`.

### DP-2 — Plan Validity Is Present-Tense

Architect-phase acceptance must be decidable from the current in-scope governing contract plus this plan. The plan may reference same-revision consistency work elsewhere, but it must not depend on hypothetical future rewrites outside scope.

### DP-3 — Supporting Documents Stay Subordinate

`docs/acceptance_matrix.md` and `docs/traceability_map.md` are required supporting-governance documents. They operationalize and trace the contract; they do not define contract validity or alternate gate logic.

### DP-4 — Template First, Refactor Later

The first deliverable is an explicit current-state handler template. It must describe the existing notebook pattern clearly enough to support later commonization review without forcing immediate refactoring.

### DP-5 — Notebook-First Execution

The canonical implementation surface remains `nbs/`. Generated Python remains derived output.

### DP-6 — Lightweight Verification Boundary

Post-commit verification in this workstream is limited to export or regeneration, compile, and import-smoke validation. Heavyweight runtime and network-dependent execution stays out of scope for this verification path.

### DP-7 — Implementation Auditability Must Stay In Scope

Canonical implementation surfaces may remain notebook-first and hook-governed, but implementation-phase acceptance must still be auditable from the fixed implementation evidence surface. For this workstream, that means later acceptance evidence for notebook and hook outcomes must be recorded through `artifacts/acceptance_gate_report.json` rather than requiring direct audit-scope expansion into `nbs/handlers/` or `.git/hooks/`.

## Plan Items

### PLAN-001 — Define The Notebook Template Target

Specify the architecture of the first explicit handler template notebook.

Required outcomes:

- this workstream produces an explicit handler template notebook under `nbs/handlers/`
- this workstream requires an explicit handler template notebook under `nbs/handlers/`, and because the governing requirements do not name a canonical filename, downstream governance documents must reference that deliverable generically rather than inventing a filename requirement that is absent from `docs/requirements.md`
- the template follows repository `nbdev` conventions
- satisfying this workstream must not depend on direct edits to generated Python files; generated `.py` output remains derived evidence rather than the canonical behavior-change path
- the template preserves the ordered Handler Template Baseline defined in `docs/requirements.md`
- the template is explicitly current-state descriptive rather than future-state prescriptive
- the template guidance explicitly identifies which baseline sections are expected to vary by provider
- the template is designed to export through the current `nbdev` flow and to remain importable after generation
- the notebook structure avoids introducing a broken `default_exp`, invalid export cell, or circular import by default
- the implementation-phase evidence contract for `REQ-AC-TEMPLATE-EXISTS`, `REQ-AC-TEMPLATE-BASELINE`, and `REQ-AC-TEMPLATE-NBDEV` is explicit: `artifacts/acceptance_gate_report.json` must name the canonical notebook target under `nbs/handlers/`, record whether the file exists, record that all baseline sections are present in order, and record the export plus import-smoke outcomes against the derived module targets

### PLAN-002 — Define Variation And Reuse Zones

Specify how the template and its paired guidance distinguish stable structure from provider variance.

Required outcomes:

- provider-specific sections are clearly marked
- reusable callback-oriented sections are clearly marked
- likely commonization candidates are labeled as discussion inputs rather than migration mandates
- guidance explains which sections are expected to vary by provider
- sections that vary by provider are explicitly framed as provider-specific rather than as mandatory refactoring targets
- the template guidance explicitly preserves the current need to absorb imperfect external data
- the template guidance does not imply immediate normalization of provider differences
- the implementation-phase evidence contract for `REQ-AC-TEMPLATE-ZONES` and `REQ-AC-PRESERVE-FLEXIBILITY` is explicit: `artifacts/acceptance_gate_report.json` must name the canonical notebook target and record visible provider-specific, reusable, and commonization-candidate markers, plus record that provider-varying sections are labeled as provider-specific rather than as normalization or refactoring mandates

### PLAN-003 — Define Usage Guidance For Authors

Specify how maintainers are expected to use the template before any broad migration effort starts.

Required outcomes:

- usage guidance explains how to start a new handler notebook from the template
- usage guidance explains how to preserve literate notebook readability
- the template scaffold is specified to keep prose explanation adjacent to code across its baseline sections, without relying on unexplained generated-code patterns
- usage guidance reinforces notebook-first authoring and forbids generated-file-only behavior changes
- usage guidance preserves flexibility for imperfect provider inputs
- the implementation-phase evidence contract for `REQ-AC-READABILITY` is explicit: `artifacts/acceptance_gate_report.json` must name the canonical notebook target and record that prose explanation remains adjacent to code across the baseline sections without unexplained generated-code patterns

### PLAN-004 — Define Hook-Governed Lightweight Verification

Specify the minimum post-commit verification design for this workstream.

Required outcomes:

- `.git/hooks/post-commit` remains the governing orchestration surface
- any helper scripts called by the hook are subordinate implementation details and must not become alternative sources of workflow authority
- project-specific acceptance granularity remains owned by `docs/requirements.md`, and the hook is not treated as the source of that granularity policy
- the documented sequence contains export or regeneration, `python -m py_compile`, and lightweight import smoke checks
- the documented post-commit path remains practical for normal development by staying limited to those lightweight stages and by excluding external-network and full-dataset execution from the post-commit path
- the verification design directly states stage-to-failure coverage: export or regeneration catches broken notebook export structure, `python -m py_compile` catches syntax errors in generated modules, and import smoke checks catch obvious import-time breakage in touched code paths
- the implementation-phase audit surface for hook-governed verification is `artifacts/acceptance_gate_report.json`, which must record the checked canonical hook target and the result of the required lightweight stages
- heavyweight operations excluded by `REQ-POST-COMMIT-LIGHTWEIGHT-BOUNDARY` remain excluded
- the verification design stays compatible with Python `>=3.7`
- this workstream does not require a fabricated `pytest tests/` target when no dedicated `tests/` deliverable is intentionally introduced; if a dedicated `tests/` target is later added, it may supply supplementary evidence rather than replace the required lightweight sequence
- this item directly states the required post-commit verification stages and directly states the excluded heavyweight categories; downstream trace or matrix documents must not be needed to complete that meaning

### PLAN-005 — Operationalize Governance Alignment In Supporting Documents

Align supporting-governance documents to the governing contract and this plan without changing the authority boundary.

Required outcomes:

- the project-specific acceptance granularity defined in `docs/requirements.md` remains the upstream source for this workstream, and requirements-level detail remains complete enough to avoid contradictory or non-auditable documentary-phase acceptance
- repository-wide audit-depth rules, abstract-term handling, and machine-readable documentary-phase audit-contract semantics remain owned by `docs/reference_standards.md`, while `docs/audit_contract.md` remains subordinate
- for requirements-, plan-, and roadmap-phase auditing, the governing machine-readable audit-status contract is decidable from `docs/requirements.md` and `docs/reference_standards.md` alone; supporting-governance documents, roadmap text, and repository-local instruction files do not add required authority to decide that contract
- for requirements-, plan-, and roadmap-phase auditing, every rule needed to decide contract validity, authority boundaries, and allowed audit-status semantics is stated in `docs/requirements.md` and `docs/reference_standards.md`; this plan consumes and preserves that two-document authority boundary rather than supplementing it with phase-local decision logic
- any structural governance defect identified in `docs/audit_report.md` is closed by repaired text in `docs/requirements.md` or `docs/reference_standards.md` before downstream plan, roadmap, matrix, or trace text is used as evidence of closure
- if `docs/plan.md` is cited for a requirement, the cited plan item directly states the mapped requirement fragment in its own text rather than relying on neighboring prose, design-principle sections, or support-document summaries
- if `docs/plan.md` is cited for a `REQ-AC-...` identifier, the cited plan item directly states the acceptance outcome itself rather than only a related deliverable class, target path, prerequisite design constraint, or surrounding narrative
- downstream traces preserve the project-specific granularity and contract-closure semantics already defined in `docs/requirements.md` and `docs/reference_standards.md`
- supporting-governance documents may index, operationalize, and cross-reference evidence, but they must not invent, extend, or forward missing requirement meaning for a cited `PLAN-...` or `RM-...` item
- downstream roadmap items that are cited for governance requirements must restate the mapped governance outcome in their own text rather than relying on generic boundary language or nearby roadmap context
- every normative `REQ-...` identifier currently defined in `docs/requirements.md` is represented in `docs/acceptance_matrix.md`
- for every normative `REQ-...` identifier currently defined in `docs/requirements.md`, `docs/acceptance_matrix.md` states acceptance layer, criterion, roadmap-phase documentary evidence path, later implementation evidence path or `not applicable`, roadmap threshold, and later implementation threshold or `not applicable`
- each acceptance-matrix row carries those required fields in the row text itself and must not rely on section defaults, neighboring rows, or surrounding prose to supply a missing field, evidence path, or threshold
- any later implementation evidence path for the template deliverable keeps the filename open when the governing requirements still mark that filename as an open decision; supporting documents must reference a handler template notebook under `nbs/handlers/` generically unless and until the governing contract resolves the filename
- any later implementation evidence path for acceptance points satisfied by notebook or hook changes outside `src/`, `tests/`, or `artifacts/` must be auditable from `artifacts/acceptance_gate_report.json`, which records the canonical target path and observed result without moving canonical authorship away from `nbs/handlers/` or `.git/hooks/post-commit`
- roadmap text that is cited for `REQ-GRAN-CHECKS` must directly state the full acceptance-matrix completeness obligation rather than only speaking about traceability discipline in general
- `docs/traceability_map.md` traces each normative `REQ-...` identifier from source through plan and roadmap evidence paths
- every requirement-to-plan and requirement-to-roadmap citation in supporting documents points only to items whose stated required outcomes directly satisfy the cited requirement
- every requirement-to-plan and requirement-to-roadmap citation in supporting documents for a `REQ-AC-...` identifier points only to items that directly state the cited acceptance outcome itself rather than only a related deliverable class, target location, prerequisite design constraint, or surrounding narrative
- supporting-document rows and trace links for `REQ-AC-TEMPLATE-BASELINE`, `REQ-AC-TEMPLATE-ZONES`, `REQ-AC-PRESERVE-FLEXIBILITY`, and `REQ-AC-READABILITY` explicitly operationalize the same artifact-backed evidence contract stated in `PLAN-001`, `PLAN-002`, and `PLAN-003`; they must not weaken those thresholds into generic template-exists or smoke-only evidence
- roadmap citations remain subordinate to the governing contract and do not become the sole source of acceptance detail that auditors need in order to judge this workstream
- neither supporting document introduces a new authority source, gate prerequisite, or substitute decision vocabulary
- roadmap-phase documentary evidence paths remain inside the declared documentation scope
- repository-local instruction files such as `AGENTS.md` may be consulted for authoring discipline but must not appear as deciding documentary evidence sources for contract closure in supporting-governance rows or traces
- when `docs/acceptance_matrix.md` and `docs/traceability_map.md` are inside the active fixed audit scope, they are aligned in the same change set to the repaired governing contract and current downstream text, while remaining subordinate operationalization surfaces only

This item is a consistency requirement for the change set, not an alternate Architect-gate algorithm. If a future audit narrows scope so that supporting documents are out of scope, plan validity still remains decidable from the governing contract plus this plan.

### PLAN-006 — Preserve Workstream Guardrails

Carry the workstream boundaries intact into downstream planning and implementation.

Required outcomes:

- any downstream requirement-to-plan citation must point only to a `PLAN-...` item whose own required outcomes explicitly state the mapped requirement outcome; plan mappings must not rely on nearby topic overlap, neighboring plan items, or general plan narrative to appear complete
- when supporting-governance documents are outside the active fixed audit scope, Architect-gate validity remains decidable from `docs/requirements.md`, `docs/reference_standards.md`, and `docs/plan.md` alone; supporting-document alignment may be scheduled in the same change set, but it is not a prerequisite input for deciding plan validity
- the plan remains subordinate to requirement thresholds and does not define an alternate documentary-phase pass/fail algorithm
- Architect-phase validity is judged from the current in-scope governing documents and this plan, not from hypothetical future rewrites proposed elsewhere
- no plan item forces immediate refactoring of existing handlers
- no plan item treats generated `.py` files as the canonical authoring surface
- success remains tied to the actual deliverables instead of to speculative framework redesign
- no plan item requires git commit operations
- this item directly states the required direct-outcome mapping discipline and does not depend on supporting-governance documents to define requirement thresholds or gate semantics

## Deliverable Architecture

### Deliverable Group A — Template Asset

- explicit handler template notebook under `nbs/handlers/`
- baseline sections preserved in required order
- prose-plus-code structure consistent with notebook-first maintenance
- artifact-backed acceptance evidence for notebook existence, ordered baseline-section coverage, and `nbdev` export/import outcomes

### Deliverable Group B — Guidance Asset

- checklist or equivalent usage guidance for authors
- markers for provider-specific, reusable, and future-commonization zones
- notes on known pain points and boundaries
- artifact-backed acceptance evidence for zone visibility and provider-specific flexibility labeling

### Deliverable Group C — Verification Asset

- hook-governed post-commit sequence definition
- export/regeneration, compile, and import-smoke stages
- explicit exclusion of heavyweight runs
- artifact-backed implementation audit record for the required lightweight sequence

### Deliverable Group D — Supporting Governance Assets

- acceptance matrix covering every normative requirement
- traceability map linking each normative requirement to plan, roadmap, and evidence paths
- implementation-evidence mappings that remain auditable from `artifacts/acceptance_gate_report.json` when canonical sources live outside the fixed implementation scope
- same-change-set operationalization of the template-content evidence thresholds for baseline, zone, flexibility, and readability acceptance points

## Requirement-to-Plan Mapping

| Plan Item | Primary Requirements Served |
|---|---|
| PLAN-001 | `REQ-NB-TEMPLATE`, `REQ-CURRENT-STATE-FIDELITY`, `REQ-NBDEV-COMPAT`, `REQ-AC-TEMPLATE-EXISTS`, `REQ-AC-TEMPLATE-BASELINE`, `REQ-AC-TEMPLATE-NBDEV` |
| PLAN-002 | `REQ-DIFFERENCE-VISIBILITY`, `REQ-PRESERVE-FLEXIBILITY`, `REQ-AVOID-PREMATURE-COMMONIZATION`, `REQ-AC-TEMPLATE-ZONES`, `REQ-AC-PRESERVE-FLEXIBILITY` |
| PLAN-003 | `REQ-READABILITY`, `REQ-AC-READABILITY` |
| PLAN-004 | `REQ-GRAN-HOOK`, `REQ-POST-COMMIT-AUTHORITY`, `REQ-POST-COMMIT-SEQUENCE`, `REQ-POST-COMMIT-LIGHTWEIGHT-BOUNDARY`, `REQ-LOW-FRICTION-VALIDATION`, `REQ-PYTHON-BASELINE`, `REQ-CHECK-EXPORT`, `REQ-CHECK-COMPILE`, `REQ-CHECK-COVERAGE`, `REQ-AC-POST-COMMIT-SEQUENCE`, `REQ-AC-POST-COMMIT-BOUNDARY` |
| PLAN-005 | `REQ-GRAN-REQS-SCOPE`, `REQ-GRAN-REQS-COMPLETE`, `REQ-GRAN-STANDARDS`, `REQ-GRAN-PLAN-AC-DIRECT`, `REQ-GRAN-ROADMAP`, `REQ-GRAN-ROADMAP-AC-DIRECT`, `REQ-GRAN-CONTRACT-DECIDABLE`, `REQ-GRAN-CONTRACT-SUBORD`, `REQ-GRAN-SUPPORTING-DOCS-ROLE`, `REQ-DIRECT-STATEMENT`, `REQ-SUPPORTING-DOC-NON-SURROGATE`, `REQ-GRAN-CHECKS`, `REQ-CONTRACT-CLOSURE-AUTHORITY`, `REQ-CONTRACT-CLOSURE-SUPPORT`, `REQ-CONTRACT-CLOSURE-EVIDENCE`, `REQ-CONTRACT-CLOSURE-DOWNSTREAM`, `REQ-CONTRACT-CLOSURE-SUPPORT-SEPARATION`, `REQ-AC-DIRECT-STATEMENT`, `REQ-AC-SUPPORTING-DOC-NON-SURROGATE` |
| PLAN-006 | `REQ-GRAN-PLAN`, `REQ-CONTRACT-CLOSURE-PLAN`, `REQ-CONTRACT-CLOSURE-PRESENT-STATE`, `REQ-AVOID-PREMATURE-COMMONIZATION`, `REQ-AC-NO-REFACTOR` |

## Phase Breakdown

### Phase 0 — Governing Contract Closure

| Step | Action | Plan Item |
|---|---|---|
| G1 | close any structural governance defect in `docs/requirements.md` before relying on downstream mappings | PLAN-005 |
| G2 | close any structural governance defect in `docs/reference_standards.md` before relying on downstream mappings | PLAN-005 |
| G3 | treat `docs/audit_report.md` as informative input only and carry closure into authority-bearing text | PLAN-005 |

### Phase 1 — Template Design

| Step | Action | Plan Item |
|---|---|---|
| A1 | define the notebook template target and required baseline sections | PLAN-001 |
| A2 | define provider-specific, reusable, and commonization-candidate zones | PLAN-002 |
| A3 | define author usage guidance and readability expectations | PLAN-003 |
| A4 | define the artifact-backed notebook-content evidence contract for baseline, zone, flexibility, and readability acceptance points | PLAN-001, PLAN-002, PLAN-003 |

### Phase 2 — Verification Design

| Step | Action | Plan Item |
|---|---|---|
| B1 | define the hook-governed lightweight verification sequence | PLAN-004 |
| B2 | define explicit heavyweight exclusions and compatibility guardrails | PLAN-004 |

### Phase 3 — Supporting Governance Alignment

| Step | Action | Plan Item |
|---|---|---|
| C1 | align `docs/acceptance_matrix.md` to the current normative requirement set | PLAN-005 |
| C2 | align `docs/traceability_map.md` to the current normative requirement set and evidence boundaries | PLAN-005 |
| C3 | confirm no supporting document redefines the authority boundary | PLAN-005 |
| C4 | keep template-content evidence thresholds identical across plan and supporting-governance documents | PLAN-005 |

### Phase 4 — Downstream Guardrails

| Step | Action | Plan Item |
|---|---|---|
| D1 | confirm no step forces immediate migration of existing handlers | PLAN-006 |
| D2 | confirm notebook-first authoring remains intact | PLAN-006 |
| D3 | confirm no step requires git commit operations | PLAN-006 |

## Architect Gate Alignment

This plan does not define an independent Architect-gate algorithm. Architect-phase pass or rejection remains governed by `docs/requirements.md` and `docs/reference_standards.md`, with this plan serving only as the design response within that authority boundary.

## Non-Goals

This plan does not:

- claim that the template notebook already exists
- claim that `.git/hooks/post-commit` is already implemented
- force migration of existing handlers into a shared pipeline during this phase
- authorize direct generated-code edits as the canonical behavior change
- require git commit operations

## Audit Closure Intent

This revision closes the targeted structural risks by:

- repairing governing-contract closure rules upstream before using downstream documents as consistency evidence
- removing semantically invalid requirement-to-plan mappings
- aligning support-document traces to the plan items that actually carry the required outcomes
- keeping support-document completion from becoming a prerequisite for deciding plan validity
- removing prospective upstream rewrites as a prerequisite for deciding plan validity
- keeping the governing authority in `docs/requirements.md` and `docs/reference_standards.md`
- keeping supporting-governance documents required but subordinate
