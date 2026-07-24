# ---
# jupyter:
#   jupytext:
#     formats: ipynb,.pct.py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.5
#   kernelspec:
#     display_name: python3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # MARIS Data Guide
#
# > A reference for data providers and data users

# %% [markdown]
# ## About MARIS
#
# The [IAEA Marine Radioactivity Information System (MARIS)](https://maris.iaea.org) provides open access to radioactivity measurements in marine environments worldwide. Developed and maintained by the [IAEA Marine Environmental Laboratories](https://www.iaea.org/about/organizational-structure/department-of-nuclear-sciences-and-applications/division-of-iaea-environment-laboratories) in Monaco, MARIS integrates measurements from regional monitoring programmes, event-driven datasets, and historical scientific literature into a single, freely accessible database.

# %% [markdown]
# ## Sample types
#
# All measurements are organized into four sample type groups:
#
# | Sample type | What it covers | Primary unit |
# |---|---|---|
# | **SEAWATER** | Dissolved and filtered water samples (seawater and brackish water) | Bq m⁻³ |
# | **BIOTA** | Marine organisms — fish, shellfish, seaweed, and other biota | Bq kg⁻¹ (wet or dry weight) |
# | **SEDIMENT** | Bottom sediments, including core profiles | Bq kg⁻¹ or Bq m⁻² |
# | **SUSPENDED** | Suspended particulate matter in the water column | Bq kg⁻¹ |

# %% [markdown]
# ## Measurement fields
#
# Each record contains:
#
# - **Location** — latitude, longitude, station name, named area
# - **Time** — sampling date (encoded as seconds since 1970-01-01 UTC in NetCDF4)
# - **Depth** — sampling depth and total water column depth
# - **Nuclide** — identity via a MARIS standard ID linked to a lookup table
# - **Activity** — measured value or minimum detectable activity (MDA)
# - **Uncertainty** — 1σ absolute uncertainty in the same unit as the activity
# - **Detection limit flag** — `=` (measured), `<` (below detection limit), `ND` (not detected), or `DE` (derived/aggregated)
# - **Unit** — MARIS standard unit ID from a lookup table
# - Sample-type-specific fields: species and body part (BIOTA); sediment type and core interval (SEDIMENT); filter status (SEAWATER)
# - Method fields: sampling method, preparation method, counting method
#
# → See [Field Definitions](field-definition.ipynb) for the complete field reference.  
# → See [Sample ID Coverage](sample-id-coverage.ipynb) for the status of `SMP_ID` / `SMP_ID_PROVIDER` capture across all handlers.

# %% [markdown]
# ## Nomenclature and lookup tables
#
# Enumerated fields (nuclide identity, species, units, sediment type, body part, etc.) are stored as integer IDs referencing standardised lookup tables maintained by MARIS. This design ensures consistency across datasets from different providers.
#
# | Field | Lookup table |
# |---|---|
# | Nuclide identity | `dbo_nuclide.xlsx` |
# | Unit | `dbo_unit.xlsx` |
# | Species | `dbo_species.xlsx` |
# | Biological group | derived from `dbo_species.xlsx` |
# | Body part | `dbo_bodypar.xlsx` |
# | Sediment type | `dbo_sedtype.xlsx` |
# | Detection limit | `dbo_detectlimit.xlsx` |
# | Laboratory | `dbo_lab.xlsx` |
# | Sampling method | `dbo_sampmet.xlsx` |
# | Preparation method | `dbo_prepmet.xlsx` |
# | Counting method | `dbo_counmet.xlsx` |
# | Named area | `dbo_area.xlsx` |

# %% [markdown]
# ## Data formats
#
# MARIS data is available in two formats:
#
# **NetCDF4** (primary format)  
# Each file is self-contained: measurements, variable metadata, lookup tables for all used nomenclatures, and bibliographic information are bundled together. Data is organized into groups by sample type. The `publisher_postprocess_logs` global attribute records every curation step applied to the dataset, providing a permanent audit trail.
#
# **CSV** (legacy format for database import)  
# Flat files with one file per sample type, compatible with the MARIS master database ingestion pipeline.

# %% [markdown]
# ## How data is curated
#
# Data from providers arrives in many formats and uses provider-specific nomenclature. Before entering MARIS, each dataset is processed through the marisco curation pipeline:
#
# 1. **Nomenclature mapping** — nuclide names, species names, body parts, and sediment types are mapped to MARIS standard IDs using fuzzy-matched lookup tables, with manual review of uncertain matches.
# 2. **Unit standardisation** — seawater activities are converted to Bq m⁻³; biota activities carry a wet-weight or dry-weight flag; uncertainties are expressed as 1σ absolute values.
# 3. **Coordinate and date validation** — coordinates are converted to decimal degrees; dates are parsed to a common datetime; invalid or missing values are dropped.
# 4. **Detection limit encoding** — provider-specific flags are mapped to the four MARIS standard codes (`=`, `<`, `ND`, `DE`).
# 5. **Audit trail** — every curation step is logged and stored in the NetCDF4 file's `publisher_postprocess_logs` global attribute.

# %% [markdown]
# ## Available datasets
#
# | Dataset | Provider | Sample types | Coverage |
# |---|---|---|---|
# | [MARIS Legacy](../handlers/maris_legacy.ipynb) | MARIS Master Database | All types | Global, historical |
# | [HELCOM](../handlers/helcom.ipynb) | HELCOM MORS | SEAWATER, BIOTA, SEDIMENT | Baltic Sea |
# | [OSPAR](../handlers/ospar.ipynb) | ODIMS OSPAR | BIOTA | NE Atlantic |
# | [TEPCO](../handlers/tepco.ipynb) | Fukushima monitoring (TEPCO / NRA) | SEAWATER, BIOTA, SEDIMENT | NW Pacific |
# | [GEOTRACES](../handlers/geotraces.ipynb) | BODC GEOTRACES IDP2021 | SEAWATER | Global |
#
# For guides on working with these datasets and writing new handlers, see the [How-to guides](../how-to/mifa-pattern.ipynb) section.
