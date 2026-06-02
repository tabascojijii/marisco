# Acceptance Matrix

| Requirement ID | Layer | Criterion | Evidence Path | Threshold |
|---|---|---|---|---|
| REQ-DOCSET | A | Required docs exist | docs/ | all required files present |
| REQ-ROADMAP-SELF-CHECK | A | Roadmap has required self-check block | docs/roadmap.md | section exists and includes `- [x]` |
| REQ-AUDIT-OPEN-ITEMS | A | Audit report has fixed open-items block | docs/audit_report.md | `## Open-Items` exists |
| REQ-GOV-JSON-CONTRACT | A | Audit status schema is valid | audit_status.json | contract_valid |
| REQ-REASON-CODE-CONTRACT | B | Reject or escalation decisions carry valid reason codes | audit_status.json, docs/audit_report.md | prefixed code present |
| REQ-TRACEABILITY | B | Requirement-to-evidence mapping exists | docs/traceability_map.md | every active requirement mapped |
| REQ-GRAN-REQS | A | Requirements assign project-specific acceptance detail to the requirements layer | docs/requirements.md | granularity allocation block exists |
| REQ-GRAN-STANDARDS | A | Reference standards define audit granularity policy and ownership boundaries | docs/reference_standards.md | both sections exist |
| REQ-GRAN-PLAN-BOUNDARY | B | Plan declares that it translates but does not replace acceptance thresholds | docs/plan.md | granularity boundary block exists |
| REQ-GRAN-ROADMAP-BOUNDARY | B | Roadmap declares that it sequences work without becoming audit criteria | docs/roadmap.md | granularity boundary block exists |
| REQ-GRAN-CONTRACT-BOUNDARY | B | Audit contract limits itself to machine-readable structure | docs/audit_contract.md | granularity contract boundary block exists |
