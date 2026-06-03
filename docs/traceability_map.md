# Traceability Map

Authority: `docs/requirements.md` is the normative source for all REQ-IDs listed here. Plan Item column populated by Architect (2026-06-03); Roadmap Item column populated by PM (2026-06-03). This map separates roadmap-phase documentary evidence from later implementation evidence so roadmap auditing remains decidable within the fixed documentation scope required by `docs/requirements.md` and `docs/reference_standards.md`.

| Requirement ID | Source | Plan Item | Roadmap Item | Roadmap-Phase Evidence Path | Later Implementation Evidence Path |
|---|---|---|---|---|---|
| REQ-GRAN-REQS-SCOPE | `docs/requirements.md` § Granularity Allocation | PLAN-007 | RM-001, RM-002 | `docs/requirements.md`, `docs/roadmap.md`, `docs/traceability_map.md` | not applicable |
| REQ-GRAN-REQS-COMPLETE | `docs/requirements.md` § Granularity Allocation | PLAN-007 | RM-001, RM-002 | `docs/requirements.md`, `docs/roadmap.md`, `docs/traceability_map.md` | not applicable |
| REQ-GRAN-HOOK | `docs/requirements.md` § Granularity Allocation | PLAN-004 | RM-006 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/traceability_map.md` | `.git/hooks/post-commit` |
| REQ-GRAN-STANDARDS | `docs/requirements.md` § Granularity Allocation | PLAN-007 | RM-001 | `docs/reference_standards.md`, `docs/roadmap.md` | not applicable |
| REQ-GRAN-PLAN | `docs/requirements.md` § Granularity Allocation | PLAN-007 | RM-001 | `docs/plan.md`, `docs/roadmap.md` | not applicable |
| REQ-GRAN-ROADMAP | `docs/requirements.md` § Granularity Allocation | PLAN-007 | RM-001, RM-002 | `docs/roadmap.md`, `docs/traceability_map.md` | not applicable |
| REQ-GRAN-CONTRACT-DECIDABLE | `docs/requirements.md` § Granularity Allocation | PLAN-007 | RM-001, RM-002 | `docs/requirements.md`, `docs/reference_standards.md`, `docs/roadmap.md`, `docs/traceability_map.md` | not applicable |
| REQ-GRAN-CONTRACT-SUBORD | `docs/requirements.md` § Granularity Allocation | PLAN-007 | RM-001 | `docs/requirements.md`, `docs/reference_standards.md`, `docs/roadmap.md` | not applicable |
| REQ-GRAN-CHECKS | `docs/requirements.md` § Granularity Allocation | PLAN-007 | RM-001, RM-002 | `docs/acceptance_matrix.md`, `docs/traceability_map.md`, `docs/roadmap.md` | not applicable |
| REQ-NB-TEMPLATE | `docs/requirements.md` § Functional Requirements | PLAN-001 | RM-003 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/traceability_map.md` | `nbs/handlers/handler_template.ipynb`, generated `.py` |
| REQ-CURRENT-STATE-FIDELITY | `docs/requirements.md` § Functional Requirements | PLAN-001 | RM-003, RM-005 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/traceability_map.md` | `nbs/handlers/handler_template.ipynb` |
| REQ-DIFFERENCE-VISIBILITY | `docs/requirements.md` § Functional Requirements | PLAN-001, PLAN-002 | RM-004 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/traceability_map.md` | `nbs/handlers/handler_template.ipynb` |
| REQ-NBDEV-COMPAT | `docs/requirements.md` § Functional Requirements | PLAN-001 | RM-003, RM-008 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/traceability_map.md` | `nbs/handlers/handler_template.ipynb`, generated `.py` |
| REQ-POST-COMMIT-AUTHORITY | `docs/requirements.md` § Functional Requirements | PLAN-004 | RM-006 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/traceability_map.md` | `.git/hooks/post-commit` |
| REQ-POST-COMMIT-SEQUENCE | `docs/requirements.md` § Functional Requirements | PLAN-004 | RM-006 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/traceability_map.md` | `.git/hooks/post-commit` |
| REQ-POST-COMMIT-LIGHTWEIGHT-BOUNDARY | `docs/requirements.md` § Functional Requirements | PLAN-004 | RM-006 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/traceability_map.md` | `.git/hooks/post-commit` |
| REQ-PRESERVE-FLEXIBILITY | `docs/requirements.md` § Non-Functional Requirements | PLAN-002 | RM-004 | `docs/requirements.md`, `docs/roadmap.md`, `docs/traceability_map.md` | `nbs/handlers/handler_template.ipynb` |
| REQ-AVOID-PREMATURE-COMMONIZATION | `docs/requirements.md` § Non-Functional Requirements | PLAN-008 | RM-004, RM-005 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/traceability_map.md` | `nbs/handlers/` |
| REQ-READABILITY | `docs/requirements.md` § Non-Functional Requirements | PLAN-003 | RM-005 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/traceability_map.md` | `nbs/handlers/handler_template.ipynb` |
| REQ-LOW-FRICTION-VALIDATION | `docs/requirements.md` § Non-Functional Requirements | PLAN-004 | RM-006, RM-008 | `AGENTS.md`, `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/traceability_map.md` | `.git/hooks/post-commit`, hook run log |
| REQ-CHECK-EXPORT | `docs/requirements.md` § Required Checks | PLAN-004 | RM-006 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/traceability_map.md` | `.git/hooks/post-commit`, hook run log |
| REQ-CHECK-COMPILE | `docs/requirements.md` § Required Checks | PLAN-004 | RM-006 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/traceability_map.md` | generated `.py`, hook run log |
| REQ-CHECK-COVERAGE | `docs/requirements.md` § Required Checks | PLAN-004 | RM-006, RM-007 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/reference_standards.md`, `docs/traceability_map.md` | `.git/hooks/post-commit`, hook run log, `artifacts/*.json` |
| REQ-AC-TEMPLATE-EXISTS | `docs/requirements.md` § Acceptance Criteria | PLAN-001 | RM-003 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/traceability_map.md` | `nbs/handlers/handler_template.ipynb` |
| REQ-AC-TEMPLATE-BASELINE | `docs/requirements.md` § Acceptance Criteria | PLAN-001 | RM-003, RM-005 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/traceability_map.md` | `nbs/handlers/handler_template.ipynb` |
| REQ-AC-TEMPLATE-ZONES | `docs/requirements.md` § Acceptance Criteria | PLAN-002 | RM-004 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/traceability_map.md` | `nbs/handlers/handler_template.ipynb` |
| REQ-AC-TEMPLATE-NBDEV | `docs/requirements.md` § Acceptance Criteria | PLAN-001 | RM-003, RM-008 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/traceability_map.md` | `nbs/handlers/handler_template.ipynb`, generated `.py` |
| REQ-AC-POST-COMMIT-SEQUENCE | `docs/requirements.md` § Acceptance Criteria | PLAN-004 | RM-006 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/traceability_map.md` | `.git/hooks/post-commit` |
| REQ-AC-POST-COMMIT-BOUNDARY | `docs/requirements.md` § Acceptance Criteria | PLAN-004 | RM-006 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/traceability_map.md` | `.git/hooks/post-commit` |
| REQ-AC-NO-REFACTOR | `docs/requirements.md` § Acceptance Criteria | PLAN-008 | RM-004, RM-005 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/traceability_map.md` | `nbs/handlers/` |
| REQ-AC-PRESERVE-FLEXIBILITY | `docs/requirements.md` § Acceptance Criteria | PLAN-002 | RM-004 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/traceability_map.md` | `nbs/handlers/handler_template.ipynb` |
| REQ-AC-READABILITY | `docs/requirements.md` § Acceptance Criteria | PLAN-003 | RM-005 | `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/traceability_map.md` | `nbs/handlers/handler_template.ipynb` |
| REQ-PYTHON-BASELINE | `docs/requirements.md` § Constraints | PLAN-006 | RM-008 | `AGENTS.md`, `docs/requirements.md`, `docs/plan.md`, `docs/roadmap.md`, `docs/traceability_map.md` | `nbs/handlers/handler_template.ipynb`, `.git/hooks/post-commit` |
