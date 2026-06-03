# Audit Report

## Summary

- audit_target: `docs/plan.md`
- audit_scope: `AGENTS.md`, `docs/requirements.md`, `docs/plan.md`, `docs/reference_standards.md`
- scan_status: `complete`
- decision: `REJECT_TO_ARCHITECT`

## Findings

### F1

- id: `REQ-NB-TEMPLATE`
- severity: `blocking`
- finding: `docs/plan.md` の requirement-to-plan mapping は `REQ-NB-TEMPLATE` を `PLAN-001` のみへ割り当てているが、`REQ-NB-TEMPLATE` の必須断片である generated `.py` への direct edits を要件充足経路にしないことは `PLAN-001` 自身に直接書かれていない。`PLAN-003` と `PLAN-006` には notebook-first / generated-file-only 禁止の記述があるが、mapping table 上の `PLAN-001` 単独 citation では requirement 全体を直接満たしたことにならない。
- evidence:
  - `docs/requirements.md:83`
  - `docs/requirements.md:86`
  - `docs/reference_standards.md:114`
  - `docs/reference_standards.md:118`
  - `docs/plan.md:72`
  - `docs/plan.md:77`
  - `docs/plan.md:102`
  - `docs/plan.md:152`
  - `docs/plan.md:185`
- impact: `REQ-NB-TEMPLATE` に対する downstream citation が cited item 自身の stated outcome だけでは完結しておらず、semantic-exactness 条件を満たさない。

### F2

- id: `REQ-CURRENT-STATE-FIDELITY`
- severity: `blocking`
- finding: `docs/plan.md` の requirement-to-plan mapping は `REQ-CURRENT-STATE-FIDELITY` を `PLAN-001` のみへ割り当てているが、同要件の必須断片である baseline sections ごとの provider variation 明示は `PLAN-002` にあり、`PLAN-001` 自身には直接書かれていない。
- evidence:
  - `docs/requirements.md:88`
  - `docs/requirements.md:91`
  - `docs/reference_standards.md:114`
  - `docs/reference_standards.md:118`
  - `docs/plan.md:74`
  - `docs/plan.md:75`
  - `docs/plan.md:88`
  - `docs/plan.md:185`
- impact: `REQ-CURRENT-STATE-FIDELITY` に対する table citation が required outcome の一部を neighboring plan item に借用しており、direct mapping としては無効。

### F3

- id: `REQ-POST-COMMIT-AUTHORITY`
- severity: `blocking`
- finding: `docs/plan.md` の requirement-to-plan mapping は `REQ-POST-COMMIT-AUTHORITY` を `PLAN-004` に割り当てているが、要件が明示する helper scripts の subordinate status は `PLAN-004` の required outcomes に直接書かれていない。hook が governing orchestration surface である点は記載されているものの、helper scripts を alternative workflow authority にしない条件が cited item 自身で完結していない。
- evidence:
  - `docs/requirements.md:105`
  - `docs/requirements.md:108`
  - `docs/reference_standards.md:114`
  - `docs/reference_standards.md:118`
  - `docs/plan.md:111`
  - `docs/plan.md:117`
  - `docs/plan.md:188`
- impact: `REQ-POST-COMMIT-AUTHORITY` に対する plan-level citation が authority boundary requirement を full-text で保持しておらず、supporting or neighboring prose への依存が残る。

### F4

- id: `REQ-GRAN-CHECKS`
- severity: `blocking`
- finding: `docs/plan.md` の requirement-to-plan mapping は `REQ-GRAN-CHECKS` を `PLAN-005` に割り当てているが、要件が要求する acceptance-matrix 各 row の self-contained field rule は `PLAN-005` の required outcomes に直接書かれていない。`PLAN-005` は matrix の必須 fields を列挙しているが、row ごとにその fields を自項目テキストで持ち、section defaults や neighboring rows に依存してはならないという断片を落としている。
- evidence:
  - `docs/requirements.md:46`
  - `docs/requirements.md:55`
  - `docs/reference_standards.md:114`
  - `docs/reference_standards.md:119`
  - `docs/plan.md:129`
  - `docs/plan.md:131`
  - `docs/plan.md:189`
- impact: `REQ-GRAN-CHECKS` に対する citation は matrix completeness の中核条件を cited item 自身で直接再現しておらず、requirement 全体を満たす mapping になっていない。

### F5

- id: `REQ-CONTRACT-CLOSURE-EVIDENCE`
- severity: `blocking`
- finding: `docs/plan.md` の requirement-to-plan mapping は `REQ-CONTRACT-CLOSURE-EVIDENCE` を `PLAN-005` に割り当てているが、要件が明示する repository-local instruction files は deciding evidence source になれないという条件は `PLAN-005` 自身に直接書かれていない。plan 前文には `AGENTS.md` を consulted local guidance とする説明があるものの、mapping table が cite している `PLAN-005` の required outcomes には当該断片が存在しない。
- evidence:
  - `docs/requirements.md:61`
  - `docs/reference_standards.md:180`
  - `docs/plan.md:35`
  - `docs/plan.md:137`
  - `docs/plan.md:189`
- impact: `REQ-CONTRACT-CLOSURE-EVIDENCE` に対する supporting-document alignment citation が authority/evidence boundary を cited item 本文で閉じておらず、directness requirement を満たさない。

## Passed Checks

- `REQ-GRAN-PLAN`: `PLAN-006` は downstream requirement-to-plan citation が cited `PLAN-...` item 自身の required outcomes に限定されることを直接述べている。証跡: `docs/plan.md:147`
- `REQ-CONTRACT-CLOSURE-PLAN`: `PLAN-006` は supporting-governance documents が out-of-scope でも Architect-gate validity が `docs/requirements.md`、`docs/reference_standards.md`、`docs/plan.md` だけで decidable であることを直接述べている。証跡: `docs/plan.md:148`
- `REQ-LOW-FRICTION-VALIDATION`: `PLAN-004` は lightweight stage set と external-network / full-dataset exclusion を直接述べている。証跡: `docs/plan.md:113`-`docs/plan.md:116`

## Open-Items

- `docs/plan.md` の requirement-to-plan mapping table を、cited `PLAN-...` item 自身が requirement 全断片を直接述べる形へ修正すること。
- `REQ-NB-TEMPLATE` と `REQ-CURRENT-STATE-FIDELITY` は、`PLAN-001` に不足断片を追記するか、fragment coverage を誤解させない mapping へ再構成すること。
- `REQ-POST-COMMIT-AUTHORITY` は、`PLAN-004` に helper scripts subordinate rule を明記すること。
- `REQ-GRAN-CHECKS` と `REQ-CONTRACT-CLOSURE-EVIDENCE` は、`PLAN-005` に row-self-contained rule と repository-local instruction files 非権威条件を明記すること。
- 不足証跡: なし
