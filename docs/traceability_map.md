# Traceability Map

Authority: `docs/requirements.md` is the normative source for all `REQ-...` identifiers listed here. This document traces those requirements through `docs/plan.md` and `docs/roadmap.md` while remaining subordinate to the governing two-document contract formed by `docs/requirements.md` and `docs/reference_standards.md`.
The roadmap-phase evidence paths listed below are the deciding documentary paths for traceability. Consulted repository-local guidance is intentionally not used here as contract-closing authority.

| Requirement ID | Source | Plan Item | Roadmap Item | Roadmap-Phase Evidence Path | Later Implementation Evidence Path |
|---|---|---|---|---|---|
| REQ-GRAN-REQS-SCOPE | `docs/requirements.md` § Granularity Allocation | PLAN-001 | RM-001 | `docs/requirements.md`, `docs/reference_standards.md`, `docs/plan.md` | not applicable |
| REQ-GRAN-REQS-COMPLETE | `docs/requirements.md` § Granularity Allocation | PLAN-001 | RM-001 | `docs/requirements.md`, `docs/reference_standards.md` | not applicable |
| REQ-GRAN-HOOK | `docs/requirements.md` § Granularity Allocation | PLAN-004 | RM-006 | `docs/requirements.md`, `docs/reference_standards.md`, `docs/plan.md`, `docs/roadmap.md` | `.git/hooks/post-commit` |
| REQ-GRAN-STANDARDS | `docs/requirements.md` § Granularity Allocation | PLAN-001 | RM-001 | `docs/reference_standards.md` | not applicable |
| REQ-GRAN-PLAN | `docs/requirements.md` § Granularity Allocation | PLAN-006 | RM-001 | `docs/requirements.md`, `docs/plan.md` | not applicable |
| REQ-GRAN-ROADMAP | `docs/requirements.md` § Granularity Allocation | PLAN-005 | RM-002 | `docs/requirements.md`, `docs/roadmap.md`, `docs/traceability_map.md` | not applicable |
| REQ-GRAN-CONTRACT-DECIDABLE | `docs/requirements.md` § Granularity Allocation | PLAN-001 | RM-001 | `docs/requirements.md`, `docs/reference_standards.md` | `audit_status.json`, `audit_status.txt` |
| REQ-GRAN-CONTRACT-SUBORD | `docs/requirements.md` § Granularity Allocation | PLAN-001 | RM-001 | `docs/requirements.md`, `docs/reference_standards.md` | not applicable |
| REQ-GRAN-SUPPORTING-DOCS-ROLE | `docs/requirements.md` § Granularity Allocation | PLAN-001, PLAN-005 | RM-001, RM-002 | `docs/requirements.md`, `docs/reference_standards.md`, `docs/plan.md`, `docs/acceptance_matrix.md`, `docs/traceability_map.md` | not applicable |
| REQ-GRAN-CHECKS | `docs/requirements.md` § Granularity Allocation | PLAN-005 | RM-002 | `docs/acceptance_matrix.md`, `docs/traceability_map.md` | not applicable |
| REQ-CONTRACT-CLOSURE-AUTHORITY | `docs/requirements.md` § Governing Contract Closure Rules | PLAN-001 | RM-001 | `docs/requirements.md`, `docs/reference_standards.md` | `audit_status.json`, `audit_status.txt` |
| REQ-CONTRACT-CLOSURE-SUPPORT | `docs/requirements.md` § Governing Contract Closure Rules | PLAN-005 | RM-002 | `docs/requirements.md`, `docs/reference_standards.md`, `docs/acceptance_matrix.md`, `docs/traceability_map.md` | not applicable |
| REQ-CONTRACT-CLOSURE-EVIDENCE | `docs/requirements.md` § Governing Contract Closure Rules | PLAN-005 | RM-002 | `docs/requirements.md`, `docs/reference_standards.md`, `docs/acceptance_matrix.md`, `docs/traceability_map.md` | not applicable |
| REQ-CONTRACT-CLOSURE-PLAN | `docs/requirements.md` § Governing Contract Closure Rules | PLAN-001, PLAN-005 | RM-001, RM-002 | `docs/requirements.md`, `docs/reference_standards.md`, `docs/plan.md` | not applicable |
| REQ-CONTRACT-CLOSURE-DOWNSTREAM | `docs/requirements.md` § Governing Contract Closure Rules | PLAN-001, PLAN-005 | RM-001, RM-002 | `docs/requirements.md`, `docs/reference_standards.md`, `docs/plan.md`, `docs/acceptance_matrix.md`, `docs/traceability_map.md` | not applicable |
| REQ-NB-TEMPLATE | `docs/requirements.md` § Functional Requirements | PLAN-002 | RM-003 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md` | `nbs/handlers/handler_template.ipynb`, generated module under `marisco/handlers/` |
| REQ-CURRENT-STATE-FIDELITY | `docs/requirements.md` § Functional Requirements | PLAN-002 | RM-003 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md` | `nbs/handlers/handler_template.ipynb` |
| REQ-DIFFERENCE-VISIBILITY | `docs/requirements.md` § Functional Requirements | PLAN-003 | RM-004 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md` | `nbs/handlers/handler_template.ipynb` |
| REQ-NBDEV-COMPAT | `docs/requirements.md` § Functional Requirements | PLAN-002 | RM-003, RM-008 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md` | `nbs/handlers/handler_template.ipynb`, generated module under `marisco/handlers/` |
| REQ-POST-COMMIT-AUTHORITY | `docs/requirements.md` § Functional Requirements | PLAN-004 | RM-006 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md` | `.git/hooks/post-commit` |
| REQ-POST-COMMIT-SEQUENCE | `docs/requirements.md` § Functional Requirements | PLAN-004 | RM-006 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md` | `.git/hooks/post-commit`, hook run log |
| REQ-POST-COMMIT-LIGHTWEIGHT-BOUNDARY | `docs/requirements.md` § Functional Requirements | PLAN-004 | RM-006 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md` | `.git/hooks/post-commit`, hook run log |
| REQ-PRESERVE-FLEXIBILITY | `docs/requirements.md` § Non-Functional Requirements | PLAN-003 | RM-004 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md` | `nbs/handlers/handler_template.ipynb` |
| REQ-AVOID-PREMATURE-COMMONIZATION | `docs/requirements.md` § Non-Functional Requirements | PLAN-003, PLAN-006 | RM-004, RM-005 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md` | `nbs/handlers/` |
| REQ-READABILITY | `docs/requirements.md` § Non-Functional Requirements | PLAN-003 | RM-005 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md` | `nbs/handlers/handler_template.ipynb` |
| REQ-LOW-FRICTION-VALIDATION | `docs/requirements.md` § Non-Functional Requirements | PLAN-004 | RM-006, RM-008 | `docs/requirements.md`, `docs/reference_standards.md`, `docs/plan.md`, `docs/roadmap.md` | `.git/hooks/post-commit`, hook run log |
| REQ-PYTHON-BASELINE | `docs/requirements.md` § Constraints | PLAN-006 | RM-008 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md` | `nbs/handlers/handler_template.ipynb`, `.git/hooks/post-commit` |
| REQ-CHECK-EXPORT | `docs/requirements.md` § Required Checks | PLAN-004 | RM-006 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md` | `.git/hooks/post-commit`, hook run log |
| REQ-CHECK-COMPILE | `docs/requirements.md` § Required Checks | PLAN-004 | RM-006 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md` | generated module under `marisco/handlers/`, hook run log |
| REQ-CHECK-COVERAGE | `docs/requirements.md` § Required Checks | PLAN-004 | RM-006 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/reference_standards.md` | hook run log, `artifacts/acceptance_gate_report.json`, `artifacts/md_json_completeness_report.json`, `artifacts/json_schema_validation_report.json` |
| REQ-AC-TEMPLATE-EXISTS | `docs/requirements.md` § Acceptance Criteria | PLAN-002 | RM-003 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/acceptance_matrix.md` | `nbs/handlers/handler_template.ipynb` |
| REQ-AC-TEMPLATE-BASELINE | `docs/requirements.md` § Acceptance Criteria | PLAN-002 | RM-003, RM-005 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/acceptance_matrix.md` | `nbs/handlers/handler_template.ipynb` |
| REQ-AC-TEMPLATE-ZONES | `docs/requirements.md` § Acceptance Criteria | PLAN-003 | RM-004 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/acceptance_matrix.md` | `nbs/handlers/handler_template.ipynb` |
| REQ-AC-TEMPLATE-NBDEV | `docs/requirements.md` § Acceptance Criteria | PLAN-002 | RM-003, RM-008 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/acceptance_matrix.md` | `nbs/handlers/handler_template.ipynb`, generated module under `marisco/handlers/` |
| REQ-AC-POST-COMMIT-SEQUENCE | `docs/requirements.md` § Acceptance Criteria | PLAN-004 | RM-006 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/acceptance_matrix.md` | `.git/hooks/post-commit`, hook run log |
| REQ-AC-POST-COMMIT-BOUNDARY | `docs/requirements.md` § Acceptance Criteria | PLAN-004 | RM-006 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/acceptance_matrix.md` | `.git/hooks/post-commit`, hook run log |
| REQ-AC-NO-REFACTOR | `docs/requirements.md` § Acceptance Criteria | PLAN-006 | RM-004, RM-005 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/acceptance_matrix.md` | `nbs/handlers/` |
| REQ-AC-PRESERVE-FLEXIBILITY | `docs/requirements.md` § Acceptance Criteria | PLAN-003 | RM-004 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/acceptance_matrix.md` | `nbs/handlers/handler_template.ipynb` |
| REQ-AC-READABILITY | `docs/requirements.md` § Acceptance Criteria | PLAN-003 | RM-005 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/acceptance_matrix.md` | `nbs/handlers/handler_template.ipynb` |
