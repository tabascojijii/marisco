# Requirements Audit Report

## Summary
- Decision: `ESCALATION`
- Scope used for judgment: `AGENTS.md`, `docs/core_philosophy.md`, `docs/requirements.md`, `docs/reference_standards.md`
- Rationale: fixed-scope documents contain requirements-contract defects that make the requirements-phase audit interface non-unique and partially non-auditable.

## Findings
1. `REQ_CONTRACT_AUTHORITY_CONFLICT`
The machine-readable audit contract authority is split inconsistently across scoped documents. `docs/requirements.md:40-41` says the governing audit status contract must be decidable from `docs/reference_standards.md` and `docs/requirements.md` alone, and that `docs/audit_contract.md` must not be the only scoped source of authority. But `docs/reference_standards.md:102` says `docs/audit_contract.md` owns machine-readable audit output structure. Under the fixed scope, this leaves the authoritative owner of the audit I/F contract ambiguous.
Evidence: [docs/requirements.md](/abs/path/C:/dev/marisco3/marisco_clean/marisco_repo/docs/requirements.md:40), [docs/reference_standards.md](/abs/path/C:/dev/marisco3/marisco_clean/marisco_repo/docs/reference_standards.md:102)

2. `REQ_UNTRACKED_NORMATIVE_TEXT`
`docs/requirements.md` declares that all normative requirements must use `REQ-...` identifiers, but the document contains additional normative acceptance and guidance text without such identifiers. Examples include `docs/requirements.md:7-9`, `153-159`, and `188-195`. This breaks traceability against `docs/reference_standards.md:78` and `56`, which require requirement-ID based satisfaction and auditing.
Evidence: [docs/requirements.md](/abs/path/C:/dev/marisco3/marisco_clean/marisco_repo/docs/requirements.md:29), [docs/requirements.md](/abs/path/C:/dev/marisco3/marisco_clean/marisco_repo/docs/requirements.md:153), [docs/requirements.md](/abs/path/C:/dev/marisco3/marisco_clean/marisco_repo/docs/requirements.md:188), [docs/reference_standards.md](/abs/path/C:/dev/marisco3/marisco_clean/marisco_repo/docs/reference_standards.md:78)

3. `REQ_FIXED_SCOPE_EVIDENCE_GAP`
The requirements claim that acceptance for this workstream must be decidable from the fixed documentation audit scope without repository-wide discovery, but one acceptance item depends on a hook-governed documented sequence whose authoritative evidence location is not named in-scope. `docs/requirements.md:9`, `81-91`, and `193-194` require a documented post-commit sequence that is governed by `.git/hooks/post-commit`; however the fixed audit scope excludes the hook, and no in-scope document path is designated as the authoritative evidence location for that sequence. `docs/reference_standards.md:93-95` requires such references to be named in a scoped document rather than inferred.
Evidence: [docs/requirements.md](/abs/path/C:/dev/marisco3/marisco_clean/marisco_repo/docs/requirements.md:9), [docs/requirements.md](/abs/path/C:/dev/marisco3/marisco_clean/marisco_repo/docs/requirements.md:81), [docs/requirements.md](/abs/path/C:/dev/marisco3/marisco_clean/marisco_repo/docs/requirements.md:193), [docs/reference_standards.md](/abs/path/C:/dev/marisco3/marisco_clean/marisco_repo/docs/reference_standards.md:93)

## 不足証跡
- なし。今回の `ESCALATION` 判定は、固定スコープ内文書相互の契約不整合と監査可能性欠如だけで成立する。

## Open-Items
- `docs/requirements.md` と `docs/reference_standards.md` の間で、requirements-phase の machine-readable audit contract の唯一の権威文書を明示的に一本化すること。
- `docs/requirements.md` 内の未IDな規範文を `REQ-...` 識別子へ昇格させるか、参考情報へ格下げすること。
- 固定スコープだけで判定できるように、post-commit verification sequence の権威的な記載場所を in-scope 文書へ明記すること。
