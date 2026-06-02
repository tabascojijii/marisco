# Check Catalog

- `REQ-DOCSET`: Ensure all required docs listed in `docs/requirements.md` exist.
- `REQ-ROADMAP-SELF-CHECK`: Validate `docs/roadmap.md` contains `## Self-Check (Required)` and at least one `- [x]` item.
- `REQ-AUDIT-OPEN-ITEMS`: Validate `docs/audit_report.md` contains `## Open-Items`.
- `REQ-GOV-JSON-CONTRACT`: Validate top-level keys and `checks[]` keys in `audit_status.json`.
- `REQ-REASON-CODE-CONTRACT`: Validate `REJECT_*` and `ESCALATION` states include a prefixed reason code.
- `REQ-TRACEABILITY`: Ensure each active requirement has at least one evidence path in `docs/traceability_map.md`.
