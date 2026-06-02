# Reference Standards

## Coding
- Keep changes minimal and traceable.

## Documentation
- Every decision has evidence.

## Audit Interface
- Use `decision`, `reason_codes`, `owner`, `next_gate`, and `checks`.
- Keep requirement identifiers in `REQ-...` form.
- Keep reason codes in prefixed form such as `REQ_...`, `ARCH_...`, `PM_...`, or `IMPLEMENT_...`.
- Prefer explicit evidence paths over prose-only justification.

## Required Markdown Blocks
- `docs/roadmap.md` must contain `## Self-Check (Required)`.
- `docs/audit_report.md` must contain `## Open-Items`.
- `docs/escalation_report.md` must contain `## Summary` and `## Required Human Actions`.
