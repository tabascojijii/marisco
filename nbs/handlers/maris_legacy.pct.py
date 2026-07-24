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
#| default_exp handlers.maris_legacy

# %% [markdown]
# # MARIS Legacy

# %% [markdown]
# This handler ingests the MARIS master database dump (a tab-separated `.text` with all legacy datasets) and encodes each unique reference (ref_id) into a self-contained MARIS NetCDF4 file. Unlike provider-specific handlers (HELCOM, GEOTRACES, etc.), this one operates on data that is already aligned to the MARIS schema, so no nomenclature reconciliation is needed; the pipeline focuses on column selection, type casting, and encoding.
#
# The pipeline processes each ref_id through these main stages:
#
# - **Column selection and renaming**: subset to columns of interest and rename to MARIS standard names
# - **Type casting**: coercing STATION to string for VLEN NetCDF variables
# - **Drop NA columns**: remove columns that are all NaN or all "Not available" (id=0)
# - **Detection limit remapping**: map DL symbols (<, =, etc.) to MARIS enum IDs
# - **Time parsing and encoding**: parse date strings, encode as seconds since epoch
# - **Coordinate sanitization**: validate lat/lon ranges and fix separator issues
# - **Unique index**: add a sequential row ID per group
# - **NetCDF encoding**: all groups assembled with global attributes (bbox, time range, Zotero citation, processing logs)

# %%
#| export
from fastcore.all import *
import pandas as pd
import numpy as np
import re

from marisco.callbacks import (
    Callback, PerGroupCB, Transformer,
    EncodeTimeCB, RenameColumnsCB, LowerStripNameCB, SanitizeLonLatCB,
    CompareDfsAndTfmCB, RemapCB, ParseTimeCB, EncodeTimeCB)

from marisco.metadata import GlobAttrsFeeder, BboxCB, DepthRangeCB, TimeRangeCB, ZoteroCB, KeyValuePairCB
from marisco.encoders import NetCDFEncoder
from marisco.configs import NA, NC_DTYPES, get_lut, lut_path, cache_path
from marisco.match import uniq_across_dfs, lut_from, fuzzy_merge, fix_lut, make_lut, make_lut_from
from marisco.geo import ddmm_to_dd
from marisco.utils import ExtractNetcdfContents
from marisco.netcdf2csv import decode

import warnings
warnings.filterwarnings('ignore')

# %% [markdown]
# ## Configuration & file paths

# %% [markdown]
# - **fname_in**: path to the folder containing the MARIS dump data in CSV format. 
#
# - **dir_dest**: path to the folder where the NetCDF output will be saved.
#

# %%
#| exports
#fname_in = Path().home() / 'pro/data/maris/2025-06-03 MARIS_QA_shapetype_id = 1.txt'
fname_in = '../../_data/2025-06-03 MARIS_QA_shapetype_id = 1.txt'
dir_dest = '../../_data/output/dump'

# %%
#| eval: false
df = pd.read_csv(fname_in, sep='\t', encoding='utf-8', low_memory=False)

# %% [markdown]
# ## Utils

# %% [markdown]
# Below a utility class to load a specific MARIS dump dataset optionally filtered through its `ref_id`.
#

# %%
#| export
lut_smp_type = {
    'Biota': 'BIOTA',
    'Seawater': 'SEAWATER',
    'Sediment': 'SEDIMENT',
    'Suspended matter': 'SUSPENDED_MATTER'
    }


# %%
#| export
class DataLoader:
    "Load MARIS dump data filtered by ref_id, returning one DataFrame per sample type group."
    def __init__(self,
                 fname: str,                     # Path to the MARIS global dump CSV
                 exclude_ref_id: list[int]=None, # ref_ids to skip (None = skip none)
                 ):
        store_attr()
        self.df = self._load_data()

    def _load_data(self):
        df = pd.read_csv(self.fname, sep='\t', encoding='utf-8', low_memory=False)
        if self.exclude_ref_id: df = df[~df.ref_id.isin(self.exclude_ref_id)]
        return df

    def __call__(self,
                 ref_id: int                     # Reference ID of interest, or None for all
                 ) -> dict:                      # {group_name: DataFrame} dict
        df = self.df[self.df.ref_id == ref_id].copy() if ref_id else self.df.copy()
        return {lut_smp_type[name]: grp for name, grp in df.groupby('samptype') if name in lut_smp_type}


# %%
#| export
def get_zotero_key(
    dfs:dict  # Dict of {group_name: DataFrame} per sample type
    )->str:   # Zotero key extracted from URL
    "Extract Zotero bibliography key from the MARIS dump DataFrame."
    return dfs[next(iter(dfs))][['zoterourl']].iloc[0].values[0].split('/')[-1]


# %%
#| export
def get_fname(
    dfs:dict  # Dict of {group_name: DataFrame} per sample type
    )->str:   # NetCDF filename like "12345.nc"
    "Construct NetCDF filename from the ref_id in the data."
    return f"{next(iter(dfs.values()))['ref_id'].iloc[0]}.nc"


# %% [markdown]
# ## Load data

# %% [markdown]
# Here below a quick overview of the MARIS dump data structure. For example, OSPAR data has `ref_id=191`, HELCOM has `ref_id=100`.

# %%
#| eval: false
dataloader = DataLoader(fname_in)
dfs = dataloader(ref_id=191)

# %%
#| eval: false
for grp, grpdf in dfs.items():
    cols = ', '.join(grpdf.columns[:6])
    print(f"{grp:15s} ({len(grpdf):>5} rows, {len(grpdf.columns)} cols)  {cols} ...")

# %%
#| eval: false
print('Full list of seawater dataframe columns: \n', dfs['SEAWATER'].columns.to_list())

# %% [markdown]
# ## Pipeline steps

# %% [markdown]
# ### Column renaming

# %% [markdown]
# The MARIS DB dump uses its own column names (e.g. `area_id`, `activity`, `station`). Here we map them to the MARIS standard names used throughout the pipeline. This mapping is hand-maintained because the dump schema and the NetCDF schema are independent; see `nbs/api/configs.ipynb` for the canonical `NC_CSV` that the NetCDF schema defines.

# %%
#| export
cois_renaming_rules = {
    'sample_id': 'SMP_ID',
    'samplabcode': 'SMP_ID_PROVIDER',
    'latitude': 'LAT',
    'longitude': 'LON',
    'begperiod': 'TIME',
    'sampdepth': 'SMP_DEPTH',
    'totdepth': 'TOT_DEPTH',
    'station': 'STATION',
    'uncertaint': 'UNC',
    'unit_id': 'UNIT',
    'detection': 'DL',
    'area_id': 'AREA',
    'species_id': 'SPECIES',
    'biogroup_id': 'BIO_GROUP',
    'bodypar_id': 'BODY_PART',
    'sedtype_id': 'SED_TYPE',
    'volume': 'VOL',
    'salinity': 'SAL',
    'temperatur': 'TEMP',
    'sampmet_id': 'SAMP_MET',
    'prepmet_id': 'PREP_MET',
    'counmet_id': 'COUNT_MET',
    'activity': 'VALUE',
    'nuclide_id': 'NUCLIDE',
    'sliceup': 'TOP',
    'slicedown': 'BOTTOM'
}

# %%
#| eval: false
tfm = Transformer(dfs, cbs=[RenameColumnsCB(cois_renaming_rules)])

dfs_tfm = tfm()
print('Keys:', dfs_tfm.keys())
print('Columns:', dfs_tfm['SEAWATER'].columns)


# %% [markdown]
# ### STATION as string type
#
# The STATION column in the MARIS dump may arrive with mixed or numeric types, but the NetCDF template defines it as a VLEN string variable. CastStationToStringCB coerces it to string[python] and fills missing values with an empty string.
#
#

# %%
#| export
class CastStationToStringCB(PerGroupCB):
    "Convert STATION column to string type, filling any missing values with empty string"
    def each_grp(self, grp, df, tfm):
        if 'STATION' in df.columns:
            df['STATION'] = df['STATION'].fillna('').astype('string')


# %%
tfm = Transformer({
    'SEAWATER': pd.DataFrame({'STATION': ['A1', None, 42]}),
    'BIOTA': pd.DataFrame({'STATION': ['B2', None]})
}, cbs=[CastStationToStringCB()])
tfm()

test_eq(tfm.dfs['SEAWATER']['STATION'].dtype.name, 'string')
test_eq(tfm.dfs['SEAWATER']['STATION'].isna().sum(), 0)
test_eq(tfm.dfs['SEAWATER']['STATION'].to_list(), ['A1', '', '42'])
test_eq(tfm.dfs['BIOTA']['STATION'].to_list(), ['B2', ''])

# %%
#| eval: false
tfm = Transformer(dfs, cbs=[
    RenameColumnsCB(cois_renaming_rules),
    CastStationToStringCB()
    ])

dfs_tfm = tfm()
print(dfs_tfm['SEAWATER']['STATION'].dtype)


# %% [markdown]
# ### Drop all-empty columns

# %% [markdown]
# Some columns in the MARIS dump are entirely empty or contain only 'Not available' markers (id=0 in MARIS lookup tables). DropNAColumnsCB removes these columns from every group before further processing, keeping the output compact.

# %%
#| export
class DropNAColumnsCB(PerGroupCB):
    "Drop variable containing only NaN or 'Not available' (id=0 in MARIS lookup tables)."
    def __init__(
        self, 
        na_value:int=0  # MARIS NA id to drop (default 0)
        ): store_attr()
    def isMarisNA(self, col:pd.Series )->bool:              
        return len(col.unique()) == 1 and col.iloc[0] == self.na_value
    def dropMarisNA(self, df:pd.DataFrame)->pd.DataFrame:        
        na_cols = [col for col in df.columns if self.isMarisNA(df[col])]
        return df.drop(labels=na_cols, axis=1)
    def each_grp(self, grp:str, df:pd.DataFrame, tfm:Transformer):   
        tfm.dfs[grp] = df.dropna(axis=1, how="all")
        tfm.dfs[grp] = self.dropMarisNA(tfm.dfs[grp])


# %%
tfm = Transformer({
    'SEAWATER': pd.DataFrame({
        'STATION': ['A1', 'B2'],
        'EMPTY': [np.nan, np.nan],
        'MARIS_NA': [0, 0],
        'VALUE': [1.0, 2.0]
    })
}, cbs=[DropNAColumnsCB()])
tfm()

test_eq(list(tfm.dfs['SEAWATER'].columns), ['STATION', 'VALUE'])

# %%
#| eval: false
tfm = Transformer(dfs, cbs=[
    RenameColumnsCB(cois_renaming_rules),
    CastStationToStringCB(),
    DropNAColumnsCB()
    ])

dfs_tfm = tfm()
print('Columns:', list(dfs_tfm['SEAWATER'].columns))

# %% [markdown]
# ### Remap detection limit values

# %% [markdown]
# The detection column stores detection limit symbols as strings (<, =, ND, etc.), but the MARIS NetCDF format encodes these as integer identifiers from the dbo_detectlimit lookup table. RemapCB maps each symbol to its integer id using `get_lut`, with unmapped values defaulting to 0 (Not Available).

# %% [markdown]
# ::: {.callout-important}
# ## FEEDBACK TO MARIS DATA TEAM
# Future MARIS dump exports should provide the `detection` lut integer id directly rather than its symbolic representation, removing the need for this remapping step.
# :::

# %%
#| exports
lut_dl = get_lut('DL', key='name', value='id')

# %%
#| eval: false
lut_dl

# %%
dfs_mock = {
    'SEAWATER': pd.DataFrame({'DL': ['=', '<', 'ND', 'DE', None]}),
    'BIOTA': pd.DataFrame({'DL': ['=', 'ND', None]})
}
tfm = Transformer(dfs_mock, cbs=[RemapCB(lut=lut_dl, col_src='DL', col_remap='DL', default_val=0)])
tfm()

test_eq(list(tfm.dfs['SEAWATER']['DL']), [1, 2, 3, 4, 0])

# %%
#| eval: false
tfm = Transformer(dfs, cbs=[
    RenameColumnsCB(cois_renaming_rules),
    CastStationToStringCB(),
    DropNAColumnsCB(),
    RemapCB(lut=lut_dl, col_src='DL', col_remap='DL', default_val=0)
])

dfs_tfm = tfm()
print('DL values present:', sorted(dfs_tfm['BIOTA']['DL'].unique()))

# %% [markdown]
# ### Parse and encode time

# %% [markdown]
# In the MARIS NetCDF format, time is stored as an integer representing the number of seconds since a reference date (`1970-01-01 00:00:00.0`, as defined in `nbs/api/files/cdl/maris.cdl`). ParseTimeCB converts the TIME column from the original date string format, and EncodeTimeCB converts it to integer seconds.

# %%
tfm = Transformer({
    'SEAWATER': pd.DataFrame({'TIME': ['1990-01-01', None]})
}, cbs=[ParseTimeCB(), EncodeTimeCB()])
tfm()

test_eq(list(tfm.dfs['SEAWATER']['TIME']), [631152000])

# %% [markdown]
# ### Sanitize coordinates

# %% [markdown]
# Raw coordinates in the MARIS dump may use commas as decimal separators instead of periods, or fall outside valid lat/lon ranges. `SanitizeLonLatCB` converts `,` to `.` and drops rows with out-of-range values.

# %%
tfm = Transformer({
    'SEAWATER': pd.DataFrame({
        'LAT': [57.25, 91.0, '57,250'],
        'LON': [12.08, 181.0, '12,083']
    })
}, cbs=[SanitizeLonLatCB()])
tfm()

test_eq(list(tfm.dfs['SEAWATER']['LAT']), [57.25, 57.25])
test_eq(list(tfm.dfs['SEAWATER']['LON']), [12.08, 12.083])


# %% [markdown]
# ### Add sample ids

# %% [markdown]
# The MARIS dump provides `sample_id` (an internal MARIS sequential id) and `samplabcode` (the provider's original sample identifier). The renaming step maps these to the MARIS standard names `SMP_ID` and `SMP_ID_PROVIDER`. AddSampleIDCB then casts `SMP_ID` to integer and `SMP_ID_PROVIDER` to a variable-length string, filling missing values with an empty string.

# %%
#| export
class AddSampleIDCB(PerGroupCB):
    "Cast SMP_ID to int and SMP_ID_PROVIDER to string (renamed from samplabcode in the pipeline)."
    def each_grp(self, grp, df, tfm):
        df['SMP_ID'] = df['SMP_ID'].astype(int)
        df['SMP_ID_PROVIDER'] = df['SMP_ID_PROVIDER'].fillna('').astype(str)


# %%
tfm = Transformer({
    'SEAWATER': pd.DataFrame({'SMP_ID': [1, 2], 'SMP_ID_PROVIDER': [None, 'RC1']})
}, cbs=[AddSampleIDCB()])
tfm()

test_eq(tfm.dfs['SEAWATER']['SMP_ID'].dtype, int)
test_eq(tfm.dfs['SEAWATER']['SMP_ID_PROVIDER'].to_list(), ['', 'RC1'])

# %%
#| eval: false
tfm = Transformer(dfs, cbs=[
    RenameColumnsCB(cois_renaming_rules),
    CastStationToStringCB(),
    DropNAColumnsCB(),
    RemapCB(lut=lut_dl, col_src='DL', col_remap='DL', default_val=0),
    ParseTimeCB(),
    EncodeTimeCB(),
    SanitizeLonLatCB(),
    AddSampleIDCB()
])
dfs_tfm = tfm()
print(dfs_tfm['SEAWATER'][['SMP_ID', 'SMP_ID_PROVIDER']].head(3).to_string(index=False))

# %% [markdown]
# ## Encode to NetCDF

# %%
#| eval: false
tfm = Transformer(dfs, cbs=[
    RenameColumnsCB(cois_renaming_rules),
    CastStationToStringCB(),
    DropNAColumnsCB(),
    RemapCB(lut=lut_dl, col_src='DL', col_remap='DL', default_val=0),
    ParseTimeCB(),
    EncodeTimeCB(),
    SanitizeLonLatCB(),
    AddSampleIDCB()
])

dfs_tfm = tfm()
tfm.logs

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
        DepthRangeCB(),
        TimeRangeCB(),
        ZoteroCB(zotero_key),
        KeyValuePairCB('keywords', ', '.join(kw)),
        KeyValuePairCB('publisher_postprocess_logs', ', '.join(tfm.logs))
        ])()


# %%
#| eval: false
get_attrs(tfm, zotero_key='3W354SQG', kw=kw)


# %% [markdown]
# ### Encoding
#
# The `encode` function ties the full pipeline together: it loads each unique ref_id from the MARIS dump, runs the standard transformation pipeline, assembles global attributes (bbox, time range, Zotero citation, processing logs), and writes each reference as a separate NetCDF file.
#

# %%
#| eval: false
def encode(
    fname_in: str, # Path to the MARIS dump data in CSV format
    dir_dest: str, # Path to the folder where the NetCDF output will be saved
    **kwargs # Additional keyword arguments
    ):
    "Encode MARIS dump to NetCDF."
    dataloader = DataLoader(fname_in)
    ref_ids = kwargs.get('ref_ids')
    if ref_ids is None:
        ref_ids = dataloader.df.ref_id.unique()
    print('Encoding ...')
    for i, ref_id in enumerate(ref_ids):
        dfs = dataloader(ref_id=ref_id)
        print(f'{i+1}/{len(ref_ids)}: ref_id={ref_id} -> {dir_dest}/{get_fname(dfs)}')
        tfm = Transformer(dfs, cbs=[
            RenameColumnsCB(cois_renaming_rules),
            CastStationToStringCB(),
            DropNAColumnsCB(),
            RemapCB(lut=lut_dl, col_src='DL', col_remap='DL', default_val=0),
            ParseTimeCB(),
            EncodeTimeCB(),
            SanitizeLonLatCB(),
            AddSampleIDCB(),
        ])
        
        tfm()
        encoder = NetCDFEncoder(tfm.dfs, 
                                dest_fname=Path(dir_dest) / get_fname(dfs), 
                                global_attrs=get_attrs(tfm, zotero_key=get_zotero_key(dfs), kw=kw),
                                verbose=kwargs.get('verbose', False)
                                )
        encoder.encode()


# %% [markdown]
# ### Single dataset

# %%
#| eval: false
ref_id = 106
encode(
    fname_in,
    dir_dest,
    verbose=False, 
    ref_ids=[ref_id])

# %% [markdown]
# ### All datasets

# %%
#| eval: false
encode(
    fname_in, 
    dir_dest, 
    ref_ids=None,
    verbose=False)
