# Reference Standards

## Purpose
- This document is the operational reference standard for the repository workflow driven by `C:\dev\marisco3\marisco_clean\marisco_repo\.git\hooks\post-commit`.
- Architect, PM, Implementer, and Auditor prompts must treat this document as the primary behavioral standard unless `C:\dev\marisco3\marisco_clean\marisco_repo\docs\requirements.md` defines a stricter requirement.
- This document exists to define reviewable, testable workflow rules rather than broad engineering philosophy.

## Authority And Scope
- `C:\dev\marisco3\marisco_clean\marisco_repo\docs\requirements.md` is the source of truth for what must be delivered.
- `C:\dev\marisco3\marisco_clean\marisco_repo\docs\reference_standards.md` is the source of truth for how workflow participants must behave while producing and auditing those deliverables.
- Together, `docs/requirements.md` and `docs/reference_standards.md` form the normative two-document governance set for this workflow.
- For requirements-, plan-, and roadmap-phase auditing, the contract rules defined in this document are the authoritative scoped source.
- For those same phases, no additional document may be treated as a co-equal authority source for contract validity, gate semantics, or audit-status interpretation.
- Documentary-phase judgments must be made from the current contents of the active fixed audit scope, not from prospective upstream rewrites that a downstream document proposes to perform later.
- `docs/audit_contract.md` must not override this document for phases whose fixed audit scope does not include it.
- `docs/acceptance_matrix.md` and `docs/traceability_map.md` are required supporting governance documents. They operationalize and trace the two-document governance set, but they do not become alternate authority sources for deciding whether that governing contract is well-formed.
- Supporting governance documents may be required deliverables and may be audited for consistency, but their presence or alignment must not be used to redefine the governing authority boundary beyond the two-document governance set.
- Supporting-governance alignment may be scheduled or executed in the same revision stream, but unless those documents are explicitly inside the active fixed audit scope they must not become prerequisite proof for passing a documentary-phase gate.
- `docs/plan.md`, `docs/roadmap.md`, `docs/acceptance_matrix.md`, and `docs/traceability_map.md` may summarize readiness, sequencing, or coverage, but such summaries are explanatory only and must not be framed as independent gate criteria or replacement decision logic for documentary phases.
- Repository-local instruction files and companion documents such as `AGENTS.md`, `PROJECT.md`, `ARCHITECTURE.md`, `DEPENDENCIES.md`, and `CONVENTIONS.md` may be consulted for local authoring, runtime, and UX discipline, but consulting them does not make them co-equal authority sources for documentary-phase contract validity, gate semantics, or audit-status interpretation.
- `C:\dev\marisco3\marisco_clean\marisco_repo\CONVENTIONS.md` is the companion source for implementation and UX conventions.
- `C:\dev\marisco3\marisco_clean\marisco_repo\DEPENDENCIES.md` is the companion source for runtime, development, asset, and external-service dependency inventory.
- `C:\dev\marisco3\marisco_clean\marisco_repo\docs\core_philosophy.md` is informative background only and must not be treated as an independent source of audit or acceptance authority.
- `C:\dev\marisco3\marisco_clean\marisco_repo\docs\plan.md` defines the Architect’s implementation plan.
- `C:\dev\marisco3\marisco_clean\marisco_repo\docs\roadmap.md` defines the PM’s executable roadmap.
- `C:\dev\marisco3\marisco_clean\marisco_repo\src\`, `C:\dev\marisco3\marisco_clean\marisco_repo\tests\`, and `C:\dev\marisco3\marisco_clean\marisco_repo\artifacts\` contain the Implementer’s deliverables.
- Generated Python files are derived artifacts when produced by `nbdev`; notebook sources remain the canonical edit surface.

## Workflow State Model
- The nominal forward path is:
  - `[USER]`
  - `AUDIT_PASS_REQUIREMENTS`
  - `[ARCHITECT]`
  - `[AUDIT_PASS_PLAN]`
  - `[PM]`
  - `[AUDIT_PASS_ROADMAP]`
  - `[IMPLEMENT]`
  - `[AUDIT_PASS_IMPLEMENT]`
  - `[DONE]`
- `AUDIT_PASS_REQUIREMENTS` indicates that the requirements-phase audit (invoked after `[USER]`) has passed. It is a prerequisite for launching the Architect role. If the requirements audit does not pass, the result must be `ESCALATION`; there is no rejection-to-role path at this phase.
- The allowed rejection or escalation states are:
  - `REJECT_TO_ARCHITECT`
  - `REJECT_TO_PM`
  - `REJECT_TO_IMPLEMENT`
  - `ESCALATION`
- Requirements-level inconsistencies must not be pushed downstream for local repair; they must escalate.
- If an issue cannot be resolved by the currently active role without changing upstream intent, the decision must move upward rather than sideways.
- `ESCALATION` means automated progression stops and a human or principal review is required before resuming.

## Role Responsibilities

### Architect
- Read `C:\dev\marisco3\marisco_clean\marisco_repo\docs\requirements.md` and this file before revising architecture-facing deliverables.
- Create or revise `C:\dev\marisco3\marisco_clean\marisco_repo\docs\plan.md`.
- Repair structural defects in requirements interpretation, acceptance structure, and workflow design.
- Ensure required supporting governance documents exist when the workflow expects them, while keeping Architect-gate validity decidable from the governing contract and the plan text within the active plan-audit scope.

### PM
- Read `C:\dev\marisco3\marisco_clean\marisco_repo\docs\plan.md`, `C:\dev\marisco3\marisco_clean\marisco_repo\docs\requirements.md`, and this file before revising execution-facing deliverables.
- Create or revise `C:\dev\marisco3\marisco_clean\marisco_repo\docs\roadmap.md`.
- Translate plan-level intent into concrete implementation steps without changing requirements meaning.
- Maintain explicit self-check content in the roadmap.

### Implementer
- Read `C:\dev\marisco3\marisco_clean\marisco_repo\docs\roadmap.md`, `C:\dev\marisco3\marisco_clean\marisco_repo\docs\requirements.md`, and this file before changing code or tests.
- Modify only implementation deliverables unless requirements explicitly permit documentation changes.
- Produce code, tests, and artifacts that satisfy requirement IDs and roadmap intent.
- Prefer notebook sources over generated `.py` files when the repository uses `nbdev` generation.

### Auditor
- Judge only against the declared scope, requirements, artifacts, and this operational standard.
- Record evidence and violations in `C:\dev\marisco3\marisco_clean\marisco_repo\docs\audit_report.md`.
- Emit structured machine-readable audit status in the expected audit status files.
- Avoid speculative reconstruction of evidence; missing evidence is a failure condition, not a prompt to guess.

## Audit Contract
- Audit outputs must use the following top-level keys:
  - `decision`
  - `reason_codes`
  - `owner`
  - `next_gate`
  - `checks`
- `checks` entries must include:
  - `id`
  - `pass`
  - `evidence_path`
  - `metric_value`
  - `threshold`
- Requirement identifiers must use `REQ-...` format.
- Reason codes must use a role-prefixed form such as:
  - `REQ_...`
  - `ARCH_...`
  - `PM_...`
  - `IMPLEMENT_...`
- Evidence must reference concrete files or paths whenever possible.
- PASS decisions must not include failed checks.
- REJECT decisions must include at least one reason code.
- If the audit JSON contract is missing or invalid, the result must be treated as an architectural workflow failure rather than ignored.
- `audit_status.txt` is a human-readable summary of `audit_status.json`. It is a supplementary output and must not be used as the machine-readable contract artifact; `audit_status.json` is the sole basis for automated decision-making.
  - Required fields (fixed order):
    - `DECISION: <decision value>`
    - `DATE: <YYYY-MM-DD>`
    - `PHASE: <phase name>`
    - `REASON_CODES:` followed by each code as a 2-space-indented list item
    - `NEXT_GATE: <next_gate enumeration value only — no descriptive text, no punctuation beyond the token itself>`
  - The `NEXT_GATE` value in `audit_status.txt` must be one of the allowed enumeration values (`FLOW_ADVANCE`, `ARCHITECT_REWORK`, `PM_REWORK`, `IMPLEMENT_REWORK`, `ESCALATION_REVIEW`). Free-text descriptions are prohibited.

## Audit Granularity Policy
- This document defines the repository-local policy for how concrete a requirement or finding must be in order to be auditable.
- Auditors may require requirements-level specificity only when the missing detail would otherwise block a scoped, evidence-backed pass or fail decision.
- Terms such as `current pattern`, `lightweight`, `appropriate`, `existing flow`, or `similar structure` are not auditable by themselves unless the fixed audit scope also contains the governing definition or measurable boundary.
- If a requirement depends on a comparison target, required structure, validation baseline, or implementation boundary, that reference must be named in a scoped document rather than inferred from repository-wide exploration.
- Requirement-to-plan, requirement-to-roadmap, and requirement-to-evidence mappings must be semantically exact. A cited downstream item is valid only when its stated outcomes directly satisfy the referenced requirement; topical adjacency or generic governance language is insufficient.
- Plans and roadmaps may add execution detail, but auditors must not treat them as substitutes for missing requirement-level acceptance criteria.
- Findings should identify the missing contract boundary precisely enough that an upstream document owner can repair it without guessing.

## Granularity Ownership Boundary
- `post-commit` owns workflow sequencing, fixed-scope delivery, and status-token handling.
- `docs/requirements.md` owns project-specific acceptance detail and any workstream-specific exceptions to default validation rules.
- `docs/plan.md` owns design response and document architecture needed to satisfy the requirements.
- `docs/roadmap.md` owns executable task breakdown and self-check sequencing.
- `docs/audit_contract.md` may restate or exemplify the machine-readable audit output structure defined in this document, but does not hold normative authority over it for requirements-, plan-, and roadmap-phase auditing.
- `docs/acceptance_matrix.md` owns acceptance layer (A/B), criterion, roadmap-phase documentary evidence path, later implementation evidence path, roadmap threshold, and later implementation threshold mapping for all normative requirements.
- `docs/traceability_map.md` owns requirement-to-evidence traceability across phases.
- `docs/check_catalog.md` is optional and informative; it does not hold normative authority.
- Required supporting governance documents must remain subordinate to the two-document governance set. If they are incomplete or inconsistent, that is an architectural defect in supporting operationalization, not a transfer of governing authority away from `docs/requirements.md` and this document.
- Downstream planning or support documents must not add phase-local PASS/REJECT algorithms, extra gate prerequisites, or replacement decision vocabularies for requirements-, plan-, or roadmap-phase auditing.

## Decision Rules

### PASS Decisions
- Use a PASS decision only when requirements are met, required evidence exists, and no failed checks remain in scope.
- PASS decisions must align with the current workflow phase.

### Rejection Decisions
- `REJECT_TO_IMPLEMENT` is valid only when the defect is fixable within code, tests, or implementation artifacts without changing upstream intent.
- `REJECT_TO_PM` is valid only when the roadmap or execution breakdown is incomplete, inconsistent, or missing required structure, but the plan remains usable.
- `REJECT_TO_ARCHITECT` is required when the defect originates in design, requirements interpretation, missing governance contract, repeated rejection loops, or invalid audit interface behavior.

### Escalation Decisions
- `ESCALATION` is required when requirements are contradictory, undefined, or not auditable.
- `ESCALATION` is required when automated progression has entered an unresolved loop or cannot safely determine the correct upstream repair point.
- `ESCALATION` pauses automatic workflow progression pending human review.

## Required Documents
- The following documents are required by the governance workflow:
  - `docs/acceptance_matrix.md` — maps each normative requirement to its acceptance layer (A/B), criterion, evidence path, and threshold.
  - `docs/traceability_map.md` — traces each normative requirement from source document through plan and roadmap to evidence.
- Missing required governance documents are not cosmetic issues; they are workflow contract failures.
- The following documents are optional and informative. They must not be treated as normative authority sources:
  - `docs/audit_contract.md` — supplementary restatement of the audit contract defined in this document.
  - `docs/escalation_policy.md` — supplementary summary of escalation rules defined in this document.
  - `docs/check_catalog.md` — optional reference list of operationalized checks.
  - `docs/audit_examples.md` — optional format examples for audit outputs.

## Required Markdown Blocks
- `C:\dev\marisco3\marisco_clean\marisco_repo\docs\roadmap.md` must contain `## Self-Check (Required)`.
- `C:\dev\marisco3\marisco_clean\marisco_repo\docs\audit_report.md` must contain `## Open-Items`.
- `C:\dev\marisco3\marisco_clean\marisco_repo\docs\escalation_report.md` must contain:
  - `## Summary`
  - `## Required Human Actions`

## Runtime Prerequisite Rules
- This repository must not be treated as `pip install`-complete only; successful runtime behavior also depends on local initialization, local assets, and some external services.
- `maris_init` is the standard initialization step for runtime use and must be treated as a prerequisite when workflows depend on `~/.marisco/`.
- Runtime flows that require lookup tables, cache directories, temporary directories, or the NetCDF template must assume those assets are provided through the initialized `~/.marisco/` layout unless requirements explicitly define an alternative.
- Missing runtime prerequisites such as uninitialized local state, absent LUTs, absent NetCDF templates, or unavailable required local input files must be reported explicitly rather than surfacing later as ambiguous downstream failures.
- External dependencies such as GitHub-hosted raw data, Zotero metadata, and handler-specific remote sources must be treated as operational dependencies; availability failures should be described as dependency failures, not generic processing failures.

## Evidence And Artifact Rules
- Evidence should be file-backed whenever possible, not prose-only.
- For requirements-, plan-, and roadmap-phase auditing, required evidence must be satisfiable from the fixed documentation scope. Absent later implementation artifacts are not, by themselves, documentary-phase failures unless an in-scope document incorrectly claims those artifacts already exist.
- For documentary phases, an in-scope plan or roadmap may schedule consistency repairs in supporting governance documents, but auditors must not treat that scheduled repair as a prerequisite proof of pass unless the supporting documents are also part of the fixed audit scope for that phase.
- For those documentary phases, repository-local instruction files such as `AGENTS.md` may guide authoring behavior but must not be required as authority-bearing evidence for whether the governing contract is closed.
- When a supporting governance document traces a requirement through `docs/plan.md` or `docs/roadmap.md`, every cited plan or roadmap item must itself contain the relevant required outcome. Auditors must reject mappings that require semantic guesswork or cross-item inference to become true.
- When downstream documents mention repository-local instruction files, those mentions must be framed as consulted guidance or implementation discipline only. They must not be written as blocking documentary-phase gate conditions, deciding evidence paths, or replacement authority.
- When a phase-specific fixed documentation scope includes supporting governance documents such as `docs/acceptance_matrix.md` or `docs/traceability_map.md`, those documents may be audited for consistency and completeness, but they must still be interpreted as subordinate operationalization of the governing two-document contract rather than as replacement authority.
- The following artifacts are part of the workflow evidence contract:
  - `C:\dev\marisco3\marisco_clean\marisco_repo\artifacts\acceptance_gate_report.json`
  - `C:\dev\marisco3\marisco_clean\marisco_repo\artifacts\md_json_completeness_report.json`
  - `C:\dev\marisco3\marisco_clean\marisco_repo\artifacts\json_schema_validation_report.json`
- When those artifacts exist as a set, their `execution_id` values must agree.
- During implementation-phase auditing, missing required artifacts or mismatched `execution_id` values are contract failures, not soft warnings.

## Validation And Test Baseline
- Implementation-phase auditing must include `pytest tests/` unless the requirements document explicitly defines a different local validation baseline.
- Lightweight validation may be used in earlier documentation-oriented phases, but implementation acceptance requires executable evidence.
- Earlier documentation-oriented phases must be pass/fail decidable from documentary evidence alone; they may require phase-appropriate implementation planning, but not the runtime presence of future deliverables.
- Post-commit verification should prefer fast checks first, with heavier verification delegated to manual execution or CI where appropriate.

## Notebook-First And nbdev Rules
- This repository is notebook-first where `nbdev`-generated modules exist.
- Generated `.py` files with autogenerated headers must not be treated as the canonical authoring surface.
- Template work for handlers must begin as current-state documentation of the existing notebook pattern, not as forced future-state refactoring.
- Future commonization may be discussed, but template creation must not require immediate migration of existing handlers.

## Handler And Shared Logic Boundary
- Handlers are responsible for provider-specific ingestion and normalization.
- Shared logic that is demonstrably reusable should be moved into callbacks, shared helpers, or utility functions rather than copied across handlers.
- Callback pipelines should remain readable and ordered according to transformation flow.
- Provider-specific quirks should remain in the provider notebook until reuse is clear and stable.
- Commonization must reduce duplication without hiding provider-specific meaning behind oversized abstractions.

## CLI And User-Facing Behavior
- Public CLI entrypoints must validate user input before beginning expensive work whenever validation can be done at the CLI boundary.
- User-facing failures at the CLI boundary must exit non-zero and explain what was invalid.
- When valid choices are from a fixed set, those choices should be shown in the error message.
- Long-running operations should announce start, show progress by stage or item when practical, and announce completion.
- Successful runs should identify what was produced and where it was written.
- Cache-aware behavior should be visible to users when it materially affects runtime behavior.
- Overwrite-prone or destructive behavior should require explicit confirmation when it affects user-managed local state.

## Coding And Change Discipline
- Keep changes minimal, reviewable, and traceable to requirement or roadmap intent.
- Fix root causes where practical, but do not widen scope without documented justification.
- Do not silently change workflow contracts, reason-code vocabularies, or audit interfaces.
- Prefer explicit file-based evidence over narrative claims of correctness.

## Failure Communication Rules
- Do not fail silently for invalid input, missing prerequisites, or missing evidence.
- Do not emit low-information user-facing failures such as `Failed`, `Error`, or `not found` without naming the target and impact.
- Warning-style messages are appropriate only for recoverable data-quality issues or partial enrichment failures that do not invalidate the output contract.
- Exception-style failures are appropriate for unsupported states, missing required prerequisites, invalid internal assumptions, or contract-breaking conditions.
- Failure messages should state what failed, which file or dependency was involved, whether processing can continue, and what should be checked next when a next step exists.

## Audit Scope Discipline
- Respect the fixed audit scope supplied by the workflow.
- Inclusion in a fixed audit scope does not, by itself, elevate a file into governing authority.
- Do not rely on repository-wide recursive discovery when a scoped audit has been defined.
- Do not infer missing evidence from nearby files; record the gap explicitly instead.

## Prohibited Actions
- Do not edit generated `.py` artifacts directly when notebook sources are the intended source of truth.
- Do not perform git commit operations from inside the role prompts when the hook explicitly reserves commit control for itself.
- Do not invent requirement IDs, reason codes, or evidence paths that cannot be traced to repository content.
- Do not downgrade requirements-level defects into local implementation fixes merely to keep the workflow moving.

## Escalation Principles
- Escalation is a safety mechanism, not a failure of collaboration.
- Repeated rejection loops with the same root cause should be promoted upward rather than retried indefinitely.
- When evidence is structurally missing, the workflow should stop clearly rather than continue ambiguously.
