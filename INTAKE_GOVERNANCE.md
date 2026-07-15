# Intake Boundary Governance

> 💡 This document is normative for all YAML-driven handler work in `marisco 3.0`.
>
> Its purpose is to preserve the architectural boundary introduced in the modular pipeline under `marisco/handlers/pipeline/` and to prevent structural drift, provider-specific bloat, and silent schema corruption.

These rules apply to every new dataset integrated through:

- `config/handlers/{dataset}.yaml`
- `config/handlers/{dataset}_loader.py`
- `marisco/handlers/general.py`
- `marisco/handlers/pipeline/*.py`

> 🚨 A pull request that violates this document must not be merged.

---

## The Architectural Triad

marisco 3.0 is built on a strict 3-tier boundary. Each tier has one job only.

```text
Raw Provider Artifact
(ZIP / XLSX / CSV / messy workbook / mixed cells)
        |
        |  physical ingestion + cleansing only
        v
config/handlers/{dataset}_loader.py
load_and_cleanse(cfg: HandlerConfig) -> dict[str, pd.DataFrame]
        |
        |  raw-schema but physically clean tables
        v
config/handlers/{dataset}.yaml
HandlerConfig.from_yaml(...)
        |
        |  declarative mapping / melt / nomenclature contract
        v
marisco/handlers/pipeline/
  contracts.py   -> logical schema
  intake.py      -> IntakePlan + loader dispatch
  gates.py       -> Gate 1 + Gate 2
  assembly.py    -> preflight/finalize pipeline assembly
  output.py      -> required-column guard + NetCDF write
        |
        |  canonical MARIS DataFrames
        v
NetCDFEncoder.encode()
        |
        v
Binary NetCDF4 output
```

### 1. The Disposable Loader [THE HOW]

| Field | Rule |
| --- | --- |
| Location | `config/handlers/{dataset}_loader.py` |
| Required Shape | Accepts `cfg: HandlerConfig`, Returns `dict[str, pd.DataFrame]` (e.g., `{"SEAWATER": df}`) |
| Scope | Physical boundary ingestion only |

The loader is responsible for physical boundary ingestion only. It may open ZIP archives, select workbook sheets, strip spreadsheet artifacts, normalize broken cell formats, and remove non-measurement noise.

The loader is disposable by design. It is allowed to be dataset-specific, ugly, and local, because its purpose is to absorb one provider’s file physics without contaminating the shared engine.

Typical physical tasks include:

| Typical Task | Example |
| --- | --- |
| Network fetch | `requests.get(cfg.url, timeout=60)` |
| Archive handling | `zipfile.ZipFile(...)` |
| Workbook loading | `pd.read_excel(..., sheet_name="Data")` |
| Datetime normalization | `pd.to_datetime(..., format="mixed", utc=True)` |
| Numeric normalization | `pd.to_numeric(..., errors="raise")` |
| Noise removal | Dropping columns such as workbook notes, references, tracer labels, or merged-cell debris |

> 🚨 The loader must not become a second pipeline.

### 2. The Declarative Contract [THE WHAT]

| Field | Rule |
| --- | --- |
| Location | `config/handlers/{dataset}.yaml` |
| Nature | Zero execution logic |
| Parsed By | `HandlerConfig.from_yaml(...)` in `marisco/handlers/pipeline/contracts.py` |

This file contains zero execution logic. It is a typed declaration of intent, parsed by `HandlerConfig.from_yaml(...)` in `marisco/handlers/pipeline/contracts.py`.

Its job is to describe:

| Domain | YAML Responsibility |
| --- | --- |
| Provider identity | `provider metadata / data_source` |
| Canonical bridge | `columns / rename_cols / normalize_case` |
| Time materialization | `parse_datetime / time_format` |
| Wide-to-long structure | `melt (meta_cols & spec)` |
| Controlled remapping | `unit_conversions / nomenclatures (nuclide_lut, unit_lut, lab_lut)` |
| Output metadata | `output (global_attrs, keywords)` |
| Extension points | `optional loader paths, pre_cbs, and post_cbs` |

The YAML is the structural bridge between raw cleansed provider columns and the MARIS canonical model. This is where a column such as `Latitude_degN` becomes `LAT`.

### 3. The Stateless Core Engine [THE REGULATOR]

| Field | Rule |
| --- | --- |
| Location | `marisco/handlers/pipeline/` |
| Principle | Agnostic to provider file physics |
| Must Not Know | Excel layouts, nested ZIP formats, or how to strip provider footnotes |

This layer is intentionally agnostic to provider file physics. It must not know Excel layouts, nested ZIP formats, or how to strip provider footnotes. Its responsibilities are fixed:

| Module | Fixed Responsibility |
| --- | --- |
| `contracts.py` | Defines `HandlerConfig` / `PluginSpec`. Computes `missing_required_columns`. Validates NetCDF attributes via `ensure_known_global_attrs(...)`. |
| `intake.py` | Defines `IntakePlan`. Dispatches generic delimited loading via `load_data()`. Rejects unsupported Excel defaults and dispatches custom loaders through `call_loader()`. |
| `gates.py` | Runs Gate 1 in `load_handler_config(...)`. Runs Gate 2 in `gap_check(...)` to emit fail-fast diagnostics when canonical columns are absent, null, or empty. |
| `assembly.py` | Builds the standard callback chain. Splits execution into pre-lossy and post-lossy phases via `run_preflight(...)` and `run_finalize(...)`. |
| `output.py` | Revalidates required columns via `validate_required_columns(...)`. Drops non-NetCDF noise through `project_netcdf_columns(...)`. Serializes via `write_netcdf(...)`. |

---

## Execution and Validation Model

The public orchestrator is `marisco/handlers/general.py`.

### `verify(yaml_path: str | Path, fname_out: str = None) -> PipelineState`

The non-writing validation path. It enforces both validation gates:

| Gate | Enforcement |
| --- | --- |
| Gate 1 | YAML type validation through Pydantic in `_RawHandlerContract.model_validate(...)` and global attribute vocabulary checks |
| Gate 2 | Deep processed-DataFrame consistency validation through `gap_check(cfg, state.dfs)`, blocking on nulls or empty payloads in critical fields (`LAT`, `LON`, `TIME`) |

### `encode(yaml_path: str | Path, fname_out: str = None) -> None`

Performs the full regulated production path:

```text
_load_cfg(...) ➔ _init_state(...) ➔ _run_preflight(...) ➔ _run_finalize(...) ➔ write_netcdf(...)
```

---

## Strict Codified Commandments

### Loader Commandments

Inside `config/handlers/{dataset}_loader.py`:

| ✅ DO | ❌ DO NOT |
| --- | --- |
| Do implement a single dataset-specific function: `load_and_cleanse(cfg: HandlerConfig, grp: str = "SEAWATER") -> dict[str, pd.DataFrame]` | Do not rename raw provider columns to MARIS canonical keys (`LAT`, `LON`, `TIME`, `VALUE`) inside Python |
| Do explicitly target workbook sheets with `sheet_name=...` | Do not hardcode MARIS lookup integers such as nuclide IDs, unit IDs, or lab IDs in Python |
| Do use `pd.to_datetime(..., format="mixed", utc=True)` when provider date cells are mixed or unstable | Do not implement declarative wide-to-long melt logic or nomenclature remapping in the loader |
| Do use `pd.to_numeric(..., errors="raise")` for numeric fields so rogue string garbage fails immediately | Do not encode provider logic as hidden callback behavior or write NetCDF-aware logic |
| Do strip quotes, blank-string artifacts, and cell remnants |  |
| Do drop non-MARIS measurement noise before the shared pipeline begins |  |
| Do return a physically clean raw-schema DataFrame dictionary keyed by MARIS group name |  |

### YAML Contract Commandments

Inside `config/handlers/{dataset}.yaml`:

| ✅ DO | ❌ DO NOT |
| --- | --- |
| Do declare `loader:` when the dataset requires non-delimited ingestion or custom boundary cleansing | Do not embed string parsing, workbook repair instructions, or type-casting procedures in YAML |
| Do map raw cleansed provider columns to canonical MARIS fields under `columns:` | Do not embed Python execution snippets or shell commands in YAML |
| Do define `parse_datetime:` and `time_format:` when the shared parser should materialize `TIME` | Do not hardcode physical cleansing steps in callback declarations |
| Do define `melt.meta_cols` and `melt.spec` for wide-to-long nuclide conversion |  |
| Do define `nomenclatures:` (`nuclide_lut`, `unit_lut`, `lab_lut`) and `output.global_attrs` declaratively |  |

### Core Engine Commandments

Inside `marisco/handlers/pipeline/`:

| ✅ DO | ❌ DO NOT |
| --- | --- |
| Do keep `IntakePlan` and default intake limited to generic delimited loading | Do not add provider-specific Excel parsing or ZIP stream handling to the shared core modules |
| Do preserve Gate 1 and Gate 2 as mandatory, non-bypassable checks | Do not teach the core engine about one provider’s broken headers, footnotes, or local date oddities |
| Do keep `output.py` focused on final invariants, attribute assembly, and serialization |  |

---

## Border Patrol Review Checklist (Mandatory for PRs)

Every pull request that touches handler ingestion must be blocked or approved using the following checks:

- [ ] **Check 1: Leakage of Logic**
Question: Does the custom loader file contain strings like `LAT`, `LON`, `TIME`, `VALUE`, or explicit MARIS lookup keys and IDs?
Decision: If YES, REJECT the pull request. The loader is a physical cleanser, not a logical contract executor.

- [ ] **Check 2: Leakage of Physics**
Question: Does `gates.py`, `intake.py`, `assembly.py`, `output.py`, or any shared callback know how to parse a specific provider workbook or open zipped streams?
Decision: If YES, REJECT the pull request. Provider file physics must remain isolated in the loader.

- [ ] **Check 3: Schema Deviations**
Question: Does the pipeline bypass `IntakePlan`, `HandlerConfig.from_yaml(...)`, Gate 1, Gate 2, or the guarded `write_netcdf(...)` path?
Decision: If YES, REJECT the pull request.

---

## Final Principle

> 🚨 The success of marisco 3.0 depends on disciplined asymmetry: loaders are allowed to be disposable, YAML contracts are required to be declarative, and the core engine is required to remain stateless and provider-blind. Any contribution that collapses these roles is a regression.
