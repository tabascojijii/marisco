# Audit Report

Execution-ID: PM_AUDIT-20260604T143816Z-4e0806
Phase: PM_AUDIT
Decision: REJECT_TO_PM
Next-Gate: PM_REWORK

## Summary

固定スコープ監査を `AGENTS.md`、`docs/requirements.md`、`docs/plan.md`、`docs/roadmap.md`、`docs/reference_standards.md`、`docs/acceptance_matrix.md`、`docs/traceability_map.md` に対して完了した。

必須 docset である `docs/acceptance_matrix.md` と `docs/traceability_map.md` は存在する。`docs/requirements.md` にある全 `REQ-...` は両文書に現れている。

否決理由は文書欠落ではない。`docs/traceability_map.md` における `RM-001` 引用の一部が、`docs/roadmap.md` の `RM-001` 本文だけでは直接充足されない要求まで含んでおり、`docs/requirements.md` と `docs/reference_standards.md` の direct-mapping 規則に反している。

## Findings

### F-001

`docs/traceability_map.md` の `RM-001` 引用に過剰マッピングが残っている。

根拠:

- `REQ-GRAN-REQS-COMPLETE` は、要求文書側で監査可能性を塞ぐ欠落を閉じることに加え、構造的欠陥修復時は upstream 修復を先に閉じることを求めるが、`RM-001` が直接述べているのは後者だけである。`docs/requirements.md:37` と `docs/traceability_map.md:13` に対し、`docs/roadmap.md:30` は要求全体を直接再記述していない。
- `REQ-GRAN-CONTRACT-DECIDABLE` は、requirements-phase から roadmap-phase までの machine-readable audit-status contract が `docs/requirements.md` と `docs/reference_standards.md` だけから可判定であることを求めるが、`RM-001` は authority boundary と in-scope 決定性は述べる一方、machine-readable contract そのものの可判定性を直接述べていない。`docs/requirements.md:44`、`docs/traceability_map.md:20`、`docs/roadmap.md:32-39` を参照。
- `REQ-GRAN-CONTRACT-SUBORD` は `docs/audit_contract.md` の subordinate 性を直接要件化しているが、`RM-001` には `docs/audit_contract.md` への直接言及がない。`docs/requirements.md:45`、`docs/traceability_map.md:21`、`docs/roadmap.md:29-39` を参照。
- `REQ-CONTRACT-CLOSURE-PLAN` は Architect gate の可判定性を governing contract と `docs/plan.md` 自体から保つことを求めるが、`RM-001` が直接述べているのは roadmap completion の present-tense decidability であり、Architect gate の可判定性そのものではない。`docs/requirements.md:63`、`docs/traceability_map.md:27`、`docs/roadmap.md:33-39` を参照。

影響:

- `docs/traceability_map.md` は `docs/reference_standards.md:115-121` および `docs/reference_standards.md:185-186` の semantic-exactness 規則を満たしていない。

### F-002

`docs/acceptance_matrix.md` と `docs/traceability_map.md` の supporting-governance 直結性主張が、上記の過剰マッピング解消前提のまま食い違っている。

根拠:

- `docs/acceptance_matrix.md:19` は roadmap citation が semantically exact であることを閾値にしている。
- `docs/acceptance_matrix.md:24` は downstream citation が referenced requirement を直接満たすことを要求している。
- しかし `docs/traceability_map.md:13`、`docs/traceability_map.md:20-21`、`docs/traceability_map.md:27` は、`RM-001` 本文に直接ない要件断片まで同一 roadmap item に載せている。

影響:

- active scope に入っている supporting-governance 文書同士が same-change-set consistency に達しておらず、`REQ-GRAN-CHECKS` と `REQ-CONTRACT-CLOSURE-SUPPORT` を満たせない。

## 不足証跡

なし

## Decision Basis

`docs/requirements.md` と `docs/reference_standards.md` の governing contract 自体は監査可能であり、required docset も存在するため `ESCALATION` ではない。問題は PM 管轄の roadmap / supporting-governance 運用化に限定されているため、判定は `REJECT_TO_PM`、owner は `PM`、next gate は `PM_REWORK` とする。

## Open-Items

| ID | Severity | Requirement-Ref | Reason-Code | Evidence | Fix-Instruction | Owner |
|---|---|---|---|---|---|---|
| OI-001 | Major | `REQ-GRAN-REQS-COMPLETE`, `REQ-GRAN-CONTRACT-DECIDABLE`, `REQ-GRAN-CONTRACT-SUBORD`, `REQ-CONTRACT-CLOSURE-PLAN` | `PM_TRACE_RM001_OVERMAPPED` | `docs/traceability_map.md:13`, `docs/traceability_map.md:20-21`, `docs/traceability_map.md:27`, `docs/roadmap.md:29-39` | `RM-001` をその本文が直接述べる要件断片にだけ絞って trace を狭めるか、欠けている要件断片を直接述べる新規または改訂 `RM-...` 項目を追加し、trace row を再対応させること | PM |
| OI-002 | Major | `REQ-GRAN-CHECKS`, `REQ-CONTRACT-CLOSURE-SUPPORT`, `REQ-GRAN-ROADMAP` | `PM_SUPPORTING_DOC_DIRECTNESS_MISMATCH` | `docs/acceptance_matrix.md:19`, `docs/acceptance_matrix.md:24`, `docs/traceability_map.md:13`, `docs/traceability_map.md:20-21`, `docs/traceability_map.md:27` | `docs/acceptance_matrix.md` と `docs/traceability_map.md` を同一 change set で再整合し、各 `RM-...` citation が requirement fragment を直接満たす状態に直すこと | PM |
