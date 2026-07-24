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
#| default_exp handlers.tepco

# %% [markdown]
# # TEPCO 
# > Data pipeline (handler) to convert TEPCO dataset ([Source](https://radioactivity.nsr.go.jp/ja/list/349/list-1.html)) to `NetCDF` format

# %% [markdown]
# > **Refactoring in progress.** This handler is being updated to use the new `marisco` API (fuzzy matching, `make_lut` / `make_lut_from`, `RemapCB`), following the approach used in the HELCOM and GEOTRACES handlers. Exports and execution are temporarily disabled.

# %% [markdown]
# **[newer version in progress using the RAMDAS new API]**

# %%
#| hide
# %load_ext autoreload
# %autoreload 2

# %%
#| eval: false
import warnings
warnings.filterwarnings('ignore')

# %%
#| eval: false
import pandas as pd
import re
import numpy as np
import fastcore.all as fc
from tqdm import tqdm
from collections import defaultdict

from marisco.callbacks import (
    Callback, 
    Transformer,
    EncodeTimeCB, 
    SanitizeLonLatCB,
    EncodeTimeCB, 
    )

from marisco.encoders import NetCDFEncoder

from marisco.metadata import (
    GlobAttrsFeeder, 
    BboxCB,
    TimeRangeCB,
    ZoteroCB, 
    KeyValuePairCB    
    )

from marisco.netcdf2csv import decode

# %% [markdown]
# ## Configuration & file paths

# %%
#| eval: false
fname_coastal_water = 'https://radioactivity.nra.go.jp/cont/en/results/sea/coastal_water.csv'
fname_clos1F = 'https://radioactivity.nra.go.jp/cont/en/results/sea/close1F_water.xlsx'
fname_iaea_orbs = 'https://raw.githubusercontent.com/RML-IAEA/iaea.orbs/refs/heads/main/src/iaea/orbs/stations/station_points.csv'

fname_out = '../../_data/output/tepco.nc'


# %% [markdown]
# ## Load data

# %% [markdown]
# We here load the data from the [NRA (Nuclear Regulatory Authority)](https://radioactivity.nra.go.jp/en/results) website. For the moment, we only process radioactivity concentration data in the seawater around Fukushima Dai-ichi NPP [TEPCO] (`coastal_water.csv`) and in the `close1F_water.xlsx` file.
#
# In near future, MARIS will provide a dedicated handler for all related [ALPS data](https://radioactivity.nra.go.jp/en/results#sec-12) including measurements not only provided by TEPCO but also MOE, NRA, MLITT and Fukushima Prefecture.
#
#

# %% [markdown]
# :::{.callout-important}
# ## FEEDBACK TO DATA PROVIDER
#
# The **coastal_water.csv** file contains two sections: the measurements and the locations. We identify below the line number where the locations begin. A single point of truth for the location of the stations would ease the processing in future.
#
# :::

# %%
#| eval: false
def find_location_section(df, 
                          col_idx=0,
                          pattern='Sampling point number'
                          ):
    "Find the line number where location data begins."
    mask = df.iloc[:, col_idx] == pattern
    indices = df[mask].index
    return indices[0] if len(indices) > 0 else -1


# %%
#| eval: false
find_location_section(pd.read_csv(fname_coastal_water, low_memory=False))


# %% [markdown]
# :::{.callout-important}
# ## FEEDBACK TO DATA PROVIDER
#
# Distinct parsing of the time from `coastal_water.csv` and `close1F_water.xlsx` files are required. Indeed:
#
# - `coastal_water.csv` uses the format `YYYY/MM/DD` in the `Sampling  HH:MM` and 
# - `close1F_water.xlsx` uses the format `YYYY-MM-DD HH:MM:SS`.
#
# :::

# %%
#| eval: false
def fix_sampling_time(x):
    if pd.isna(x): 
        return '00:00:00'
    else:
        hour, min =  x.split(':')[:2]
        return f"{hour if len(hour) == 2 else '0' + hour}:{min}:00"


# %%
#| eval: false
def get_coastal_water_df(fname_coastal_water):
    "Get the measurements dataframe from the `coastal_water.csv` file."
    
    locs_idx = find_location_section(pd.read_csv(fname_coastal_water, 
                                      skiprows=0, low_memory=False))
    
    df = pd.read_csv(fname_coastal_water, skiprows=1, 
                     nrows=locs_idx - 1,
                     low_memory=False)
    df.dropna(subset=['Sampling point number'], inplace=True)
    df['Sampling time'] = df['Sampling time'].map(fix_sampling_time)
    
    df['TIME'] = df['Sampling date'].replace('-', '/') + ' ' + df['Sampling time']
    
    df = df.drop(columns=['Sampling date', 'Sampling time'])
    return df


# %%
#| eval: false
df_coastal_water = get_coastal_water_df(fname_coastal_water)
df_coastal_water.tail()

# %%
coi = [o for o in df_coastal_water.columns if "134Cs" in o]

df_coastal_water[coi + ['Sampling point number', 'TIME']].head(30)

# %%
coi

# %%
df_coastal_water.dropna(subset=coi, how='any')[coi + ['Sampling point number', 'TIME']]

# %%
mask = df_coastal_water['134Cs radioactivity concentration (Bq/L)'] == 'ND'
df_coastal_water[mask][coi + ['Sampling point number', 'TIME']]

# %%
len(df_coastal_water)


# %% [markdown]
# :::{.callout-important}
# ## FEEDBACK TO DATA PROVIDER
#
# Identification of the stations location requires three distinct files:
#
# - the second section of the `coastal_water.csv` file
# - the `R6zahyo.pdf` file further processed by [https://github.com/RML-IAEA/iaea.orbs](https://github.com/RML-IAEA/iaea.orbs)
# - the second sections of all sheets of `close1F_water.xlsx` file
#   
# All files and sheets required to look up the location of the stations.
#
# :::

# %%
#| eval: false
def get_locs_coastal_water(fname_coastal_water):
    locs_idx = find_location_section(pd.read_csv(fname_coastal_water, 
                                      skiprows=0, low_memory=False))
    
    df = pd.read_csv(fname_coastal_water, skiprows=locs_idx+1, 
                     low_memory=False).iloc[:, :3]
    
    df.columns = ['STATION', 'LON', 'LAT']
    df.dropna(subset=['LAT'], inplace=True)
    df['org'] = 'coastal_seawater.csv'
    return df


# %%
#| eval: false
df_locs_coastal_water = get_locs_coastal_water(fname_coastal_water)
print(f'Nb. of stations: {len(df_locs_coastal_water)}')
df_locs_coastal_water.head()

# %%
#| eval: false
df_locs_coastal_water.STATION.unique()


# %% [markdown]
# :::{.callout-important}
# ## FEEDBACK TO DATA PROVIDER
#
# Data contained in the `close1F_water.xlsx` file are spread in several sheets (one per station). Each sheet further contains two sections: the measurements and the locations. 
#
# For each sheet, we have to identify the line number where to split both measurements and the location. We then need to further iterate over all sheets to concatenate the results.
#
# :::

# %%
#| eval: false
def get_clos1F_df(fname_clos1F):
    "Get measurements dataframe from close1F_water.xlsx file and parse datetime."
    excel_file = pd.ExcelFile(fname_clos1F)
    dfs = {}
    
    for sheet_name in tqdm(excel_file.sheet_names):
        locs_idx = find_location_section(pd.read_excel(excel_file, 
                                                       sheet_name=sheet_name,
                                                       skiprows=1))
        df = pd.read_excel(excel_file, 
                   sheet_name=sheet_name, 
                   skiprows=1,
                   nrows=locs_idx-1)
        
        df.dropna(subset=['Sampling point number'], inplace=True)
        df['Sampling date'] = df['Sampling date']\
            .astype(str)\
            .apply(lambda x: x.split(' ')[0]\
            .replace('-', '/'))
            
        dfs[sheet_name] = df
    
    df = pd.concat(dfs.values(), ignore_index=True)
    df.dropna(subset=['Sampling date'], inplace=True)
    df['TIME'] = df['Sampling date'] + ' ' + df['Sampling time'].astype(str)
    df = df.drop(columns=['Sampling date', 'Sampling time'])
    return df


# %%
#| eval: false
df_clos1F = get_clos1F_df(fname_clos1F)
df_clos1F.head()

# %%
#| eval: false
df_clos1F['Sampling point number'].unique()


# %%
#| eval: false
def get_locs_clos1F(fname_clos1F):
    "Get locations dataframe from close1F_water.xlsx file from each sheets."
    excel_file = pd.ExcelFile(fname_clos1F)
    dfs = {}
    
    for sheet_name in tqdm(excel_file.sheet_names):
        locs_idx = find_location_section(pd.read_excel(excel_file, 
                                                       sheet_name=sheet_name,
                                                       skiprows=1))
        df = pd.read_excel(excel_file, 
                           sheet_name=sheet_name, 
                           skiprows=locs_idx+2)
            
        dfs[sheet_name] = df
    
    df = pd.concat(dfs.values(), ignore_index=True).iloc[:, :3]
    df.dropna(subset=['Sampling coordinate North latitude (Decimal)'], inplace=True)    
    df.columns = ['STATION', 'LON', 'LAT']
    df['org'] = 'close1F.csv'
    return df


# %%
#| eval: false
df_locs_clos1F = get_locs_clos1F(fname_clos1F)
print(f'Nb. of stations: {len(df_locs_clos1F)}')
df_locs_clos1F.head()

# %% [markdown]
# :::{.callout-important}
# ## FEEDBACK TO DATA PROVIDER
#
# The `close1F_water.xlsx` file contains station locations that are not present in the `coastal_water.csv` dataset, as demonstrated in the comparison below:
# :::

# %%
#| eval: false
set(df_locs_clos1F.STATION) - set(df_locs_coastal_water.STATION)


# %% [markdown]
# :::{.callout-important}
# ## FEEDBACK TO DATA PROVIDER
#
# In theory all locations are supposed to be provided in the [R6zahyo.pdf](https://radioactivity.nra.go.jp/cont/en/results/sea/R6zahyo.pdf) file. This file is further processed by https://github.com/RML-IAEA/iaea.orbs and the result is provided in the `station_points.csv` file. 
#
# However, this file lacks complete coverage of locations referenced in both `coastal_water.csv` and `close1F_water.xlsx` files, while simultaneously containing additional locations not present in either (see below). A more standardized and comprehensive location reference system would significantly improve the efficiency and reliability of the data ingestion process.
#
# :::

# %%
#| eval: false
def get_locs_orbs(fname_iaea_orbs):
    df = pd.read_csv(fname_iaea_orbs)
    df.columns = ['org', 'STATION', 'LON', 'LAT']
    return df


# %%
#| eval: false
df_locs_orbs = get_locs_orbs(fname_iaea_orbs)
df_locs_orbs.head()

# %%
#| eval: False
set(df_locs_orbs.STATION) - (set(df_locs_clos1F.STATION) | set(df_locs_coastal_water.STATION))


# %%
#| eval: false
def concat_locs(dfs):
    "Concatenate and drop duplicates from coastal_seawater.csv and iaea_orbs.csv (kept)"
    df = pd.concat(dfs)
    # Group by org to be used for sorting
    df['org_grp'] = df['org'].apply(
        lambda x: 1 if x == 'coastal_seawater.csv' else 2 if x == 'close1F.csv' else 0)
    df.sort_values('org_grp', ascending=True, inplace=True)
    # Drop duplicates and keep orbs data first
    df.drop_duplicates(subset='STATION', keep='first', inplace=True)
    df.drop(columns=['org_grp'], inplace=True)
    df.sort_values('STATION', ascending=True, inplace=True)
    return df


# %%
#| eval: false
df_locs = concat_locs([df_locs_clos1F, df_locs_coastal_water, df_locs_orbs])
df_locs.head()


# %%
#| eval: false
def align_dfs(df_from, df_to):
    "Align columns structure of df_from to df_to."
    df = defaultdict()    
    for c in df_to.columns:
        df[c] = df_from[c].values if c in df_from.columns else np.nan
    return pd.DataFrame(df)


# %%
# | eval: false
align_dfs(df_clos1F, df_coastal_water).head()


# %%
#| eval: false
def concat_dfs(df_coastal_water, df_clos1F):
    "Concatenate and drop duplicates from coastal_seawater.csv and close1F_water.xlsx (kept)"
    df_clos1F = align_dfs(df_clos1F, df_coastal_water)
    df = pd.concat([df_coastal_water, df_clos1F])
    return df


# %%
#| eval: false
df_meas = concat_dfs(df_coastal_water, df_clos1F)
df_meas.head()


# %%
#| eval: false
def georef_data(df_meas, df_locs):
    "Georeference measurements dataframe using locations dataframe."
    assert "Sampling point number" in df_meas.columns and "STATION" in df_locs.columns
    return pd.merge(df_meas, df_locs, how="inner", 
                    left_on='Sampling point number', right_on='STATION')


# %%
#| eval: false
df_meas_georef = georef_data(df_meas, df_locs)
df_meas_georef.head()


# %%
#| eval: false
def load_data(fname_coastal_water, fname_clos1F, fname_iaea_orbs):
    "Load, align and georeference TEPCO data"
    df_locs = concat_locs(
        [get_locs_coastal_water(fname_coastal_water), 
         get_locs_clos1F(fname_clos1F),
         get_locs_orbs(fname_iaea_orbs)])
    df_meas = concat_dfs(get_coastal_water_df(fname_coastal_water), get_clos1F_df(fname_clos1F))
    df_meas.dropna(subset=['Sampling point number'], inplace=True)
    return {'SEAWATER': georef_data(df_meas, df_locs)}


# %%
#| eval: false
dfs = load_data(fname_coastal_water, fname_clos1F, fname_iaea_orbs)
dfs['SEAWATER'].head()

# %%
#| eval: false
print(f"# of cols, rows: {dfs['SEAWATER'].shape}")
dfs['SEAWATER'].head()

# %%
#| eval: false
dfs['SEAWATER'].STATION.unique()

# %%
np.sum(dfs['SEAWATER'] == "ND")

# %%
dfs['SEAWATER'][['TIME', '134Cs radioactivity concentration (Bq/L)', '134Cs detection limit (Bq/L)']]


# %% [markdown]
# ## Remove 約 (about) character
#     

# %% [markdown]
# :::{.callout-important}
# ## FEEDBACK TO DATA PROVIDER
#
# We systematically remove the `約` character. Please confirm that this is the correct way to handle this. We could imagine that mentioning uncertainty would be less ambiguous in future.
#
# :::

# %%
#| eval: false
class RemoveJapanaseCharCB(Callback):
    "Remove 約 (about) char"
    def _transform_if_about(self, value, about_char='約'):
        if pd.isna(value): return value
        return (value.replace(about_char, '') if str(value).count(about_char) != 0 
                else value)
    
    def __call__(self, tfm): 
        for k in tfm.dfs.keys():
            cols_rdn = [c for c in tfm.dfs[k].columns if ('(Bq/L)' in c) and (tfm.dfs[k][c].dtype == 'object')]
            tfm.dfs[k][cols_rdn] = tfm.dfs[k][cols_rdn].map(self._transform_if_about)


# %%
tfm = Transformer(dfs, cbs=[
    RemoveJapanaseCharCB()])

tfm()['SEAWATER'].sample(10)


# %% [markdown]
# ## Fix values range string

# %% [markdown]
# :::{.callout-important}
# ## FEEDBACK TO DATA PROVIDER
#
# Value ranges are provided as strings (e.g '4.0E+00<&<8.0E+00' or '1.0～2.7'). We replace them by their mean. Please confirm that this is the correct way to handle this. Again, mentioning uncertainty would be less ambiguous in future.
#
# :::

# %%
#| eval: false
class FixRangeValueStringCB(Callback):
    "Replace range values (e.g '4.0E+00<&<8.0E+00' or '1.0～2.7') by their mean"
    
    def _extract_and_calculate_mean(self, s):
        # For scientific notation ranges
        float_strings = re.findall(r"[+-]?\d+\.?\d*E?[+-]?\d*", s)
        if float_strings:
            float_numbers = np.array(float_strings, dtype=float)
            return float_numbers.mean()
        return s
    
    def _transform_if_range(self, value):
        if pd.isna(value): 
            return value
        value = str(value)
        # Check for both range patterns
        if '<&<' in value or '～' in value:
            return self._extract_and_calculate_mean(value)
        return value

    def __call__(self, tfm): 
        for k in tfm.dfs.keys():
            cols_rdn = [c for c in tfm.dfs[k].columns 
                       if ('(Bq/L)' in c) and (tfm.dfs[k][c].dtype == 'object')]
            # tfm.dfs[k][cols_rdn] = tfm.dfs[k][cols_rdn].map(self._transform_if_range).astype(float)
            tfm.dfs[k][cols_rdn] = tfm.dfs[k][cols_rdn].map(self._transform_if_range)


# %%
tfm = Transformer(dfs, cbs=[
    RemoveJapanaseCharCB(),
    FixRangeValueStringCB()
    ])

df_test = tfm()['SEAWATER']
df_test.sample(10)

# %% [markdown]
# ## Select columns of interest

# %% [markdown]
# We select the columns of interest and in particular the elements of interest, in our case radionuclides.

# %%
#| eval: false
common_coi = ['LON', 'LAT', 'TIME', 'STATION']
nuclides_pattern = '(Bq/L)'


# %%
#| eval: false
class SelectColsOfInterestCB(Callback):
    "Select columns of interest."
    def __init__(self, common_coi, nuclides_pattern): fc.store_attr()
    def __call__(self, tfm):
        nuc_of_interest = [c for c in tfm.dfs['SEAWATER'].columns if nuclides_pattern in c]
        tfm.dfs['SEAWATER'] = tfm.dfs['SEAWATER'][self.common_coi + nuc_of_interest]


# %%
#| eval: false
tfm = Transformer(dfs, cbs=[
    RemoveJapanaseCharCB(),
    FixRangeValueStringCB(),
    SelectColsOfInterestCB(common_coi, nuclides_pattern)
    ])

df_test = tfm()['SEAWATER'] 
df_test.sample(5)


# %% [markdown]
# ## Reshape: wide to long
#
# So that we can extract information such as nuclide name, unit, derived quantities such as uncertainty, detection limit, ...

# %%
#| eval: false
class WideToLongCB(Callback):
    """
    Get TEPCO nuclide names as values not column names 
    to extract contained information (nuclide name, unc, dl, ...).
    """
    def __init__(self, id_vars=['LON', 'LAT', 'TIME', 'STATION']): 
        fc.store_attr()
        
    def __call__(self, tfm): 
        tfm.dfs['SEAWATER'] = pd.melt(tfm.dfs['SEAWATER'], id_vars=self.id_vars)
#| eval: false


# %%
#| eval: false
tfm = Transformer(dfs, cbs=[
    RemoveJapanaseCharCB(),
    FixRangeValueStringCB(),
    SelectColsOfInterestCB(common_coi, nuclides_pattern),
    WideToLongCB()
    ])

df_test = tfm()['SEAWATER'] 
df_test.head()


# %% [markdown]
# ## Extract

# %% [markdown]
# Nulide name, dl, unc, ... are extracted from column names as embedded in TEPCO data source.

# %% [markdown]
# ### Nuclide name

# %%
#| eval: false
def extract_nuclide(text: str) -> str:
    "Extract the nuclide identifier from a measurement variable name using regex."
    pattern = r'^(Total\s+(?:alpha|beta)|[^\s]+)'
    match = re.match(pattern, text, re.IGNORECASE)
    return match.group(1) if match else text 


# %% [markdown]
# For instance:

# %%
print(extract_nuclide("Total alpha radioactivity concentration (Bq/L)"))
print(extract_nuclide("131I radioactivity concentration (Bq/L)"))


# %%
#| eval: false
class ExtractNuclideNameCB(Callback):
    "Extract nuclide name from TEPCO data."
    def __init__(self, src_col='variable', dest_col='NUCLIDE'): fc.store_attr()
    def __call__(self, tfm): 
        tfm.dfs['SEAWATER'][self.dest_col] = tfm.dfs['SEAWATER'][self.src_col].map(extract_nuclide)


# %%
#| eval: false
tfm = Transformer(dfs, cbs=[
    RemoveJapanaseCharCB(),
    FixRangeValueStringCB(),
    SelectColsOfInterestCB(common_coi, nuclides_pattern),
    WideToLongCB(),
    ExtractNuclideNameCB()
    ])

df_test = tfm()['SEAWATER'] 
df_test.sample(5)


# %% [markdown]
# ### Unit

# %%
#| eval: false
class ExtractUnitCB(Callback):
    "Extract unit from TEPCO data."
    def __init__(self, src_col='variable', dest_col='UNIT'): fc.store_attr()
    def __call__(self, tfm): 
        tfm.dfs['SEAWATER'][self.dest_col] = tfm.dfs['SEAWATER'][self.src_col].str.extract(r'\((.*?)\)')


# %%
#| eval: false
tfm = Transformer(dfs, cbs=[
    RemoveJapanaseCharCB(),
    FixRangeValueStringCB(),
    SelectColsOfInterestCB(common_coi, nuclides_pattern),
    WideToLongCB(),
    ExtractNuclideNameCB(),
    ExtractUnitCB()
    ])

df_test = tfm()['SEAWATER'] 
df_test.sample(5)


# %% [markdown]
# ### Value type
# Is it a measurement or derived detection such as detection limit or uncertainty?

# %%
#| eval: false
class ExtractValueTypeCB(Callback):
    "Extract value type from TEPCO data."
    def __init__(self, src_col='variable', dest_col='type'): fc.store_attr()
    def __call__(self, tfm): 
        tfm.dfs['SEAWATER'][self.dest_col] = np.select(
            [
                tfm.dfs['SEAWATER'][self.src_col].str.contains('detection limit', case=False),
                tfm.dfs['SEAWATER'][self.src_col].str.contains('statistical error', case=False)],
            ['DL', 'UNC'],
            default='VALUE'
        )


# %%
#| eval: false
tfm = Transformer(dfs, cbs=[
    RemoveJapanaseCharCB(),
    FixRangeValueStringCB(),
    SelectColsOfInterestCB(common_coi, nuclides_pattern),
    WideToLongCB(),
    ExtractNuclideNameCB(),
    ExtractUnitCB(),
    ExtractValueTypeCB()
    ])

df_test = tfm()['SEAWATER'] 
df_test.sample(5)


# %% [markdown]
# ## Reshape: long to wide
# Send `type` column to columns names (`VALUE`, `DL`, `UNC`)
#

# %%
#| eval: false
class LongToWideCB(Callback):
    "Reshape: long to wide"
    def __init__(self, src_col='variable', dest_col='type'): fc.store_attr()
    def __call__(self, tfm): 
        tfm.dfs['SEAWATER'] = pd.pivot_table(
            tfm.dfs['SEAWATER'],
            values='value',
            index=['LON', 'LAT', 'TIME', 'STATION', 'NUCLIDE', 'UNIT'],
            columns='type',
            aggfunc='first'
        ).reset_index()
        tfm.dfs['SEAWATER'].reset_index(inplace=True)
        tfm.dfs['SEAWATER'].rename(columns={'index': 'SMP_ID'}, inplace=True)


# %%
#| eval: false
tfm = Transformer(dfs, cbs=[
    RemoveJapanaseCharCB(),
    FixRangeValueStringCB(),
    SelectColsOfInterestCB(common_coi, nuclides_pattern),
    WideToLongCB(),
    ExtractNuclideNameCB(),
    ExtractUnitCB(),
    ExtractValueTypeCB(),
    LongToWideCB()
    ])

df_test = tfm()['SEAWATER'] 
df_test.sample(5)

# %%
df_test[df_test.VALUE == 'ND'].groupby('NUCLIDE').size().sort_values(ascending=False)

# %%
df_test[df_test.VALUE == 'ND']


# %%
df_test.VALUE == 'ND'

# %% [markdown]
# ## Remap `UNIT` name to MARIS nomenclature

# %% [markdown]
# Data are reported in `Bq/L` but MARIS uses `Bq/m3` instead. So we assign it to MARIS `unit_id` = 3 (Bq/L).
# Later in the processing pipeline, we will convert the values from Bq/L to Bq/m3 by multiplying VALUE, DL, and DLV by 1000.

# %%
#| eval: false
unit_mapping = {'Bq/L': 1}


# %%
#| eval: false
class RemapUnitNameCB(Callback):
    """
    Remap `UNIT` name to MARIS id.
    """
    def __init__(self, unit_mapping): fc.store_attr()
    def __call__(self, tfm):
        tfm.dfs['SEAWATER']['UNIT'] = tfm.dfs['SEAWATER']['UNIT'].map(self.unit_mapping)



# %%
#| eval: false
tfm = Transformer(dfs, cbs=[
    RemoveJapanaseCharCB(),
    FixRangeValueStringCB(),
    SelectColsOfInterestCB(common_coi, nuclides_pattern),
    WideToLongCB(),
    ExtractNuclideNameCB(),
    ExtractUnitCB(),
    ExtractValueTypeCB(),
    LongToWideCB(),
    RemapUnitNameCB(unit_mapping)
    ])

df_test = tfm()['SEAWATER'] 
df_test.sample(5)

# %% [markdown]
# ## Remap `NUCLIDE` name to MARIS nomenclature

# %%
#| eval: false
nuclide_mapping = {
    '131I': 29,
    '134Cs': 31,
    '137Cs': 33,
    '125Sb': 24,
    'Total beta': 103,
    '238Pu': 67,
    '239Pu+240Pu': 77,
    '3H': 1,
    '89Sr': 11,
    '90Sr': 12,
    'Total alpha': 104,
    '132I': 100,
    '136Cs': 102,
    '58Co': 8,
    '105Ru': 97,
    '106Ru': 17,
    '140La': 35,
    '140Ba': 34,
    '132Te': 99,
    '60Co': 9,
    '144Ce': 37,
    '54Mn': 6
}


# %%
#| eval: false
class RemapNuclideNameCB(Callback):
    "Remap `NUCLIDE` name to MARIS id."
    def __init__(self, nuclide_mapping): fc.store_attr()
    def __call__(self, tfm):
        tfm.dfs['SEAWATER']['NUCLIDE'] = tfm.dfs['SEAWATER']['NUCLIDE'].map(self.nuclide_mapping)


# %%
#| eval: false
tfm = Transformer(dfs, cbs=[
    RemoveJapanaseCharCB(),
    FixRangeValueStringCB(),
    SelectColsOfInterestCB(common_coi, nuclides_pattern),
    WideToLongCB(),
    ExtractNuclideNameCB(),
    ExtractUnitCB(),
    ExtractValueTypeCB(),
    LongToWideCB(),
    RemapUnitNameCB(unit_mapping),
    RemapNuclideNameCB(nuclide_mapping)
    ])

df_test = tfm()['SEAWATER'] 
df_test.sample(5)

# %%
df_test.dropna(subset=['DL', 'VALUE'], how='any')


# %% [markdown]
# ## Remap `VALUE`, `DL`, `DLV` 

# %% [markdown]
# We remap `DL` (Detection Limit) value to MARIS ids as follows:
#     

# %% [markdown]
# - First check if activity (`VALUE`) is reported as "ND", based on reported detection limit `DL`:
#
# ```
# if VALUE is "ND":
#     if not DL: 
#         VALUE, DLV, DL = NaN, NaN, 3
#     else:
#         VALUE, DLV, DL = DL, DL, 2
# ```
#
# - Then if activity (`VALUE`) is reported:
#   
# ```
# if VALUE:
#     VALUE, DLV, DL = VALUE, DL, 1
# ```
#
# but if not reported, then based on detection level (`DL`) reported:
#
# ```
# else:
#     if DL:
#         VALUE, DLV, DL = DL, DL, 2
#     else:
#         VALUE, DLV, DL = NaN, NaN, NaN (should be dropped)
# ```
#
# With 1: Detected value (=), 2: Detection limit (<), 3: Not detected (ND)
# and where:
#
# - `VALUE` is the activity reported by TEPCO
# - `DL` is initially the detection limit as reported by TEPCO but later on remapped to MARIS detection level nomenclature (categorical)
# - `DLV` is the detection limit value as reported by TEPCO (copied from `DL`)
#
#
#

# %%
#| eval: false
class RemapVALUE_DL_DLV_CB(Callback):
    "Remap `DL`, `DLV`, `VALUE` based on TEPCO -> MARIS rules."    
    def map_all_columns(self, row):
        """Map all three columns (VALUE, DL, DLV) at once based on TEPCO rules"""
        value, dl = row['VALUE'], row['DL']
        new_value, new_dlv, new_dl = value, dl, 1
        
        if value == 'ND':
            if pd.isna(dl):
                new_value, new_dlv, new_dl = np.nan, np.nan, 3
            else:
                new_value, new_dlv, new_dl = dl, dl, 2
                
        elif pd.isna(value):
            if pd.isna(dl):
                new_value, new_dlv, new_dl = np.nan, np.nan, np.nan
            else:
                new_value, new_dlv, new_dl = dl, dl, 2
                
        return pd.Series({
            'VALUE': new_value,
            'DLV': new_dlv, 
            'DL': new_dl
        })
        
    def __call__(self, tfm):
        mapped = tfm.dfs['SEAWATER'].apply(self.map_all_columns, axis=1)
        tfm.dfs['SEAWATER'][['VALUE', 'DLV', 'DL']] = mapped
        tfm.dfs['SEAWATER']['DL'] = tfm.dfs['SEAWATER']['DL'].astype(int)
        tfm.dfs['SEAWATER']['VALUE'] = tfm.dfs['SEAWATER']['VALUE'].astype(float)


# %%
#| eval: false
tfm = Transformer(dfs, cbs=[
    RemoveJapanaseCharCB(),
    FixRangeValueStringCB(),
    SelectColsOfInterestCB(common_coi, nuclides_pattern),
    WideToLongCB(),
    ExtractNuclideNameCB(),
    ExtractUnitCB(),
    ExtractValueTypeCB(),
    LongToWideCB(),
    RemapUnitNameCB(unit_mapping),
    RemapNuclideNameCB(nuclide_mapping),
    RemapVALUE_DL_DLV_CB()
    ])

df_test = tfm()['SEAWATER'] 
df_test.sample(20)


# %% [markdown]
# ## Convert activity to `Bq/m3`

# %% [markdown]
# Earlier in the pipeline, we assigned MARIS `unit_id` = 3 (Bq/L) to TEPCO `UNIT` = `Bq/L`.
# Now we need to convert the values from Bq/L to Bq/m3 by multiplying VALUE, DL, and DLV by 1000.

# %%
#| eval: false
class ConvertToBqM3CB(Callback):
    "Convert from Bq/L to Bq/m3."    
    def __call__(self, tfm, factor=1000):
        tfm.dfs['SEAWATER']['VALUE'] = tfm.dfs['SEAWATER']['VALUE'] * factor
        # Convert DLV to float, handling NaN values
        tfm.dfs['SEAWATER']['DLV'] = pd.to_numeric(tfm.dfs['SEAWATER']['DLV'], errors='coerce')
        tfm.dfs['SEAWATER']['DLV'] = tfm.dfs['SEAWATER']['DLV'] * factor


# %%
#| eval: false
tfm = Transformer(dfs, cbs=[
    RemoveJapanaseCharCB(),
    FixRangeValueStringCB(),
    SelectColsOfInterestCB(common_coi, nuclides_pattern),
    WideToLongCB(),
    ExtractNuclideNameCB(),
    ExtractUnitCB(),
    ExtractValueTypeCB(),
    LongToWideCB(),
    RemapUnitNameCB(unit_mapping),
    RemapNuclideNameCB(nuclide_mapping),
    RemapVALUE_DL_DLV_CB(),
    ConvertToBqM3CB()
    ])

df_test = tfm()['SEAWATER'] 
df_test.sample(20)


# %% [markdown]
# ## Parse & encode time

# %%
#| eval: false
class ParseTimeCB(Callback):
    "Parse time column from TEPCO."
    def __init__(self, time_name='TIME'): fc.store_attr()
    def __call__(self, tfm):
        tfm.dfs['SEAWATER'][self.time_name] = pd.to_datetime(tfm.dfs['SEAWATER'][self.time_name], 
                                                             format='%Y/%m/%d %H:%M:%S', errors='coerce')


# %%
#| eval: false
tfm = Transformer(dfs, cbs=[
    RemoveJapanaseCharCB(),
    FixRangeValueStringCB(),
    SelectColsOfInterestCB(common_coi, nuclides_pattern),
    WideToLongCB(),
    ExtractNuclideNameCB(),
    ExtractUnitCB(),
    ExtractValueTypeCB(),
    LongToWideCB(),
    RemapUnitNameCB(unit_mapping),
    RemapNuclideNameCB(nuclide_mapping),
    RemapVALUE_DL_DLV_CB(),
    ConvertToBqM3CB(),
    ParseTimeCB(),
    EncodeTimeCB(),
    
    ])

df_test = tfm()['SEAWATER'] 
df_test.sample(5)

# %% [markdown]
# ## Sanitize coordinates

# %%
#| eval: false
tfm = Transformer(dfs, cbs=[
    RemoveJapanaseCharCB(),
    FixRangeValueStringCB(),
    SelectColsOfInterestCB(common_coi, nuclides_pattern),
    WideToLongCB(),
    ExtractNuclideNameCB(),
    ExtractUnitCB(),
    ExtractValueTypeCB(),
    LongToWideCB(),
    RemapUnitNameCB(unit_mapping),
    RemapNuclideNameCB(nuclide_mapping),
    RemapVALUE_DL_DLV_CB(),
    ConvertToBqM3CB(),
    ParseTimeCB(),
    EncodeTimeCB(),
    SanitizeLonLatCB()
    ])

df_test = tfm()['SEAWATER']
df_test.sample(5)


# %% [markdown]
# ## Add Sample ID

# %% [markdown]
# The `SMP_ID_PROVIDER` column stores the original sample ID from the data provider. TEPCO does not provide sample IDs, so this column will be set to None for all records.

# %%
#| eval: false
class AddSampleIdCB(Callback):
    "Convert from Bq/L to Bq/m3."    
    def __call__(self, tfm, factor=1000):
        tfm.dfs['SEAWATER']['SMP_ID'] = range(1, len(tfm.dfs['SEAWATER']) + 1)
        tfm.dfs['SEAWATER']['SMP_ID_PROVIDER'] = ""


# %%
#| eval: false
tfm = Transformer(dfs, cbs=[
    RemoveJapanaseCharCB(),
    FixRangeValueStringCB(),
    SelectColsOfInterestCB(common_coi, nuclides_pattern),
    WideToLongCB(),
    ExtractNuclideNameCB(),
    ExtractUnitCB(),
    ExtractValueTypeCB(),
    LongToWideCB(),
    RemapUnitNameCB(unit_mapping),
    RemapNuclideNameCB(nuclide_mapping),
    RemapVALUE_DL_DLV_CB(),
    ConvertToBqM3CB(),
    ParseTimeCB(),
    EncodeTimeCB(),
    SanitizeLonLatCB(),
    AddSampleIdCB(),
    ])

df_test = tfm()['SEAWATER']
df_test.sample(5)

# %% [markdown]
# ## Encode to NetCDF

# %%
#| eval: false
tfm = Transformer(dfs, cbs=[
    RemoveJapanaseCharCB(),
    FixRangeValueStringCB(),
    SelectColsOfInterestCB(common_coi, nuclides_pattern),
    WideToLongCB(),
    ExtractNuclideNameCB(),
    ExtractUnitCB(),
    ExtractValueTypeCB(),
    LongToWideCB(),
    RemapUnitNameCB(unit_mapping),
    RemapNuclideNameCB(nuclide_mapping),
    RemapVALUE_DL_DLV_CB(),
    ConvertToBqM3CB(),
    ParseTimeCB(),
    EncodeTimeCB(),
    SanitizeLonLatCB(),
    AddSampleIdCB(),
    ])

dfs_tfm = tfm()
tfm.logs

# %%
dfs_tfm['SEAWATER'].sample(10)

# %%
#| eval: false
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
#| eval: false
def get_attrs(tfm, zotero_key, kw=kw):
    "Retrieve global attributes from MARIS dump."
    return GlobAttrsFeeder(tfm.dfs, cbs=[
        BboxCB(),
        TimeRangeCB(),
        ZoteroCB(zotero_key),
        KeyValuePairCB('keywords', ', '.join(kw)),
        KeyValuePairCB('publisher_postprocess_logs', ', '.join(tfm.logs))
        ])()


# %%
#| eval: false
get_attrs(tfm, zotero_key='JEV6HP5A', kw=kw)


# %%
#| eval: false
def encode(
    fname_out: str, # Path to the folder where the NetCDF output will be saved
    **kwargs # Additional keyword arguments
    ):
    "Encode TEPCO data to NetCDF."
    dfs = load_data(fname_coastal_water, fname_clos1F, fname_iaea_orbs)
    
    tfm = Transformer(dfs, cbs=[
        RemoveJapanaseCharCB(),
        FixRangeValueStringCB(),
        SelectColsOfInterestCB(common_coi, nuclides_pattern),
        WideToLongCB(),
        ExtractNuclideNameCB(),
        ExtractUnitCB(),
        ExtractValueTypeCB(),
        LongToWideCB(),
        RemapUnitNameCB(unit_mapping),
        RemapNuclideNameCB(nuclide_mapping),
        RemapVALUE_DL_DLV_CB(),
        ConvertToBqM3CB(),
        ParseTimeCB(),
        EncodeTimeCB(),
        SanitizeLonLatCB(),
        AddSampleIdCB()
    ])        
    tfm()
    encoder = NetCDFEncoder(tfm.dfs, 
                            dest_fname=fname_out, 
                            global_attrs=get_attrs(tfm, zotero_key='JEV6HP5A', kw=kw),
                            verbose=kwargs.get('verbose', False)
                            )
    encoder.encode()


# %%
#| eval: false
encode(fname_out, verbose=False)

# %%
#| eval: false
decode(fname_in=fname_out, verbose=True)

# %%
#| eval: false
df_output = pd.read_csv("../../_data/output/tepco_SEAWATER.csv")
df_output.head()

# %% [markdown]
# Can you summarize the pipeline above and highlight:
# - the key transformation steps
# - the main hurdles
