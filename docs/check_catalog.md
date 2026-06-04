# Check Catalog

- `REQ-DOCSET`: Ensure all required docs listed in `docs/requirements.md` exist.
- `REQ-ROADMAP-SELF-CHECK`: Validate `docs/roadmap.md` contains `## Self-Check (Required)` and at least one `- [x]` item.
- `REQ-AUDIT-OPEN-ITEMS`: Validate `docs/audit_report.md` contains `## Open-Items`.
- `REQ-ACCEPTANCE-GATE-REPORT`: Validate `artifacts/acceptance_gate_report.json` exists and contains the required machine-readable acceptance fields.
- `REQ-EXECUTION-ID-ALIGNMENT`: Validate `docs/audit_report.md` and `artifacts/acceptance_gate_report.json` agree on the shared execution identifier when both declare one.
- `REQ-GOV-JSON-CONTRACT`: Validate top-level keys and `checks[]` keys in `audit_status.json`.
- `REQ-REASON-CODE-CONTRACT`: Validate `REJECT_*` and `ESCALATION` states include a prefixed reason code.
- `REQ-TRACEABILITY`: Ensure each active requirement has at least one evidence path in `docs/traceability_map.md`.
- `REQ-GRAN-REQS`: Validate `docs/requirements.md` explicitly assigns project-specific acceptance detail to the requirements layer rather than leaving it implicit in downstream documents.
- `REQ-GRAN-STANDARDS`: Validate `docs/reference_standards.md` defines repository-local audit granularity policy and document ownership boundaries.
- `REQ-GRAN-PLAN-BOUNDARY`: Validate `docs/plan.md` states that it translates requirements without replacing acceptance thresholds.
- `REQ-GRAN-ROADMAP-BOUNDARY`: Validate `docs/roadmap.md` states that it sequences execution without becoming the source of audit criteria.
- `REQ-GRAN-CONTRACT-BOUNDARY`: Validate `docs/audit_contract.md` limits itself to machine-readable output structure rather than project-specific requirement policy.
