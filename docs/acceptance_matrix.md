# Acceptance Matrix

| Requirement ID | Layer | Criterion | Evidence Path | Threshold |
|---|---|---|---|---|
| REQ-DOCSET | A | Required docs exist | docs/ | all required files present |
| REQ-ROADMAP-SELF-CHECK | A | Roadmap has required self-check block | docs/roadmap.md | section exists and includes `- [x]` |
| REQ-AUDIT-OPEN-ITEMS | A | Audit report has fixed open-items block | docs/audit_report.md | `## Open-Items` exists |
| REQ-GOV-JSON-CONTRACT | A | Audit status schema is valid | audit_status.json | contract_valid |
| REQ-REASON-CODE-CONTRACT | B | Reject or escalation decisions carry valid reason codes | audit_status.json, docs/audit_report.md | prefixed code present |
| REQ-TRACEABILITY | B | Requirement-to-evidence mapping exists | docs/traceability_map.md | every active requirement mapped |
