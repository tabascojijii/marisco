# Acceptance Matrix

Authority: `docs/requirements.md` defines all normative requirements. This document maps them to acceptance layers, criteria, evidence paths, and thresholds for use in roadmap- and implementation-phase auditing.

Layer A = blocking acceptance gate. Layer B = supporting quality check.

| Requirement ID | Layer | Criterion | Evidence Path | Threshold |
|---|---|---|---|---|
| REQ-AC-TEMPLATE-EXISTS | A | Handler template notebook exists under `nbs/handlers/` | `nbs/handlers/` | file present and non-empty |
| REQ-AC-TEMPLATE-BASELINE | A | Template reflects the 8-section Handler Template Baseline defined in `docs/requirements.md` | `nbs/handlers/` | all 8 ordered sections present |
| REQ-AC-TEMPLATE-ZONES | A | Template marks provider-specific vs. reusable zones explicitly | `nbs/handlers/` | zone markers present in template |
| REQ-AC-TEMPLATE-NBDEV | A | Template participates in `nbdev` export flow without breaking imports | `nbs/handlers/`, generated `.py` | export succeeds; no import errors on affected modules |
| REQ-AC-POST-COMMIT-SEQUENCE | A | Post-commit verification sequence exists, is hook-governed, and includes all 3 stages defined in `REQ-POST-COMMIT-SEQUENCE` | `docs/requirements.md` § REQ-POST-COMMIT-SEQUENCE | all 3 stages (export, compile, import-smoke) documented |
| REQ-AC-POST-COMMIT-BOUNDARY | A | Verification sequence excludes all heavyweight execution categories defined in `REQ-POST-COMMIT-LIGHTWEIGHT-BOUNDARY` | `docs/requirements.md` § REQ-POST-COMMIT-LIGHTWEIGHT-BOUNDARY | 4 heavyweight exclusions documented |
| REQ-AC-NO-REFACTOR | A | No requirement in this phase forces immediate refactoring of existing handlers | `docs/requirements.md` | no mandatory handler migration clause present |
| REQ-NB-TEMPLATE | B | Template created as notebook under `nbs/handlers/`, follows `nbdev` conventions, requires no direct `.py` edits | `nbs/handlers/` | notebook present; `default_exp` and exported cells correct |
| REQ-CURRENT-STATE-FIDELITY | B | Template reflects current-state Handler Template Baseline, not a future architecture | `nbs/handlers/` | baseline sections match `docs/requirements.md` § Handler Template Baseline |
| REQ-DIFFERENCE-VISIBILITY | B | Template distinguishes provider-specific, reusable, and commonization-candidate zones | `nbs/handlers/` | all 3 zone types marked |
| REQ-NBDEV-COMPAT | B | Template exportable via current `nbdev` flow; exported files importable; no broken exports or circular imports | generated `.py` | export and import succeed without error |
| REQ-POST-COMMIT-SEQUENCE | B | 3-stage verification sequence (export, compile, import-smoke) defined in scoped governance documents | `docs/requirements.md` | all 3 stages enumerated |
| REQ-POST-COMMIT-LIGHTWEIGHT-BOUNDARY | B | Heavyweight exclusions (dataset downloads, remote API, full NetCDF runs, regression suites) enumerated | `docs/requirements.md` | 4 exclusions listed |
| REQ-CHECK-EXPORT | B | Notebook/export changes validated through export/regeneration stage | hook run log | export stage executes without error |
| REQ-CHECK-COMPILE | B | Generated Python files pass `python -m py_compile` and import-smoke | generated `.py` | no compile or import-time errors |
| REQ-CHECK-COVERAGE | B | Check set detects broken export structure, syntax errors, and import-time breakage | hook run log | all 3 failure categories detectable |
