# Plan — Handler Template Workstream

**Phase:** Architect
**Date:** 2026-06-03
**Authority Sources:** `docs/requirements.md`, `docs/reference_standards.md`

---

## Purpose

This plan translates the requirements-phase governance baseline into a concrete design and implementation strategy. It names plan items (PLAN-xxx) that each PM roadmap step and traceability-map row can reference. It does not redefine acceptance thresholds owned by `docs/requirements.md` or workflow routing owned by `post-commit`.

---

## Contract Inconsistency Resolution

This section fulfills the Architect mandate to make requirements-vs-reference_standards contract tensions explicit before implementation begins.

### TENSION-1 — pytest Scope Boundary

**Tension:** `docs/reference_standards.md § Validation And Test Baseline` states: "Implementation-phase auditing must include `pytest tests/` unless the requirements document explicitly defines a different local validation baseline." `docs/requirements.md § Validation Baseline For This Workstream` states: "pytest tests/ is not required for requirements-, plan-, or roadmap-phase acceptance of this workstream" and conditionally defers to implementation-phase rules if `src/`, `tests/`, or `artifacts/` content is introduced.

**Analysis:** The requirements document only exempts documentation-and-template phases (requirements, plan, roadmap). It does not unconditionally exempt the full workstream. When implementation artifacts under `src/` or `tests/` are introduced, `reference_standards.md` resumes authority and `pytest tests/` applies. For this workstream specifically, the deliverables are (a) a notebook template file and (b) a post-commit hook script. The notebook template is a documentation artifact; its acceptance is verified by the nbdev export/import smoke path, not by pytest. The hook script is a procedural shell/Python script whose acceptance is verified by the stages it itself runs on commit. No `src/` or `tests/` deliverables are scoped in this workstream.

**Resolution:** `pytest tests/` is not required for this workstream. If a future workstream introduces `src/` or `tests/` content, the implementation-phase rule in `reference_standards.md` resumes unconditionally. This plan does not relax that future obligation. Plan items in this workstream use the lightweight validation baseline defined in `docs/requirements.md § Validation Baseline For This Workstream`.

### TENSION-2 — Artifact Evidence Contract vs. Documentation Phase

**Tension:** `docs/reference_standards.md § Evidence And Artifact Rules` identifies three JSON artifacts as part of the workflow evidence contract: `artifacts/acceptance_gate_report.json`, `artifacts/md_json_completeness_report.json`, and `artifacts/json_schema_validation_report.json`. These artifacts require matching `execution_id` values when present as a set. However, this workstream's acceptance baseline is documentation-level, and the hook that generates these artifacts is itself a deliverable of this workstream.

**Analysis:** The artifact evidence rule applies to the hook-driven implementation-phase flow. The artifacts are outputs of the hook's post-commit run, not pre-conditions for plan-phase acceptance. During the plan phase, evidence is file-backed documentation (`docs/requirements.md`, `docs/acceptance_matrix.md`, `docs/traceability_map.md`). When the hook is delivered and triggered post-commit, it must generate all three artifacts with consistent `execution_id` values to satisfy the implementation-phase contract.

**Resolution:** Plan item PLAN-005 requires the hook to generate all three artifacts with a shared `execution_id` on each invocation. This resolves the tension: the artifacts are deliverables of the hook (produced at implementation time), not prerequisites for plan-phase documentation acceptance. This plan makes the obligation explicit so the PM and Implementer cannot omit it.

### TENSION-3 — REQ-GRAN-CHECKS and acceptance_matrix Authority

**Tension:** `docs/requirements.md § REQ-GRAN-CHECKS` states: "Operationalized checks and pass thresholds belong in `docs/acceptance_matrix.md`." `docs/reference_standards.md § Granularity Ownership Boundary` states the same. The existing `docs/acceptance_matrix.md` currently has evidence paths pointing to `nbs/handlers/` before the template exists and to `hook run log` before the hook exists. This is structurally forward-looking.

**Analysis:** The acceptance matrix correctly anticipates deliverables. The evidence paths are declared targets, not assertions of current existence. This is consistent with `docs/requirements.md § Governance Document Attestation` approach: the matrix is a binding contract about where evidence must appear when implementation completes. No inconsistency exists; the forward-looking paths are intentional.

**Resolution:** No document change required. Plan items must produce artifacts at the declared evidence paths. PLAN-001 through PLAN-004 map to those paths explicitly.

---

## Open Decision Resolutions

These resolve `docs/requirements.md § Open Decisions` before implementation begins.

### OD-1 — Template Notebook Filename

**Decision:** `nbs/handlers/handler_template.ipynb`

**Rationale:** The filename follows the existing handler naming convention in `nbs/handlers/` (provider name + `.ipynb`). `handler_template` is unambiguous as a template rather than a provider implementation. It is consistent with the repository's snake_case module naming.

### OD-2 — Scaffold vs. Scaffold-Plus-Guidance

**Decision:** Scaffold with inline authoring guidance (scaffold-plus-guidance).

**Rationale:** A pure scaffold without guidance produces an ambiguous template that forces every adopter to re-derive the intent of each section. Inline guidance in Markdown cells (prose adjacent to code cells) satisfies `REQ-READABILITY` and `REQ-CURRENT-STATE-FIDELITY` simultaneously. Guidance must not prescribe future-state architecture; it must describe current-state intent. Zone annotations (provider-specific, reusable, commonization-candidate) are a form of inline guidance and are required by `REQ-DIFFERENCE-VISIBILITY`.

### OD-3 — Calibration Reference Handler

**Decision:** Use the HELCOM handler (`nbs/handlers/helcom.ipynb`) as the primary calibration reference.

**Rationale:** A calibration reference is needed to verify that the template's section ordering and content fidelity match an existing real-world handler. HELCOM is a well-known provider in the MARIS ecosystem and its notebook is expected to exemplify the typical callback-based pipeline pattern. If HELCOM's notebook structure diverges from the Handler Template Baseline, the Implementer must note the divergence without modifying HELCOM. Template fidelity is judged against the Baseline definition in `docs/requirements.md § Handler Template Baseline`, not against the calibration handler alone.

---

## Plan Items

### PLAN-001 — Template Notebook: Structure and Content

**Goal:** Create `nbs/handlers/handler_template.ipynb` containing all 8 ordered sections of the Handler Template Baseline defined in `docs/requirements.md § Handler Template Baseline`.

**Scope:**
- Title and purpose statement cell
- Configuration and input source notes cell
- `load_data` section with scaffold code cell and inline guidance prose
- Transformation pipeline section with callback scaffold and inline guidance prose
- Metadata construction section (`get_attrs` scaffold) with inline guidance prose
- `encode` section with scaffold and inline guidance prose
- Verification / smoke-check section with scaffold
- Notes section identifying provider-specific content, likely reusable logic, and known pain points
- `default_exp` directive per `REQ-NB-TEMPLATE` (e.g., `#| default_exp handlers.handler_template`)
- Export cell markers (`#| export`) on cells that should generate module output

**Acceptance linkage:**
`REQ-AC-TEMPLATE-EXISTS`, `REQ-AC-TEMPLATE-BASELINE`, `REQ-AC-TEMPLATE-NBDEV`, `REQ-NB-TEMPLATE`, `REQ-CURRENT-STATE-FIDELITY`, `REQ-NBDEV-COMPAT`

**Evidence path:** `nbs/handlers/handler_template.ipynb`, generated `.py` module under `marisco/handlers/`

**Constraint:** The template must be validated against OD-3 (HELCOM calibration reference). If HELCOM's section ordering differs from the Baseline, the discrepancy must be noted in the template's Notes section without modifying HELCOM.

---

### PLAN-002 — Template Notebook: Zone Annotations

**Goal:** Annotate every section in the template with explicit zone markers.

**Zone types (three required per `REQ-DIFFERENCE-VISIBILITY`):**
1. `[PROVIDER-SPECIFIC]` — logic that will differ per provider
2. `[REUSABLE]` — logic based on existing shared callbacks or utilities
3. `[COMMONIZATION-CANDIDATE]` — logic repeated across handlers that could be shared later

**Implementation approach:** Zone markers appear as Markdown cell annotations or inline comments. Each section must carry at least one zone label. Sections that span multiple zones must be sub-annotated.

**Constraint:** Zone labels must not imply that provider-specific sections require normalization. `REQ-PRESERVE-FLEXIBILITY` and `REQ-AC-PRESERVE-FLEXIBILITY` require that provider-specific sections are labeled without a forced-refactoring mandate.

**Acceptance linkage:** `REQ-DIFFERENCE-VISIBILITY`, `REQ-AC-TEMPLATE-ZONES`, `REQ-PRESERVE-FLEXIBILITY`, `REQ-AC-PRESERVE-FLEXIBILITY`

**Evidence path:** `nbs/handlers/handler_template.ipynb` (zone markers present in rendered notebook)

---

### PLAN-003 — Template Notebook: Literate-Programming Style

**Goal:** Ensure every section in the template has prose explanation adjacent to code cells.

**Requirements:**
- Each of the 8 Baseline sections must contain at least one Markdown cell with a prose explanation before or adjacent to the code cell.
- Prose must explain intent (what this section does and why), not merely restate the code.
- No unexplained generated-code patterns are permitted.
- Style must be consistent with existing handler notebooks (checked against OD-3 calibration reference).

**Constraint:** Do not rewrite or reformat existing handler notebooks. Style consistency is assessed by reading, not by automated reformatting.

**Acceptance linkage:** `REQ-READABILITY`, `REQ-AC-READABILITY`

**Evidence path:** `nbs/handlers/handler_template.ipynb` (prose present in each section)

---

### PLAN-004 — Post-Commit Hook: Design and Implementation

**Goal:** Create `.git/hooks/post-commit` that implements the 3-stage verification sequence defined in `docs/requirements.md § REQ-POST-COMMIT-SEQUENCE`.

**Hook architecture:**
- The hook is the governance authority for post-commit workflow (per `REQ-POST-COMMIT-AUTHORITY`).
- Helper scripts invoked by the hook are subordinate implementation details; the hook remains the single declared authority.
- The hook must be executable (`chmod +x .git/hooks/post-commit` or equivalent).

**3-stage sequence (all stages required per `REQ-POST-COMMIT-SEQUENCE`):**

1. **Stage 1 — Notebook Export:** Run `nbdev_export` or equivalent to regenerate Python modules from notebooks including the new template. Exit non-zero on failure.

2. **Stage 2 — Compile Check:** Run `python -m py_compile` on all generated modules touched by the commit (at minimum `marisco/handlers/handler_template.py` and any other modified generated modules). Exit non-zero on failure.

3. **Stage 3 — Import Smoke Check:** Run a lightweight import verification on affected modules (e.g., `python -c "import marisco.handlers.handler_template"`). Exit non-zero on failure.

**Heavyweight exclusions enforced (per `REQ-POST-COMMIT-LIGHTWEIGHT-BOUNDARY`):**
The hook must not invoke: full provider dataset downloads, remote API calls, full NetCDF production runs, or full regression suites.

**Python version target (per `REQ-PYTHON-BASELINE`):** Hook and any helper scripts must target Python `>=3.7`.

**Acceptance linkage:** `REQ-POST-COMMIT-AUTHORITY`, `REQ-POST-COMMIT-SEQUENCE`, `REQ-POST-COMMIT-LIGHTWEIGHT-BOUNDARY`, `REQ-AC-POST-COMMIT-SEQUENCE`, `REQ-AC-POST-COMMIT-BOUNDARY`, `REQ-LOW-FRICTION-VALIDATION`, `REQ-CHECK-EXPORT`, `REQ-CHECK-COMPILE`, `REQ-CHECK-COVERAGE`

**Evidence path:** `.git/hooks/post-commit` (file present and executable), hook run log

---

### PLAN-005 — Hook Artifact Generation

**Goal:** Ensure the hook generates the three JSON artifacts required by `docs/reference_standards.md § Evidence And Artifact Rules` on each invocation, with a shared `execution_id` across all three.

**Required artifacts:**
- `artifacts/acceptance_gate_report.json`
- `artifacts/md_json_completeness_report.json`
- `artifacts/json_schema_validation_report.json`

**Contract requirements:**
- Each artifact must include an `execution_id` field.
- When all three artifacts are present, their `execution_id` values must agree.
- Missing required artifacts or mismatched `execution_id` values are contract failures per `reference_standards.md`.

**Implementation approach:**
- Generate a UUID or timestamp-based `execution_id` at hook invocation start.
- Pass it to each artifact-generating step.
- Write artifacts to `artifacts/` directory (create directory if absent).

**Acceptance linkage:** `docs/reference_standards.md § Evidence And Artifact Rules` (resolves TENSION-2)

**Evidence path:** `artifacts/acceptance_gate_report.json`, `artifacts/md_json_completeness_report.json`, `artifacts/json_schema_validation_report.json`

---

### PLAN-006 — Python Version Compatibility

**Goal:** Verify that all new code introduced by this workstream targets Python `>=3.7`.

**Scope:**
- Template notebook's exported Python cells
- Hook script and any helper scripts

**Verification method:**
- Static review: avoid syntax or standard-library features introduced after Python 3.7.
- The hook's Stage 2 (`python -m py_compile`) implicitly validates syntax compatibility on the executing Python version. If the repository's CI or development environment uses Python 3.7+, compatibility is verified at runtime.

**Acceptance linkage:** `REQ-PYTHON-BASELINE`

**Evidence path:** `nbs/handlers/handler_template.ipynb`, `.git/hooks/post-commit`

---

### PLAN-007 — Traceability Map: Plan Item Column Update

**Goal:** Populate the Plan Item column in `docs/traceability_map.md` for all normative requirements.

**Authority:** `docs/traceability_map.md` states: "Plan Item and Roadmap Item columns are populated by the Architect and PM respectively; they are marked TBD until those phases complete."

**Action:** Replace all TBD values in the Plan Item column with the PLAN-xxx references defined in this plan. The Roadmap Item column remains TBD until the PM phase completes.

**Acceptance linkage:** `docs/reference_standards.md § Granularity Ownership Boundary` (traceability map owns requirement-to-evidence traceability)

**Evidence path:** `docs/traceability_map.md`

---

### PLAN-008 — Non-Refactoring Constraint Enforcement

**Goal:** Confirm that no plan item requires immediate refactoring of existing handlers.

**Verification:**
- PLAN-001 through PLAN-007 must not include steps that modify existing handler notebooks (`nbs/handlers/*.ipynb` other than the new template).
- OD-3 calibration reference (HELCOM) is read-only during template creation.
- If discrepancies between the Baseline and existing handlers are observed, they must be noted in the template's Notes section, not corrected in the handler.

**Acceptance linkage:** `REQ-AVOID-PREMATURE-COMMONIZATION`, `REQ-AC-NO-REFACTOR`

**Evidence path:** `docs/requirements.md` § REQ-AVOID-PREMATURE-COMMONIZATION (no mandatory migration clause), `nbs/handlers/` (existing handler notebooks unchanged)

---

## Phase Breakdown

### Phase 1 — Documentation Finalization (Architect output, pre-PM)

| Step | Action | Plan Item |
|---|---|---|
| A1 | Complete and publish this `docs/plan.md` | — |
| A2 | Update `docs/traceability_map.md` Plan Item column | PLAN-007 |
| A3 | Confirm `docs/acceptance_matrix.md` evidence paths are consistent with plan | — |

### Phase 2 — Template Notebook Implementation (Implementer)

| Step | Action | Plan Item |
|---|---|---|
| I1 | Create `nbs/handlers/handler_template.ipynb` with all 8 Baseline sections | PLAN-001 |
| I2 | Annotate all sections with zone markers | PLAN-002 |
| I3 | Verify literate-programming style; add prose to any bare sections | PLAN-003 |
| I4 | Verify Python `>=3.7` compatibility of exported cells | PLAN-006 |
| I5 | Run `nbdev_export`; confirm no import errors on generated module | PLAN-001, PLAN-004 Stage 1-3 (manual) |

### Phase 3 — Post-Commit Hook Implementation (Implementer)

| Step | Action | Plan Item |
|---|---|---|
| H1 | Create `.git/hooks/post-commit` with 3-stage sequence | PLAN-004 |
| H2 | Implement artifact generation with shared `execution_id` | PLAN-005 |
| H3 | Verify hook excludes all heavyweight execution categories | PLAN-004 |
| H4 | Verify hook is executable and triggers on commit | PLAN-004 |
| H5 | Verify Python `>=3.7` compatibility of hook scripts | PLAN-006 |

### Phase 4 — Acceptance Verification (Auditor, post-implementation)

| Check | Plan Item | Evidence Path |
|---|---|---|
| Template exists and is non-empty | PLAN-001 | `nbs/handlers/handler_template.ipynb` |
| All 8 Baseline sections present | PLAN-001 | `nbs/handlers/handler_template.ipynb` |
| Zone markers present (3 types) | PLAN-002 | `nbs/handlers/handler_template.ipynb` |
| nbdev export succeeds | PLAN-001 | generated `.py` module |
| No import errors | PLAN-001 | generated `.py` module |
| Hook exists and is executable | PLAN-004 | `.git/hooks/post-commit` |
| Hook includes all 3 stages | PLAN-004 | `.git/hooks/post-commit` |
| Hook excludes heavyweight execution | PLAN-004 | `.git/hooks/post-commit` |
| 3 JSON artifacts with matching execution_id | PLAN-005 | `artifacts/*.json` |
| No existing handler notebook modified | PLAN-008 | `nbs/handlers/` |

---

## Verification Strategy

### Pre-Implementation Verification (Architect / PM)
- `docs/acceptance_matrix.md`: confirm all Layer A requirements have evidence paths that PLAN-001 through PLAN-008 will satisfy.
- `docs/traceability_map.md`: confirm Plan Item column is populated (completed by PLAN-007).
- No code changes or git commits by the Architect role.

### Implementation-Phase Verification (Implementer)
- After PLAN-001/I5: `nbdev_export` succeeds; `python -c "import marisco.handlers.handler_template"` succeeds.
- After PLAN-004/H4: commit a test change and verify the hook runs the 3 stages without error.
- After PLAN-005/H2: verify `artifacts/` contains all three JSON files with matching `execution_id`.

### Post-Implementation Audit Gate
- Auditor verifies against `docs/acceptance_matrix.md` Layer A requirements.
- Evidence must be file-backed (not prose-only) per `reference_standards.md § Evidence And Artifact Rules`.
- `audit_status.json` and `audit_status.txt` must be emitted with correct structure per `reference_standards.md § Audit Contract`.

---

## Granularity Boundary

- This plan translates requirements into a repository document strategy and implementation approach.
- This plan names plan items (PLAN-xxx) so that `docs/traceability_map.md` and `docs/roadmap.md` have concrete references.
- This plan does not redefine acceptance thresholds owned by `docs/requirements.md`.
- This plan does not redefine audit routing or transition logic owned by `post-commit`.
- If a requirement is found to be too abstract after this plan is written, the repair target is `docs/requirements.md` or `docs/reference_standards.md`, not this plan.

---

## Audit Alignment

- `docs/requirements.md` is the canonical source for acceptance thresholds and validation baseline.
- `docs/reference_standards.md` is the behavioral standard for workflow participants.
- `docs/acceptance_matrix.md` is the normative mapping from requirements to evidence (Layer A/B).
- `docs/traceability_map.md` is the normative traceability record.
- This plan is the Architect's design document; it is subordinate to requirements and reference_standards for acceptance authority.
- `docs/roadmap.md` translates this plan into executable PM steps; it must not introduce new acceptance criteria.

---

## Risks

| Risk | Mitigation |
|---|---|
| Template encodes too much future architecture | OD-2 mandates scaffold-plus-guidance; PLAN-008 prohibits handler refactoring |
| Template sections diverge from HELCOM calibration | PLAN-001 requires noting divergence in Notes section without modifying HELCOM |
| Hook becomes too heavy over time | PLAN-004 enforces `REQ-POST-COMMIT-LIGHTWEIGHT-BOUNDARY`; heavyweight steps are explicitly listed as prohibited |
| Artifact `execution_id` mismatch breaks implementation gate | PLAN-005 requires `execution_id` generated once at hook invocation and shared across all three artifacts |
| Python `>=3.7` incompatibility introduced | PLAN-006 requires static review plus Stage 2 compile check as runtime guard |
