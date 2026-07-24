# ---
# jupyter:
#   jupytext:
#     formats: ipynb,.pct.py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.5
# ---

# %%
#| default_exp handlers.helcom

# %% [markdown]
# # HELCOM

# %% [markdown]
# This handler ingests raw [HELCOM (Helsinki Commission — Baltic Marine Environment Protection Commission)](https://helcom.fi/about-us/) Monitoring of Radioactive Substances (MORS) data and transforms it into the MARIS NetCDF format through a pipeline that standardises nomenclatures, parses time and coordinates, melts dual-value sediment rows into long format, and computes uncertainties, detection-limit flags, and weight variables. 
#
# For detailed guidance on the reconciliation workflow used throughout this handler, see the [writing-a-handler](https://fr.anckalbi.net/marisco/how-to/writing-a-handler.html) and [reconcile-nomenclature](https://fr.anckalbi.net/marisco/how-to/reconcile-nomenclature.html) how-to guides. 
#
# For the MARIS data model and field conventions, see the [reference guide](https://fr.anckalbi.net/marisco/reference/guide.html) and [field definitions](https://fr.anckalbi.net/marisco/reference/field-definition.html).

# %% [markdown]
# The pipeline processes the data through these main stages:
#
# - **Nomenclature reconciliation** — nuclides, species, body parts, sediment types, and filtering status mapped to MARIS lookups via fuzzy matching and expert overrides
# - **Time and coordinate standardisation** — date parsing with fallback to year/month/day columns, lat/lon conversion from ddmmmm to decimal degrees
# - **Wide-to-long sediment melt** — dual-value rows (Bq/kg + Bq/m²) split into separate measurement rows
# - **Value transformation** — absolute uncertainty from relative percentage, detection-limit flag assignment, unit code assignment
# - **Sample metadata** — depth, salinity, temperature, station identifiers, sediment slice positions, weight variables
# - **NetCDF encoding** — all groups assembled into a self-contained file with global attributes (bounding box, time range, Zotero citation, processing logs)

# %%
#| hide
# %load_ext autoreload
# %autoreload 2

# %%
#| export
from fastcore.all import *
import pandas as pd
import numpy as np
import re

from marisco.configs import NA, NC_DTYPES, get_lut, lut_path, cache_path
from marisco.match import uniq_across_dfs, lut_from, fuzzy_merge, fix_lut, make_lut, make_lut_from
from marisco.geo import ddmm_to_dd
from marisco.utils import ExtractNetcdfContents
from marisco.callbacks import (
    Callback, PerGroupCB, Transformer,
    EncodeTimeCB, LowerStripNameCB, SanitizeLonLatCB,
    CompareDfsAndTfmCB, RemapCB)
from marisco.metadata import GlobAttrsFeeder, BboxCB, DepthRangeCB, TimeRangeCB, ZoteroCB, KeyValuePairCB
from marisco.encoders import NetCDFEncoder
from marisco.netcdf2csv import decode

import warnings
warnings.filterwarnings('ignore')

# %%
#| hide
pd.set_option('display.max_rows', 100)

# %% [markdown]
# ## Configuration & file paths

# %% [markdown]
# - **src_dir**: path to the [maris-crawlers](https://github.com/franckalbinet/maris-crawlers) folder containing the HELCOM data in CSV format.
#
# - **fname_out**: path and filename for the NetCDF output.The path can be defined as a relative path. 
#
# - **Zotero key**: used to retrieve attributes related to the dataset from [Zotero](https://www.zotero.org/). The MARIS datasets include a [library](https://maris.iaea.org/datasets) available on [Zotero](https://www.zotero.org/groups/2432820/maris/library). 
#

# %%
#| exports
src_dir = 'https://raw.githubusercontent.com/franckalbinet/maris-crawlers/refs/heads/main/data/processed/HELCOM%20MORS'
fname_out = '../../_data/output/100-HELCOM-MORS-2024.nc'
zotero_key ='26VMZZ2Q' # HELCOM MORS zotero key

# %% [markdown]
# ## Load data

# %% [markdown]
# [Helcom MORS (Monitoring of Radioactive Substances in the Baltic Sea) data](https://helcom.fi/about-us) is provided as a zipped Microsoft Access database. We automatically fetch and convert this dataset with database tables exported as `.csv` files using a Github action here: [maris-crawlers](https://github.com/franckalbinet/maris-crawlers/blob/main/.github/workflows/fetch-data-sources.yml). 
#
# The dataset is then accessible in an amenable format for the `marisco` data pipeline.

# %%
#| exports
default_smp_types = {  
    'BIO': 'BIOTA', 
    'SEA': 'SEAWATER', 
    'SED': 'SEDIMENT'
}


# %%
#| export
def load_data(
        fname_in # Path to raw HELCOM csv dataset
        ):
    "Load HELCOM data; returns dict of DataFrames keyed by sample type."
    res = {}
    for prefix,smp_type in default_smp_types.items():
        smp = pd.read_csv(f'{fname_in}/{prefix}01.csv').rename(str.lower, axis='columns')
        meas = pd.read_csv(f'{fname_in}/{prefix}02.csv').rename(str.lower, axis='columns')
        res[smp_type] = smp.merge(meas, on='key')
    return res


# %% [markdown]
# `dfs` is a dictionary of dataframes created from the Helcom dataset located at the path `src_dir`. The data to be included in each dataframe is sorted by sample type. Each dictionary is defined with a key equal to the sample type. 

# %%
#| eval: false
dfs = load_data(src_dir)
test_eq(list(dfs.keys()), ['BIOTA', 'SEAWATER', 'SEDIMENT'])

# %%
#| eval: false
for k,v in dfs.items():
    print(f"{k}: {v.shape[0]} rows, {v.shape[1]} cols")
    print(v.columns.tolist(), '\n')

# %% [markdown]
# ## Normalize nuclide names

# %% [markdown]
# ### Fix trailing spaces

# %% [markdown]
# :::{.callout-important}
# ## FEEDBACK TO DATA PROVIDER
# Trailing whitespace in nuclide names: ~325 rows across the dataset contain nuclide values with one or more trailing spaces (e.g. 'PU238 ', 'CS137 ', 'SR90 '). These should be trimmed at source.
# :::
#

# %% [markdown]
# For instance, rows where the raw nuclide name has trailing whitespace:

# %%
#| eval: false
bad = pd.concat(dfs.values(), ignore_index=True).query('nuclide != nuclide.str.strip()')
print(f"{len(bad)} rows with trailing spaces. Examples:\n")
print(bad.drop_duplicates('nuclide')['nuclide'].to_list()[:8])

# %% [markdown]
# `LowerStripNameCB` lowercases and strips them into a standardised `NUCLIDE` column.

# %%
#| eval: false
tfm = Transformer(dfs, cbs=[LowerStripNameCB(col_src='nuclide', col_dst='NUCLIDE')])
tfm()

for df in tfm.dfs.values():
    test_eq(df['NUCLIDE'], df['NUCLIDE'].str.lower().str.strip())
print(f"All nuclide names normalised across {len(tfm.dfs)} sample groups.")

# %% [markdown]
# ### Align nuclide names with MARIS

# %% [markdown]
# HELCOM nuclide names are lowercased and stripped by `LowerStripNameCB` above, but some names need expert overrides: combined totals like `cs134137` (caesium-134+137 sum, maps to `cs134_137_tot`), compound codes like `cm243244` (curium-243+244), and clearly-as-typos like `cs143` (likely cs137). We reconcile these by following the same semi-automated workflow used across marisco handlers: 
#
# 1. get familiar with the provider's codes, 
# 2. try an automatic mapping, 
# 3. fix what it got wrong, 
# 4. and check the result.

# %% [markdown]
# We derive the unique nuclide values from the data after lowercase/normalisation, then fuzzy‑match them against the MARIS nuclide reference table.

# %% [markdown]
# **Try an automatic mapping**
#
# *Derive unique provider values and fuzzy-match against MARIS reference.*

# %%
#| eval: false
provider_lut = lut_from(tfm(), 'NUCLIDE')
maris_ref = get_lut('NUCLIDE', as_df=True)

print("provider_lut:", provider_lut.columns.tolist())
print("maris_ref:   ", maris_ref.columns.tolist())

merged = fuzzy_merge(provider_lut, maris_ref, left_on='value', right_on='nc_name')

# %% [markdown]
# **Inspect the borderline matches**
#
# *Review non-exact matches to identify cases the fuzzy matcher could not resolve.*

# %%
#| eval: false
# Entries with score > 0 need human review
non_exact = merged[merged.score > 0].sort_values('score', ascending=False)
print(non_exact)

# %% [markdown]
# The table above shows the borderline cases. Some are legitimate combined-total nuclides (`cs134137`, `cm243244`, `pu239240`, `pu238240`) that should map to their MARIS `_tot` counterparts. Others are typos or historical artefacts, e.g. `cs143`, `cs145`, `cs142`, `cs141`, `cs144`, `cs140`, `cs146`, `cs139`, `cs138`, are all clearly variants of cs137. `k-40` is simply k40 with a hyphen. These overrides are captured below.

# %% [markdown]
# **Fix what it got wrong**
#
# *Apply expert overrides for cases the fuzzy match could not resolve correctly.*

# %% [markdown]
# :::{.callout-important}
# ## FEEDBACK TO DATA PROVIDER
# **Inconsistent nuclide naming conventions** — Most nuclide names follow the standard alphanumeric format (e.g. `cs137`, `k40`), but a few entries are inconsistent:
# - `k-40` uses a hyphen, unlike other entries (should be `k40`)
# - A cluster of entries (`cs140`–`cs146`, `cs138`, `cs139`) appear to be typos for `cs137`
#
# A standardised nuclide pick-list at the point of entry would prevent these issues.
#
# :::
#

# %%
#| exports
fixes_nuclide_names = {
    'cs134137': 'cs134_137_tot',
    'cm243244': 'cm243_244_tot',
    'pu239240': 'pu239_240_tot',
    'pu238240': 'pu238_240_tot',
    'cs143': 'cs137',
    'cs145': 'cs137',
    'cs142': 'cs137',
    'cs141': 'cs137',
    'cs144': 'cs137',
    'k-40': 'k40',
    'cs140': 'cs137',
    'cs146': 'cs137',
    'cs139': 'cs137',
    'cs138': 'cs137'
    }

# %% [markdown]
# The dictionary below records our expert decisions for every case the fuzzy matcher got wrong. Each entry maps a provider nuclide value to its correct MARIS `nc_name`. The `fix_lut` function applies these overrides and resets the score to 0.

# %%
fixed = fix_lut(merged, fixes_nuclide_names, maris_ref,
                left_on='value', right_on='nc_name', id_col='nuclide_id')

# Verify: no unresolved matches remain
unresolved = fixed[fixed['score'] > 0]
print(unresolved if len(unresolved) else "All nuclide entries resolved. ✓")

# %% [markdown]
# **Assemble the final mapping**
#
# The four steps above (unique values, fuzzy match, expert overrides, verification) told us what the correct MARIS translations are. The `make_lut` function packages that knowledge, the expert fixes and the MARIS reference table, into a single function that the Transformer can call later, when it is processing the data through the pipeline.

# %%
#| exports
# Resolved nuclide lookup table (provider → MARIS nuclide_id); lazy, resolves at Transformer time
nuclide_lut = make_lut('NUCLIDE', fixes=fixes_nuclide_names)

# %% [markdown]
# The `nuclide_lut` lookup table is passed to the generic `RemapCB` callback, which looks up the MARIS nuclide reference table behind the scenes when the Transformer runs. The mapping translates `NUCLIDE` (the provider string after lowercasing and stripping) into `NUCLIDE` (the MARIS integer nuclide_id) across all sample-type groups.

# %% [markdown]
# Let's verify the full pipeline works:

# %%
#| eval: false
tfm = Transformer(dfs, cbs=[
    LowerStripNameCB(col_src='nuclide', col_dst='NUCLIDE'),
    RemapCB(lut=nuclide_lut, col_remap='NUCLIDE', col_src='NUCLIDE')
    ])
    
dfs_out = tfm()

# %%
#| eval: false
print(f"NUCLIDE is integer MARIS IDs in all {len(dfs_out)} groups. ✓")
for key in dfs_out.keys():
    test_eq(dfs_out[key]['NUCLIDE'].dtype, 'int64')

# %% [markdown]
# A quick sanity check confirms that the expert-mapped nuclides like cs134_137_tot and cs137 are properly assigned to actual rows in the output:

# %%
#| eval: false
for name, ncid in [('cs134_137_tot', 76), ('cs137', 33)]:
    n = (dfs_out['BIOTA'].NUCLIDE == ncid).sum()
    print(f"{name} (id={ncid}): {n} rows")
    test_ne(n, 0)

# %% [markdown]
# ## Standardize time

# %% [markdown]
# HELCOM provides dates in a `DATE` column (format `MM/DD/YY HH:MM:SS`), but ~1,500 rows across the dataset have missing `DATE` values. The raw data also includes separate `YEAR`, `MONTH`, `DAY` columns as fallback, though some rows have `MONTH=0` or `DAY=0` (unknown), which we set to 1.
#
# `ParseTimeCB` handles this in three steps: it parses the `DATE` column using pandas, replaces `MONTH=0` / `DAY=0` with 1, and fills any remaining missing `TIME` values by constructing dates from the `YEAR`/`MONTH`/`DAY` columns.

# %% [markdown]
# :::{.callout-important}
# ## FEEDBACK TO DATA PROVIDER
#
# Time/date is provided in `DATE`, `YEAR`, `MONTH`, and `DAY` columns. The `DATE` column contains ~1,500 missing values across the dataset. These should ideally be populated at source. Additionally, `MONTH=0` or `DAY=0` occurs when the day or month is unknown; we set these to 1 as a convention, but a standardised sentinel value for unknown components would be clearer.
# :::

# %%
#| eval: false
# Show rows with missing or zero date components in SEAWATER
df = dfs['SEAWATER']
bad_dates = df[df['date'].isna()]
bad_parts  = df[(df['day'] == 0) | (df['month'] == 0)]

print(f"Missing DATE values: {len(bad_dates)} rows")
print(f"Zero day or month:  {len(bad_parts)} rows")
print(bad_dates[['date','year','month','day']].head(3))


# %%
#| export
class ParseTimeCB(PerGroupCB):
    "Parse HELCOM DATE (MM/DD/YY HH:MM:SS) with fallback to YEAR/MONTH/DAY."
    def each_grp(self, grp, df, tfm):
        df['TIME'] = pd.to_datetime(df['date'], format='%m/%d/%y %H:%M:%S', errors='coerce')
        for c in ['day','month']: df.loc[df[c]==0,c] = 1
        m = df['TIME'].isna()
        df.loc[m,'TIME'] = pd.to_datetime(df.loc[m, ['year','month','day']], errors='coerce')



# %% [markdown]
# Applying `ParseTimeCB` across all sample-type groups:

# %%
#| eval: false
tfm = Transformer(dfs, cbs=[ParseTimeCB()])
dfs_out = tfm()

print(f"TIME column added across {len(dfs_out)} groups. ✓")
print(dfs_out['SEAWATER'][['TIME']].head(3))
test_eq('TIME' in dfs_out['SEAWATER'].columns, True)
test_eq(dfs_out['SEAWATER']['TIME'].isna().sum(), 0)

# %% [markdown]
# NetCDF stores time as milliseconds since an origin (here `1970-01-01`, as defined in the template's CDL). `EncodeTimeCB` converts the parsed `TIME` column to this integer format; rows with unresolvable dates are dropped (8 in SEAWATER, 1 in SEDIMENT).

# %% [markdown]
# Applying `ParseTimeCB` and `EncodeTimeCB` together:

# %%
#| eval: false
tfm = Transformer(dfs, cbs=[ParseTimeCB(), EncodeTimeCB()])
dfs_out = tfm()

print(f"TIME encoded as int64 in all {len(dfs_out)} groups. ✓")
test_eq(dfs_out['SEAWATER']['TIME'].dtype, 'int64')
test_eq(dfs_out['SEAWATER']['TIME'].isna().sum(), 0)

# %% [markdown]
# ## Melt sediment values

# %% [markdown]
# HELCOM sediment records are in wide format: each row carries two parallel measurement columns (`VALUE_Bq/kg` and `value_bq/m²`, plus their associated uncertainty and detection-limit columns). MARIS expects tidy/long format; one measurement per row with a UNIT code identifying the original column. So we unpivot (melt) the sediment data, creating separate rows for each measurement type.
#
# To make the transformation explicit: the melt copies values from each measurement-type group into columns prefixed with `_` (`_VALUE`, `_UNC`, `_DL`, `_UNIT`). The underscore marks these as intermediate; they will be renamed to their final MARIS-standard column names in a later step. 

# %% [markdown]
# :::{.callout-important}
# ## FEEDBACK TO DATA PROVIDER
# **Tidy/long format would simplify ingestion.** HELCOM supplies sediment measurements in wide format (Bq/kg and Bq/m² columns on the same row). MARIS expects one measurement per row with a unit identifier. This means every sediment row with data in both columns must be split into two rows during ingestion, an extra transformation step that a long-format delivery would avoid.
# :::

# %%
# Let's see what the sediment data looks like and why we need to split
sed = dfs['SEDIMENT']

cols = ['key','nuclide','value_bq/kg','< value_bq/kg','error%_kg','value_bq/m²','< value_bq/m²','error%_m²']
print("Random sample of 3 sediment rows:")
print(sed[cols].sample(3).to_string(index=False), '\n')

# How many rows have data in BOTH columns?
both = sed[sed['value_bq/kg'].notna() & sed['value_bq/m²'].notna()]
print(f"Rows with values in BOTH Bq/kg and Bq/m²: {len(both):,} out of {len(sed):,} ({100*len(both)/len(sed):.0f}%)")

# %% [markdown]
# The mapping below defines which raw columns correspond to `VALUE`, uncertainty (`UNC`), and detection limit (`DL`) for each measurement type, together with the MARIS unit ID to assign.

# %%
#| exports
# Column mappings per sediment measurement type: MARIS-standard column name → raw HELCOM column name
coi_sediment = {
    'kg_type': {
        'VALUE': 'value_bq/kg',  # Activity concentration per unit mass
        'UNC': 'error%_kg',      # Relative uncertainty (percent)
        'DL': '< value_bq/kg',   # Detection limit flag/level
        'UNIT': 3,               # Unit ID for Bq/kg
    },
    'm2_type': {
        'VALUE': 'value_bq/m²',  # Activity per unit area
        'UNC': 'error%_m²',      # Relative uncertainty (percent)
        'DL': '< value_bq/m²',   # Detection limit flag/level
        'UNIT': 2,               # Unit ID for Bq/m²
    }
}


# %% [markdown]
# `SplitSedimentValuesCB` reads each measurement-type group from the mapping above, checks which rows have data in that group's `VALUE`/`UNC`/`DL` columns, and copies those values into a standard set of temporary columns prefixed with `_`. It then concatenates all measurement-type subsets into a single sediment dataframe. The underscore prefix marks these columns as intermediate (they will be finally renamed in a later step).

# %%
#| export
class MeltSedimentValuesCB(PerGroupCB):
    "Melt HELCOM dual-value sediment rows into separate rows per measurement type (Bq/kg, Bq/m²)."
    grps = ['SEDIMENT']
    def __init__(self, coi:dict  # Column-of-interest mapping, keyed by unit variant (kg, m²)
            ): store_attr()

    def each_grp(self, grp, df, tfm):
        parts = []
        for cols in self.coi.values():
            sel = df[[cols[v] for v in ['VALUE','UNC','DL']]].notna().any(axis=1)
            if not sel.any(): continue
            parts.append(df[sel].rename(columns={
                cols['VALUE']:'_VALUE', cols['UNC']:'_UNC',
                cols['DL']:'_DL'}).assign(_UNIT=cols['UNIT']))
        if parts: tfm.dfs[grp] = pd.concat(parts, ignore_index=True)


# %%
#| eval: false
tfm = Transformer(dfs, cbs=[MeltSedimentValuesCB(coi_sediment)])
dfs_out = tfm()

print(f"SEDIMENT rows: {dfs['SEDIMENT'].shape[0]} → {dfs_out['SEDIMENT'].shape[0]} after melt")
test_eq('_VALUE' in dfs_out['SEDIMENT'].columns, True)
test_eq('_UNIT' in dfs_out['SEDIMENT'].columns, True)
test_eq(dfs_out['SEDIMENT']['_UNIT'].isin([2, 3]).all(), True)

# %% [markdown]
# ## Sanitize value

# %% [markdown]
# :::{.callout-important}
# ## FEEDBACK TO DATA PROVIDER
#
# Some of the HELCOM datasets contain missing values in the `VALUE` column, see output after applying the `SanitizeValueCB` callback.
#
# :::

# %% [markdown]
# HELCOM measurement values live in differently named columns depending on the sample type — `value_bq/m³` for seawater, `value_bq/kg` for biota, and `_VALUE` for sediment (created by the previous melt step). `SanitizeValueCB` collects these into a single `VALUE` column and drops rows that lack a measurement value, since MARIS requires a non-null measurement for every record.

# %%
#| exports
coi_val = {'SEAWATER' : {'VALUE': 'value_bq/m³'},
           'BIOTA':  {'VALUE': 'value_bq/kg'},
           'SEDIMENT': {'VALUE': '_VALUE'}}


# %%
#| export
class SanitizeValueCB(PerGroupCB):
    "Sanitize measurement values by removing blanks and standardizing to use the `VALUE` column."
    def __init__(self,
                 coi: Dict[str, Dict[str, str]], # Columns of interest. Format: {group_name: {'VALUE': 'column_name'}}
                 ):
        store_attr()

    def each_grp(self, grp, df, tfm):
        value_col = self.coi[grp]['VALUE']
        tfm.dfs[grp] = df.dropna(subset=[value_col])
        tfm.dfs[grp]['VALUE'] = tfm.dfs[grp][value_col]


# %%
#| eval: false
tfm = Transformer(dfs, cbs=[MeltSedimentValuesCB(coi_sediment),
                            SanitizeValueCB(coi_val),
                            ])
dfs_out = tfm()

print(f"VALUE column created across all {len(dfs_out)} groups.")
for key in dfs_out.keys():
    test_eq('VALUE' in dfs_out[key].columns, True)
    test_eq(dfs_out[key]['VALUE'].isna().sum(), 0)

# %% [markdown]
# ## Normalize uncertainty

# %% [markdown]
# HELCOM provides measurement uncertainty as a relative percentage, but MARIS requires absolute (standard) uncertainty. The percentage column also has a different name in each sample group (`error%_m³` for seawater, `error%` for biota, `_UNC` for sediment). `NormalizeUncCB` converts each group's percentage column to an absolute `UNC` column by multiplying the percentage by the measured value.
#

# %%
#| exports
coi_units_unc = {
    'SEAWATER': ('VALUE', 'error%_m³'),
    'BIOTA':    ('VALUE', 'error%'),
    'SEDIMENT': ('VALUE', '_UNC'),
}


# %%
#| export
class NormalizeUncCB(PerGroupCB):
    "Convert relative uncertainty (percent) to absolute (standard) uncertainty per group."
    def __init__(self,
                 coi: dict=coi_units_unc,  # {group: (meas_col, unc_col)}
                ):
        store_attr()

    def each_grp(self, grp, df, tfm):
        if grp not in self.coi: return
        meas_col, unc_col = self.coi[grp]
        df['UNC'] = df[unc_col] * df[meas_col] / 100


# %% [markdown]
# Run `NormalizeUncCB` on mock data from all three groups. The output confirms the conversion produces the expected absolute uncertainties. The assertions below verify the arithmetic inline.
#

# %%
#| eval: false
tfm = Transformer(dfs, cbs=[
    MeltSedimentValuesCB(coi_sediment), 
    SanitizeValueCB(coi_val),
    NormalizeUncCB()])

tfm()['SEDIMENT'][['VALUE', 'UNC', '_UNIT']].head()

# %%
# Verify NormalizeUncCB computes correctly on mock data
dfs_mock = {
    'SEAWATER': pd.DataFrame({'VALUE': [5.3, 19.9], 'error%_m³': [32.0, 20.0]}),
    'BIOTA':    pd.DataFrame({'VALUE': [135.3],     'error%':    [3.57]}),
    'SEDIMENT': pd.DataFrame({'VALUE': [1200.0, 250.0], '_UNC': [20.0, 20.0]}),
}
tfm = Transformer(dfs_mock, cbs=[NormalizeUncCB()])
tfm()

# %%
test_eq(tfm.dfs['SEAWATER']['UNC'].to_list(), [5.3*32/100, 19.9*20/100])
test_eq(tfm.dfs['BIOTA']['UNC'].to_list(),    [135.3*3.57/100])
test_eq(tfm.dfs['SEDIMENT']['UNC'].to_list(), [1200.0*20/100, 250.0*20/100])
print("NormalizeUncCB on mock data: all assertions passed. ✓")

# %% [markdown]
# ## Remap units

# %% [markdown]
# HELCOM encodes units differently per sample type. SEAWATER uses Bq/m³ (implied by the column name `value_bq/m³`). BIOTA uses Bq/kg with a `basis` column distinguishing wet weight (W), dry weight (D), or fresh weight (F). SEDIMENT gets its unit from the melt step's `_UNIT` column (Bq/kg or Bq/m²). `RemapUnitCB` collects these into a single MARIS-standard `UNIT` column.

# %% [markdown]
# For the `BIOTA` sample type, the base unit is `Bq/kg`, as indicated in the `value_bq/kg` column. The distinction between wet (W) and dry weight (D) is specified in the basis column.

# %%
#| eval: false
dfs['BIOTA'][['value_bq/kg', 'basis']].head(1)

# %% [markdown]
# For the `SEAWATER` sample type, the unit is `Bq/m³` as indicated in the `value_bq/m³` column.

# %%
#| eval: false
dfs['SEAWATER'][['value_bq/m³']].head(1)

# %% [markdown]
# We can now review the units that are available in MARIS:

# %%
#| eval: false
print(get_lut('UNIT', as_df=True))

# %% [markdown]
# We define unit renaming rules for HELCOM in an **ad hoc** way:

# %%
#| exports
lut_units = {
    'SEAWATER': 1,  # 'Bq/m3'
    'SEDIMENT': '_UNIT',  # Accounted for in MeltSedimentValuesCB
    'BIOTA': {
        'D': 4,  # 'Bq/kgd'
        'W': 5,  # 'Bq/kgw'
        'F': 5   # 'Bq/kgw' (fresh assumed = wet)
    }
}


# %% [markdown]
# We define the `RemapUnitCB` callback to set the `UNIT` column in the DataFrames based on the lookup table `lut_units`.

# %%
#| export
#| exports
class RemapUnitCB(PerGroupCB):
    "Set the MARIS-standard UNIT column from per-sample-type conventions (column name, basis column, or melt result)."
    def __init__(self,
                 lut_units: dict=lut_units  # Per-group unit mapping: group -> literal ID or {basis_code -> ID}
                ):
        store_attr()

    def each_grp(self, grp, df, tfm):
        if grp == 'SEAWATER': df['UNIT'] = self.lut_units[grp]
        elif grp == 'BIOTA': df['UNIT'] = df['basis'].apply(lambda x: self.lut_units[grp].get(x, 0))
        elif grp == 'SEDIMENT': df['UNIT'] = df['_UNIT']


# %% [markdown]
# A quick sanity check on mock data confirms the callback assigns the correct UNIT IDs for every sample type. SEAWATER always gets unit 1 (Bq/m³). BIOTA rows get 4 for dry weight, 5 for wet/fresh weight, and 0 for unknown basis codes. SEDIMENT picks up whatever `_UNIT` the melt step assigned, either 2 (Bq/m²) or 3 (Bq/kg):

# %%
# Verify RemapUnitCB assigns correct UNIT IDs on mock data
dfs_mock = {
    'SEAWATER': pd.DataFrame({'dummy': [1, 2]}),
    'BIOTA':    pd.DataFrame({'basis': ['D', 'W', 'F', 'X']}),
    'SEDIMENT': pd.DataFrame({'_UNIT': [2, 3, 2]}),
}
tfm = Transformer(dfs_mock, cbs=[RemapUnitCB()])
tfm()

test_eq(tfm.dfs['SEAWATER']['UNIT'].to_list(), [1, 1])
test_eq(tfm.dfs['BIOTA']['UNIT'].to_list(),   [4, 5, 5, 0])
test_eq(tfm.dfs['SEDIMENT']['UNIT'].to_list(), [2, 3, 2])
print("RemapUnitCB on mock data: all assertions passed. ✓")

# %% [markdown]
# Running the full pipeline up to this point on the real HELCOM data confirms the units are assigned correctly across all sample-type groups:

# %%
tfm = Transformer(dfs, cbs=[
    MeltSedimentValuesCB(coi_sediment),
    SanitizeValueCB(coi_val),
    NormalizeUncCB(),
    RemapUnitCB(),
])
dfs_out = tfm()

for grp in ['SEAWATER', 'BIOTA', 'SEDIMENT']:
    print(f"{grp}: UNIT values = {dfs_out[grp]['UNIT'].unique()}")

test_eq(set(dfs_out['SEAWATER']['UNIT'].unique()), {1})
test_eq(set(dfs_out['SEDIMENT']['UNIT'].unique()), {2, 3})
test_eq(set(dfs_out['BIOTA']['UNIT'].unique()), {0, 4, 5})

# %% [markdown]
# ## Remap detection limit

# %% [markdown]
# HELCOM encodes detection limits in provider-specific columns: `< value_bq/m³` for seawater, `< value_bq/kg` for biota, and `_DL` for sediment after the melt step (see [Melt sediment values](#melt-sediment-values)). When the raw column contains `<`, the measurement is a detection limit; otherwise it is a detected value. MARIS uses the following integer codes for this distinction:

# %%
#| eval: false
print(get_lut('DL', as_df=True))

# %% [markdown]
# The `coi_dl` mapping below specifies which raw column holds the detection-limit information for each sample group. `RemapDetectionLimitCB` converts these to the MARIS-standard `DL` column, assigning code `2` for detection limits (where the raw value is `<`) and `1` for detected values.

# %%
#| exports
coi_dl = {'SEAWATER' : {'DL' : '< value_bq/m³'},
          'BIOTA':  {'DL' : '< value_bq/kg'},
          'SEDIMENT': {'DL' : '_DL'}}


# %%
#| export
class RemapDetectionLimitCB(PerGroupCB):
    "Map HELCOM `<` / detected-value conventions to MARIS detection-limit integer codes (2 for DL, 1 for detected)."
    def __init__(self, 
                 coi: dict,  # Dict of column hosting the detection limit info for each sample type
                ):
        store_attr()
        
    def each_grp(self, grp, df, tfm):
        dl = self.coi[grp]['DL']
        df['DL'] = df[dl].apply(lambda x: 2 if x == '<' else 1)


# %%
# Verify RemapDetectionLimitCB assigns correct DL codes on mock data
dfs_mock = {
    'SEAWATER': pd.DataFrame({'< value_bq/m³': ['<', '=', '<', None]}),
    'BIOTA':    pd.DataFrame({'< value_bq/kg': ['<', None, '=', '<']}),
    'SEDIMENT': pd.DataFrame({'_DL': ['=', None, '<', '<']}),
}
tfm = Transformer(dfs_mock, cbs=[RemapDetectionLimitCB(coi_dl)])
tfm()

test_eq(tfm.dfs['SEAWATER']['DL'].to_list(), [2, 1, 2, 1])
test_eq(tfm.dfs['BIOTA']['DL'].to_list(),    [2, 1, 1, 2])
test_eq(tfm.dfs['SEDIMENT']['DL'].to_list(), [1, 1, 2, 2])
print("RemapDetectionLimitCB on mock data: all assertions passed. ✓")

# %% [markdown]
# Running the full pipeline up to this point on the real HELCOM data confirms that every sample-type group gets the correct detection-limit codes:

# %%
#| eval: false
tfm = Transformer(dfs, cbs=[
    MeltSedimentValuesCB(coi_sediment),
    SanitizeValueCB(coi_val),
    NormalizeUncCB(),
    RemapUnitCB(),
    RemapDetectionLimitCB(coi_dl),
])
dfs_out = tfm()

for grp in ['SEAWATER', 'BIOTA', 'SEDIMENT']:
    print(f"{grp}: DL values = {dfs_out[grp]['DL'].unique()}")

test_eq(set(dfs_out['SEAWATER']['DL'].unique()), {1, 2})
test_eq(set(dfs_out['BIOTA']['DL'].unique()),   {1, 2})
test_eq(set(dfs_out['SEDIMENT']['DL'].unique()), {1, 2})


# %% [markdown]
# ## Remap Biota species

# %% [markdown]
# The HELCOM Biota dataset records species using HELCOM's RUBIN code system, which is documented in the accompanying `RUBIN_NAME.csv` lookup table. We align these scientific names with the MARIS species nomenclature following the same inspect-match-fix workflow used for nuclide names above. The mapping involves two steps: each RUBIN code is first looked up against the provider's nomenclature to get a scientific name, then that scientific name is mapped to a MARIS species_id via fuzzy matching and expert overrides.
#
# 1. **Try an automatic mapping**: Read the provider's `RUBIN_NAME.csv` and derive unique scientific names, then fuzzy-match them against the MARIS species reference.
# 2. **Inspect the borderline matches**: *Review non-exact matches to identify cases the fuzzy matcher could not resolve.
# 3. **Fix what it got wrong***: Apply expert overrides for cases the fuzzy match could not resolve correctly.*
# 4. **Assemble the final mapping**: Package the results into a lookup function the Transformer can call later.

# %%
#| exports
provider_lut_species = pd.read_csv(f'{src_dir}/RUBIN_NAME.csv')
print(provider_lut_species.head())

# %% [markdown]
# :::{.callout-important}
# ## FEEDBACK TO DATA PROVIDER
#
# Some `rubin` codes in the HELCOM Biota dataset do not appear in the `RUBIN_NAME.csv` lookup table. This includes entries with trailing spaces (`FUCU VES `, `GADU MOR  `) and apparently missing codes (`FUCU SPP`, `FURC LUMB`, `STUC PECT`). Trailing spaces should be trimmed at source, and any valid RUBIN codes missing from the lookup table should be added.
# :::

# %%
#| eval: false
set(dfs['BIOTA']['rubin']) - set(provider_lut_species['RUBIN'])

# %%
#| eval: false
maris_ref = get_lut('SPECIES', as_df=True)
print(maris_ref.head())

# %%
#| eval: false
# Fuzzy-merge provider scientific names against MARIS species names
merged = fuzzy_merge(provider_lut_species, maris_ref,
                     left_on='SCIENTIFIC NAME', right_on='species')

# %%
#| eval: false
# Inspect non-exact matches
non_exact = merged[merged.score > 0].sort_values('score', ascending=False)
print(non_exact[['SCIENTIFIC NAME', 'species', 'score']].to_string())

# %%
#| exports
fixes_species = {
    'LAMINARIA SACCHARINA': 'Saccharina latissima',
    'CARDIUM EDULE': 'Cerastoderma edule',
    'CHARA BALTICA': 'NOT AVAILABLE',
    'PSETTA MAXIMA': 'Scophthalmus maximus'
    }

# %%
#| eval: false
fixed = fix_lut(merged, fixes_species, maris_ref,
                left_on='SCIENTIFIC NAME', right_on='species', id_col='species_id')

unresolved = fixed[fixed['score'] > 0]
print(unresolved[['SCIENTIFIC NAME', 'species']] if len(unresolved) else "All species entries resolved. ✓")

# %% [markdown]
# Four entries (`ENCHINODERMATA CIM`, `MACOMA BALTICA`, `STIZOSTEDION LUCIOPERCA`, `STUCKENIA PECTINATE`) return non-zero fuzzy-match scores, but the matches are semantically correct: `Echinodermata`, `Macoma balthica`, `Sander lucioperca`, and `Stuckenia pectinata` are the right MARIS equivalents. No further overrides needed.

# %%
#| exports
species_lut = make_lut_from(provider_lut_species, 'RUBIN', 'SCIENTIFIC NAME', 'SPECIES', fixes=fixes_species)

# %% [markdown]
# Verify species lookup on mock data:

# %%
dfs_mock = {'BIOTA': pd.DataFrame({'rubin': ['ABRA BRA', 'CARD EDU', 'CHAR BALT']})}
tfm = Transformer(dfs_mock, cbs=[RemapCB(lut=species_lut, col_remap='SPECIES', col_src='rubin')])
tfm()
test_eq(tfm.dfs['BIOTA']['SPECIES'].to_list(), [271, 274, 0])

# %% [markdown]
# Map species on real HELCOM Biota data:

# %%
#| eval: false
tfm = Transformer({'BIOTA': dfs['BIOTA'].copy()}, cbs=[
    LowerStripNameCB(col_src='nuclide', col_dst='NUCLIDE'),
    RemapCB(lut=species_lut, col_remap='SPECIES', col_src='rubin')
])
dfs_out = tfm()
test_eq(dfs_out['BIOTA']['SPECIES'].isna().sum(), 0)
test_eq(dfs_out['BIOTA']['SPECIES'].dtype, 'int64')
print(f"SPECIES mapped to integer MARIS IDs across {len(dfs_out['BIOTA'])} rows. ✓")

# %%
#| eval: false
# Verify species mapping on real data
tfm = Transformer({'BIOTA': dfs['BIOTA'].copy()}, cbs=[
    LowerStripNameCB(col_src='nuclide', col_dst='NUCLIDE'),
    RemapCB(lut=species_lut, col_remap='SPECIES', col_src='rubin')
])
dfs_out = tfm()
test_eq(dfs_out['BIOTA']['SPECIES'].dtype, 'int64')
print(f"SPECIES mapped to integer MARIS IDs across {len(dfs_out['BIOTA'])} rows. \u2713")

# %% [markdown]
# ## Remap Body Part

# %% [markdown]
# Biota tissue is recorded as HELCOM TISSUE codes documented in the accompanying `TISSUE.csv` lookup table. We reconcile these with the MARIS body-part nomenclature following the same inspect-match-fix workflow used for species above.
#

# %%
#| exports
provider_lut_tissues = pd.read_csv(f'{src_dir}/TISSUE.csv')
print(provider_lut_tissues.head())

# %%
#| eval: false
maris_ref = get_lut('BODY_PART', as_df=True)
print(maris_ref.head())

# Fuzzy-merge provider tissue descriptions against MARIS body-part names
merged = fuzzy_merge(provider_lut_tissues, maris_ref,
                     left_on='TISSUE_DESCRIPTION', right_on='bodypar')

# %%
# Inspect non-exact matches
#| eval: false
non_exact = merged[merged.score > 0].sort_values('score', ascending=False)
print(non_exact[['TISSUE_DESCRIPTION', 'bodypar', 'score']].to_string())

# %% [markdown]
# We address several entries that were not correctly matched, as detailed below:

# %%
#| exports
fixes_biota_tissues = {
    'WHOLE FISH WITHOUT HEAD AND ENTRAILS': 'Whole animal eviscerated without head',
    'WHOLE FISH WITHOUT ENTRAILS': 'Whole animal eviscerated',
    'SKIN/EPIDERMIS': 'Skin',
    'ENTRAILS': 'Viscera'
    }

# %%
#| eval: false
maris_ref = get_lut('BODY_PART', as_df=True)
fixed = fix_lut(merged, fixes_biota_tissues, maris_ref,
                left_on='TISSUE_DESCRIPTION', right_on='bodypar', id_col='bodypar_id')

unresolved = fixed[fixed['score'] > 0]
print(unresolved[['TISSUE_DESCRIPTION', 'bodypar']] if len(unresolved) else "All body-part entries resolved. \u2713")

# %% [markdown]
# **Assemble the final mapping**
#
# The steps above (unique values, fuzzy match, expert overrides, verification) told us what the correct MARIS translations are. The `make_lut_from` function packages that knowledge into a callable that the Transformer can use later.

# %%
#| exports
lut_tissues = make_lut_from(provider_lut_tissues,
                             'TISSUE', 'TISSUE_DESCRIPTION', 'BODY_PART',
                             fixes=fixes_biota_tissues)

# %% [markdown]
# Verify body part lookup on mock data:

# %%
# Verify body part lookup on mock data
dfs_mock = {'BIOTA': pd.DataFrame({'tissue': [1, 5, 12]})}
tfm = Transformer(dfs_mock, cbs=[RemapCB(lut=lut_tissues, col_remap='BODY_PART', col_src='tissue')])
tfm()
test_eq(tfm.dfs['BIOTA']['BODY_PART'].dtype, 'int64')
print("BODY_PART mapped as integer on mock data. \u2713")

# %% [markdown]
# Map body part on real HELCOM Biota data:

# %%
#| eval: false
tfm = Transformer({'BIOTA': dfs['BIOTA'].copy()}, cbs=[
    LowerStripNameCB(col_src='nuclide', col_dst='NUCLIDE'),
    RemapCB(lut=lut_tissues, col_remap='BODY_PART', col_src='tissue')])
dfs_out = tfm()
test_eq(dfs_out['BIOTA']['BODY_PART'].isna().sum(), 0)
test_eq(dfs_out['BIOTA']['BODY_PART'].dtype, 'int64')
print(f'BODY_PART mapped to integer MARIS IDs across {len(dfs_out['BIOTA'])} rows. \u2713')

# %% [markdown]
# ## Remap Biological Group

# %% [markdown]
# Unlike nuclide names, species, and body parts which required fuzzy matching against MARIS nomenclature followed by expert overrides, the biological group assignment is straightforward. The MARIS `SPECIES` lookup table already includes a `biogroup_id` column. Since each HELCOM Biota row now has `SPECIES` as an integer MARIS ID (mapped in the previous step), we just need to look up the corresponding biological group.

# %%
#| exports
lut_biogroup = get_lut('SPECIES', key='species_id', value='biogroup_id')

# %% [markdown]
# Let's verify this works on mock data. We assign `SPECIES` IDs (as if the species-remap step already ran), then look up `BIO_GROUP`:

# %%
# Verify biogroup lookup on mock species IDs
dfs_mock = {'BIOTA': pd.DataFrame({'SPECIES': [271, 274, 0]})}
tfm = Transformer(dfs_mock, cbs=[
    RemapCB(lut=lut_biogroup, col_remap='BIO_GROUP', col_src='SPECIES', grps=['BIOTA'])
])
tfm()
test_eq(tfm.dfs['BIOTA']['BIO_GROUP'].to_list(), [4, 14, 0])
print('BIO_GROUP mapped correctly on mock data. ✓')

# %% [markdown]
# Now apply to real HELCOM Biota data, chained after the species remap:

# %%
#| eval: false
tfm = Transformer({'BIOTA': dfs['BIOTA'].copy()}, cbs=[
    LowerStripNameCB(col_src='nuclide', col_dst='NUCLIDE'),
    RemapCB(lut=species_lut, col_remap='SPECIES', col_src='rubin'),
    RemapCB(lut=lut_biogroup, col_remap='BIO_GROUP', col_src='SPECIES'),
])
dfs_out = tfm()
test_eq(dfs_out['BIOTA']['BIO_GROUP'].isna().sum(), 0)
test_eq(dfs_out['BIOTA']['BIO_GROUP'].dtype, 'int64')
print(f'BIO_GROUP mapped to integer MARIS IDs across {len(dfs_out["BIOTA"])} rows. ✓')

# %% [markdown]
# ## Remap Sediment Types

# %% [markdown]
# HELCOM sediment types are recorded as integer `SEDI` codes documented in the accompanying `SEDIMENT_TYPE.csv` lookup table. We reconcile these with the MARIS sediment-type nomenclature following the same inspect-match-fix workflow used for nuclide names and species above.

# %%
#| exports
provider_lut_sed = pd.read_csv(f'{src_dir}/SEDIMENT_TYPE.csv')
print(provider_lut_sed.head())

# %% [markdown]
# :::{.callout-important}
# ## FEEDBACK TO DATA PROVIDER
#
# The `SEDI` values `56` and `73` are not found in the `SEDIMENT_TYPE.csv` lookup table provided. Note there are many `nan` values. We reassign them to `-99` for now but should be clarified/fixed. This is demonstrated below.
#
# :::

# %%
#| eval: false
set(dfs['SEDIMENT']['sedi'].unique()) - set(provider_lut_sed['SEDI'])

# %% [markdown]
# **Try an automatic mapping**
#
# *Derive provider sediment types from the lookup table and fuzzy-match against MARIS reference.*

# %%
#| eval: false
maris_ref = get_lut('SED_TYPE', as_df=True)

print("provider_lut_sed:", provider_lut_sed.columns.tolist())
print("maris_ref:   ", maris_ref.columns.tolist())

merged = fuzzy_merge(provider_lut_sed, maris_ref, left_on='SEDIMENT TYPE', right_on='sedtype')

# %% [markdown]
# **Fix what it got wrong**
#
# Apply expert overrides for cases the fuzzy match could not resolve correctly. Two are simple typos in the provider lookup table (`MUD AND GARVEL` → `Mud and gravel`, `CLACIAL CLAY` → `Glacial clay`). `NO DATA` maps to `(Not available)`.

# %% [markdown]
# :::{.callout-important}
# ## FEEDBACK TO MARIS DATA TEAM
#
# The MARIS `SED_TYPE` lookup table uses parenthesised `(Not available)` for its sentinel entry, while every other MARIS reference table uses the bare `Not available` (e.g. `SPECIES`, `BODY_PART`, `UNIT`). This inconsistency should be aligned so that all LUTs use the same sentinel form.
# :::

# %%
#| exports
# Expert overrides for sediment type names
# 'NO DATA' maps to '(Not available)' rather than 'Not available' due to 
# an inconsistency in the MARIS SED_TYPE reference table — the sentinel entry 
# uses parentheses while other LUTs use the bare form. This should be aligned.
fixes_sediments = {
    'NO DATA': '(Not available)',
    'MUD AND GARVEL': 'Mud and gravel',
    'CLACIAL CLAY': 'Glacial clay',
}

# %%
#| eval: false
fixed = fix_lut(merged, fixes_sediments, maris_ref,
                left_on='SEDIMENT TYPE', right_on='sedtype', id_col='sedtype_id')
unresolved = fixed[fixed['score'] > 0]
print(unresolved[['SEDIMENT TYPE', 'sedtype']] if len(unresolved) else "All sediment type entries resolved. \u2713")

# %% [markdown]
# The steps above (unique values, fuzzy match, expert overrides, verification) told us what the correct MARIS translations are. The `make_lut_from` function packages that knowledge, the expert fixes and the MARIS reference table, into a single function that the Transformer can call later, when it is processing data through the pipeline.

# %% [markdown]
# A dedicated `CleanSedimentCodesCB` replaces the invalid SEDI codes (56, 73, NaN) with -99 before the nomenclature lookup, making it explicit which step handles data-cleaning vs. nomenclature mapping. When the data provider fixes these codes, simply drop this callback from the pipeline.

# %%
#| exports
sed_replace_lut = {56: -99, 73: -99}


# %%
#| export
class CleanSedimentCodesCB(PerGroupCB):
    "Replace invalid HELCOM SEDI codes with -99 sentinel before nomenclature lookup."
    grps = ['SEDIMENT']
    def __init__(self, 
                 replace_lut # sediment helcom -> maris lookup table
                 ): 
           store_attr()
    def each_grp(self, grp, df, tfm):
        df['sedi'] = df['sedi'].replace(self.replace_lut).fillna(-99)


# %%
#| exports
sediment_lut = make_lut_from(provider_lut_sed, 'SEDI', 'SEDIMENT TYPE', 'SED_TYPE', fixes=fixes_sediments)

# %% [markdown]
# Verify sediment type lookup on mock data:

# %%
#| eval: false
dfs_mock = {'SEDIMENT': pd.DataFrame({'sedi': [0, 1, -99, 56, 73]})}
tfm = Transformer(dfs_mock, cbs=[
    CleanSedimentCodesCB(replace_lut=sed_replace_lut),
    RemapCB(lut=sediment_lut, col_remap='SED_TYPE', col_src='sedi'),
])
tfm()
test_eq(tfm.dfs['SEDIMENT']['SED_TYPE'].dtype, 'int64')
print('SED_TYPE mapped as integer on mock data.')

# %% [markdown]
# Apply sediment type lookup to real HELCOM SEDIMENT data:

# %%
#| eval: false
tfm = Transformer(dfs, cbs=[
    CleanSedimentCodesCB(replace_lut=sed_replace_lut),
    RemapCB(lut=sediment_lut, col_remap='SED_TYPE', col_src='sedi', grps=['SEDIMENT']),
])
dfs_out = tfm()
test_eq(dfs_out['SEDIMENT']['SED_TYPE'].isna().sum(), 0)
test_eq(dfs_out['SEDIMENT']['SED_TYPE'].dtype, 'int64')
print(f'SED_TYPE mapped to integer MARIS IDs across {len(dfs_out["SEDIMENT"])} rows.')

# %% [markdown]
# ## Remap Filtering Status

# %% [markdown]
# Unlike nuclide names, species, and body parts which had a dedicated provider lookup table, HELCOM filtering status has no provider-side LUT. The `filt` column appears only in the seawater data. We inspect the unique values directly from the data and then map them to the MARIS `FILT` nomenclature via a plain dictionary.

# %% [markdown]
# Inspect unique filt values across the data:

# %%
#| eval: false
uniq_across_dfs(dfs, 'filt')

# %% [markdown]
# How does MARIS filtering nomenclature looks like:
#

# %%
#| eval: false
maris_ref = get_lut('FILT', as_df=True)
print(maris_ref.head())

# %% [markdown]
# With only four categories to remap, the generic `RemapCB` callback does the job directly, it accepts a plain `dict` as its `lut` parameter, so no custom callback is needed.

# %%
#| exports
lut_filtered = {
    'N': 2, # No
    'n': 2, # No
    'F': 1 # Yes
}

# %% [markdown]
# `RemapCB(lut=lut_filtered, col_remap='FILT', col_src='filt')` converts the HELCOM `filt` codes to MARIS-standard `FILT` identifiers.

# %% [markdown]
# Let us verify on mock data:

# %%
# Verify on mock data
dfs_mock = {'SEAWATER': pd.DataFrame({'filt': ['N', 'F', 'n', 'Y', None]})}
tfm = Transformer(dfs_mock, cbs=[RemapCB(lut=lut_filtered, col_remap='FILT', col_src='filt')])
tfm()
test_eq(tfm.dfs['SEAWATER']['FILT'].to_list(), [2, 1, 2, 0, 0])
print("FILT mapped correctly on mock data. \u2713")

# %%
#| eval: false
tfm = Transformer(dfs, cbs=[RemapCB(lut=lut_filtered, col_remap='FILT', col_src='filt', grps=['SEAWATER'])])
tfm()

print(tfm.dfs['SEAWATER'][['filt', 'FILT']].head())


# %% [markdown]
# ## Add sample ID
#
# HELCOM identifies each record with a `KEY` column. MARIS requires two identifier columns: `SMP_ID` (an internal sequential id) and `SMP_ID_PROVIDER` (the provider's original key). We generate the sequential id and copy the `KEY` column as the provider identifier.

# %% [markdown]
# - `SMP_ID` is an internal unique identifier for each sample
# - `SMP_ID_PROVIDER` is provided by the data provider

# %%
#| export
class AddSampleIDCB(PerGroupCB):
    "Assign internal sequential SMP_ID and preserve provider KEY as SMP_ID_PROVIDER."
    def each_grp(self, grp, df, tfm):
        df['SMP_ID'] = range(1, len(df) + 1)
        df['SMP_ID_PROVIDER'] = df['key'].astype(str)


# %%
# Verify sample IDs on mock data
dfs_mock = {'BIOTA': pd.DataFrame({'key': ['A1', 'A2']})}
tfm = Transformer(dfs_mock, cbs=[AddSampleIDCB()])
tfm()
test_eq(tfm.dfs['BIOTA']['SMP_ID'].to_list(), [1, 2])
test_eq(tfm.dfs['BIOTA']['SMP_ID_PROVIDER'].to_list(), ['A1', 'A2'])

# %%
#| eval: false
tfm = Transformer(dfs, cbs=[AddSampleIDCB()])
print(tfm()['SEAWATER'][['SMP_ID', 'SMP_ID_PROVIDER']].head())


# %% [markdown]
# ## Add depths

# %% [markdown]
# HELCOM stores sampling depth as `sdepth` (seawater, biota) and total depth as `tdepth` (seawater, sediment). The raw CSV may contain these as strings. `AddDepthCB` renames them to the MARIS-standard `SMP_DEPTH` and `TOT_DEPTH` columns and casts them as float.

# %%
#| export
class AddDepthCB(PerGroupCB):
    "Rename HELCOM sdepth/tdepth columns to MARIS-standard SMP_DEPTH/TOT_DEPTH and cast as float."
    def each_grp(self, grp, df, tfm):
        if 'sdepth' in df.columns: df['SMP_DEPTH'] = df['sdepth'].astype(float)
        if 'tdepth' in df.columns: df['TOT_DEPTH'] = df['tdepth'].astype(float)


# %% [markdown]
# Verify AddDepthCB renames and casts correctly on mock data:

# %%
dfs_mock = {
    "SEAWATER": pd.DataFrame({"key": ["S1"], "sdepth": ["5.0"], "tdepth": ["42.0"]}),
    "BIOTA":    pd.DataFrame({"key": ["B1"], "sdepth": ["3.5"]}),
    "SEDIMENT": pd.DataFrame({"key": ["D1"], "tdepth": ["120.0"]}),
}
tfm = Transformer(dfs_mock, cbs=[AddDepthCB()])
tfm()

test_eq(tfm.dfs["SEAWATER"]["SMP_DEPTH"].to_list(), [5.0])
test_eq(tfm.dfs["SEAWATER"]["TOT_DEPTH"].to_list(), [42.0])
test_eq(tfm.dfs["BIOTA"]["SMP_DEPTH"].to_list(), [3.5])
test_eq("TOT_DEPTH" not in tfm.dfs["BIOTA"].columns, True)
test_eq(tfm.dfs["SEDIMENT"]["TOT_DEPTH"].to_list(), [120.0])
test_eq("SMP_DEPTH" not in tfm.dfs["SEDIMENT"].columns, True)
print("AddDepthCB on mock data: all assertions passed. \u2713")

# %% [markdown]
# Using real data:

# %%
#| eval: false
tfm = Transformer(dfs, cbs=[AddDepthCB()])
dfs_out = tfm()
print(dfs_out['BIOTA'][['SMP_DEPTH']].head())
print(dfs_out['SEAWATER'][['TOT_DEPTH']].head())


# %% [markdown]
# ## Add Salinity
#
# HELCOM stores water salinity in a `salin` column (PSU units, present only in seawater data). `AddSalinityCB` renames it to the MARIS-standard `SAL` column and casts to float.

# %% [markdown]
# :::{.callout-important}
# ## FEEDBACK TO DATA PROVIDER
#
# The HELCOM dataset includes a column for the salinity of the water (`salin`). According to the HELCOM documentation, the `salin` column represents "Salinity of water in PSU units".
#
# In the SEAWATER dataset, three entries have salinity values greater than 50 PSU. While salinity values greater than 50 PSU are possible, these entries may require further verification. Notably, these three entries have a salinity value of 99.99 PSU, which suggests potential data entry errors.
# :::

# %%
#| export
class AddSalinityCB(PerGroupCB):
    "Add salinity (SAL) from HELCOM salin column where present."
    def each_grp(self, grp, df, tfm):
        if 'salin' in df.columns: df['SAL'] = df['salin'].astype(float)


# %%
# Verify AddSalinityCB on mock data
dfs_mock = {
    "SEAWATER": pd.DataFrame({"key": ["S1"], "salin": ["7.5"]}),
    "BIOTA":    pd.DataFrame({"key": ["B1"]}),
}
tfm = Transformer(dfs_mock, cbs=[AddSalinityCB()])
tfm()

test_eq(tfm.dfs["SEAWATER"]["SAL"].to_list(), [7.5])
test_eq("SAL" not in tfm.dfs["BIOTA"].columns, True)
print("AddSalinityCB on mock data: all assertions passed. ✓")

# %%
#| eval: false
tfm = Transformer(dfs, cbs=[AddSalinityCB()])
dfs_out = tfm()
print(dfs_out['SEAWATER'][['SAL']].drop_duplicates().head())


# %% [markdown]
# ## Add Station

# %% [markdown]
# HELCOM identifies each sampling location with a `station` column present in all sample-type groups. `AddStationCB` copies the provider's `station` column to the MARIS-standard `STATION` column, filling missing values with an empty string.

# %% [markdown]
# Verify `AddStationCB` on mock data:

# %%
#| export
class AddStationCB(PerGroupCB):
    "Add station to all DataFrames."
    def each_grp(self, grp, df, tfm): df['STATION'] = df['station'].fillna('').astype(str)


# %%
# Verify AddStationCB on mock data
dfs_mock = {
    "SEAWATER": pd.DataFrame({"station": ["SD24", None]}),
    "BIOTA":    pd.DataFrame({"station": ["SD24"]}),
    "SEDIMENT": pd.DataFrame({"station": ["BY1", "BY2"]}),
}
tfm = Transformer(dfs_mock, cbs=[AddStationCB()])
tfm()

test_eq(tfm.dfs["SEAWATER"]["STATION"].to_list(), ["SD24", ""])
test_eq(tfm.dfs["BIOTA"]["STATION"].to_list(),    ["SD24"])
test_eq(tfm.dfs["SEDIMENT"]["STATION"].to_list(), ["BY1", "BY2"])
print("AddStationCB on mock data: all assertions passed.")

# %%
#| eval: false
tfm = Transformer(dfs, cbs=[AddStationCB()])
print(tfm()['SEAWATER'][['STATION']].head())


# %% [markdown]
# ## Add Temperature

# %% [markdown]
# :::{.callout-important}
# ## FEEDBACK TO DATA PROVIDER
#
# The HELCOM dataset includes a column for the temperature of the water (`ttemp`). According to the HELCOM documentation, the `ttemp` column represents:
# > 'Water temperature in Celsius (ºC) degrees of sampled water'
#
# In the SEAWATER dataset, 92 entries have temperature values greater than 50°C (all reading 99.9°C, concentrated in DHIG samples). These appear to be data entry errors and should be verified at source.
# :::

# %% [markdown]
# HELCOM stores water temperature in a `ttemp` column (degrees Celsius, present only in seawater data). `AddTemperatureCB` renames it to the MARIS-standard `TEMP` column and casts to float.

# %%
#| export
class AddTemperatureCB(PerGroupCB):
    "Add temperature (TEMP) from HELCOM ttemp column."
    grps = ['SEAWATER']
    def each_grp(self, grp, df, tfm): 
        df['TEMP'] = df['ttemp'].astype(float)



# %%
#| eval: false
tfm = Transformer(dfs, cbs=[AddTemperatureCB()])
dfs_out = tfm()
print(dfs_out['SEAWATER']['TEMP'].dropna().head())


# %% [markdown]
# ## Add slice position (TOP and BOTTOM)

# %% [markdown]
# HELCOM sediment cores record slice positions in `uppsli` (top of slice, cm) and `lowsli` (bottom of slice, cm) columns. `RemapSedSliceTopBottomCB` renames these to the MARIS-standard `TOP` and `BOTTOM` columns.

# %%
#| export
class RemapSedSliceTopBottomCB(PerGroupCB):
    "Remap Sediment slice top and bottom to MARIS format."
    grps = ['SEDIMENT']
    def each_grp(self, grp, df, tfm):
        df['TOP'] = df['uppsli']
        df['BOTTOM'] = df['lowsli']


# %%
# Verify RemapSedSliceTopBottomCB assigns TOP and BOTTOM correctly on mock data
dfs_mock = {'SEDIMENT': pd.DataFrame({'uppsli': [0.0, 5.0, 10.0], 'lowsli': [5.0, 10.0, 15.0]})}
tfm = Transformer(dfs_mock, cbs=[RemapSedSliceTopBottomCB()])
tfm()
test_eq(tfm.dfs['SEDIMENT']['TOP'].to_list(), [0.0, 5.0, 10.0])
test_eq(tfm.dfs['SEDIMENT']['BOTTOM'].to_list(), [5.0, 10.0, 15.0])
print("RemapSedSliceTopBottomCB on mock data: all assertions passed.")

# %%
#| eval: false
tfm = Transformer(dfs, cbs=[RemapSedSliceTopBottomCB()])
tfm()
print(tfm.dfs['SEDIMENT'][['TOP','BOTTOM']].head())


# %% [markdown]
# ## Compute weights

# %% [markdown]
# ### Clean basis codes

# %% [markdown]
# HELCOM BIOTA samples record a `basis` column with values D (dry weight), W (wet weight), and F. The HELCOM documentation only defines D and W.

# %% [markdown]
# ::: {.callout-important}
# ## FEEDBACK TO DATA PROVIDER
#
# The BIOTA dataset reports `F` in the `basis` column for 25 rows. The HELCOM guidelines only define D (dry weight) and W (wet weight). The `F` values appear to be fresh weight, which we treat as wet weight, but this should be confirmed or corrected at source.
# :::

# %% [markdown]
# We use `RemapCB` to convert `F` to `W`, leaving D and NaN unchanged.

# %%
#| exports
basis_fix = {'F': 'W'}


# %% [markdown]
# ### Compute weight variables

# %% [markdown]
# MARIS stores three weight-related variables:
# - `PERCENTWT` — dry weight as a decimal fraction of fresh weight (HELCOM `dw%` divided by 100)
# - `DRYWT` — dry weight in grams
# - `WETWT` — fresh weight in grams
#
# HELCOM provides `dw%` for both BIOTA and SEDIMENT. BIOTA also has a `weight` column whose interpretation depends on the `basis` column: if basis is D, `weight` is dry weight; if W, `weight` is wet weight. We derive the complementary weight using `PERCENTWT`.

# %% [markdown]
# ::: {.callout-important}
# ## FEEDBACK TO DATA PROVIDER
#
# **`dw%` > 100%** — 20 BIOTA rows and 625 SEDIMENT rows have a dry-weight percentage greater than 100%, which would imply the dry weight exceeds the fresh weight. These should be verified.
# :::

# %% [markdown]
# ::: {.callout-important}
# ## FEEDBACK TO DATA PROVIDER
#
# **`dw%` = 0%** — 6 BIOTA rows and 302 SEDIMENT rows have zero dry-weight percentage, which is physically impossible. We treat these as missing.
# :::

# %% [markdown]
# We define a dedicated callback rather than using the generic RemapCB because the basis column also feeds into the weight calculations below. Making the correction explicit keeps each step auditable.

# %%
#| export
class CleanBasisCB(PerGroupCB):
    "Map basis F to W (BIOTA)."
    grps = ['BIOTA']
    def each_grp(self, grp, df, tfm):
        df['basis'] = df['basis'].replace(basis_fix)


# %% [markdown]
# For SEDIMENT, the dw% column is the only weight information available. We divide by 100 to get a decimal fraction and drop zero values (physically impossible) as missing.

# %%
#| export
class PercentWeightCB(PerGroupCB):
    "Compute PERCENTWT = dw% / 100 (SEDIMENT)."
    grps = ['SEDIMENT']
    def each_grp(self, grp, df, tfm):
        df['PERCENTWT'] = df['dw%'] / 100
        df.loc[df['PERCENTWT'] == 0, 'PERCENTWT'] = np.nan


# %% [markdown]
# For BIOTA, we have both the percentage and the actual weight. The basis column tells us which weight (dry or wet) was recorded, so we can derive the other from PERCENTWT.

# %%
#| export
class WeightCB(PerGroupCB):
    "Compute DRYWT / WETWT from weight + basis (BIOTA)."
    grps = ['BIOTA']
    def each_grp(self, grp, df, tfm):
        df['PERCENTWT'] = df['dw%'] / 100
        df.loc[df['PERCENTWT'] == 0, 'PERCENTWT'] = np.nan
        for cond, col in [(df['basis'] == 'D', 'DRYWT'), (df['basis'] == 'W', 'WETWT')]:
            df.loc[cond, col] = df['weight']
        has = df['PERCENTWT'].notna()
        df.loc[(df['basis'] == 'D') & has, 'WETWT'] = df['weight'] / df['PERCENTWT']
        df.loc[(df['basis'] == 'W') & has, 'DRYWT'] = df['weight'] * df['PERCENTWT']


# %% [markdown]
# The mock test below checks all three callbacks work together: basis F→W correction, PERCENTWT computation (including zero → NaN), and the dry/wet derivation.

# %%
dfs_mock = {
    'BIOTA': pd.DataFrame({
        'basis': ['D', 'W', 'F'],
        'weight': [100.0, 200.0, 150.0],
        'dw%': [25.0, 30.0, 40.0],
    }),
    'SEDIMENT': pd.DataFrame({
        'dw%': [80.0, 0.0, 110.0],
    }),
}

tfm = Transformer(dfs_mock, cbs=[
    CleanBasisCB(),
    PercentWeightCB(),
    WeightCB(),
])
tfm()

b = tfm.dfs['BIOTA']
assert b['basis'].to_list() == ['D', 'W', 'W']
assert b['PERCENTWT'].to_list() == [0.25, 0.30, 0.40]
assert b['DRYWT'].to_list() == [100.0, 60.0, 60.0]
assert b['WETWT'].to_list() == [400.0, 200.0, 150.0]

s = tfm.dfs['SEDIMENT']
assert s['PERCENTWT'].to_list()[0] == 0.80
assert np.isnan(s['PERCENTWT'].to_list()[1])
assert s['PERCENTWT'].to_list()[2] == 1.10

print("All assertions passed. ✓")

# %% [markdown]
# **Usage on real data:**

# %%
#| eval: false
tfm = Transformer(dfs, cbs=[
    CleanBasisCB(),
    PercentWeightCB(),
    WeightCB(),
])
dfs_out = tfm()

cols = ['basis', 'dw%', 'PERCENTWT', 'weight', 'DRYWT', 'WETWT']
print(dfs_out['BIOTA'][cols].sample(5).to_string(index=False))

# %% [markdown]
# Running the pipeline on real HELCOM data shows the weight columns populated correctly, with NaN for rows where dw% was missing or zero.

# %%
#| eval: false
cols = ['dw%', 'PERCENTWT']
print(dfs_out['SEDIMENT'].dropna(subset=['dw%'])[cols].head(3).to_string(index=False))

# %%
#| eval: false
cols = ['dw%', 'PERCENTWT']
print(tfm.dfs['SEDIMENT'].dropna(subset=['dw%'])[cols].head(3).to_string(index=False))


# %% [markdown]
# ## Standardize Coordinates

# %% [markdown]
# HELCOM provides geographical coordinates in two formats per lat/lon: decimal degrees (`dddddd`) and degrees+minutes (`ddmmmm`). Column names vary by sample type: BIOTA uses `'latitude dddddd'` while SEAWATER and SEDIMENT use `'latitude (dddddd)'` (with parentheses). `ParseCoordinatesCB` finds the columns by substring matching, prefers decimal degrees, and falls back to the ddmmmm format when the decimal value is missing or zero.

# %% [markdown]
# :::{.callout-important}
# ## FEEDBACK TO DATA PROVIDER
#
# Coordinate column names are inconsistent: BIOTA omits parentheses (`latitude dddddd`), SEAWATER and SEDIMENT include them (`latitude (dddddd)`). This should be standardised at source.
#
# Eight SEAWATER rows have zero or NaN values for both latitude and longitude; these are dropped.
# :::

# %% [markdown]
# `ParseCoordinatesCB` works in two steps. First, it finds the four coordinate columns by
# scanning for names containing `lat`/`lon` and `dddddd`/`ddmmmm`. Second, for each row
# it reads the decimal-degree column; if the value is missing or zero, it falls back to
# the degree-minute column (converting via `ddmm_to_dd`). Rows where both formats are
# missing or zero are dropped.

# %%
#| export
class ParseCoordinatesCB(PerGroupCB):
    "Parse lat/lon from decimal-degree or degree-minute columns, preferring decimal."
    def __init__(self, fn_convert_cor):
        store_attr()

   
    def each_grp(self, grp, df, tfm):
        cols = df.columns
        lat_d = next(c for c in cols if 'lat' in c.lower() and 'dddddd' in c.lower())
        lat_m = next(c for c in cols if 'lat' in c.lower() and 'ddmmmm' in c.lower())
        lon_d = next(c for c in cols if 'lon' in c.lower() and 'dddddd' in c.lower())
        lon_m = next(c for c in cols if 'lon' in c.lower() and 'ddmmmm' in c.lower())

        for dec_c, min_c, name in [(lon_d, lon_m, 'LON'), (lat_d, lat_m, 'LAT')]:
            dec = pd.to_numeric(df[dec_c], errors='coerce')
            minute = pd.to_numeric(df[min_c], errors='coerce')
            df[name] = dec
            mask = (dec.isna() | (dec == 0)) & minute.notna()
            df.loc[mask, name] = minute[mask].apply(self.fn_convert_cor)

        tfm.dfs[grp] = df[(df['LAT'].notna()) & (df['LON'].notna()) & (df['LAT'] != 0) & (df['LON'] != 0)]


# %% [markdown]
# Verify ParseCoordinatesCB on mock data. Row 1 has valid decimal degrees. Row 2 has zero decimal, falling back to ddmmmm (5420 → 54.3333). Row 3 has both missing and is dropped.

# %%
dfs_mock = {'SEAWATER': pd.DataFrame({
    'latitude (dddddd)': [54.28, 0, np.nan, 61.50, 0],
    'latitude (ddmmmm)': [np.nan, 54.20, 54.20, np.nan, np.nan],
    'longitude (dddddd)': [12.32, 0, np.nan, 21.40, 0],
    'longitude (ddmmmm)': [np.nan, 12.15, 12.15, np.nan, np.nan],
})}
tfm = Transformer(dfs_mock, cbs=[ParseCoordinatesCB(ddmm_to_dd)])
tfm()

# Row 0: valid decimal → used as-is
# Row 1: zero decimal → fallback to ddmmmm (54.20 → 54.3333, 12.15 → 12.25)
# Row 2: NaN decimal → fallback to ddmmmm
# Row 3: valid decimal with ddmmmm available → still uses decimal
# Row 4: zero decimal + NaN minute → stays 0 / 0 → dropped
test_eq(tfm.dfs['SEAWATER']['LAT'].to_list(), [54.28, 54.333333, 54.333333, 61.5])
test_eq(tfm.dfs['SEAWATER']['LON'].to_list(), [12.32, 12.25, 12.25, 21.4])
test_eq(len(tfm.dfs['SEAWATER']), 4)
print("ParseCoordinatesCB on mock data: all assertions passed. ✓")


# %%
#| eval: false
tfm = Transformer(dfs, cbs=[ParseCoordinatesCB(ddmm_to_dd)])
dfs_out = tfm()
print(dfs_out['BIOTA'][['LAT', 'LON']].head())

# %% [markdown]
# ## NetCDF encoder

# %%
#| eval: false
tfm = Transformer(dfs, cbs=[
    # Nuclide normalisation and mapping
    LowerStripNameCB(col_src='nuclide', col_dst='NUCLIDE'),
    RemapCB(lut=nuclide_lut, col_remap='NUCLIDE', col_src='NUCLIDE'),

    # Time
    ParseTimeCB(),
    EncodeTimeCB(),

    # Value columns (sediment melt, value, uncertainty)
    MeltSedimentValuesCB(coi_sediment),
    SanitizeValueCB(coi_val),
    NormalizeUncCB(),

    # Unit and detection limit
    RemapUnitCB(),
    RemapDetectionLimitCB(coi_dl),

    # BIOTA lookups: species, body part, biological group
    RemapCB(lut=species_lut, col_remap='SPECIES', col_src='rubin', grps=['BIOTA']),
    RemapCB(lut=lut_tissues, col_remap='BODY_PART', col_src='tissue', grps=['BIOTA']),
    RemapCB(lut=lut_biogroup, col_remap='BIO_GROUP', col_src='SPECIES', grps=['BIOTA']),

    # Sediment type
    CleanSedimentCodesCB(replace_lut=sed_replace_lut),
    RemapCB(lut=sediment_lut, col_remap='SED_TYPE', col_src='sedi', grps=['SEDIMENT']),

    # Filtering status (seawater)
    RemapCB(lut=lut_filtered, col_remap='FILT', col_src='filt', grps=['SEAWATER']),

    # Sample identifiers
    AddSampleIDCB(),

    # Depth, salinity, temperature
    AddDepthCB(),
    AddSalinityCB(),
    AddTemperatureCB(),

    # Sediment slice positions
    RemapSedSliceTopBottomCB(),

    # Weights (BIOTA and SEDIMENT)
    CleanBasisCB(),
    PercentWeightCB(),
    WeightCB(),

    # Coordinates
    ParseCoordinatesCB(ddmm_to_dd),
    SanitizeLonLatCB(),

    # Station
    AddStationCB()
])

dfs_out = tfm()
print(dfs_out['BIOTA'].head())

# %% [markdown]
# ### Example change logs

# %%
tfm.logs

# %% [markdown]
# ### Feed global attributes

# %%
#| export
kw = ['oceanography', 'Earth Science > Oceans > Ocean Chemistry> Radionuclides',
      'Earth Science > Human Dimensions > Environmental Impacts > Nuclear Radiation Exposure',
      'Earth Science > Oceans > Ocean Chemistry > Ocean Tracers, Earth Science > Oceans > Marine Sediments',
      'Earth Science > Oceans > Ocean Chemistry, Earth Science > Oceans > Sea Ice > Isotopes',
      'Earth Science > Oceans > Water Quality > Ocean Contaminants',
      'Earth Science > Biological Classification > Animals/Vertebrates > Fish',
      'Earth Science > Biosphere > Ecosystems > Marine Ecosystems',
      'Earth Science > Biological Classification > Animals/Invertebrates > Mollusks',
      'Earth Science > Biological Classification > Animals/Invertebrates > Arthropods > Crustaceans',
      'Earth Science > Biological Classification > Plants > Macroalgae (Seaweeds)']


# %%
#| exports
def get_attrs(
    tfm: Transformer, # Transformer object
    zotero_key: str, # Zotero dataset record key
    kw: list = kw # List of keywords
    ) -> dict: # Global attributes
    "Retrieve all global attributes."
    return GlobAttrsFeeder(tfm.dfs, cbs=[
        BboxCB(),
        DepthRangeCB(),
        TimeRangeCB(),
        ZoteroCB(zotero_key),
        KeyValuePairCB('keywords', ', '.join(kw)),
        KeyValuePairCB('publisher_postprocess_logs', ', '.join(tfm.logs))
        ])()


# %%
#| eval: false
get_attrs(tfm, zotero_key=zotero_key, kw=kw)


# %% [markdown]
# ### Encoding

# %%
#| exports
def encode(
    fname_out: str, # Output file name
    **kwargs # Additional arguments
    ) -> None:
    "Encode data to NetCDF."
    dfs = load_data(src_dir)
    tfm = Transformer(dfs, cbs=[
                            LowerStripNameCB(col_src='nuclide', col_dst='NUCLIDE'),
                            RemapCB(lut=nuclide_lut, col_remap='NUCLIDE', col_src='NUCLIDE'),
                            ParseTimeCB(),
                            EncodeTimeCB(),
                            MeltSedimentValuesCB(coi_sediment),
                            SanitizeValueCB(coi_val),
                            NormalizeUncCB(),
                            RemapUnitCB(),
                            RemapDetectionLimitCB(coi_dl),
                            RemapCB(lut=species_lut, col_remap='SPECIES', col_src='rubin', grps=['BIOTA']),
                            RemapCB(lut=lut_tissues, col_remap='BODY_PART', col_src='tissue', grps=['BIOTA']),
                            RemapCB(lut=lut_biogroup, col_remap='BIO_GROUP', col_src='SPECIES', grps=['BIOTA']),
                            CleanSedimentCodesCB(replace_lut=sed_replace_lut),
                            RemapCB(lut=sediment_lut, col_remap='SED_TYPE', col_src='sedi', grps=['SEDIMENT']),
                            RemapCB(lut=lut_filtered, col_remap='FILT', col_src='filt', grps=['SEAWATER']),
                            AddSampleIDCB(),
                            AddDepthCB(),
                            AddSalinityCB(),
                            AddTemperatureCB(),
                            RemapSedSliceTopBottomCB(),
                            CleanBasisCB(),
                            PercentWeightCB(),
                            WeightCB(),
                            ParseCoordinatesCB(ddmm_to_dd),
                            SanitizeLonLatCB(),
                            AddStationCB()
                            ])
    tfm()
    encoder = NetCDFEncoder(tfm.dfs, 
                            dest_fname=fname_out, 
                            global_attrs=get_attrs(tfm, zotero_key=zotero_key, kw=kw),
                            # custom_maps=tfm.custom_maps,
                            verbose=kwargs.get('verbose', False),
                           )
    encoder.encode()


# %%
#|eval: false
encode(fname_out, verbose=False)

# %% [markdown]
# ## NetCDF → CSV (MARIS DB import) 
#
# The MARIS data processing workflow involves two key steps:
#
# 1. **NetCDF to Standardized CSV Compatible with OpenRefine Pipeline**
#    - Convert standardized NetCDF files to CSV formats compatible with OpenRefine using the `NetCDFDecoder`.
#    - Preserve data integrity and variable relationships.
#    - Maintain standardized nomenclature and units.
#
# 2. **Database Integration**
#    - Process the converted CSV files using OpenRefine.
#    - Apply data cleaning and standardization rules.
#    - Export validated data to the MARIS master database.
#
# This section focuses on the first step: converting NetCDF files to a format suitable for OpenRefine processing using the `NetCDFDecoder` class.

# %%
#|eval: false
#decode(fname_in=fname_out, verbose=True)
