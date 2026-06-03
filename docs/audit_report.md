# Plan Audit Report

## Summary
- 監査対象: `AGENTS.md`, `docs/requirements.md`, `docs/plan.md`, `docs/reference_standards.md`
- 監査対象相: `docs/plan.md`
- 完全走査: 実施済み
- 判定: `REJECT_TO_ARCHITECT`

## Scope Discipline
- 判定は固定スコープ4ファイルのみを根拠とした。
- リポジトリ再帰探索は未実施。
- スコープ外ファイルの内容は根拠に使っていない。

## Findings

### F-001
- 概要: `docs/plan.md` が Architect ゲートの成立条件として `docs/acceptance_matrix.md` と `docs/traceability_map.md` への適合を要求しており、固定監査スコープ外の証跡を plan 相判定に持ち込んでいる。
- 根拠:
  - `docs/requirements.md:9`
  - `docs/requirements.md:176-178`
  - `docs/reference_standards.md:12-13`
  - `docs/reference_standards.md:162-173`
  - `docs/plan.md:196-202`
- 判定理由: requirements と reference standards は、requirements・plan・roadmap 相の判定を固定 documentation scope だけで可決可能にすることを要求している。ところが plan は out-of-scope 文書への適合を Architect gate 条件として再導入しており、plan 相の可決条件を上流正本より厳しくしている。

### F-002
- 概要: `docs/plan.md` の主計画は governance repair に偏っており、requirements が定義する本来の workstream deliverables を実現する実行計画が不足している。
- 根拠:
  - `docs/requirements.md:23-27`
  - `docs/requirements.md:131-135`
  - `docs/plan.md:57-159`
  - `docs/plan.md:174-190`
  - `docs/plan.md:215-221`
- 判定理由: requirements の deliverables は handler template notebook、provider-specific と reusable の checklist、hook-governed lightweight post-commit flow、利用方法 documentation である。plan は acceptance matrix と traceability map の改修を中心に構成され、上記 deliverables を作るための Architect-to-PM 実行計画が欠ける。

### F-003
- 概要: `docs/plan.md` が `docs/audit_report.md` を authority source として扱い、同ファイル起点で defect 群を定義しているが、当該ファイルはこの監査の固定スコープにも、requirements と reference standards が定める plan 相の正本集合にも含まれない。
- 根拠:
  - `docs/requirements.md:40-47`
  - `docs/reference_standards.md:9-13`
  - `docs/reference_standards.md:114`
  - `docs/plan.md:5`
  - `docs/plan.md:9`
  - `docs/plan.md:20-30`
  - `docs/plan.md:225-231`
- 判定理由: plan 相の governing contract は `docs/requirements.md` と `docs/reference_standards.md` で決定される。plan が `docs/audit_report.md` を authority source として昇格させると、固定スコープ外の監査結果に依存した設計根拠が生じ、plan 単体の客観監査性を損なう。

### F-004
- 概要: `docs/plan.md` が `33/33` という固定件数閾値を独自に宣言しており、requirements の「every normative requirement」基準を件数基準へ置換している。
- 根拠:
  - `docs/requirements.md:38`
  - `docs/requirements.md:42-47`
  - `docs/plan.md:96-105`
  - `docs/plan.md:227`
- 判定理由: requirements は acceptance matrix に対し「全 normative `REQ-...`」の被覆を要求しており、固定件数は source-of-truth ではない。plan の `33/33` は requirements 変更時に即座に陳腐化し得るため、threshold を plan で再定義している。

## 不足証跡
- `docs/plan.md` が参照する `docs/audit_report.md` の実内容は固定スコープ外のため未検証。
- `docs/plan.md` が検証条件に使う `docs/acceptance_matrix.md` と `docs/traceability_map.md` の実内容は固定スコープ外のため未検証。

## Open-Items
- OI-001: `docs/plan.md` の Architect gate 条件から固定スコープ外証跡依存を除去し、plan 相の可決条件を `docs/requirements.md` と `docs/reference_standards.md` に従属させること。
- OI-002: governance repair とは別に、handler template notebook、zone checklist、hook-governed lightweight post-commit flow、usage documentation へ到達する計画項目を `docs/plan.md` に追加すること。
- OI-003: `docs/plan.md` の authority source から `docs/audit_report.md` を外し、監査結果への依存が必要な箇所は参考情報として降格すること。
- OI-004: `33/33` の固定件数表現を削除し、coverage 基準を requirements 正本の `every normative REQ-...` 参照へ置換すること。

## Decision
- decision: `REJECT_TO_ARCHITECT`
- owner: `Architect`
- next_gate: `ARCHITECT_REWORK`
- reason_codes:
  - `ARCH_PLAN_OUT_OF_SCOPE_GATE`
  - `ARCH_PLAN_DELIVERABLE_GAP`
  - `ARCH_PLAN_AUTHORITY_DRIFT`
  - `ARCH_PLAN_THRESHOLD_DRIFT`
