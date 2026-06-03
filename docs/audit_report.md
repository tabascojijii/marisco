# Audit Report

## Scope
- Completed full read of `AGENTS.md`
- Completed full read of `docs/requirements.md`
- Completed full read of `docs/plan.md`
- Completed full read of `docs/reference_standards.md`
- No repository-wide recursive discovery performed

## Decision
- `REJECT_TO_ARCHITECT`

## Findings
1. `ARCH_REQ_GRAN_CHECKS_MAPPING_INCOMPLETE`
   `docs/requirements.md:0043-0049` requires `docs/acceptance_matrix.md` coverage to include acceptance layer, criterion, roadmap evidence path, later implementation evidence path or `not applicable`, and both roadmap and later implementation thresholds or `not applicable` for every normative `REQ-...` identifier. `docs/plan.md:0120-0130` maps `REQ-GRAN-CHECKS` to `PLAN-005`, but `PLAN-005` states only requirement representation, tracing, direct citation discipline, authority boundary preservation, and in-scope roadmap evidence paths. It does not directly state the missing acceptance-matrix field set or threshold obligations required by `REQ-GRAN-CHECKS`. Under `docs/reference_standards.md:0113-0115`, this is not a semantically exact requirement-to-plan mapping.
2. `ARCH_REQ_GRAN_HOOK_MAPPING_OVERCLAIM`
   `docs/requirements.md:0036` defines `REQ-GRAN-HOOK` as a two-part rule: the reusable `post-commit` hook is an orchestration surface, and it is not the source of project-specific granularity policy. `docs/plan.md:0103-0115` maps `REQ-GRAN-HOOK` to `PLAN-004`, but `PLAN-004` only states that `.git/hooks/post-commit` remains the governing orchestration surface. The plan item does not directly state the second required outcome that project-specific granularity remains owned elsewhere. Under `docs/reference_standards.md:0113-0115`, the cited plan item overclaims coverage.

## Checks
| id | pass | evidence_path | metric_value | threshold |
|---|---|---|---|---|
| `REQ-GRAN-CHECKS` | `false` | `docs/requirements.md:0043-0049; docs/plan.md:0120-0130; docs/plan.md:0179-0180; docs/reference_standards.md:0113-0115` | `plan_item_missing_acceptance_layer_criterion_evidence_and_threshold_fields` | `plan_item_directly_states_all_required_matrix_fields_and_thresholds` |
| `REQ-GRAN-HOOK` | `false` | `docs/requirements.md:0036; docs/plan.md:0103-0115; docs/plan.md:0179; docs/reference_standards.md:0113-0115` | `plan_item_states_only_orchestration_surface` | `plan_item_directly_states_orchestration_surface_and_non_granularity_policy_boundary` |

## 不足証跡
- None

## Open-Items
- Revise `PLAN-005` so the cited plan item directly states every `REQ-GRAN-CHECKS` matrix-field and threshold obligation if that requirement will continue to map to `PLAN-005`.
- Revise `PLAN-004` or the requirement-to-plan mapping so `REQ-GRAN-HOOK` is cited only to a plan item that directly states both required outcome fragments.
