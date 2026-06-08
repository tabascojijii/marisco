# marisco Architecture and Roadmap Revamp

## 1. Purpose

This document replaces the previous roadmap with an implementation-oriented architecture for `marisco` that prioritizes:

1. Data Integrity
2. High Modularization
3. Technical Hospitality
4. Compatibility with the existing nbdev notebook-to-module workflow

The target state is not a generic workflow framework. It is a strict, source-aware, notebook-authored pipeline architecture where:

- `argparse` owns runtime entrance and operator ergonomics
- `pydantic` owns boundary validation and typed runtime contracts
- `prefect` owns orchestration, retries, logging, and task composition
- `nbdev` remains the single source of truth for Python module generation

---

## 2. What the Repository Does Today

## 2.1 Observed nbdev export pattern

The current repository is already organized around notebook export:

- `nbs/handlers/*.ipynb` exports dataset-specific handler modules into `marisco/handlers/*.py`
- `nbs/api/*.ipynb` exports shared library modules such as `configs.py`, `callbacks.py`, `encoders.py`, `metadata.py`, and `utils.py`
- `nbs/cli/*.ipynb` exports CLI modules into `marisco/cli/*.py`

This means the repo is **not** using “one notebook per entire application.” It is using:

- one notebook per exported module
- a mix of shared notebooks and source-specific handler notebooks

That pattern is solid and should be preserved.

## 2.2 Current entrypoint shape

The current CLI is built with `fastcore.script` rather than `argparse`.

Observed examples:

- `marisco.cli.to_nc` dynamically imports a handler and forwards `src` and `dest`
- `marisco.cli.init` bootstraps `~/.marisco`, writes a config file, and downloads LUTs/templates

This is flexible enough for demos, but too weak for strict runtime contracts.

## 2.3 Current handler shape

Each source notebook exports one source-specific handler module. That module typically contains:

- source URLs or local file defaults at module scope
- raw loader functions
- source-specific callback classes
- metadata assembly
- one `encode(...)` function that acts as the public entrypoint

Examples observed in current handlers:

- `helcom.py` hardcodes `src_dir`, `fname_out`, and a Zotero key
- `geotraces.py` hardcodes `fname_in` and `fname_out`
- `tepco.py` hardcodes three remote inputs and one output path
- `ospar.py` follows the same pattern as `helcom.py`

This is the core coupling problem: source configuration, loading, transformation, metadata, and orchestration are all mixed together inside handler modules.

---

## 3. Current Bottlenecks

## 3.1 Hardcoded runtime behavior

The current architecture leaks execution concerns into module scope:

- source URLs are defined as constants inside handlers
- output paths are defined inside handlers
- source-specific defaults are not modeled as typed runtime options
- CLI logic depends on knowing whether a handler expects `fname_in` or not

This makes composition brittle and discourages reuse.

## 3.2 External state dependency

The current config layer depends on:

- `~/.marisco`
- generated `configs.toml`
- runtime download of LUT files and NetCDF template assets

This is a direct threat to reproducibility and technical hospitality. A pipeline should not require hidden user-home bootstrapping before it can validate or transform data.

## 3.3 Weak typing at the data boundary

There is essentially no strict boundary model for external data.

Current behavior relies on:

- pandas reads
- implicit column assumptions
- downstream callback failures when required fields are absent or malformed

This is the wrong failure location. Validation must happen immediately after data enters the system.

## 3.4 Monolithic handler orchestration

Handlers currently behave like mini-applications. A single `encode()` call tends to do all of the following:

- fetch or read source data
- merge source tables
- transform records
- build global attrs
- instantiate `NetCDFEncoder`
- write final output

That is too much responsibility for one entrypoint and makes block-level reuse difficult.

## 3.5 Memory and compute pressure

Observed code-level risks:

- `Transformer` defaults to `inplace=False`, which copies DataFrames
- `NetCDFEncoder` hardcodes `complevel=9`
- large merges happen before there is any task-level orchestration or chunk strategy
- cleanup, retry, and staging are not first-class workflow concepts

These issues are exactly where Prefect should help.

## 3.6 Notebook sprawl without architectural boundaries

The repo is correctly notebook-first, but several notebooks currently mix:

- reusable library code
- source-specific logic
- smoke examples
- path-bound demonstration code

nbdev is not the problem here. The missing piece is a clearer contract for what each notebook is allowed to own.

---

## 4. Architectural Decision

The new execution stack is:

```text
Argparse -> Pydantic -> Prefect -> Domain Blocks -> Encoder
```

More precisely:

```text
CLI arguments
  -> typed run options
  -> source adapter selection
  -> Prefect flow
  -> fetch/read task
  -> boundary validation task
  -> normalization task(s)
  -> transformation task(s)
  -> metadata task
  -> encoding task
  -> output validation task
  -> atomic publish / cleanup
```

### Design rule

No external payload may cross the pipeline boundary unvalidated.

That rule applies equally to:

- Zotero metadata responses
- future INIS API payloads
- CSV rows
- Excel rows
- intermediate normalized records built from source files

---

## 5. Target Layering

## 5.1 Layer 1: Argparse for entrance flexibility

`argparse` will replace `fastcore.script` as the primary runtime entry layer.

Its job is intentionally narrow:

- parse operator intent
- choose source and mode
- resolve environment selection
- construct typed run options
- start the correct Prefect flow

Typical arguments:

```bash
marisco to-nc --source helcom --input ./data --output ./out/helcom.nc
marisco to-nc --source inis --query "Baltic Cs-137" --limit 10 --mode dry-run
marisco to-nc --source zotero --record-key 26VMZZ2Q --output ./out/zotero.nc
```

Recommended common flags:

- `--source`
- `--input`
- `--output`
- `--mode`
- `--limit`
- `--chunk-size`
- `--complevel`
- `--log-level`
- `--retries`
- `--dry-run`
- `--validate-only`

### Important boundary

`argparse` should not contain business logic. It only builds typed input models and hands them to the orchestration layer.

## 5.2 Layer 2: Pydantic for contracts and fail-fast validation

Pydantic has two separate jobs in the new architecture.

### Job A: Runtime configuration contracts

Examples:

- `RunOptions`
- `FlowOptions`
- `OutputOptions`
- source-specific option models such as `HelcomOptions`, `InisOptions`, `ZoteroOptions`

### Job B: Data boundary contracts

Examples:

- raw external response models
- normalized source record models
- metadata response models
- final domain models before DataFrame materialization or encoding

### Validation policy

Validation occurs at the earliest stable boundary:

1. Raw external response envelope
2. Raw source record
3. Normalized internal record
4. Output artifact summary

Failures at stages 1 through 3 are fatal and should not be retried unless the failure is transport-related.

## 5.3 Layer 3: Prefect for orchestration

Prefect introduces explicit operational structure:

- `@task` for atomic transformation/fetch/validation/encoding steps
- `@flow` for dataset orchestration
- built-in logging
- selective retries
- visibility into task boundaries
- future deployment compatibility if orchestration expands

### Retry policy

Retryable:

- API transport failure
- timeout
- temporary remote unavailability
- transient file lock or network read failure

Not retryable:

- schema mismatch
- required column missing
- invalid enum value
- invalid runtime arguments
- deterministic transform failure

## 5.4 Layer 4: nbdev as the authoring system

All architectural changes must continue to originate in `nbs/`.

The generated `.py` files remain artifacts, not authorship targets.

That means:

- we do not break the notebook export system
- we make notebook boundaries cleaner
- we move orchestration, models, and adapters into notebook-exported modules

---

## 6. Modular “Block-like” Pipeline Design

## 6.1 Principle

Every reusable pipeline step becomes an isolated block, implemented as a Prefect task plus a typed input/output contract where useful.

Examples:

- fetch source payload
- read CSV chunk
- read Excel sheet
- validate external record
- normalize column names
- map units
- map nuclides
- enrich metadata
- encode NetCDF
- validate generated output

Each block should be:

- single-purpose
- source-agnostic where possible
- independently testable
- composable into multiple flows

## 6.2 Source adapter pattern

To support swapping Zotero for INIS without rewriting downstream processing, source-specific logic should be isolated in adapters.

Recommended pattern:

```text
source adapter
  -> fetch raw payload
  -> validate raw payload
  -> normalize into internal record model
  -> hand off to shared transform blocks
```

Examples:

- `fetch_zotero_records_task`
- `fetch_inis_records_task`
- `normalize_external_record_task`

Both source adapters should emit the same internal contract once normalized.

## 6.3 Shared downstream core

Once data is normalized, downstream tasks should be source-independent whenever possible:

- `partition_records_task`
- `build_dataframe_task`
- `apply_common_transforms_task`
- `build_global_attrs_task`
- `encode_netcdf_task`
- `validate_netcdf_task`

This is the exact point of “block-like” reusability.

---

## 7. Validation Strategy for INIS Migration

The upcoming INIS migration should be designed now, not bolted on later.

## 7.1 Boundary-first strategy

For INIS, introduce three model layers:

### Layer A: Raw response models

These validate:

- envelope shape
- pagination structure
- required top-level keys
- field presence and type sanity

### Layer B: Source-normalized record models

These convert INIS-specific field names into a stable internal representation.

Examples:

- `title`
- `authors`
- `publication_year`
- `abstract`
- `keywords`
- `source_identifier`
- `geo_refs`
- `measurement_records`

### Layer C: marisco domain models

These express what the pipeline truly needs, independent of source naming.

Examples:

- `ExternalDatasetRecord`
- `MeasurementRecord`
- `LocationRecord`
- `ReferenceMetadata`

## 7.2 Failure behavior

For INIS, fail immediately when:

- a required field is absent
- field type coercion fails
- an enum/domain value is invalid and cannot be normalized safely
- the API response no longer matches the modeled schema

The flow must stop before transformation tasks mutate or aggregate invalid content.

## 7.3 Quarantine option

For high-volume ingestion, a controlled quarantine path may be added later:

- valid records proceed
- invalid records are emitted to a structured error report

But this should be an explicit mode such as `--mode quarantine`, not the default. Default behavior remains fail-fast.

---

## 8. Notebook Architecture Recommendation

## 8.1 Recommendation

Do **not** make one notebook equal one entire end-to-end flow plus all reusable components.

Do **not** put every shared function into one giant utility notebook.

The recommended pattern is:

- shared component notebooks for reusable models, tasks, and infrastructure
- one source notebook per source adapter / source flow entrypoint
- one CLI notebook family for entrypoints

In practice:

### Shared notebooks

- `nbs/api/config.ipynb`
- `nbs/pipeline/models.ipynb`
- `nbs/pipeline/tasks.ipynb`
- `nbs/pipeline/flows.ipynb`
- `nbs/sources/common.ipynb`

### Source notebooks

- `nbs/handlers/helcom.ipynb`
- `nbs/handlers/ospar.ipynb`
- `nbs/handlers/tepco.ipynb`
- `nbs/handlers/geotraces.ipynb`
- future `nbs/handlers/inis.ipynb`
- future `nbs/handlers/zotero.ipynb`

## 8.2 Practical rule

Each source notebook should own:

- source-specific option models if they are small
- source-specific fetch/read logic
- source-specific normalization logic
- one public flow entrypoint or one public adapter entrypoint

Each source notebook should **not** own:

- generic run option models
- generic retry logic
- generic output publishing
- generic NetCDF write policy
- generic validation helpers

## 8.3 Best-fit mapping for this repo

For this codebase, the cleanest mapping is:

- one notebook per exported module
- one exported module per concern
- source notebooks remain thin and import shared blocks

That keeps nbdev happy and reduces cross-notebook duplication.

---

## 9. Proposed Package Structure

```text
marisco/
  __init__.py
  config.py
  cli/
    __init__.py
    main.py
    to_nc.py
    validate.py
  pipeline/
    __init__.py
    models.py
    tasks.py
    flows.py
    io.py
    validation.py
  sources/
    __init__.py
    base.py
    zotero.py
    inis.py
  handlers/
    __init__.py
    helcom.py
    ospar.py
    tepco.py
    geotraces.py
  encoders.py
  metadata.py
  callbacks.py
  configs.py
  data/
    luts/
    nc/
    cdl/
```

Recommended notebook structure:

```text
nbs/
  api/
    config.ipynb
    callbacks.ipynb
    encoders.ipynb
    metadata.ipynb
    configs.ipynb
  cli/
    main.ipynb
    to_nc.ipynb
    validate.ipynb
  pipeline/
    models.ipynb
    tasks.ipynb
    flows.ipynb
    io.ipynb
    validation.ipynb
  sources/
    base.ipynb
    zotero.ipynb
    inis.ipynb
  handlers/
    helcom.ipynb
    ospar.ipynb
    tepco.ipynb
    geotraces.ipynb
```

---

## 10. Typed Runtime Models

Illustrative shape:

```python
from pathlib import Path
from typing import Literal, Optional
from pydantic import BaseModel, Field, HttpUrl


class OutputOptions(BaseModel):
    output_path: Path
    complevel: int = Field(default=4, ge=0, le=9)
    overwrite: bool = False
    staging_dir: Optional[Path] = None


class FlowOptions(BaseModel):
    mode: Literal["run", "dry-run", "validate-only"] = "run"
    chunk_size: int = Field(default=50_000, gt=0)
    retries: int = Field(default=2, ge=0, le=10)
    log_level: str = "INFO"


class RunOptions(BaseModel):
    source: Literal["helcom", "ospar", "tepco", "geotraces", "zotero", "inis"]
    output: OutputOptions
    flow: FlowOptions


class HelcomOptions(RunOptions):
    source: Literal["helcom"] = "helcom"
    input_dir: str | HttpUrl


class InisOptions(RunOptions):
    source: Literal["inis"] = "inis"
    query: str
    limit: int = Field(default=100, gt=0, le=10_000)
```

These models become the only legal inputs to the orchestration layer.

---

## 11. Prefect Task Taxonomy

Recommended task families:

## 11.1 Boundary tasks

- `fetch_remote_payload_task`
- `read_csv_task`
- `read_excel_sheet_task`
- `validate_raw_payload_task`
- `validate_raw_record_task`

## 11.2 Normalization tasks

- `normalize_columns_task`
- `normalize_record_task`
- `normalize_datetime_task`
- `normalize_coordinates_task`

## 11.3 Domain transform tasks

- `map_nuclides_task`
- `map_units_task`
- `map_detection_limit_task`
- `reshape_wide_to_long_task`
- `build_sample_ids_task`

## 11.4 Output tasks

- `build_global_attrs_task`
- `encode_netcdf_task`
- `validate_netcdf_task`
- `publish_output_task`
- `cleanup_task`

---

## 12. PoC Blueprint: Notebook Skeleton

The following is the recommended shape for a notebook-exported handler module.

```python
#| default_exp handlers.inis

#| export
from __future__ import annotations

from pathlib import Path
from typing import Literal

import pandas as pd
from pydantic import BaseModel, Field, ValidationError
from prefect import flow, task, get_run_logger

from marisco.encoders import NetCDFEncoder


#| export
class InisRunOptions(BaseModel):
    source: Literal["inis"] = "inis"
    query: str
    output_path: Path
    limit: int = Field(default=100, gt=0, le=10_000)
    complevel: int = Field(default=4, ge=0, le=9)
    dry_run: bool = False


#| export
class InisRawRecord(BaseModel):
    record_id: str
    title: str
    publication_year: int | None = None
    abstract: str | None = None


#| export
class NormalizedRecord(BaseModel):
    source_id: str
    title: str
    year: int | None = None
    abstract: str | None = None


#| export
@task(retries=2, retry_delay_seconds=3)
def fetch_inis_records(options: InisRunOptions) -> list[dict]:
    logger = get_run_logger()
    logger.info("Fetching INIS records for query=%s", options.query)
    # Replace this stub with the actual API client call.
    return [
        {
            "record_id": "inis-001",
            "title": "Example record",
            "publication_year": 2025,
            "abstract": "Example abstract",
        }
    ]


#| export
@task
def validate_raw_records(payload: list[dict]) -> list[InisRawRecord]:
    return [InisRawRecord.model_validate(item) for item in payload]


#| export
@task
def normalize_records(records: list[InisRawRecord]) -> list[NormalizedRecord]:
    normalized = []
    for record in records:
        normalized.append(
            NormalizedRecord(
                source_id=record.record_id,
                title=record.title.strip(),
                year=record.publication_year,
                abstract=record.abstract,
            )
        )
    return normalized


#| export
@task
def build_dataframe(records: list[NormalizedRecord]) -> pd.DataFrame:
    return pd.DataFrame([record.model_dump() for record in records])


#| export
@task
def validate_dataframe_contract(df: pd.DataFrame) -> pd.DataFrame:
    required = {"source_id", "title"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required normalized columns: {sorted(missing)}")
    return df


#| export
@task
def encode_output(df: pd.DataFrame, options: InisRunOptions) -> Path:
    # Placeholder example. Real implementation will map records into MARIS-ready groups.
    dfs = {"SEAWATER": df}
    encoder = NetCDFEncoder(
        dfs=dfs,
        dest_fname=str(options.output_path),
        global_attrs={"title": "INIS export"},
        verbose=False,
    )
    encoder.encode()
    return options.output_path


#| export
@flow(name="inis-to-netcdf")
def run_inis_flow(options: InisRunOptions) -> Path | None:
    payload = fetch_inis_records(options)
    raw_records = validate_raw_records(payload)
    normalized = normalize_records(raw_records)
    df = build_dataframe(normalized)
    df = validate_dataframe_contract(df)

    if options.dry_run:
        return None

    return encode_output(df, options)
```

### Why this shape works

- the notebook exports a clean Python module
- all external data is validated immediately
- each task is isolated and reusable
- orchestration is explicit
- source-specific logic is thin
- downstream shared tasks can later move into `marisco.pipeline.tasks`

---

## 13. CLI Direction

Recommended CLI structure:

```text
marisco to-nc --source helcom --input ./raw --output ./out/helcom.nc
marisco to-nc --source geotraces --input ./geotraces.csv --output ./out/geotraces.nc
marisco to-nc --source inis --query "marine radionuclides" --limit 50 --output ./out/inis.nc
marisco validate --source inis --query "marine radionuclides"
```

Recommended implementation pattern:

1. Parse arguments with `argparse`
2. Build the correct Pydantic options model
3. Dispatch to the correct Prefect flow
4. Return structured exit codes

### Exit code policy

- `0`: success
- `2`: CLI argument error
- `3`: validation error
- `4`: remote fetch or I/O failure
- `5`: transform or encoding failure

---

## 14. Specific Changes Required by Area

## 14.1 Config and assets

Move toward:

- bundled package assets
- `importlib.resources`
- typed settings

Move away from:

- `maris_init`
- `~/.marisco`
- runtime LUT/template download
- path lookups backed by generated home-directory config

## 14.2 Handler refactor

Every handler should be decomposed into:

- source options
- load/fetch tasks
- validation tasks
- normalize tasks
- dataset-specific mapping tasks
- shared encode/publish tasks

The public API should shift from loose `encode(fname_in=..., fname_out=...)` patterns to typed flow entrypoints.

## 14.3 Encoder policy

`NetCDFEncoder` should stop hardcoding compression behavior.

It should accept runtime write options such as:

- compression level
- atomic write staging path
- overwrite policy

## 14.4 Transformer policy

The current `Transformer(..., inplace=False)` default is not aligned with memory pressure concerns.

Recommended direction:

- default to in-place operation in heavy data paths
- only copy when a task contract or isolation requirement justifies it
- make mutation policy explicit in task boundaries

---

## 15. Roadmap

## Phase 1. Document and contract the new boundaries

Deliverables:

- this revised architecture document
- typed runtime model design
- source adapter contract design
- notebook ownership rules

Success criteria:

- shared understanding of the target execution stack

## Phase 2. Remove home-directory bootstrapping assumptions

Deliverables:

- new `config.py`
- bundled asset loading via `importlib.resources`
- retirement plan for `maris_init`

Success criteria:

- pipeline can run without `~/.marisco` initialization

## Phase 3. Introduce typed CLI models and `argparse`

Deliverables:

- new CLI entrypoints using `argparse`
- `RunOptions` and source-specific option models
- `validate` mode

Success criteria:

- no handler is invoked from loosely typed raw CLI strings alone

## Phase 4. Introduce Prefect orchestration skeleton

Deliverables:

- `pipeline/models.py`
- `pipeline/tasks.py`
- `pipeline/flows.py`
- structured retries and logging

Success criteria:

- at least one source runs through Prefect flow and tasks

## Phase 5. Pilot a single handler migration

Recommended first pilot: `HELCOM`

Why:

- it already exhibits loader complexity
- it has merge pressure
- it contains source-specific remapping logic worth modularizing

Deliverables:

- HELCOM loader task split
- Pydantic boundary validation for loaded records
- shared downstream tasks extracted where possible

Success criteria:

- HELCOM runs through typed Prefect orchestration with no module-level execution assumptions

## Phase 6. Migrate remaining handlers

Targets:

- OSPAR
- TEPCO
- GEOTRACES

Success criteria:

- each handler is reduced to a thin source adapter plus source flow entrypoint

## Phase 7. Add INIS adapter

Deliverables:

- INIS raw response models
- INIS normalization tasks
- shared downstream reuse

Success criteria:

- INIS can be plugged into the same downstream architecture without custom orchestration logic

## Phase 8. Tighten output integrity and observability

Deliverables:

- NetCDF output validation task
- atomic staging and publish
- richer Prefect logging
- structured error reports

Success criteria:

- failures are stage-specific, inspectable, and safe

---

## 16. Recommended First Implementation Sequence

1. Add `nbs/api/config.ipynb` for bundled assets and typed settings
2. Add `nbs/pipeline/models.ipynb`
3. Add `nbs/pipeline/tasks.ipynb`
4. Add `nbs/pipeline/flows.ipynb`
5. Replace `fastcore.script` CLI entrypoints with `argparse` notebooks
6. Migrate HELCOM as the first typed Prefect flow
7. Remove `maris_init` and home-directory LUT bootstrapping
8. Introduce `InisRunOptions`, `InisRawRecord`, and normalization models before the actual INIS connector ships

---

## 17. Final Recommendation

The right future for `marisco` is not “more flexibility everywhere.” It is:

- strict validation at the boundary
- flexible composition at the task level
- thin, source-specific adapters
- shared downstream blocks
- notebook-authored modules with clear ownership

In short:

`marisco` should evolve from **handler-centered scripts** into a **typed, notebook-authored orchestration system**.

The governing rule is simple:

**Let operators be flexible at the CLI, but let data be unforgiving at the boundary.**
