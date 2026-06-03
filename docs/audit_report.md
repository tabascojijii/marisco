# Audit Report

## Summary

- audit_target: `docs/plan.md`
- audit_scope: `AGENTS.md`, `docs/requirements.md`, `docs/plan.md`, `docs/reference_standards.md`
- scan_status: `complete`
- decision: `REJECT_TO_ARCHITECT`

## Findings

### F1

- id: `REQ-GRAN-PLAN`
- severity: `blocking`
- finding: `docs/plan.md` の要件対応表が `REQ-GRAN-PLAN` を `PLAN-006` に割り当てているが、`PLAN-006` の必須成果は要件閾値への従属と代替アルゴリズム禁止しか明示しておらず、同要件が要求する downstream requirement-to-plan citation の semantic-exactness 条件を自項目内で直接述べていない。
- evidence:
  - `docs/requirements.md:39`
  - `docs/reference_standards.md:114`
  - `docs/reference_standards.md:115`
  - `docs/reference_standards.md:118`
  - `docs/plan.md:133`
  - `docs/plan.md:134`
  - `docs/plan.md:147`
  - `docs/plan.md:148`
  - `docs/plan.md:188`
- impact: `docs/plan.md` 自身の requirement-to-plan mapping が nearby plan item への依存で成立しており、plan-phase で要求される direct mapping 条件を満たさない。

### F2

- id: `REQ-CONTRACT-CLOSURE-PLAN`
- severity: `blocking`
- finding: `docs/plan.md` の要件対応表が `REQ-CONTRACT-CLOSURE-PLAN` を `PLAN-006` に割り当てているが、同要件の中核である supporting-governance documents が out-of-scope の場合でも gate validity が governing contract と plan だけで decidable であることは `PLAN-005` の注記で述べられており、`PLAN-006` 自体には直接書かれていない。
- evidence:
  - `docs/requirements.md:62`
  - `docs/reference_standards.md:179`
  - `docs/reference_standards.md:181`
  - `docs/plan.md:139`
  - `docs/plan.md:147`
  - `docs/plan.md:148`
  - `docs/plan.md:188`
- impact: `REQ-CONTRACT-CLOSURE-PLAN` に対する plan-level citation が self-contained ではなく、cited item 自身に必要成果が存在しない。

## Passed Checks

- `REQ-NB-TEMPLATE`: `PLAN-001` が `nbs/handlers/` 配下の notebook、`nbdev` 準拠、generated `.py` 非正本を直接述べている。証跡: `docs/plan.md:72`-`docs/plan.md:77`
- `REQ-POST-COMMIT-SEQUENCE`: `PLAN-004` が export/regeneration、`python -m py_compile`、import smoke checks を直接述べている。証跡: `docs/plan.md:111`-`docs/plan.md:117`
- `REQ-LOW-FRICTION-VALIDATION`: `PLAN-004` が lightweight stage set と external-network/full-dataset exclusion を直接述べている。証跡: `docs/plan.md:113`-`docs/plan.md:116`

## Open-Items

- `docs/plan.md` の requirement-to-plan mapping table を、各 requirement が実際に直接述べられている `PLAN-...` 項目へ修正すること。
- `REQ-GRAN-PLAN` と `REQ-CONTRACT-CLOSURE-PLAN` については、必要なら `PLAN-006` に不足成果を追記するか、mapping を `PLAN-005` を含む正しい項目へ付け替えること。
- 不足証跡: なし
