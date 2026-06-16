# CLAUDE.md — marisco

## AI startup trigger

Before any exploration or autonomous work, read `AGENTS.md` first and follow it as the top-priority operating policy.

- `AGENTS.md` is the permanent AI behavior baseline for this repository.
- Read `docs/architecture.md` in full before any broad search, path hunting, or file discovery commands.
- For any handler investigation, run `python token_saver.py handlers/<handler_name>` first and use that emitted Markdown as the primary context.
- Do not ingest raw `.ipynb` notebook JSON wholesale.

Mandatory orientation rule:

1. Read `AGENTS.md`.
2. Read this file.
3. Read `docs/architecture.md`.
4. Name the target layer you are working in before exploring:
   - ingestion / facade
   - transformation / parser
   - metadata overlay
   - encoding / projection

If the task is about metadata retrieval, callback contracts, Zotero-shaped global attributes, INIS, Zenodo, or TITANICA, start from the metadata overlay layer in `docs/architecture.md` and then inspect `nbs/api/metadata.ipynb` through notebook-safe tooling. Do not begin with repository-wide search.

## What this project is

**marisco** is a data curation tool developed at the IAEA Marine Environmental Laboratories (Monaco) for [MARIS](https://maris.iaea.org), the IAEA's open-access marine radioactivity repository.

**The problem it solves:** Marine radioactivity data comes from many providers — regional monitoring programmes (HELCOM, OSPAR), event-driven datasets (TEPCO data following Fukushima), individual research papers, and more. Each uses different file formats, nomenclature, units, and detection-limit conventions. MARIS ingests all of them into a single central database, but aligning them requires significant curation work.

**What marisco does:** It replaces a manual OpenRefine-based curation workflow with a reproducible Python pipeline. For each dataset, marisco:

1. Reads the raw provider data in whatever format it arrives
2. Aligns it to the MARIS data schema — standardising nomenclature, units, detection levels, and sample-type classification
3. Encodes the curated dataset as a self-contained **NetCDF4 file** that bundles measurements, variable metadata, lookup tables of used nomenclatures, and bibliographic global attributes in a single file
4. Can also export `.csv` files compatible with the existing OpenRefine → MARIS central-DB import pipeline

**How MARIS data is disseminated:** Via the web interface (https://maris.iaea.org), a data API, and as NetCDF files — marisco-generated NetCDF files feed all three channels.

## Critical rule — reading notebooks

**Never use `Read` on `.ipynb` files.** For handler work, prefer `python token_saver.py handlers/<handler_name>` first. If notebook inspection is still required, use this tiered approach instead:

```bash
# 1. Locate a cell by symbol (Bash tool)
rg -n "sample_id" nbs/handlers/helcom.ipynb

# 2. View the relevant chunk by line range (Bash tool)
uv run python -c "from fastcore.tools import view; print(view('nbs/handlers/helcom.ipynb', (42, 65)))"

# 3. Broad survey — signatures only, no outputs (Bash tool)
uv run python -c "from toolslm.xml import folder2ctx; print(folder2ctx('nbs/api', sigs_only=True, out=False, file_re=r'.*\.ipynb', skip_folder_re=r'.*checkpoints.*'))"

# 4. Single notebook as clean XML (Bash tool)
uv run python -c "from toolslm.xml import nb2xml; print(nb2xml('nbs/foo.ipynb', out=False))"
```

Prefer scoped paths (`nbs/api`, `nbs/cli`) over full `nbs/` — handlers alone is 200KB, full tree is 387KB. Use full `nbs/` only when explicitly asked for a broad survey. See `nbs/CLAUDE.md` for full parameter reference.

## token_saver protocol

`token_saver.py` is the default notebook-safe context extraction tool for handler work.

```bash
python token_saver.py handlers/geotraces
python token_saver.py handlers/helcom
```

Use it to combine:

1. Notebook Markdown cells from `nbs/...`
2. Clean exported Python from `marisco/...`

This is the preferred context for AI-assisted development because it strips notebook outputs while preserving design intent and production logic.

## Critical rule — nbdev

**Never edit `.py` files in `marisco/`. They are auto-generated from notebooks.** All code lives in `nbs/`.

### Windows nbdev safeguards

On Windows, do not casually run:

- `nbdev_export`
- `python -m nbdev.cli export`

These forms are banned for AI agents because Windows path resolution and local module shadowing can send execution through the wrong entry point. The required export pattern is:

```bash
python -c "import nbdev.cli; nbdev.cli.nb_export('nbs/api/metadata.ipynb', lib_path='marisco')"
```

Adapt the notebook path as needed, but preserve the `import nbdev.cli` form. Prefer this import-driven invocation even when exporting a different notebook.

[See docs/development_knowledge_base.md for full architectural context](docs/development_knowledge_base.md)

### Build / export command contract

Use the import-first form below as the only valid Windows notebook export command:

```bash
python -c "import nbdev.cli; nbdev.cli.nb_export('nbs/api/metadata.ipynb', lib_path='marisco')"
```

Rules:

- Replace only the notebook path; keep the `python -c "import nbdev.cli; nbdev.cli.nb_export(...)"` shape intact.
- Do not substitute `nbdev_export` or `python -m nbdev.cli export`.
- If a notebook change affects generated code or `_modidx.py`, fix the notebook first, then re-export with this command form.
- [See docs/architecture.md for implementation details](docs/architecture.md)

### Index integrity rule

`_modidx.py` is part of the generated nbdev surface. Do not hand-edit generated `.py` files to resolve merge conflicts, unblock imports, or patch symbol exposure. That is a red-card workflow because it can desynchronize the notebook SSOT from the exported API and pollute the symbol index.

If `_modidx.py` or exported modules look wrong:

1. Fix the notebook first.
2. Re-export through the import-driven nbdev path.
3. Regenerate or overwrite the index through a controlled generation path if Windows file-locking interferes.

[See docs/development_knowledge_base.md for full architectural context](docs/development_knowledge_base.md)

Documentation follows the [`fastcore.docments`](https://fastcore.fast.ai/docments.html) convention: parameter documentation lives inline with the argument, not in a docstring body. nbdev picks these up automatically and renders them into the Quarto-based documentation site.

```python
def draw_n(n:int,        # Number of cards to draw
           replace:bool=True  # Draw with replacement?
          )->list:        # List of cards
    "Draw `n` cards."
```

Always use this style — inline `#` comments after type annotations — rather than numpy/Google-style docstrings.

## The four sample type groups

All measurements belong to one of four groups (also the NetCDF4 groups within each output file):

- `SEAWATER` — dissolved/filtered water samples (Bq/m³)
- `BIOTA` — marine organisms (Bq/kg wet or dry weight)
- `SEDIMENT` — bottom sediments (Bq/kg or Bq/m²)
- `SUSPENDED_MATTER` — suspended particles

## How the package works

Each data provider has a **handler** (`nbs/handlers/*.ipynb`). Every handler exposes an `encode(fname_out)` function that:

1. Loads raw provider data → `Dict[str, pd.DataFrame]` (one per sample type group)
2. Runs a `Transformer` with an ordered list of `Callback` objects that standardise the data
3. Feeds transformed data to `GlobAttrsFeeder` for NetCDF global attributes (bbox, time range, Zotero bibliographic metadata)
4. Writes output via `NetCDFEncoder`

## Architecture index

This section is a compact reminder only. The authoritative orientation document is [`docs/architecture.md`](docs/architecture.md), which must be read before repository exploration.

### Macro flow

- Source data enters through handlers, is normalized by callback pipelines, enriched by metadata callbacks, encoded to MARIS NetCDF, then optionally decoded to OpenRefine-compatible CSV.
- The main CLI path is `maris_init` -> `maris_to_nc` -> handler `encode()` -> `Transformer` -> `GlobAttrsFeeder` -> `NetCDFEncoder`.
- NetCDF is the canonical artifact; CSV exists as a compatibility bridge for MARIS legacy ingestion.
- [See docs/architecture.md for implementation details](docs/architecture.md)

### Layer responsibilities

- SSOT / generation layer: notebooks in `nbs/` are the source of truth, while `marisco/` and `_modidx.py` are generated projections.
- Ingestion / transformation layer: handlers, `Transformer`, `PerGroupCB`, `Remapper`, and provider-specific callbacks normalize heterogeneous source data.
- Metadata / projection layer: `GlobAttrsFeeder` assembles `obj.attrs`, `NetCDFEncoder` writes the canonical file, and decoder modules project back to CSV when needed.
- [See docs/architecture.md for implementation details](docs/architecture.md)

### Windows adaptation

- Windows-safe nbdev work must use import-driven `nb_export(...)`, not shell entry points.
- File-locking, `_modidx.py` regeneration issues, and TLS EOF behavior are expected environment constraints and should be handled structurally.
- For live external API work on Windows, keep real retrieval semantics and add `curl.exe` fallback instead of silently degrading to mocks.
- [See docs/architecture.md for implementation details](docs/architecture.md)

## CLI tools

The CLI commands (`maris_init`, `maris_to_nc`, etc.) are defined in `nbs/cli/` and built with [`fastcore.script`](https://fastcore.fast.ai/script.html). The `@call_parse` decorator on a function generates the CLI entry point — arguments are inferred from the function signature. Entry points are declared in `settings.ini` under `console_scripts`.

## Architecture and coding guidelines

When implementing external API retrieval on Windows, assume Python `urlopen()` may fail with TLS EOF or connection reset even when the remote endpoint itself is healthy. For live retrieval code, build a system-native `curl.exe` fallback through `subprocess.run(...)` unless a stronger repository-standard transport layer already exists.

Do not silently swap to mock data during live verification unless fallback is explicitly enabled in configuration. Live tests should prove real retrieval rather than accidentally validating only the parser against a local mock.

[See docs/development_knowledge_base.md for full architectural context](docs/development_knowledge_base.md)

## Setup

```bash
export ZOTERO_API_KEY=your_key_here
maris_init   # downloads template, lookup tables, creates ~/.marisco/
```

## Go deeper

- `AGENTS.md` — permanent AI operating rules and notebook-safety policy
- `docs/architecture.md` — system architecture reference: macro flow, layer boundaries, SSOT model, and Windows safeguards
- `docs/development_knowledge_base.md` — architecture safeguards, Windows/Anaconda failure modes, and nbdev recovery patterns
- `nbs/handlers/CLAUDE.md` — handler pattern, column naming, how to add a new handler
- `nbs/api/CLAUDE.md` — core abstractions: Callback/Transformer, Remapper, configs, encoders
- `nbs/CLAUDE.md` — nbdev workflow, editing and building
