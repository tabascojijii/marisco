# 🏗️ MARISCO System Architecture Reference

This document is a repository-grounded architecture reference for `marisco`, written from a notebook-safe scan performed on June 16, 2026 across `AGENTS.md`, `CLAUDE.md`, `docs/development_knowledge_base.md`, `token_saver.py`, `nbs/api/*`, `nbs/handlers/*`, `marisco/*.py`, `marisco/handlers/*.py`, `marisco/cli/*.py`, and `marisco/_modidx.py`.

## 1. Architectural Philosophy & Core Principles

### Single Source of Truth (SSOT)

`marisco` is an nbdev repository. The authoritative design surface lives in `nbs/`, while `marisco/` and `marisco/_modidx.py` are generated projections of that source model.

- `nbs/api/*.ipynb` define the reusable platform: callbacks, configs, metadata feeders, encoders, decoders, utilities, and bootstrap helpers.
- `nbs/handlers/*.ipynb` define provider-specific ingestion pipelines.
- `marisco/*.py` and `marisco/handlers/*.py` are export artifacts and must be treated as read-only views of notebook truth.
- `marisco/_modidx.py` is not incidental metadata. It is the exported symbol graph of the public API and an early warning surface for notebook/export/index drift.

This is structuralism in practice: the architecture is not "the Python files alone", but the relationship between literate notebooks, generated modules, and the symbol index that proves the export succeeded.

### Technical Hospitality

The core design goal is to shield downstream consumers from upstream messiness.

- Provider files arrive with inconsistent units, date formats, nomenclature, coordinates, and detection-limit semantics.
- Metadata providers may return irregular external payloads.
- Downstream consumers, especially NetCDF encoding and MARIS ingestion, should receive stable, typed, validated structures.

The practical contract is:

- measurement tables are normalized into MARIS-standard columns such as `TIME`, `LAT`, `LON`, `NUCLIDE`, `VALUE`, `UNIT`, and `DL`
- sample groups are split into the four canonical domains: `SEAWATER`, `BIOTA`, `SEDIMENT`, and `SUSPENDED_MATTER`
- global metadata is emitted as clean NetCDF attributes via `obj.attrs`
- bibliographic creator information is serialized as a string contract suitable for NetCDF attributes

### Callback-Oriented Composition

The system favors ordered, auditable micro-transformations over monolithic parser functions.

- `Transformer` applies an ordered list of `Callback` objects to provider data.
- `GlobAttrsFeeder` applies the same pattern to global metadata.
- `run_cbs()` appends callback docstrings to `logs`, making operational intent part of the final artifact.

This gives MARISCO three useful properties at once: composability, inspectability, and permanent audit trails.

## 2. Macro Architecture & Data Pipeline Flow

```text
                    +------------------------------+
                    |  External / Local Sources    |
                    |------------------------------|
                    | CSV / XLSX / TXT / PDF / API |
                    | Zotero library               |
                    | INIS API                     |
                    +--------------+---------------+
                                   |
                                   v
                    +------------------------------+
                    |  Handler Facade              |
                    |------------------------------|
                    | load_data(...)               |
                    | provider-specific callbacks  |
                    | encode(...)                  |
                    +--------------+---------------+
                                   |
                                   v
                    +------------------------------+
                    |  Transformation Layer        |
                    |------------------------------|
                    | Transformer                  |
                    | PerGroupCB / Callback        |
                    | Remapper + IMFA pattern      |
                    | ParseTime / unit / DL / geo  |
                    +--------------+---------------+
                                   |
                                   v
                    +------------------------------+
                    |  Metadata Overlay Layer      |
                    |------------------------------|
                    | GlobAttrsFeeder              |
                    | BboxCB / DepthRangeCB        |
                    | TimeRangeCB                  |
                    | ZoteroCB / InisCB            |
                    | KeyValuePairCB               |
                    +--------------+---------------+
                                   |
                                   v
                    +------------------------------+
                    |  Encoding Layer              |
                    |------------------------------|
                    | NetCDFEncoder                |
                    | template: maris-template.nc  |
                    | enums from LUTs              |
                    | NC_VARS / NC_GROUPS mapping  |
                    +--------------+---------------+
                                   |
                                   v
                    +------------------------------+
                    |  Canonical Output            |
                    |------------------------------|
                    | MARIS NetCDF4 dataset        |
                    | data + enums + global attrs  |
                    +--------------+---------------+
                                   |
                                   v
                    +------------------------------+
                    |  Compatibility Projection    |
                    |------------------------------|
                    | NetCDFDecoder                |
                    | netcdf2csv.decode()          |
                    | OpenRefine-compatible CSVs   |
                    +------------------------------+
```

Operationally, the main CLI path is:

1. `maris_init` bootstraps `~/.marisco/`, downloads lookup tables, and downloads the NetCDF template.
2. `maris_to_nc` imports a handler module such as `marisco.handlers.helcom` and calls its `encode()` function.
3. The handler loads raw provider data, runs a `Transformer`, builds metadata with `GlobAttrsFeeder`, and writes a NetCDF file through `NetCDFEncoder`.
4. If needed, `nc_to_csv` or `netcdf2csv.decode()` projects the NetCDF artifact back into MARIS legacy CSV format for central database ingestion.

## 3. Layered Component Breakdown

### 3.1 Notebook / Generation Layer

This layer is the architectural foundation, not just tooling.

- `nbs/` is the authoring surface.
- `marisco/` is the generated execution surface.
- `marisco/_modidx.py` is the exported symbol manifest that ties notebooks to public API documentation.
- `token_saver.py` is the AI-safe bridge: it resolves a module, performs import-driven nbdev export, extracts notebook markdown, pairs it with exported Python, and emits a hybrid Markdown context.

`token_saver.py` matters architecturally because it protects SSOT discipline while still making notebook-driven code reviewable in low-token environments.

### 3.2 Configuration / Registry Layer

`nbs/api/configs.ipynb` and `marisco/configs.py` provide the canonical registry of MARIS semantics.

- `NC_VARS` maps handler-facing uppercase columns to NetCDF variable names.
- `NC_GROUPS` maps logical groups to NetCDF group names.
- `NC_DTYPES` defines the enum-backed categorical universe.
- `CSV_VARS` and `CSV_DTYPES` define the legacy CSV projection surface.
- `NC_GLOBAL_ATTRS` defines the allowed NetCDF global attribute names.
- `lut_path()`, `lut_fname()`, `cache_path()`, `nc_tpl_path()`, and `get_time_units()` locate packaged resources and template semantics.

This layer is what lets heterogeneous handlers converge on one stable encoding contract.

### 3.3 Ingestion / Facade Layer

Handlers are the provider-facing facades of the system.

- `helcom`, `ospar`, `tepco`, and `geotraces` are the primary operational handlers exposed by `marisco/cli/to_nc.py`.
- `maris_legacy` is a migration-oriented handler exposed separately by `marisco/cli/db_to_nc.py`.
- Each handler exports `encode(...)`, which gives the CLI a uniform entry point regardless of source complexity.

Representative handler families:

- `geotraces` is a wide-to-long, parser-heavy seawater pipeline with group dispatch into `SEAWATER` and `SUSPENDED_MATTER`.
- `helcom` and `ospar` are nomenclature-heavy, IMFA-driven pipelines over crawler-prepared tabular inputs.
- `tepco` is a multi-file reconciliation pipeline with provider-specific parsing, location fusion, and detection-limit normalization.
- `maris_legacy` is a reverse-ingestion bridge from the historical MARIS database dump into dataset-specific NetCDF artifacts.

### 3.4 Transformation / Parser Layer

This is the operational core of MARISCO.

#### Transformer model

`Transformer` accepts either:

- `Dict[str, pd.DataFrame]` for multi-group handlers, or
- a single `pd.DataFrame` for pre-split pipelines such as `geotraces`

It then applies ordered callbacks through `run_cbs()`.

#### Generic transformation primitives

The core callback library in `marisco.callbacks` provides reusable normalization building blocks:

- `PerGroupCB` for group-aware transformations
- `SanitizeLonLatCB` for coordinate validation
- `LowerStripNameCB` for canonical text normalization
- `RemapCB` for lookup-based normalization
- `SelectColumnsCB` and `RenameColumnsCB` for schema shaping
- `RemoveAllNAValuesCB` for record pruning
- `ParseTimeCB`, `EncodeTimeCB`, and `DecodeTimeCB` for temporal conversion
- `CompareDfsAndTfmCB` for change tracking
- `UniqueIndexCB` for row identity creation

#### Provider-specific parser walls

Handlers add provider-specific callbacks where generic ones are insufficient.

- `helcom` and `ospar` each define their own `ParseTimeCB` aligned to source-specific date quirks while still fitting the shared callback contract.
- `geotraces` adds callbacks for wide-to-long reshaping, unit extraction, filtering-status extraction, sampling-method extraction, longitude unshifting, and group dispatch.
- `tepco` adds callbacks for removing `約`, parsing range strings, reshaping, extracting value types, and remapping `VALUE` / `DL` / `DLV`.

#### IMFA and Remapper

`Remapper` in `marisco.utils` operationalizes MARISCO's recurring nomenclature workflow:

1. Inspect provider vocabulary
2. Match against MARIS lookup tables
3. Fix mismatches explicitly
4. Apply the frozen mapping through callbacks

This pattern appears repeatedly in handlers for nuclides, species, body parts, sediment types, and other enum-backed fields.

### 3.5 Metadata / Overlay Layer

`GlobAttrsFeeder` is the metadata twin of `Transformer`. It builds `obj.attrs` by running ordered callbacks over transformed dataframes.

Current live metadata components:

- `BboxCB` computes geospatial bounds from coordinates
- `DepthRangeCB` computes vertical coverage
- `TimeRangeCB` computes temporal coverage from encoded time
- `ZoteroClient` retrieves bibliography from the MARIS Zotero group library
- `ZoteroCB` injects `id`, `title`, `summary`, and `creator_name` from Zotero
- `INISClient` retrieves bibliography from the INIS API
- `InisCB` injects the same core fields and, when present, `references` and `metadata_link`
- `KeyValuePairCB` injects static overlays such as `keywords` and `publisher_postprocess_logs`
- `GlobAttrsFeeder` rejects attribute names not listed in `NC_GLOBAL_ATTRS`

This layer is where technical hospitality becomes explicit: messy provenance and bibliographic state are normalized into a stable global attribute surface rather than leaking into downstream encoding code.

#### Important current-truth note on bibliographic sources

The current exported metadata layer already supports more than one bibliographic source, but only part of the overall pipeline is source-neutral:

- `ZoteroCB` uses the Zotero item key as `id`.
- `InisCB` uses the INIS record identifier as `id` and may also emit `references` and `metadata_link`.
- Both callbacks normalize their output onto the same `GlobAttrsFeeder` surface: `id`, `title`, `summary`, and `creator_name`, with `creator_name` serialized as a JSON string.

This means the canonical NetCDF metadata contract is broader than "every dataset has a Zotero key", but it does not yet mean every downstream compatibility path is metadata-source-agnostic.

### 3.6 Encoding / Projection Layer

`NetCDFEncoder` is the canonical projection mechanism from normalized tables to MARIS NetCDF4.

Its responsibilities are:

- open the MARIS template from `nc_tpl_path()`
- copy root and group dimensions from the template
- map handler columns through `NC_VARS`
- create enum types from `NC_DTYPES` and lookup tables through `Enums`
- sanitize enum NaNs before writing
- copy variable attributes from the template
- write group data for each canonical sample type

This means the output file is not just a flat data dump. It is a schema-bearing artifact containing:

- data variables
- enum definitions
- template-defined variable metadata
- computed and fetched global attributes

### 3.7 Reverse Projection / Compatibility Layer

MARISCO's NetCDF artifact is canonical, but not the end of the institutional workflow.

- `NetCDFDecoder` remaps NetCDF variables back into human-readable tables.
- `netcdf2csv.decode()` applies additional compatibility callbacks for the MARIS master database path.
- `ValidateEnumsCB` checks whether a file's enum mappings still match current MARIS lookup tables.
- `AddZoteroArchiveLocationCB` injects the legacy `ref_id` bridge through a Zotero-specific archive lookup.
- `SampleIDConversionCB` handles the distinction between provider IDs and MARISCO-generated sample IDs.

The important asymmetry here is that NetCDF metadata accepts source-specific record identifiers, but the legacy CSV compatibility path still assumes a Zotero-resolvable record when it tries to populate `REF_ID`.

This layer exists because MARISCO modernizes the curation pipeline without severing compatibility with the legacy OpenRefine and central database ingestion path.

## 4. Cross-Cutting Concerns & Environment Safeguards

### Windows / Anaconda Environment Adaptation

The repository explicitly treats Windows behavior as an architectural concern, not an operational footnote.

- nbdev shell entry points such as `nbdev_export` are banned for AI agents on Windows
- the required export path is import-driven: `python -c "import nbdev.cli; nbdev.cli.nb_export(...)"`
- `token_saver.py` follows that import-first pattern automatically
- the knowledge base records file-lock sensitivity and `_modidx.py` regeneration concerns as normal recovery scenarios, not edge cases

The same applies to network retrieval design:

- `AGENTS.md`, `CLAUDE.md`, and the knowledge base require `curl.exe` fallback for Windows TLS EOF or connection-reset scenarios when implementing external API access
- the current exported INIS retrieval path is already curl-based, while the broader repository rule still frames this as a boundary concern rather than a decoder or encoder concern

### AI-Driven Development Guardrails

This repository binds AI behavior into the architecture itself.

- `AGENTS.md` is the top-priority operating policy
- `CLAUDE.md` reinforces notebook-safe exploration and nbdev discipline
- raw `.ipynb` ingestion is forbidden as a default workflow
- handler investigation must begin with `python token_saver.py handlers/<name>`
- generated modules under `marisco/` are not valid authoring surfaces

These rules are not merely process notes. They preserve the integrity of the SSOT model and reduce the risk of silent notebook/export/index divergence.

### Auditability as a First-Class Concern

MARISCO persists transformation intent, not just results.

- callback docstrings are collected into `tfm.logs`
- handlers inject those logs into `publisher_postprocess_logs`
- literate notebooks preserve why a mapping or sanitization exists
- `_modidx.py` preserves what the exported API surface actually is

This gives the project a rare but important property: data curation decisions remain inspectable after the pipeline has finished running.

### Architectural Summary

At its strongest, MARISCO is a four-part machine:

1. notebook-authored structural truth in `nbs/`
2. callback-driven normalization of heterogeneous marine radioactivity data
3. metadata overlay that makes outputs self-describing and citation-ready
4. template-based NetCDF projection with a backward-compatibility bridge to legacy CSV ingestion

The most important nuance from the current scan is that the canonical NetCDF metadata contract is already broader than Zotero alone: INIS-backed callbacks can emit the same core fields plus `references` / `metadata_link`. The remaining structural mismatch lives in the legacy CSV bridge, which still assumes a Zotero-oriented archive lookup for `REF_ID`.
