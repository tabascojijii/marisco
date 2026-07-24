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
# # Sample ID Coverage
# > Status of `SMP_ID` and `SMP_ID_PROVIDER` capture across all marisco handlers

# %% [markdown]
# ## Background
#
# Every measurement row in a MARIS NetCDF4 file requires two identity fields:
#
# | MARISCO column | NetCDF variable | CSV variable | Purpose |
# |---|---|---|---|
# | `SMP_ID` | `id` *(dimension)* | — | Marisco-generated sequential integer; unique within a sample-type group in a given file |
# | `SMP_ID_PROVIDER` | `id_provider` | `samplabcode` | Original sample identifier supplied by the data provider; stored verbatim; empty when the provider does not supply one |
#
# `SMP_ID` is the NetCDF4 dimension — every group must have it and it must be unique within that group.  
# `SMP_ID_PROVIDER` is optional from the data-model perspective, but should always be populated when the provider ships an identifier, as it enables traceability back to the source dataset.

# %% [markdown]
# ## Status summary
#
# | Handler | `SMP_ID` | `SMP_ID_PROVIDER` | Provider has IDs? | Notes |
# |---|---|---|---|---|
# | **helcom** | ✅ auto-incremented per group | ✅ from `key` column | Yes | Reference implementation |
# | **ospar** | ✅ auto-incremented per group | ✅ from `sample id` column | Yes | — |
# | **geotraces** | ✅ auto-incremented per group | ✅ from `BODC Bottle Number:INTEGER` | Yes | Fixed: was incorrectly placed in `SMP_ID` |
# | **tepco** | ✅ auto-incremented (SEAWATER only) | ⚠️ empty string `""` | No | — |
# | **maris_legacy** | ✅ from legacy MARIS DB `sample_id` | ❌ missing | Rarely | `samplabcode` not captured; nearly always null in legacy data |

# %% [markdown]
# ## Per-handler details
#
# ### helcom — ✅ Complete (reference pattern)
#
# HELCOM exposes a `key` column that uniquely identifies each measurement in the MORS database.  
# The handler creates both columns inside a dedicated callback:
#
# ```python
# df['SMP_ID'] = range(1, len(df) + 1)          # marisco internal id
# df['SMP_ID_PROVIDER'] = df['key'].astype(str)  # provider id verbatim
# ```
#
# This is the **canonical pattern** all handlers should follow when the provider supplies an identifier.
#
# ---
#
# ### ospar — ✅ Complete
#
# OSPAR supplies a `sample id` column. The handler mirrors the HELCOM pattern:
#
# ```python
# df['SMP_ID'] = range(1, len(df) + 1)
# df['SMP_ID_PROVIDER'] = df['sample id'].astype(str)
# ```
#
# ---
#
# ### geotraces — ✅ Fixed
#
# The `BODC Bottle Number:INTEGER` field is renamed to `SMP_ID_PROVIDER` via `renaming_rules` in `RenameColumnCB`, then `AddSampleIDCB` generates a sequential `SMP_ID` and casts `SMP_ID_PROVIDER` to string:
#
# ```python
# renaming_rules = {
#     ...
#     'BODC Bottle Number:INTEGER': 'SMP_ID_PROVIDER'
# }
#
# class AddSampleIDCB(Callback):
#     def __call__(self, tfm):
#         for _, df in tfm.dfs.items():
#             df['SMP_ID'] = range(1, len(df) + 1)
#             df['SMP_ID_PROVIDER'] = df['SMP_ID_PROVIDER'].astype(str)
# ```
#
# `AddSampleIDCB` runs after `DispatchToGroupCB`, so it iterates over both `SEAWATER` and `SUSPENDED_MATTER` groups.
#
# **Previously:** the BODC Bottle Number was mapped directly to `SMP_ID` via `renaming_rules`, leaving `SMP_ID_PROVIDER` absent and the NetCDF dimension populated with raw provider integers.
#
# ---
#
# ### tepco — ⚠️ `SMP_ID_PROVIDER` present but empty
#
# TEPCO monitoring data does not carry sample identifiers. The `AddSampleIdCB` callback handles both columns for the SEAWATER group (the only group present in TEPCO data):
#
# ```python
# tfm.dfs['SEAWATER']['SMP_ID'] = range(1, len(tfm.dfs['SEAWATER']) + 1)
# tfm.dfs['SEAWATER']['SMP_ID_PROVIDER'] = ""
# ```
#
# **Minor concern:** `SMP_ID_PROVIDER` is set to an empty string `""` rather than a null/`None`. Depending on encoder behaviour this may surface as an empty-string column rather than a missing-value column. Using `None` or `pd.NA` would be more consistent.
#
# ---
#
# ### maris_legacy — ⚠️ `SMP_ID_PROVIDER` not captured
#
# The legacy MARIS CSV format contains two ID-related fields:
#
# | CSV column | Meaning |
# |---|---|
# | `sample_id` | MARIS central-database internal integer ID |
# | `samplabcode` | Provider lab code (maps to `SMP_ID_PROVIDER` in `CSV_VARS`) |
#
# The handler renames `sample_id` → `SMP_ID` (correct: this is already the MARIS internal ID) but does not capture `samplabcode` as `SMP_ID_PROVIDER`.
#
# In practice `samplabcode` is nearly always null in the legacy export (~1 non-null value out of ~420 000 records), so the impact is low. The column should still be mapped for correctness and forward-compatibility.
#
# `UniqueIndexCB()` is also used in the legacy pipeline, but it creates a separate `ID` column (a plain DataFrame reset-index, unrelated to `SMP_ID`).

# %% [markdown]
# ## Known issues and recommended fixes
#
# ### 1. ~~geotraces — remap BODC Bottle Number to `SMP_ID_PROVIDER`~~ ✅ Resolved
#
# Fixed in `geotraces.ipynb`: `BODC Bottle Number:INTEGER` is now mapped to `SMP_ID_PROVIDER` via `renaming_rules`, and `AddSampleIDCB` generates a sequential `SMP_ID` per group.
#
# ### 2. tepco — use `None` instead of `""` for absent provider ID (low priority)
#
# ```python
# tfm.dfs['SEAWATER']['SMP_ID_PROVIDER'] = None  # was ""
# ```
#
# ### 3. maris_legacy — map `samplabcode` to `SMP_ID_PROVIDER` (low priority)
#
# Add `'samplabcode': 'SMP_ID_PROVIDER'` to the `col_remap` dictionary in `maris_legacy.ipynb`. Because the column is nearly always null in the legacy export this is a cosmetic fix for schema completeness.
#
# ### 4. field-definition.ipynb — align `SMP_ID` / `SMP_ID_PROVIDER` entries
#
# The current `field-definition.ipynb` lists a single 'Sample ID' row that conflates both columns and references `smp_id` (NetCDF) and `samplabcode` (CSV). The correct mapping is:
#
# | Field | MARISCO column | NetCDF variable | CSV variable |
# |---|---|---|---|
# | Internal sample ID | `SMP_ID` | `id` *(dimension)* | — |
# | Provider sample ID | `SMP_ID_PROVIDER` | `id_provider` | `samplabcode` |
#
# `field-definition.ipynb` should be updated to reflect this split.
