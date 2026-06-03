# Plan Audit Report

## Summary
- 対象: `AGENTS.md`, `docs/requirements.md`, `docs/plan.md`, `docs/reference_standards.md`
- 監査方式: 固定スコープ全件読了後に判定
- 判定: `REJECT_TO_ARCHITECT`

## Findings
1. `docs/plan.md` が Architect gate 判定条件を独自に再定義している。
Evidence:
- `docs/plan.md:190-198`
- `docs/requirements.md:38-40`
- `docs/requirements.md:52-56`
- `docs/reference_standards.md:25-44`
- `docs/reference_standards.md:123-137`
Why this fails:
- `REQ-GRAN-PLAN` は plan が要求閾値を tighten, relax, replace してはならないと定義している。
- `REQ-CONTRACT-CLOSURE-AUTHORITY` は gate semantics と audit-status interpretation を `docs/requirements.md` と `docs/reference_standards.md` の二文書で完結させることを要求している。
- しかし `docs/plan.md` は `## Architect Gate Criteria` を設け、gate 充足条件を plan 自身で列挙している。これは post-commit 正本の遷移語彙と判定契約を plan が参照するだけに留めず、局所的な判定アルゴリズムを追加している。
Impact:
- Plan 監査の許可判定語彙と gate semantics の authority boundary が `docs/plan.md` 側へ漏れ、Architect 再作業が必要。

2. `docs/plan.md` が「全ての現行 normative requirement identifier を coverage 表現する」と述べながら、明示マッピングから `REQ-GRAN-STANDARDS` を落としている。
Evidence:
- `docs/plan.md:32`
- `docs/plan.md:109`
- `docs/plan.md:151-160`
- `docs/requirements.md:37`
Why this fails:
- `docs/plan.md` は coverage を「all currently normative requirement identifiers」で表現すると宣言している。
- しかし `Requirement-to-Plan Mapping` に `REQ-GRAN-STANDARDS` の明示トレースが存在しない。
- `REQ-GRAN-REQS-COMPLETE` と整合する documentary trace を plan 自身が示せていない。
Impact:
- Plan 内の自己宣言と実際の requirement trace が不整合であり、完全性の面で Architect 修正が必要。

## Insufficient Evidence
- `docs/plan.md:7` と `docs/plan.md:18` は `docs/audit_report.md` を informative input として参照している。
- `docs/plan.md:22-25` は「current audit identifies two plan-structure failures」と述べている。
- ただし今回の固定監査スコープに `docs/audit_report.md` は含まれないため、この監査では当該主張を証跡として採用していない。

## Checks
| id | result | evidence_path | metric_value | threshold |
|---|---|---|---|---|
| `REQ-GRAN-PLAN` | FAIL | `docs/plan.md:190-198` | `architect_gate_criteria_redefined_in_plan` | `plan_must_not_replace_or_redefine_gate_thresholds` |
| `REQ-CONTRACT-CLOSURE-AUTHORITY` | FAIL | `docs/plan.md:190-198` | `gate_semantics_partially_defined_in_plan` | `gate_semantics_decidable_from_requirements_and_reference_only` |
| `REQ-GRAN-REQS-COMPLETE` | FAIL | `docs/plan.md:32; docs/plan.md:109; docs/plan.md:151-160` | `declared_all_req_coverage_but_req_gran_standards_not_traced` | `documentary_trace_must_be_complete_and_noncontradictory` |

## Open-Items
- `docs/plan.md` から独自 gate criteria を除去し、`docs/reference_standards.md` の遷移語彙と判定契約への参照宣言に縮退させること。
- `REQ-GRAN-STANDARDS` の plan 上の充足位置を明示するか、「all currently normative requirement identifiers」という自己宣言を修正して整合させること。

## Decision
- `REJECT_TO_ARCHITECT`
