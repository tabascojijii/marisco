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
#| default_exp handlers.geotraces

# %% [markdown]
# # Geotraces

# %% [markdown]
# The [BODC GEOTRACES Intermediate Data Product 2021](https://www.geotraces.org/geotraces-intermediate-data-product-2021/) is one of the most comprehensive compilations of ocean radionuclide measurements to date, assembling water-column and suspended-particulate data from international oceanographic cruises worldwide.
#
# This notebook documents the full curation workflow applied to bring that dataset into alignment with [MARIS](https://maris.iaea.org) data standards: selecting the radionuclide variables within MARIS scope, reshaping the wide-format source, extracting metadata encoded in column names (unit, filtering status, sampling method), standardising nuclide nomenclature, coordinates, and units, and splitting measurements into SEAWATER and SUSPENDED_MATTER groups before encoding as a self-contained NetCDF4 file. The same workflow can be run end-to-end without inspecting the notebook via the `maris_to_nc` CLI tool.
#
# Our approach is inspired by [Literate Programming](https://www.wikiwand.com/en/articles/Literate_programming): code and explanation live side by side so data providers can follow the reasoning behind every curation decision and data users can understand exactly what was done to the data and why. Where the raw data contains inconsistencies or opportunities for improvement, they are flagged directly in the relevant section as feedback for future releases.

# %%
#| hide
from nbdev.showdoc import show_doc
# %load_ext autoreload
# %autoreload 2

# %%
#| export
from fastcore.all import *
import pandas as pd
import numpy as np
import re

from marisco.callbacks import (
    Callback, 
    PerGroupCB,
    Transformer, 
    ParseTimeCB,
    SanitizeLonLatCB, 
    EncodeTimeCB,
    RemapCB
)

from marisco.metadata import (
    GlobAttrsFeeder, 
    BboxCB,
    DepthRangeCB, 
    TimeRangeCB,
    ZoteroCB,
    KeyValuePairCB
)

from marisco.configs import AVOGADRO, get_lut, lut_path

from marisco.netcdf2csv import decode
from marisco.encoders import NetCDFEncoder

# %%
#| hide
import warnings
pd.set_option('display.max_rows', 200)
warnings.filterwarnings('ignore')

# %% [markdown]
# ## Configuration & file paths

# %% [markdown]
# - **fname_in**: path to the folder containing the HELCOM data in CSV format. The path can be defined as a relative path. 
#
# - **fname_out**: path and filename for the NetCDF output.The path can be defined as a relative path. 
#
# - **Zotero key**: used to retrieve attributes related to the dataset from [Zotero](https://www.zotero.org/). The MARIS datasets include a [library](https://maris.iaea.org/datasets) available on [Zotero](https://www.zotero.org/groups/2432820/maris/library). 
#

# %%
# | exports
fname_in = '../../_data/geotraces/GEOTRACES_IDP2021_v2/seawater/ascii/GEOTRACES_IDP2021_Seawater_Discrete_Sample_Data_v2.csv'
fname_out = '../../_data/output/190-geotraces-2021.nc'
zotero_key = '97UIMEXN'

# %% [markdown]
# ## Load data

# %%
#| exports
load_data = lambda fname: pd.read_csv(fname_in)

# %%
#| eval: false
df = load_data(fname_in)

# %%
print(f'df shape: {df.shape}')
df.columns

# %% [markdown]
# ## Select columns of interest

# %% [markdown]
# The raw Geotraces CSV arrives in [**wide**](https://data.europa.eu/apps/data-visualisation-guide/wide-versus-long-data) format with 1,188 columns; mostly non-radionuclide parameters (nutrients, trace metals, quality flags) outside MARIS scope. The first step is to select only the radionuclide columns: `common_coi` lists the 6 metadata columns always kept as identifiers, and `nuclides_pattern` matches 80 measurement columns, reducing the table to 86. The regex patterns match on measurement column names, so companion quality-flag (`QV:`) columns are naturally excluded. The wide structure is then reshaped to long form in a later step.

# %%
#| exports
# Metadata columns always kept as identifiers when reshaping wide → long
common_coi = ['yyyy-mm-ddThh:mm:ss.sss', 'Longitude [degrees_east]',
              'Latitude [degrees_north]', 'Bot. Depth [m]', 'DEPTH [m]', 'BODC Bottle Number:INTEGER']

# Regex patterns identifying radionuclide measurement columns
nuclides_pattern = ['^TRITI', '^Th_228', '^Th_23[024]', '^Pa_231', 
                    '^U_236_[DT]', '^Be_', '^Cs_137', '^Pb_210', '^Po_210',
                    '^Ra_22[3468]', '^Np_237', '^Pu_239_[D]', '^Pu_240', '^Pu_239_Pu_240',
                    '^I_129', '^Ac_227']  


# %%
#| export
class SelectColsOfInterestCB(Callback):
    "Select columns of interest from the wide Geotraces dataframe."
    def __init__(self,
                 common_coi: list,       # Non-nuclide columns always kept as id_vars
                 nuclides_pattern: list  # Regex patterns matching nuclide column names
                 ): store_attr()
    def __call__(self, tfm):
        nuc_of_interest = [c for c in tfm.df.columns if 
                           any(re.match(pattern, c) for pattern in self.nuclides_pattern)]
        tfm.df = tfm.df[self.common_coi + nuc_of_interest]


# %% [markdown]
# For instance: 

# %%
tfm = Transformer(df, cbs=[
    SelectColsOfInterestCB(common_coi, nuclides_pattern)
])

df_test = tfm()

# %%
print(f'First ten cols: {df_test.columns[:10]}')

# All metadata columns preserved
for col in common_coi: test_eq(col in df_test.columns, True)

# Quality flag columns stripped
test_eq(any('QV:' in c for c in df_test.columns), False)

# %% [markdown]
# **Columns matched by the nuclides patterns**  
# From the 1,188 raw columns, the patterns above select these 80 radionuclide measurement columns:

# %% hide_input=true
#| echo: false
#| output: true
# Actually load the data — just the column names
df_cols = pd.read_csv(fname_in, nrows=0)  # just the header

nuclides_pattern = ['^TRITI', '^Th_228', '^Th_23[024]', '^Pa_231', 
                    '^U_236_[DT]', '^Be_', '^Cs_137', '^Pb_210', '^Po_210',
                    '^Ra_22[3468]', '^Np_237', '^Pu_239_[D]', '^Pu_240', '^Pu_239_Pu_240',
                    '^I_129', '^Ac_227']

for pat in nuclides_pattern:
    matched = [c for c in df.columns if re.match(pat, c)]
    print(f"  {pat:20s} → {len(matched):2d} cols  e.g. {matched[:3]}")
print(f"\nTotal nuclide columns selected: {sum(1 for c in df_cols.columns if any(re.match(p,c) for p in nuclides_pattern))} of {len(df.columns)}")


# %% [markdown]
# ## Reshape: wide to long
#
# The raw Geotraces CSV is in wide format: each row holds up to 80 radionuclide
# measurements crammed into separate columns, and metadata like unit, sampling
# methodology, and filter status is embedded in the column names themselves (e.g.
# `Th_230_D_CONC_BOTTLE [uBq/kg]`). This is unworkable for curation. Melting to
# long format folds all measurements into a single `VALUE` column and a `NUCLIDE`
# column that carries the full column-name string; which we can then parse to
# extract unit, method, and filter status in the next step.

# %%
#| export
class WideToLongCB(Callback):
    "Reshape wide nuclide columns to long format so unit, method, and filter status can be extracted from column names."
    def __init__(self,
                 common_coi: list,         # Non-nuclide columns kept as id_vars in melt
                 nuclides_pattern: list,   # Regex patterns identifying nuclide columns
                 var_name: str='NUCLIDE',  # Output column name for nuclide identifiers
                 value_name: str='VALUE',  # Output column name for measurement values
                 ): 
        store_attr()
        
    def __call__(self, tfm):
        nuc_of_interest = [c for c in tfm.df.columns if 
                           any(re.match(pattern, c) for pattern in self.nuclides_pattern)]
        tfm.df = pd.melt(tfm.df, id_vars=self.common_coi, value_vars=nuc_of_interest, 
                          var_name=self.var_name, value_name=self.value_name)
        tfm.df.dropna(subset=self.value_name, inplace=True)


# %%
tfm = Transformer(df, cbs=[
    SelectColsOfInterestCB(common_coi, nuclides_pattern),
    WideToLongCB(common_coi, nuclides_pattern)
])
df_test = tfm()

# %%
print(f'Long format: {df_test.shape[0]} rows × {df_test.shape[1]} cols')
# id columns all preserved
for col in common_coi: test_eq(col in df_test.columns, True)
# nuclide name and value columns created
test_eq('NUCLIDE' in df_test.columns, True)
test_eq('VALUE' in df_test.columns, True)
# no original wide nuclide columns remain
test_eq(any(re.match(p, c) for p in nuclides_pattern for c in df_test.columns), False)


# %% [markdown]
# ## Extract

# %% [markdown]
# Geotraces encodes **unit**, **filtering status**, and **sampling method** inside the column names themselves, for example `Th_230_D_CONC_BOTTLE [uBq/kg]` holds all three. These need to be parsed out into dedicated columns before they can drive unit conversion, MARIS nomenclature mapping, and quality checks.

# %% [markdown]
# ### Unit

# %% [markdown]
# Units appear in square brackets at the end of every nuclide column name. The five distinct units found in this dataset are `uBq/kg`, `mBq/kg`, `TU`, `atoms/kg`, and `pmol/kg`; each needs to be mapped to the corresponding MARIS unit code in a later step.

# %%
#| export
class ExtractUnitCB(Callback):
    "Extract measurement unit from nuclide column names (e.g. 'Cs_137_D_CONC_BOTTLE [uBq/kg]' → 'uBq/kg')."
    def __init__(self,
                 var_name: str='NUCLIDE'  # Column containing nuclide names with embedded units in brackets
                 ): 
        store_attr()
        self.unit_col_name = 'UNIT'

    def extract_unit(self, s):
        match = re.search(r'\[(.*?)\]', s)
        return match.group(1) if match else None
        
    def __call__(self, tfm):
        tfm.df[self.unit_col_name] = tfm.df[self.var_name].apply(self.extract_unit)


# %%
tfm = Transformer(df, cbs=[
    SelectColsOfInterestCB(common_coi, nuclides_pattern),
    WideToLongCB(common_coi, nuclides_pattern),
    ExtractUnitCB()
])
df_test = tfm()

# %%
print(f'Units found: {sorted(df_test.UNIT.unique())}')
test_eq('UNIT' in df_test.columns, True)
test_eq(set(df_test.UNIT.unique()), {'TU', 'uBq/kg', 'atoms/kg', 'mBq/kg', 'pmol/kg'})

# %% [markdown]
# ### Filtering status

# %% [markdown]
# Phase codes embedded in nuclide column names encode both filtering status and sample type group. The second underscore component after the nuclide name indicates the phase: `D` (dissolved, FILT=1, SEAWATER), `T` (total, FILT=2, SEAWATER), and `TP` / `LPT` / `SPT` (suspended particulate matter fractions, all FILT=1, SUSPENDED_MATTER). These are parsed into dedicated `FILT` and `GROUP` columns that drive sample type classification and downstream quality checks.

# %%
#| exports
# Phase code embedded in column names → FILT status and sample type group
phase = {
    'D': {'FILT': 1, 'group': 'SEAWATER'},
    'T': {'FILT': 2, 'group': 'SEAWATER'},
    'TP': {'FILT': 1, 'group': 'SUSPENDED_MATTER'}, 
    'LPT': {'FILT': 1, 'group': 'SUSPENDED_MATTER'},
    'SPT': {'FILT': 1, 'group': 'SUSPENDED_MATTER'}}


# %%
#| export
class ExtractFilteringStatusCB(Callback):
    "Extract filtering status and sample-type group from nuclide column names using phase code (e.g. _D_, _T_, _TP_)."
    def __init__(self,
                 phase: dict,              # Phase code → {FILT, group} mapping (e.g. {'D': {'FILT': 1, 'group': 'SEAWATER'}})
                 var_name: str='NUCLIDE'   # Column containing nuclide names with embedded phase codes
                 ): 
        store_attr()
        self.filt_col_name = 'FILT'

    def extract_filt_status(self, s):
        matched_string = self.match(s)
        return self.phase[matched_string.group(1)][self.filt_col_name] if matched_string else None

    def match(self, s):
        return re.search(r'_(' + '|'.join(self.phase.keys()) + ')_', s)
        
    def extract_group(self, s):
        matched_string = self.match(s)
        return self.phase[matched_string.group(1)]['group'] if matched_string else None
        
    def __call__(self, tfm):
        tfm.df[self.filt_col_name] = tfm.df[self.var_name].apply(self.extract_filt_status)
        tfm.df['GROUP'] = tfm.df[self.var_name].apply(self.extract_group)


# %%
tfm = Transformer(df, cbs=[
    SelectColsOfInterestCB(common_coi, nuclides_pattern),
    WideToLongCB(common_coi, nuclides_pattern),
    ExtractUnitCB(),
    ExtractFilteringStatusCB(phase)
])
df_test = tfm()

# %%
print(f'Groups found: {sorted(df_test.GROUP.dropna().unique())}')
print(f'Filtering values: {sorted(df_test.FILT.dropna().unique())}')
test_eq('FILT' in df_test.columns, True)
test_eq('GROUP' in df_test.columns, True)
test_eq(set(df_test.GROUP.dropna().unique()), {'SEAWATER', 'SUSPENDED_MATTER'})
test_eq(set(df_test.FILT.dropna().unique()).issubset({1, 2}), True)

# %% [markdown]
# ### Sampling method

# %% [markdown]
# Sampling method codes appear as the last underscore component before the unit brackets in nuclide column names, for example `BOTTLE` in `Th_230_D_CONC_BOTTLE [uBq/kg]`. The four distinct methods found in this dataset are `BOTTLE` (rosette/CTD bottle, code 1), `FISH` (continuous towfish, code 18), `PUMP` (in situ pump, code 14), and `UWAY` (underway uncontaminated seawater supply, code 24). These are mapped to MARIS sampling method codes and recorded in the `SAMP_MET` column, enabling sample classification and cross dataset comparisons between different collection techniques.

# %%
#| exports
# Sampling method code → MARIS method ID mapping (to be validated)
smp_method = {
    'BOTTLE': 1,
    'FISH': 18,
    'PUMP': 14,
    'UWAY': 24}


# %%
#| export
class ExtractSamplingMethodCB(Callback):
    "Extract sampling method from nuclide names."
    def __init__(self, 
                 smp_method:dict = smp_method, # Sampling method lookup table
                 var_name='NUCLIDE',            # Column name containing nuclide names
                 smp_method_col_name = 'SAMP_MET' # Column name for sampling method in output df
                 ): 
        store_attr()

    def extract_smp_method(self, s):
        match = re.search(r'_(' + '|'.join(self.smp_method.keys()) + ') ', s)
        return self.smp_method[match.group(1)] if match else None
        
    def __call__(self, tfm):
        tfm.df[self.smp_method_col_name] = tfm.df[self.var_name].apply(self.extract_smp_method)


# %%
tfm = Transformer(df, cbs=[
    SelectColsOfInterestCB(common_coi, nuclides_pattern),
    WideToLongCB(common_coi, nuclides_pattern),
    ExtractUnitCB(),
    ExtractFilteringStatusCB(phase),
    ExtractSamplingMethodCB(smp_method)
])
df_test = tfm()

# %%
print(f'Sampling methods found: {sorted(df_test.SAMP_MET.dropna().unique())}')
test_eq('SAMP_MET' in df_test.columns, True)
test_eq(set(df_test.SAMP_MET.dropna().unique()).issubset(set(smp_method.values())), True)

# %% [markdown]
# ## Remap to MARIS nuclide names 

# %% [markdown]
# Geotraces nuclide column names begin with provider-specific strings (e.g. `TRITIUM`, `Pu_239_Pu_240`, `Th_230`, `U_236`) that must be remapped to MARIS standard nomenclature before any lookup tables can be applied. Most names follow a regular pattern: strip the phase-code suffix (`_D`, `_T`, `_TP`, etc.), then lowercase and remove underscores — `Th_230` becomes `th230`, `U_236` becomes `u236`. Two exceptions need explicit overrides: `TRITIUM` maps to `h3` (the standard nuclide symbol for tritium), and `Pu_239_Pu_240` is a combined total activity that MARIS records as `pu239_240_tot`. The `RenameNuclideCB` applies the override dictionary first, then falls back to the general lowercasing rule for everything else.

# %%
#| exports
# Provider-specific nuclide name overrides for MARIS standardisation
nuclides_name = {'TRITIUM': 'h3', 'Pu_239_Pu_240': 'pu239_240_tot'}


# %%
#| export
class RenameNuclideCB(Callback):
    "Remap nuclides name to MARIS standard."
    def __init__(self,
                 nuclides_name: dict,     # Provider-specific name overrides e.g. {'TRITIUM': 'h3'}
                 var_name: str='NUCLIDE'  # Column containing nuclide names to standardize
                 ): 
        store_attr()
        self.patterns = ['_D', '_T', '_TP', '_LPT', '_SPT']

    def extract_nuclide_name(self, s):
        match = re.search(r'(.*?)(' + '|'.join(self.patterns) + ')', s)
        return match.group(1) if match else None

    def standardize_name(self, s):
        s = self.extract_nuclide_name(s)
        return self.nuclides_name[s] if s in self.nuclides_name else s.lower().replace('_', '')
        
    def __call__(self, tfm):
        tfm.df[self.var_name] = tfm.df[self.var_name].apply(self.standardize_name)


# %%
tfm = Transformer(df, cbs=[
    SelectColsOfInterestCB(common_coi, nuclides_pattern),
    WideToLongCB(common_coi, nuclides_pattern),
    ExtractUnitCB(),
    ExtractFilteringStatusCB(phase),
    ExtractSamplingMethodCB(smp_method),
    RenameNuclideCB(nuclides_name)
])
df_test = tfm()

# %%
nuclides = set(df_test.NUCLIDE.unique())
print(f'Nuclides after rename: {sorted(nuclides)}')
test_eq('h3' in nuclides, True)              # TRITIUM → h3 override
test_eq('pu239_240_tot' in nuclides, True)   # Pu_239_Pu_240 special case
test_eq(all(n == n.lower() for n in nuclides), True)  # all names lowercased

# %%
#| eval: false
df_test.NUCLIDE.unique()

# %% [markdown]
# :::{.callout-important}
# ## FEEDBACK TO DATA PROVIDER
#
# Several measurements are negative (see grouped counts below). Please review these values and provide detection-limit flags or handling guidance in future data releases.
#
# :::

# %%
#| eval: false
df_test[df_test.VALUE < 0].groupby('NUCLIDE').size()

# %% [markdown]
# ## Standardize unit

# %% [markdown]
# Geotraces encodes units inside nuclide column names, and five distinct
# units appear across the dataset: TU, uBq/kg, mBq/kg, atoms/kg, and
# pmol/kg. Some of these share a common MARIS unit ID despite different
# magnitudes — uBq/kg and mBq/kg both map to unit ID 3 but differ by a
# factor of 1000, which must be accounted for in the conversion factor.
# Similarly, pmol/kg must be converted via Avogadro's number before it
# matches the atoms/kg unit ID. The mapping below handles both the unit
# remapping and the value rescaling:

# %%
#| exports
# Geotraces unit → MARIS unit ID and conversion factor mapping
units_lut = {
    'TU': {'id': 7, 'factor': 1},
    'uBq/kg': {'id': 3, 'factor': 1e-6},
    'atoms/kg': {'id': 9, 'factor': 1},
    'mBq/kg': {'id': 3, 'factor': 1e-3},
    'pmol/kg': {'id': 9, 'factor': 1e-12 * AVOGADRO}
    }


# %%
#| export
class StandardizeUnitCB(Callback):
    "Remap Geotraces unit strings to MARIS unit IDs, rescaling measurement values by the appropriate conversion factor where units share a common MARIS unit ID (e.g. uBq/kg and mBq/kg both map to ID 3 but differ 1000x)."
    def __init__(self, 
                 units_lut: dict,              # Unit string → {id, factor} conversion mapping
                 unit_col_name: str='UNIT',    # Column containing unit strings to remap
                 var_name: str='VALUE'         # Column containing measurement values to rescale
                 ): 
        store_attr()
        
    def __call__(self, tfm):
        # Convert/rescale values
        tfm.df[self.var_name] *= tfm.df[self.unit_col_name].map(
            {k: v['factor'] for k, v in self.units_lut.items()})
        
        # Match MARIS unit id
        tfm.df[self.unit_col_name] = tfm.df[self.unit_col_name].map(
            {k: v['id'] for k, v in self.units_lut.items()})


# %%
tfm = Transformer(df, cbs=[
    SelectColsOfInterestCB(common_coi, nuclides_pattern),
    WideToLongCB(common_coi, nuclides_pattern),
    ExtractUnitCB(),
    ExtractFilteringStatusCB(phase),
    ExtractSamplingMethodCB(smp_method),
    RenameNuclideCB(nuclides_name),
    StandardizeUnitCB(units_lut)
])
df_test = tfm()

# %%
print(f'Unit IDs after standardization: {sorted(df_test.UNIT.unique())}')
test_eq(set(df_test.UNIT.unique()), {3, 7, 9})  # TU→7, uBq/kg+mBq/kg→3, atoms/kg+pmol/kg→9

# %% [markdown]
# ## Rename common columns

# %% [markdown]
# Geotraces uses provider-specific column names for coordinates, depth, and sample identifiers — with units and metadata embedded as suffixes in brackets — that don't match MARIS standard nomenclature (TIME, LON, LAT, TOT_DEPTH, SMP_DEPTH, SMP_ID_PROVIDER). These are remapped via `RenameColumnCB` before NetCDF encoding.

# %%
#| exports
# Geotraces column name → MARIS standard name mapping
renaming_rules = {
    'yyyy-mm-ddThh:mm:ss.sss': 'TIME',
    'Longitude [degrees_east]': 'LON',
    'Latitude [degrees_north]': 'LAT',
    'DEPTH [m]': 'SMP_DEPTH',
    'Bot. Depth [m]': 'TOT_DEPTH',
    'BODC Bottle Number:INTEGER': 'SMP_ID_PROVIDER'
}


# %%
#| export
class RenameColumnCB(Callback):
    "Remap Geotraces-specific coordinate, depth, and sample-ID column names to MARIS standard nomenclature."
    def __init__(self,
                 lut: dict=renaming_rules  # Provider column name → MARIS standard name mapping
                 ): store_attr()
    def __call__(self, tfm):
        new_col_names = [self.lut[name] if name in self.lut else name for name in tfm.df.columns]
        tfm.df.columns = new_col_names


# %%
tfm = Transformer(df, cbs=[
    SelectColsOfInterestCB(common_coi, nuclides_pattern),
    WideToLongCB(common_coi, nuclides_pattern),
    ExtractUnitCB(),
    ExtractFilteringStatusCB(phase),
    ExtractSamplingMethodCB(smp_method),
    RenameNuclideCB(nuclides_name),
    StandardizeUnitCB(units_lut),
    RenameColumnCB(renaming_rules)
])
df_test = tfm()

# %%
print(f'Columns after rename: {list(df_test.columns)}')
# MARIS standard names present
for new_name in renaming_rules.values(): test_eq(new_name in df_test.columns, True)
# Provider names removed
for old_name in renaming_rules.keys(): test_eq(old_name in df_test.columns, False)


# %% [markdown]
# ## Unshift longitudes

# %% [markdown]
# Geotraces encodes longitudes in the [0, 360] range (e.g. 230°E instead of −130°), which is incompatible with the MARIS [-180, 180] convention. The callback subtracts 180 to realign all longitudes to the standard range.

# %%
#| export
class UnshiftLongitudeCB(Callback):
    "Shift longitudes from Geotraces [0, 360] convention to MARIS [-180, 180] by subtracting 180."
    def __init__(self,
                 lon_col_name: str='LON'  # Column containing longitudes in [0, 360] to shift
                 ): 
        store_attr()
    def __call__(self, tfm):
        tfm.df[self.lon_col_name] = tfm.df[self.lon_col_name] - 180


# %%
tfm = Transformer(df, cbs=[
    SelectColsOfInterestCB(common_coi, nuclides_pattern),
    WideToLongCB(common_coi, nuclides_pattern),
    ExtractUnitCB(),
    ExtractFilteringStatusCB(phase),
    ExtractSamplingMethodCB(smp_method),
    RenameNuclideCB(nuclides_name),
    StandardizeUnitCB(units_lut),
    RenameColumnCB(renaming_rules),
    UnshiftLongitudeCB()
])
df_test = tfm()

# %%
print(f'LON range: [{df_test.LON.min():.4f}, {df_test.LON.max():.4f}]')
test_eq(df_test.LON.between(-180, 180).all(), True)


# %% [markdown]
# ## Dispatch to groups

# %% [markdown]
# The pipeline so far produces a single flat dataframe containing both seawater and suspended-particulate-matter measurements side by side. These two sample types belong to separate NetCDF4 groups (and use different units, different detection-limit conventions, etc.), so they need to be split into per-group dataframes before encoding. The `DispatchToGroupCB` partitions the flat result by the `GROUP` column and drops the column — the group label becomes the dict key rather than persisting as a data column.

# %%
#| export
class DispatchToGroupCB(Callback):
    "Split flat dataframe into per-group dict keyed by sample type (SEAWATER, SUSPENDED_MATTER, …)."
    def __init__(self,
                 group_name: str='GROUP'  # Column whose distinct values become the output dict keys
                 ): 
        store_attr()
        
    def __call__(self, tfm):
        tfm.dfs = dict(tuple(tfm.df.groupby(self.group_name)))
        for key in tfm.dfs:
            tfm.dfs[key] = tfm.dfs[key].drop(self.group_name, axis=1)


# %%
tfm = Transformer(df, cbs=[
    SelectColsOfInterestCB(common_coi, nuclides_pattern),
    WideToLongCB(common_coi, nuclides_pattern),
    ExtractUnitCB(),
    ExtractFilteringStatusCB(phase),
    ExtractSamplingMethodCB(smp_method),
    RenameNuclideCB(nuclides_name),
    StandardizeUnitCB(units_lut),
    RenameColumnCB(renaming_rules),
    UnshiftLongitudeCB(),
    DispatchToGroupCB()
])
dfs_test = tfm()

# %%
print(f'Groups: {list(dfs_test.keys())}')
test_eq(set(dfs_test.keys()), {'SEAWATER', 'SUSPENDED_MATTER'})
# GROUP column consumed as dict key, not passed through
test_eq('GROUP' in dfs_test['SEAWATER'].columns, False)
test_eq('GROUP' in dfs_test['SUSPENDED_MATTER'].columns, False)

# %% [markdown]
# ## Add sample ID

# %% [markdown]
# After wide-to-long melting, each BODC Bottle Number (renamed to `SMP_ID_PROVIDER`) appears once per measured nuclide — 8,779 distinct provider IDs across 19,139 seawater rows, and 1,849 across 7,606 suspended-matter rows. The provider ID is not a row-level identifier, so a sequential `SMP_ID` is generated per group to serve as the NetCDF dimension index. For traceability the provider's stable bottle number is preserved as `SMP_ID_PROVIDER` and cast to `str` for NetCDF VLEN compatibility.

# %%
for grp, gdf in dfs_test.items():
    print(f'{grp}: {len(gdf)} rows, {gdf.SMP_ID_PROVIDER.nunique()} unique provider IDs')


# %%
#| export
class AddSampleIDCB(PerGroupCB):
    "Assign a sequential SMP_ID per sample-type group; cast SMP_ID_PROVIDER (BODC Bottle Number) to string for NetCDF VLEN compatibility."
    def each_grp(self,
                 grp: str,          # Group key e.g. 'SEAWATER', 'SUSPENDED_MATTER'
                 df: pd.DataFrame,  # DataFrame for this group
                 tfm,               # Parent Transformer
                 ):
        df['SMP_ID'] = range(1, len(df) + 1)
        df['SMP_ID_PROVIDER'] = df['SMP_ID_PROVIDER'].astype(str)


# %%
tfm = Transformer(df, cbs=[
    SelectColsOfInterestCB(common_coi, nuclides_pattern),
    WideToLongCB(common_coi, nuclides_pattern),
    ExtractUnitCB(),
    ExtractFilteringStatusCB(phase),
    ExtractSamplingMethodCB(smp_method),
    RenameNuclideCB(nuclides_name),
    StandardizeUnitCB(units_lut),
    RenameColumnCB(renaming_rules),
    UnshiftLongitudeCB(),
    DispatchToGroupCB(),
    AddSampleIDCB()
])
dfs_test = tfm()

# %%
for grp, gdf in dfs_test.items():
    print(f'{grp}: SMP_ID range 1–{gdf.SMP_ID.max()}, SMP_ID_PROVIDER dtype={gdf.SMP_ID_PROVIDER.dtype}')
# SMP_ID is sequential from 1
test_eq(dfs_test['SEAWATER']['SMP_ID'].iloc[0], 1)
test_eq(dfs_test['SUSPENDED_MATTER']['SMP_ID'].iloc[0], 1)
# SMP_ID_PROVIDER cast to string for NetCDF VLEN compatibility
test_eq(dfs_test['SEAWATER']['SMP_ID_PROVIDER'].dtype, 'str')

# %% [markdown]
# ## Parse time

# %% [markdown]
# Geotraces timestamps arrive as ISO 8601 strings in a single column (`yyyy-mm-ddThh:mm:ss.sss`). `ParseTimeCB` converts these to pandas datetime objects, enabling temporal filtering and NetCDF-compatible time encoding downstream.

# %%
tfm = Transformer(df, cbs=[
    SelectColsOfInterestCB(common_coi, nuclides_pattern),
    WideToLongCB(common_coi, nuclides_pattern),
    ExtractUnitCB(),
    ExtractFilteringStatusCB(phase),
    ExtractSamplingMethodCB(smp_method),
    RenameNuclideCB(nuclides_name),
    StandardizeUnitCB(units_lut),
    RenameColumnCB(renaming_rules),
    UnshiftLongitudeCB(),
    DispatchToGroupCB(),
    ParseTimeCB()
])
dfs_test = tfm()


# %%
print('TIME dtype:', dfs_test['SEAWATER']['TIME'].dtype)
test_eq(dfs_test['SEAWATER']['TIME'].dtype, 'datetime64[us]')

# %% [markdown]
# ## Encode time

# %% [markdown]
# Geotraces timestamps arrive as ISO 8601 strings. After `ParseTimeCB` converts them to `datetime64[us]` they are still not in a NetCDF-compatible format. The MARIS NetCDF CDL template stores time as seconds since `1970-01-01`, so `EncodeTimeCB` converts each datetime to its Unix timestamp integer. Downstream the NetCDF file declares `units: seconds since 1970-01-01T00:00:00Z` on the `TIME` variable, which client software can decode back to calendar dates on read.

# %%
tfm = Transformer(df, cbs=[
    SelectColsOfInterestCB(common_coi, nuclides_pattern),
    WideToLongCB(common_coi, nuclides_pattern),
    ExtractUnitCB(),
    ExtractFilteringStatusCB(phase),
    ExtractSamplingMethodCB(smp_method),
    RenameNuclideCB(nuclides_name),
    StandardizeUnitCB(units_lut),
    RenameColumnCB(renaming_rules),
    UnshiftLongitudeCB(),
    DispatchToGroupCB(),    
    ParseTimeCB(),
    EncodeTimeCB()
])

dfs_test = tfm()
print('TIME sample (epoch seconds):', dfs_test['SEAWATER']['TIME'].iloc[:5].values)

# %% [markdown]
# ## Sanitize coordinates
#
# `SanitizeLonLatCB` normalises comma decimal separators to dots for longitude and latitude values, and drops rows whose coordinates are exactly `(0, 0)` or fall outside the valid ranges (lon ∉ [-180, 180], lat ∉ [-90, 90]).

# %%
#|eval: false
df = pd.read_csv(fname_in)

tfm = Transformer(df, cbs=[
    SelectColsOfInterestCB(common_coi, nuclides_pattern),
    WideToLongCB(common_coi, nuclides_pattern),
    ExtractUnitCB(),
    ExtractFilteringStatusCB(phase),
    ExtractSamplingMethodCB(smp_method),
    RenameNuclideCB(nuclides_name),
    StandardizeUnitCB(units_lut),
    RenameColumnCB(renaming_rules),
    UnshiftLongitudeCB(),
    DispatchToGroupCB(),
    ParseTimeCB(),
    EncodeTimeCB(),
    SanitizeLonLatCB()
])
dfs_test = tfm()
dfs_test['SEAWATER'].head()

# %%
for grp, gdf in dfs_test.items():
    print(f'{grp}: {len(gdf)} rows after sanitize')
test_eq(all(dfs_test['SEAWATER']['LON'].between(-180, 180)), True)
test_eq(all(dfs_test['SEAWATER']['LAT'].between(-90, 90)), True)

# %% [markdown]
# ## Remap nuclides name to id

# %% [markdown]
# At this point the pipeline holds nuclides as human-readable strings (`h3`, `cs137`, …) but the NetCDF file stores them as integer enumeration types for space efficiency. The mapping from standardised name to MARIS nuclide ID is defined by the lookup table below, which `RemapCB` applies before encoding. For example `h3` → `1` and `cs137` → `33`

# %%
#| exports
# Lookup table: MARIS nc_name → nuclide_id
lut_nuclides = lambda: get_lut('NUCLIDE', reverse=False)

# %%
#|eval: false
df = pd.read_csv(fname_in)

tfm = Transformer(df, cbs=[
    SelectColsOfInterestCB(common_coi, nuclides_pattern),
    WideToLongCB(common_coi, nuclides_pattern),
    ExtractUnitCB(),
    ExtractFilteringStatusCB(phase),
    ExtractSamplingMethodCB(smp_method),
    RenameNuclideCB(nuclides_name),
    StandardizeUnitCB(units_lut),
    RenameColumnCB(renaming_rules),
    UnshiftLongitudeCB(),
    DispatchToGroupCB(),
    ParseTimeCB(),
    EncodeTimeCB(),
    SanitizeLonLatCB(),
    RemapCB(fn_lut=lut_nuclides, col_remap='NUCLIDE', col_src='NUCLIDE')
])

dfs_test = tfm()
dfs_test['SEAWATER'].NUCLIDE.unique()

# %% [markdown]
# ## NetCDF encoder

# %% [markdown]
# ### Example change logs

# %% [markdown]
# Each callback's docstring is recorded in `tfm.logs` during pipeline execution — an ordered audit trail of every transformation applied. These logs are serialised into the NetCDF output's global attribute `publisher_postprocess_logs`, providing traceability for downstream users.
#
# The two "not found" messages for `BIOTA` and `SEDIMENT` are expected: this dataset (GEOTRACES IDP2021 seawater) only contains `SEAWATER` and `SUSPENDED_MATTER` sample types.

# %%
#|eval: false
df = pd.read_csv(fname_in)

tfm = Transformer(df, cbs=[
    SelectColsOfInterestCB(common_coi, nuclides_pattern),
    WideToLongCB(common_coi, nuclides_pattern),
    ExtractUnitCB(),
    ExtractFilteringStatusCB(phase),
    ExtractSamplingMethodCB(smp_method),
    RenameNuclideCB(nuclides_name),
    StandardizeUnitCB(units_lut),
    RenameColumnCB(renaming_rules),
    UnshiftLongitudeCB(),
    DispatchToGroupCB(),
    ParseTimeCB(),
    EncodeTimeCB(),
    SanitizeLonLatCB(),
    RemapCB(fn_lut=lut_nuclides, col_remap='NUCLIDE', col_src='NUCLIDE')
])

tfm();

# %%
#|eval: false
tfm.logs

# %% [markdown]
# ### Feed global attributes

# %% [markdown]
# The global attributes that end up in the NetCDF output come from three sources:
#
# 1. **Computed from the data itself** — the `BboxCB`, `DepthRangeCB`, and `TimeRangeCB` derive spatial extent (`geospatial_lat_min/max`, `geospatial_lon_min/max`, `geospatial_bounds`), depth range (`geospatial_vertical_min/max`), and temporal coverage (`time_coverage_start/end`) from the columns in each sample-type group's dataframe.
# 2. **Pulled from an external repository** — `ZoteroCB` fetches bibliographic metadata (`id`, `title`, `summary`, `creator_name`) from the MARIS Zotero library using the dataset's `zotero_key`, so citation details stay synchronised with the library rather than being hardcoded.
# 3. **Supplied as literals** — `KeyValuePairCB` injects ad-hoc attributes like `keywords` (a controlled-vocabulary string for data discovery) and `publisher_postprocess_logs` (the transformation audit trail from `tfm.logs`).

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
        tfm, 
        zotero_key, 
        kw=kw
        ):
    "Retrieve global attributes from Geotraces dataset."
    return GlobAttrsFeeder(tfm.dfs, cbs=[
        BboxCB(),
        DepthRangeCB(),
        TimeRangeCB(),
        ZoteroCB(zotero_key),
        KeyValuePairCB('keywords', ', '.join(kw)),
        KeyValuePairCB('publisher_postprocess_logs', ', '.join(tfm.logs))
        ])()


# %%
#|eval: false
zotero_metadata = get_attrs(tfm, zotero_key=zotero_key, kw=kw)
print('Keys: ', zotero_metadata.keys())
print('Title: ', zotero_metadata['title'])


# %% [markdown]
# ### Encoding

# %% [markdown]
# The `encode()` function below is the entry point called by the CLI tool `maris_to_nc`. When a user runs:
#
# ```bash
# maris_to_nc geotraces --dest path/to/output.nc --src path/to/input.csv
# ```
#
# The CLI (`nbs/cli/to_nc.ipynb`) resolves `geotraces` to this handler module (`marisco.handlers.geotraces`), imports its `encode` function, and calls it with the provided paths:
#
# ```python
# encode = import_handler('marisco.handlers.geotraces')
# encode(fname_in=src, fname_out=dest)
# ```
#
# Two conventions make this dispatch work:
#
# 1. **Each handler exposes `encode()`** with the same signature `(fname_in, fname_out, **kwargs)` — the CLI doesn't need to know what transformations happen inside.
# 2. **The `src` parameter is optional**: handlers with built-in data paths (HELCOM, OSPAR, TEPCO) can be called with only `fname_out`, while Geotraces requires the explicit path because the raw CSV is too large to bundle.
#
# The full orchestration is laid out below — each callback in the pipeline is documented in its own section above, and `tfm.logs` captures every step as an audit trail serialised into the output NetCDF.

# %%
#| export
def encode(
        fname_in:str,    # Path to the raw Geotraces input CSV (the IDP2021 discrete sample data)
        fname_out:str,   # Destination path for the NetCDF4 output file
        **kwargs         # Pass verbose=True for detailed NetCDFEncoder output
        ):
    "Orchestrate the full Geotraces curation pipeline: load, transform, and encode to MARIS NetCDF4 format."
    df = pd.read_csv(fname_in)
    tfm = Transformer(df, cbs=[
        SelectColsOfInterestCB(common_coi, nuclides_pattern),
        WideToLongCB(common_coi, nuclides_pattern),
        ExtractUnitCB(),
        ExtractFilteringStatusCB(phase),
        ExtractSamplingMethodCB(smp_method),
        RenameNuclideCB(nuclides_name),
        StandardizeUnitCB(units_lut),
        RenameColumnCB(renaming_rules),
        UnshiftLongitudeCB(),
        DispatchToGroupCB(),
        AddSampleIDCB(),
        ParseTimeCB(),
        EncodeTimeCB(),
        SanitizeLonLatCB(),
        RemapCB(fn_lut=lut_nuclides, col_remap='NUCLIDE', col_src='NUCLIDE')
        ])
    
    tfm()
    encoder = NetCDFEncoder(tfm.dfs, 
                            dest_fname=fname_out,    
                            global_attrs=get_attrs(tfm, zotero_key=zotero_key, kw=kw),
                            verbose=kwargs.get('verbose', False)
                           )
    encoder.encode()



# %%
#|eval: false
encode(fname_in, fname_out, verbose=False)

# %% [markdown]
# ## NetCDF → CSV (MARIS DB import)
#
# The NetCDF file is the archival format, but the MARIS master database requires input in a specific CSV layout compatible with the legacy OpenRefine import pipeline. The `decode` function reads the just-encoded NetCDF, reverses enum encoding back to human-readable strings (nuclide names, unit labels, etc.), appends `SAMPLE_TYPE` and `REF_ID` columns from the Zotero metadata, and saves per-group CSV files alongside the NetCDF.
#
# The CSV step is optional — the NetCDF is the canonical output — but without it the data cannot be ingested into the central MARIS database.
#
# ```python
# # | eval: false
# decode(fname_in=fname_out, verbose=True)
# ```
#
# The resulting files (`*_SEAWATER.csv`, `*_SUSPENDED_MATTER.csv`) are then ready for verification and SQL import.
