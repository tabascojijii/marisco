# Audit Report

## Scope
- audited_files:
  - `AGENTS.md`
  - `docs/requirements.md`
  - `docs/plan.md`
  - `docs/reference_standards.md`
- audit_mode: complete_scan
- scope_rule: fixed_scope_only

## Method
- 全対象ファイルを全文読了後に判定した。
- 判定参照順は `docs/requirements.md` → `docs/plan.md` → `docs/reference_standards.md` とした。
- スコープ外文書は読まず、推測で補完しなかった。

## Findings

### 1. `docs/plan.md` が固定スコープ外文書を Architect gate の成立条件に含めている
- severity: high
- violated_requirements:
  - `REQ-GRAN-REQS-COMPLETE`
  - `REQ-GRAN-PLAN`
  - `REQ-GRAN-CONTRACT-DECIDABLE`
  - `REQ-GRAN-SUPPORTING-DOCS-ROLE`
- evidence:
  - `docs/plan.md:103-112` で `docs/acceptance_matrix.md` と `docs/traceability_map.md` の整合を plan item に含めている。
  - `docs/plan.md:197` で `the required supporting governance documents are aligned in the same change set` を gate 条件にしている。
  - `docs/requirements.md:40-49` は governing contract を `docs/requirements.md` と `docs/reference_standards.md` だけで可判定にすることを要求している。
  - `docs/reference_standards.md:14` と `docs/reference_standards.md:164-165` は supporting governance documents を subordinate と定義している。
- impact:
  - この plan は、今回の固定監査スコープ外にある文書の整合を gate 条件へ持ち込み、plan 監査の pass/fail をスコープ内文書だけで決められなくしている。

### 2. `docs/plan.md` が二文書統治集合を越えて `AGENTS.md` を authority source と宣言している
- severity: high
- violated_requirements:
  - `REQ-GRAN-PLAN`
  - `REQ-GRAN-CONTRACT-DECIDABLE`
- evidence:
  - `docs/plan.md:5` は `AGENTS.md`, `docs/requirements.md`, `docs/reference_standards.md` を `Authority Sources` として列挙している。
  - `docs/requirements.md:40-42` は plan-phase auditing の governing machine-readable contract を `docs/reference_standards.md` と `docs/requirements.md` だけで可判定にすることを要求している。
  - `docs/reference_standards.md:11-14` は `docs/requirements.md` と `docs/reference_standards.md` を normative two-document governance set と定義している。
- impact:
  - `AGENTS.md` は repository-local instruction として参照できても、governing authority source として追加宣言すると、plan が上位契約の authority boundary を拡張してしまう。

## Passed Checks
- `REQ-NB-TEMPLATE`: `docs/plan.md:76-79` は notebook-first の template target を `nbs/handlers/` に固定しており、generated `.py` を正本にしていない。
- `REQ-POST-COMMIT-SEQUENCE`: `docs/plan.md:98-100` は export/regeneration, `python -m py_compile`, import smoke checks の 3 段階を保持している。
- `REQ-POST-COMMIT-LIGHTWEIGHT-BOUNDARY`: `docs/plan.md:100` と `docs/plan.md:141-143` は heavyweight exclusion を維持している。
- `REQ-AC-NO-REFACTOR`: `docs/plan.md:120-123` と `docs/plan.md:203-207` は immediate refactor を強制していない。

## 不足証跡
- なし

## Open-Items
- `docs/plan.md` の `Authority Sources` から `AGENTS.md` を外し、governing authority を `docs/requirements.md` と `docs/reference_standards.md` に限定すること。
- `docs/plan.md` の Architect gate から、固定スコープ外文書の整合を成立条件として要求する文言を除去すること。
- supporting governance documents への言及は、実施項目または参照整合の説明に留め、plan-phase gate の可判定条件へ昇格させないこと。

## Decision
- result: `REJECT_TO_ARCHITECT`
- rationale:
  - plan-phase gate が fixed documentation scope だけでは可判定でない
  - authority boundary が two-document governance set を逸脱している
