# AGENTS.md — marisco AI Operating System

## Startup protocol

Read this file before doing any repository exploration. These rules are the permanent operating baseline for AI agents working in `marisco`.

## Architecture-first execution protocol

Before any non-trivial implementation, debugging, or test design, load the architecture map first and then the smallest relevant reference note.

- Start with `nbs/reference/README.md` if you need help routing from task type to the correct reference note.
- Always read `docs/architecture.md` before design work so you know the target layer, the SSOT projection model, and the canonical data flow.
- Read `nbs/reference/layer-application-guide.md` when you need to decide whether a rule is repository-wide or specific to a notebook-driven layer.
- For abstraction barriers, single responsibility, and "what over how", read `nbs/reference/sicp-design-memento.md`.
- For handler notebook structure, callback presentation, and tests-as-usage-examples style, read `nbs/reference/handler-doc-guide.md`.
- For callback factoring and when to extract a shared abstraction versus keep a cross-group callback, read `nbs/reference/callback-group-dispatch.md`.
- For handler anatomy, completion criteria, and verification mindset, read `nbs/reference/guide.ipynb`.

Do not start broad repository searching until these references are loaded. Use them to choose the target layer and likely file family first.

Before any `rg`, `find`, directory listing, or broad repository exploration, read `docs/architecture.md` in full and bind your work to its layer model first.

Mandatory startup sequence:

1. Read `AGENTS.md`.
2. Read `CLAUDE.md`.
3. Read `docs/architecture.md`.
4. Only then inspect files within the specific layer named by the architecture document.

If you are looking for "where something lives", do not begin with blind search. Use `docs/architecture.md` to identify the layer first:

- ingestion / facade work -> `nbs/handlers/*` plus notebook-safe handler context via `token_saver.py`
- transformation / parser work -> `nbs/api/callbacks.ipynb`, `nbs/api/utils.ipynb`, and related exported views
- metadata overlay work -> `nbs/api/metadata.ipynb` and `marisco/metadata.py`
- encoding / projection work -> `nbs/api/encoders.ipynb`, `nbs/api/decoders.ipynb`, `nbs/api/netcdf2csv.ipynb`

Blind repository-wide search before reading `docs/architecture.md` is a workflow violation because it breaks architectural orientation and encourages editing the wrong surface.

## Mandatory pre-implementation declaration

Before writing code, editing notebooks, designing tests, or proposing a refactor, emit one short paragraph that states:

- the target layer you are changing: `Ingestion/Facade`, `Transformation/Parser`, `Metadata/Overlay`, `Encoding/Projection`, `Config/Registry`, or `Utils/Infrastructure`
- the public contract you are preserving or intentionally changing
- the exact references you loaded from `docs/architecture.md` and `nbs/reference/`
- a 1-sentence architectural extraction or core constraint from the loaded reference that applies directly to this task
- the concrete evidence you expect to produce before calling the task done, such as a notebook-local usage test, an export check, a projection verification, a registry integrity check, or a helper-level verification

If you cannot name all five, stop and read the missing references before proceeding.

## Thin-agent design pointers

- `SICP Guardrails`: name the user-visible `what`, not the procedural `how`; preserve abstraction barriers; keep small interfaces that can hide representation changes. Express this as a contract, not a personal preference. See `nbs/reference/sicp-design-memento.md`.
- `Defensive Limits`: keep robustness at boundary surfaces such as file/network ingress, serialization, and final public contract checks; avoid speculative recovery branches inside core transformations unless a loaded reference explicitly justifies them. Tie each defense to a boundary or contract. See `docs/architecture.md`, `docs/development_knowledge_base.md`, and `nbs/reference/callback-group-dispatch.md`.
- `Repository-wide kernel`: apply abstraction barriers, small public surfaces, explicit contracts, and boundary-scoped defenses across all layers. See `nbs/reference/layer-application-guide.md`.
- `Literate Programming`: treat handler-style notebook narration, callback-near-evidence layout, and tests-as-usage-examples as strong rules for notebook-driven pipeline layers, not as a universal formatting mandate. See `nbs/reference/handler-doc-guide.md` and `nbs/reference/layer-application-guide.md`.
- `Diataxis`: classify the artifact before writing it. Read `nbs/reference/diataxis-memento.md`, then route to the corresponding reference material so facts, procedures, and explanations do not bleed together.
- Generated modules and `_modidx.py` are projections, not authoring surfaces. Boundary-heavy external retrieval logic should stay small, isolated, and contract-driven.

## Minimal done criteria by layer

- `Ingestion/Facade`: preserve or intentionally change the handler entry contract, keep source loading notebook-authored, and leave usage evidence near the handler flow when the notebook is the authoring surface.
- `Transformation/Parser`: prove the normalized columns, group behavior, or parser boundary through the smallest natural evidence surface for that layer, which may be notebook-local usage cells or shared API-level verification.
- `Metadata/Overlay`: verify the `obj.attrs` contract explicitly, including any Zotero-shaped or overlay-specific fields affected by the change.
- `Encoding/Projection`: verify the canonical NetCDF projection or the compatibility CSV bridge, depending on which surface you changed.
- `Config/Registry`: verify lookup, schema, naming, or reference-surface integrity without forcing handler notebook presentation rules onto a registry artifact.
- `Utils/Infrastructure`: verify the helper boundary, call surface, or extracted responsibility on the smallest natural surface for that utility.

## Scope rule for expression style

- Repository-wide rules govern abstraction, contracts, SSOT discipline, and boundary handling.
- Handler-style `How-to` narration, provider-facing prose, and tests-as-usage-examples are mandatory for notebook-driven pipeline layers, not for every config, utility, or projection artifact.
- If unsure whether a style rule is global or layer-specific, read `nbs/reference/layer-application-guide.md` before proceeding.

## Absolute notebook safety rules

- Never `cat`, dump, or otherwise ingest a raw `.ipynb` file wholesale. Treat raw notebook JSON as a token hazard.
- Never use raw `.ipynb` content as the primary context for reasoning about a handler, API module, or workflow.

## Mandatory handler context protocol

When investigating a specific handler such as `handlers/geotraces`, always do this first:

```bash
python token_saver.py handlers/geotraces
```

General rule:

```bash
python token_saver.py handlers/<handler_name>
```

- Run `token_saver.py` before reading or discussing a handler.
- Use the Markdown emitted by `token_saver.py` as the authoritative working context for the handler.
- Treat that Markdown as the only high-purity context unless a human explicitly asks for lower-level notebook inspection.

## If notebook inspection is still required

- Prefer narrow symbol search such as `rg -n "symbol" nbs/handlers/foo.ipynb`.
- Prefer scoped, line-limited, or structure-aware inspection over full-file reads.
- Never dump notebook outputs into the model context unless explicitly requested.

## nbdev rule

- Source of truth lives in `nbs/`.
- Files under `marisco/` are generated by nbdev and should not be edited directly unless the task is specifically about generated output inspection.

## Windows nbdev command contract

- On Windows, AI agents must not casually run `nbdev_export` or `python -m nbdev.cli export`.
- Those entry points are banned because Windows path resolution and local module shadowing such as a nearby `cli.py` can route execution into the wrong target or fail in confusing ways.
- The required export pattern is:

```bash
python -c "import nbdev.cli; nbdev.cli.nb_export('nbs/api/metadata.ipynb', lib_path='marisco')"
```

- Adapt the notebook path as needed, but keep the `python -c "import nbdev.cli; nbdev.cli.nb_export(...)"` form.
- If a broader export is required, use the same import-first pattern rather than the shell entry point.
- [See docs/development_knowledge_base.md for full architectural context](docs/development_knowledge_base.md)

## Workflow red cards

- Manual editing of generated `.py` files to resolve conflicts or "quick-fix" exports is forbidden.
- In this repository, direct edits to generated modules can desynchronize notebook SSOT from the exported module surface and contaminate `_modidx.py`.
- If export or indexing is broken, fix the notebook first, then regenerate the module and index through the proper import-driven nbdev path.
- If Windows file locking blocks normal rewrite behavior, use a controlled overwrite or regeneration path; do not patch generated artifacts by hand and pretend the notebook is still authoritative.
- [See docs/development_knowledge_base.md for full architectural context](docs/development_knowledge_base.md)

## Network fallback rule

- When implementing external API access on Windows, do not assume Python `urlopen()` is sufficient.
- Always consider TLS EOF / connection reset failures as an environmental risk in Windows/Anaconda environments.
- For production or live-test retrieval code, provide a system-native `curl.exe` fallback via `subprocess.run(...)` unless a stronger repository-standard transport layer already exists.
- Live tests must not silently degrade to mock data unless fallback is explicitly enabled by configuration.
- [See docs/development_knowledge_base.md for full architectural context](docs/development_knowledge_base.md)

## Architecture index

`docs/architecture.md` is the architecture sourcebook for repository orientation. Treat the summary below as a quick index, not a substitute for reading that file before exploration.

### Macro flow

- Data enters through provider handlers or legacy dump loaders, is normalized by callback pipelines, enriched through `GlobAttrsFeeder`, then encoded as MARIS NetCDF and optionally projected back to legacy CSV.
- Canonical runtime path is `maris_init` -> handler `encode()` -> `Transformer` -> `GlobAttrsFeeder` -> `NetCDFEncoder` -> optional `netcdf2csv.decode()`.
- Treat the NetCDF artifact as canonical and CSV as a compatibility projection for MARIS central DB workflows.
- [See docs/architecture.md for implementation details](docs/architecture.md)

### Layer responsibilities

- SSOT / generation layer: `nbs/` is the authoring surface; `marisco/` and `_modidx.py` are generated projections and must not be hand-patched.
- Transformation layer: handlers and callbacks absorb provider irregularities and normalize them into MARIS-standard columns and sample groups.
- Metadata / projection layer: `GlobAttrsFeeder` builds `obj.attrs`, `NetCDFEncoder` writes the canonical artifact, and decoders bridge back to legacy CSV flows.
- [See docs/architecture.md for implementation details](docs/architecture.md)

### Windows adaptation

- On Windows, use only import-driven nbdev export commands; shell entry points are banned because of path shadowing and confusing failure modes.
- Treat file-locking, `_modidx.py` drift, and TLS EOF issues as normal environment constraints, not proof that notebook logic is wrong.
- For live external retrieval on Windows, preserve real-network semantics and add `curl.exe` fallback instead of silently falling back to mocks.
- [See docs/architecture.md for implementation details](docs/architecture.md)

## Coordination with CLAUDE.md

`CLAUDE.md` must be read together with this file, but this file takes priority for AI operating behavior, especially notebook safety and handler-context acquisition.
