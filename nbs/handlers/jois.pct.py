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

# %% [markdown]
# ## Joint Ocean Ice Study
#
# The JOIS datasets comprise four years (2021-2024) of seawater radionuclide measurements from the Beaufort Sea, collected as part of the Joint Ocean Ice Study (JOIS) expeditions aboard the CCGS Louis St. Laurent. Samples were analysed at ETH Zurich / LIP (Nuria Casacuberta's group). The raw data are published as [Zenodo archives](https://zenodo.org/communities/titanica/records?q=&l=list&p=1&s=10&sort=newest), each containing a single Excel file with CTD (conductivity, temperature, depth) metadata and activity concentrations in wide format.
#
# Nuclide coverage varies by year:
#
# :::{style="width: fit-content; font-size: 0.85em; margin: 0 auto;"}
# | Year | I-129 | U-236 | U-238 | U-236/U-238 |
# |------|:-----:|:-----:|:-----:|:-----------:|
# | 2021 | ✓ | | | |
# | 2022 | ✓ | ✓ | ✓ | ✓ |
# | 2023 | ✓ | ✓ | ✓ | ✓ |
# | 2024 | ✓ | | | |
# :::
#
# The column layout is similar enough across years that the same pipeline handles all of them, with a few normalisation steps to absorb the differences.

# %%
#| default_exp handlers.jois

# %%
#| export
from fastcore.all import *
import pandas as pd
import numpy as np
import re
import requests
import zipfile
import io

from marisco.callbacks import (PerGroupCB, Callback, Transformer, EncodeTimeCB,
                                SanitizeLonLatCB, RemapCB, AddSampleIDCB)
from marisco.metadata import GlobAttrsFeeder, ZoteroCB, BboxCB, DepthRangeCB, TimeRangeCB, KeyValuePairCB
from marisco.encoders import NetCDFEncoder

# %%
#| exports
RECORDS = {
    2021: {'url': 'https://zenodo.org/records/18880401/files/annabel-payne/BGOS-JOIS-2021-v1.0.1.zip?download=1'},
    2022: {'url': 'https://zenodo.org/records/18880777/files/annabel-payne/BGOS-JOIS-2022-v1.0.1.zip?download=1'},
    2023: {'url': 'https://zenodo.org/records/18880591/files/annabel-payne/BGOS-JOIS-2023-v1.0.zip?download=1'},
    2024: {'url': 'https://zenodo.org/records/18880497/files/annabel-payne/BGOS-JOIS-2024-v1.0.1.zip?download=1'},
}
fname_out = 'JOIS_Beaufort_Sea.nc'
src_dir   = None  # remote-only, no local files


# %% [markdown]
# ## Raw data format
#
# All four JOIS ZIP archives contain a single Excel sheet with CTD metadata columns and activity concentrations in wide format: each nuclide-unit pair gets its own column (e.g. `I129_at_kg`, `I129_at_l`), and each value column has a matching `unc_` column for uncertainty. Value columns carry `( x 10^N)` suffixes in some years indicating an unscaled value. The 2021 ZIP has a stray `( x 10^6)` column header that should read `Cruise`.
#
# `load_data` handles all four years by:
# - Normalising column names (stripping scale-factor suffixes)
# - Extracting and applying scale factors to unscaled values
# - Detecting the 2023 U-236 `at_kg` columns that are missing their suffix but are in the same scale as their `at_l` counterparts
# - Concatenating all years into a single DataFrame

# %% [markdown]
# :::{.callout-important}
# ## FEEDBACK TO DATA PROVIDER
#
# Inconsistent scale-factor application across years: `I129_at_kg` values in the 2021 and 2022 Excel files are reported as raw x10^-7 (columns named `I129_at_kg ( x 10^7)`), while 2023-2024 use the same column name `I129_at_kg` with the scale already applied. The same issue affects `U236_at_kg` in 2023: `U236_at_l` has its `( x 10^6)` suffix, but `U236_at_kg` does not, even though both are in the same scale (ratio check confirms seawater density ~1025 kg/m3). The provider should confirm whether 2021-2022 data can be published with the scale applied.
# :::

# %%
#| export
def norm_cols(cols  # Column names to normalise
    ) -> list:
    "Normalise column names: strip scale-factor suffixes like ( x 10^7) or (x 10^6)."
    return [re.sub(r'\s*\([^)]*\)\s*', '', c).strip() for c in cols]


# %%
test_eq(norm_cols(['I129_at_kg ( x 10^7)', 'U236_at_l']),
        ['I129_at_kg', 'U236_at_l'])
test_eq(norm_cols(['Stn', 'Depth_m']), ['Stn', 'Depth_m'])
print("norm_cols: no-change case and suffix-stripping case pass. ✓")


# %%
#| export
def extract_scales(cols  # Column names to scan for scale-factor suffixes
    ) -> dict:
    "Return {col: factor} for columns with `( x 10^N)` suffix in original names, excluding empty-string results."
    return {k: 10**int(m.group(1)) for c in cols 
            if (m := re.search(r'\s*\(\s*x\s*10\^(\d+)\)', c)) 
            and (k := re.sub(r'\s*\([^)]*\)\s*', '', c).strip())}


# %%
scales = extract_scales(['I129_at_kg ( x 10^7)', 'U236_at_l(x10^6)', 'Stn'])
test_eq(scales, {'I129_at_kg': 10_000_000, 'U236_at_l': 1_000_000})
print("extract_scales: two scales extracted, no spurious matches. ✓")


# %%
#| export
def apply_scales(
    df,     # DataFrame to modify in place
    scales, # {col: factor} of scale factors to apply
    ) -> pd.DataFrame:
    "Multiply columns in df by their scale factor."
    for col, factor in scales.items():
        if col in df.columns: df[col] *= factor
    # 2023 U236_at_kg is missing its ( x 10^6) suffix but values are in same scale
    if any('U236' in c and c.endswith('_l') for c in scales):
        for c in ['U236_at_kg', 'unc_U236_at_kg']:
            if c in df.columns and c not in scales: df[c] *= 1e6
    return df


# %%
df = pd.DataFrame({'I129_at_kg': [1.0, 2.0], 'Stn': ['A', 'B']})
scales = {'I129_at_kg': 10_000_000}
result = apply_scales(df, scales)
test_eq(result['I129_at_kg'].tolist(), [10_000_000.0, 20_000_000.0])
test_eq(result['Stn'].tolist(), ['A', 'B'])
print("apply_scales: value columns scaled, non-value columns unchanged. ✓")


# %%
#| export
def load_data(
    recs=None, # Optional dict of year->record; defaults to all RECORDS
    ) -> dict:
    "Fetch all JOIS records from Zenodo, align column names, apply scale factors, and return a single `SEAWATER` DataFrame."
    recs = recs or RECORDS
    parts = []
    for r in recs.values():
        resp = requests.get(r['url'], timeout=60); resp.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
            xl_name = next(n for n in z.namelist() if n.lower().endswith(('.xlsx', '.xls')))
            df = pd.ExcelFile(io.BytesIO(z.read(xl_name))).parse(sheet_name=0)
        cols = list(df.columns)
        scales = extract_scales(cols)
        cols = norm_cols(cols)
        if cols[0] == '': cols[0] = 'Cruise'
        df.columns = cols
        df = apply_scales(df, scales)
        parts.append(df)
    return {'SEAWATER': pd.concat(parts, ignore_index=True)}


# %%
#| eval: false
dfs = load_data()

# %%
#|eval: false
print(dfs['SEAWATER'].describe(include='number').T[['count', 'mean', 'min', 'max']])


# %% [markdown]
# ## Rename and standardise columns
#
# The raw JOIS columns encode nuclide, unit, and sometimes method in a single string
# (e.g. `I129_at_kg`), with a couple of exceptions (`U238_ppb`, `U236_U238`).
# We map CTD column names to MARIS uppercase standards, combine separate date/time
# string columns, and handle the two special-case columns.
#
# We address these in three callbacks. All run on the `SEAWATER` group only, since
# JOIS has no biota, sediment, or suspended matter.

# %% [markdown]
# :::{.callout-important}
# ## FEEDBACK TO DATA PROVIDER
#
# Column headers in the JOIS and GEOTRACES datasets encode multiple pieces of information (nuclide, unit, measurement method) into a single string. This adds friction to data ingestion, since every new dataset with a different naming convention requires custom parsing logic. MARIS prefers a tidy data layout ([Wickham 2014, doi:10.18637/jss.v059.i10](https://www.jstatsoft.org/article/view/v059i10)) where each column holds a single variable, and metadata like nuclide, unit, and method are stored as separate columns, not baked into the header.
# :::

# %%
#| export
class RenameNucColsCB(PerGroupCB):
    "Align U238_ppb and U236_U238 column names to {Nuc}_{Unit} pattern before melting."
    grps = ['SEAWATER']
    def each_grp(self, grp, df, tfm):
        df.rename(columns={
            'U238_ppb': 'U238_at_ppb', 'U236_U238': 'U236_U238_at_ratio',
            'unc_U238_ppb': 'unc_U238_at_ppb', 'unc_U236_U238': 'unc_U236_U238_at_ratio',
        }, inplace=True)


# %%
# Verify RenameNucColsCB renames columns correctly on mock data
dfs_mock = {'SEAWATER': pd.DataFrame({'U238_ppb': [1.0], 'U236_U238': [2.0], 'I129_at_kg': [3.0]})}
tfm = Transformer(dfs_mock, cbs=[RenameNucColsCB()])
tfm()
test_eq('U238_at_ppb' in tfm.dfs['SEAWATER'].columns, True)
test_eq('U236_U238_at_ratio' in tfm.dfs['SEAWATER'].columns, True)
test_eq('I129_at_kg' in tfm.dfs['SEAWATER'].columns, True)
print("RenameNucColsCB: columns renamed correctly on mock data. ✓")

# %%
#|eval: false
tfm = Transformer(dfs, cbs=[RenameNucColsCB()])
tfm()
print("Columns after RenameNucColsCB:", [c for c in tfm.dfs['SEAWATER'].columns if '238' in c or '236' in c])


# %% [markdown]
# ### Align nuclide column names
#
# Most JOIS concentration columns follow a `{Nuclide}_{Unit}` pattern (`I129_at_kg`, `I129_at_l`, `U236_at_kg`). Two columns do not:
#
# - `U238_ppb` names the measurand method (parts-per-billion) as the unit part, which would cause the melt split to produce `NUCLIDE=U238_at` and `UNIT=ppb`. We rename it to `U238_at_ppb` so the split is clean.
# - `U236_U238` uses an underscore as a separator between two nuclide names, not between nuclide and unit. We rename it to `U236_U238_at_ratio`.
#
# The downstream `MeltJOISCB` splits every value column on `_at_` to derive `NUCLIDE` and `UNIT`. These renames are done in anticipation of that step, ensuring every column meets the `{Nuclide}_{Unit}` contract so the melt can proceed consistently.

# %%
#| export
class RenameColsCB(PerGroupCB):
    "Map JOIS provider CTD and sample columns to MARIS standard names."
    grps = ["SEAWATER"]
    def each_grp(self, grp, df, tfm):
        df.rename(columns={
            "Latitude_degN": "LAT", "Longitude_degE": "LON",
            "Depth_m": "SMP_DEPTH", "Temperature_degC": "TEMP",
            "Salinity_psu": "SAL", "Station": "STATION",
            "sample_number": "SMP_ID_PROVIDER",
        }, inplace=True)


# %%
# Verify RenameColsCB maps provider columns to MARIS names
dfs_mock = {'SEAWATER': pd.DataFrame({'Latitude_degN': [70.5], 'Longitude_degE': [-140.0],
                                       'Depth_m': [200.0], 'sample_number': [101]})}
tfm = Transformer(dfs_mock, cbs=[RenameColsCB()])
tfm()
test_eq('LAT' in tfm.dfs['SEAWATER'].columns, True)
test_eq('LON' in tfm.dfs['SEAWATER'].columns, True)
test_eq('SMP_DEPTH' in tfm.dfs['SEAWATER'].columns, True)
test_eq('SMP_ID_PROVIDER' in tfm.dfs['SEAWATER'].columns, True)
print("RenameColsCB: provider columns mapped to MARIS names. ✓")


# %%
#|eval: false
tfm = Transformer(dfs, cbs=[RenameNucColsCB(), RenameColsCB()])
tfm()
print("Sample of renamed columns:\n", tfm.dfs['SEAWATER'][['LAT', 'LON', 'STATION', 'SMP_DEPTH', 'SMP_ID_PROVIDER']].head(2).to_string())


# %%
#| export
class ParseDateTimeCB(PerGroupCB):
    "Combine JOIS Date and Time columns into a single TIME column."
    grps = ["SEAWATER"]
    def __init__(self, col_date="Date",  # Source date column name
                 col_time="Time"):       # Source time column name
        store_attr()
    def each_grp(self, grp, df, tfm):
        df["TIME"] = pd.to_datetime(df[self.col_date].astype(str) + "T" + df[self.col_time].astype(str))
        df.drop(columns=[self.col_date, self.col_time], inplace=True)


# %%
# Verify ParseDateTimeCB combines Date and Time into TIME
dfs_mock = {'SEAWATER': pd.DataFrame({'Date': ['2021-08-19'], 'Time': ['08:00:00']})}
tfm = Transformer(dfs_mock, cbs=[ParseDateTimeCB()])
tfm()
test_eq('TIME' in tfm.dfs['SEAWATER'].columns, True)
test_eq('Date' not in tfm.dfs['SEAWATER'].columns, True)
print(f"ParseDateTimeCB: TIME = {tfm.dfs['SEAWATER']['TIME'].iloc[0]}. ✓")

# %%
#|eval: false
tfm = Transformer(dfs, cbs=[RenameNucColsCB(), RenameColsCB(), ParseDateTimeCB()])
tfm()
print("First 3 TIME values:\n", tfm.dfs['SEAWATER']['TIME'].head(3).to_string())

# %% [markdown]
# ::: {.callout-note}
#
# #### Note for MARIS DB team
#
# The JOIS datasets include a `Pressure_dbar` column with CTD pressure values. This parameter is currently not present in the MARIS output schema. If useful for the database, it could be added alongside the other CTD metadata fields.
#   The extra CTD columns (`Conservative_Temp`, `Potential_Temp`, `Absolute_Salinity`, `Sigma0`, `Insitu_Density`, `unc_129_pct`) and the `Cruise` column are not mapped in the NC_CSV dict (the central remapping from internal column names to NetCDF/CSV output names), so they are dropped after the melt. If the data team decides these fields are useful, the fix should go in NC_CSV, not in this handler.
#
# :::

# %% [markdown]
# ## Reshape wide to long
#
# The raw JOIS data uses wide format: each sample has one row, and nuclide-unit concentrations are spread across separate columns (`I129_at_kg`, `I129_at_l`, `U236_at_kg`, etc.). MARIS requires long format (one row per measurement) with columns for `NUCLIDE`, `UNIT`, `VALUE`, and `UNC`.
#
# `MeltJOISCB` melts the value columns, merges the matching uncertainty columns, then splits each column name on `_at_` to derive the nuclide name and unit. Rows where `VALUE` is NaN are dropped.

# %%
#| exports
# Columns kept as identifiers during the wide-to-long reshape
META_COLS = ['Cruise', 'STATION', 'SMP_ID_PROVIDER', 'LAT', 'LON',
             'TIME', 'Pressure_dbar', 'SMP_DEPTH', 'TEMP', 'SAL']

# Columns to melt into VALUE/UNC long format
VAL_COLS = ['I129_at_kg', 'I129_at_l', 'U236_at_kg', 'U236_at_l',
            'U238_at_ppb', 'U236_U238_at_ratio']


# %%
#| export
class MeltJOISCB(PerGroupCB):
    "Reshape JOIS wide nuclide columns to long format with NUCLIDE, UNIT, VALUE, UNC columns."
    grps = ['SEAWATER']
    def __init__(self,
                 meta_cols,  # Columns to keep as identifiers
                 val_cols,   # Value columns to melt
                 val_name='VALUE',  # Name of melted value column
                 unc_name='UNC'):   # Name of uncertainty column
        store_attr()
    def each_grp(self, grp, df, tfm):
        vals = df.melt(id_vars=self.meta_cols, value_vars=self.val_cols,
                       var_name='nuclide_raw', value_name=self.val_name)
        uncs = df.melt(id_vars=self.meta_cols,
                       value_vars=[f'unc_{c}' for c in self.val_cols],
                       value_name=self.unc_name)
        uncs['nuclide_raw'] = uncs['variable'].str.replace('unc_', '', regex=False)
        out = vals.merge(uncs[self.meta_cols + ['nuclide_raw', self.unc_name]],
                         on=self.meta_cols + ['nuclide_raw'])
        out.dropna(subset=self.val_name, inplace=True)
        out['NUCLIDE'] = out['nuclide_raw'].str.split('_at_').str[0]
        out['UNIT']    = 'at_' + out['nuclide_raw'].str.split('_at_').str[1]
        del out['nuclide_raw']
        tfm.dfs[grp] = out


# %%
# Verify MeltJOISCB produces correct NUCLIDE, UNIT, VALUE, UNC columns on mock data
dfs_mock = {'SEAWATER': pd.DataFrame({
    'Cruise': ['2021'], 'STATION': ['CB4'], 'SMP_ID_PROVIDER': [1],
    'I129_at_kg': [6.4e8], 'unc_I129_at_kg': [2.0e7],
    'I129_at_l': [6.6e8], 'unc_I129_at_l': [2.1e7],
})}
MOCK_META = ['Cruise', 'STATION', 'SMP_ID_PROVIDER']
MOCK_VALS = ['I129_at_kg', 'I129_at_l']
tfm = Transformer(dfs_mock, cbs=[MeltJOISCB(MOCK_META, MOCK_VALS)])
tfm()
out = tfm.dfs['SEAWATER']
test_eq(len(out), 2)
test_eq(out['NUCLIDE'].tolist(), ['I129', 'I129'])
test_eq(out['UNIT'].tolist(), ['at_kg', 'at_l'])
test_eq(out['VALUE'].tolist(), [6.4e8, 6.6e8])
print("MeltJOISCB on mock data: 2 rows, correct NUCLIDE/UNIT split. ✓")

# %%
#|eval: false
tfm = Transformer(dfs, cbs=[RenameNucColsCB(), RenameColsCB(), ParseDateTimeCB(),
                             MeltJOISCB(META_COLS, VAL_COLS)])
tfm()
out = tfm.dfs['SEAWATER']
print(f"Shape: {out.shape}")
print("NUCLIDE values:", out['NUCLIDE'].unique())
print("UNIT values:", out['UNIT'].unique())
print(out[['NUCLIDE', 'UNIT', 'VALUE', 'UNC']].head(6).to_string())

# %% [markdown]
# :::{.callout-important}
# ## FEEDBACK TO DATA PROVIDER
#
# Uncertainty values in 2024 are three orders of magnitude lower than in 2021-2023 (relative uncertainty ~0.0002% versus ~3-5%), with no documented change in analytical method or instrumentation. All three uncertainty representations (`unc_I129_at_kg`, `unc_I129_at_l`, `unc_129_pct`) are internally consistent within each year. The provider should confirm whether this reflects a genuine precision improvement or a data reporting issue.
# :::
#

# %% [markdown]
# ## Convert U-238 units
#
# JOIS reports U-238 in parts-per-billion (ppb, mass of U per mass of seawater), while MARIS requires atoms per kg. `ConvertU238CB` converts the VALUE column for U-238 rows using:
#
# $$\text{atoms/kg} = C_{\text{ppb}} \times 10^{-9} \times \frac{N_A}{M_{238}}$$
#
# where $N_A = 6.02214076 \times 10^{23}\ \text{mol}^{-1}$ is Avogadro's number and $M_{238} = 238.05\ \text{g/mol}$ is the molar mass of U-238, giving a conversion factor of $2.530 \times 10^{12}\ \text{atoms/kg per ppb}$. Rows with other nuclides are left unchanged.

# %%
#| exports
# Convert U-238 from ppb to atoms/kg: ppb * 1e-9 * (1/238.05) * 6.02214076e23
U238_PPB_TO_AT_KG = 2.529_697e12


# %%
#| export
class ConvertU238CB(PerGroupCB):
    "Convert U-238 VALUE from ppb to atoms/kg."
    grps = ['SEAWATER']
    def each_grp(self, grp, df, tfm):
        m = df['NUCLIDE'] == 'U238'
        df.loc[m, 'VALUE'] *= U238_PPB_TO_AT_KG
        df.loc[m, 'UNC'] *= U238_PPB_TO_AT_KG
        df.loc[m, 'UNIT'] = 'at_kg'


# %%
# Verify ConvertU238CB scales VALUE and UNC for U-238 only
dfs_mock = {'SEAWATER': pd.DataFrame({
    'NUCLIDE': ['I129', 'U238'],
    'UNIT': ['at_kg', 'at_ppb'],
    'VALUE': [1.0, 2.0],
    'UNC': [0.1, 0.2],
})}
tfm = Transformer(dfs_mock, cbs=[ConvertU238CB()])
tfm()
out = tfm.dfs['SEAWATER']
test_eq(out.loc[out['NUCLIDE']=='U238', 'VALUE'].iloc[0], 2.0 * U238_PPB_TO_AT_KG)
test_eq(out.loc[out['NUCLIDE']=='U238', 'UNC'].iloc[0], 0.2 * U238_PPB_TO_AT_KG)
test_eq(out.loc[out['NUCLIDE']=='U238', 'UNIT'].iloc[0], 'at_kg')
print("ConvertU238CB: I-129 unchanged, U-238 scaled, UNIT updated. ✓")

# %%
#|eval: false
tfm = Transformer(dfs, cbs=[RenameNucColsCB(), RenameColsCB(), ParseDateTimeCB(),
                             MeltJOISCB(META_COLS, VAL_COLS),
                             ConvertU238CB()])
tfm()
out = tfm.dfs['SEAWATER']
u238 = out[out['NUCLIDE']=='U238']
print(f"U-238 rows: {len(u238)}, mean VALUE = {u238['VALUE'].mean():.2e} atoms/kg")
i129 = out[out['NUCLIDE']=='I129']
print(f"I-129 rows: {len(i129)}, mean VALUE = {i129['VALUE'].mean():.2e} atoms/kg")

# %% [markdown]
# ## Remap nomenclatures to MARIS identifiers
#
# The melt produces string columns: `NUCLIDE` (I129, U236, U238, U236_U238), `UNIT` (at_kg, at_l, at_ppb, at_ratio), and missing `LAB` and `AREA` columns. MARIS stores these as integer foreign-key IDs from the central nomenclatures.
#
# `RemapCB` maps source column values through a lookup table to a target column. For constants like `LAB` (ETH Zurich/LIP, ID 345) and `AREA` (Beaufort Sea, ID 4256), an empty LUT with a `default_val` injects the same value for every row.

# %%
#| exports
# MARIS nuclide IDs confirmed via get_lut('NUCLIDE')
NUCLIDE_LUT = {'I129': 28, 'U236': 108, 'U238': 64, 'U236_U238': 131}

# MARIS unit IDs confirmed via get_lut('UNIT')
UNIT_LUT = {'at_kg': 9, 'at_l': 12, 'at_ratio': 6}

# %%
# Verify RemapCB assigns correct NUCLIDE, UNIT, LAB, AREA IDs
dfs_mock = {'SEAWATER': pd.DataFrame({
    'NUCLIDE': ['I129', 'U236'],
    'UNIT': ['at_kg', 'at_l'],
    'VALUE': [1.0, 2.0],
    'UNC': [0.1, 0.2],
})}
tfm = Transformer(dfs_mock, cbs=[
    RemapCB(lut=NUCLIDE_LUT, col_remap='NUCLIDE', col_src='NUCLIDE'),
    RemapCB(lut=UNIT_LUT, col_remap='UNIT', col_src='UNIT'),
    RemapCB(lut={}, col_remap='LAB', col_src='NUCLIDE', default_val=345),
    RemapCB(lut={}, col_remap='AREA', col_src='NUCLIDE', default_val=4256),
])
tfm()
out = tfm.dfs['SEAWATER']
test_eq(out['NUCLIDE'].tolist(), [28, 108])
test_eq(out['UNIT'].tolist(), [9, 12])
test_eq(out['LAB'].tolist(), [345, 345])
test_eq(out['AREA'].tolist(), [4256, 4256])
print("RemapCB: all nomenclatures mapped to correct MARIS IDs. ✓")

# %%
#|eval: false
tfm = Transformer(dfs, cbs=[
    RenameNucColsCB(), RenameColsCB(), ParseDateTimeCB(),
    MeltJOISCB(META_COLS, VAL_COLS),
    ConvertU238CB(),
    RemapCB(lut=NUCLIDE_LUT, col_remap='NUCLIDE', col_src='NUCLIDE'),
    RemapCB(lut=UNIT_LUT, col_remap='UNIT', col_src='UNIT'),
    RemapCB(lut={}, col_remap='LAB', col_src='NUCLIDE', default_val=345),
    RemapCB(lut={}, col_remap='AREA', col_src='NUCLIDE', default_val=4256),
])
tfm()
out = tfm.dfs['SEAWATER']
print(out[['NUCLIDE', 'UNIT', 'LAB', 'AREA']].drop_duplicates().to_string())

# %% [markdown]
# ## Standardise final columns
#
# Three shared callbacks complete the pipeline:
#
# - `SanitizeLonLatCB`: validates longitude/latitude ranges and ensures correct sign convention
# - `EncodeTimeCB`: encodes the TIME column into the NetCDF-compatible numeric representation
# - `AddSampleIDCB`: assigns a sequential `SMP_ID` and preserves the provider's `SMP_ID_PROVIDER`
#
# All three are imported from `marisco.callbacks` and require no configuration for JOIS.

# %%
#|eval: false
tfm = Transformer(dfs, cbs=[
    RenameNucColsCB(), RenameColsCB(), ParseDateTimeCB(),
    MeltJOISCB(META_COLS, VAL_COLS),
    ConvertU238CB(),
    RemapCB(lut=NUCLIDE_LUT, col_remap='NUCLIDE', col_src='NUCLIDE'),
    RemapCB(lut=UNIT_LUT, col_remap='UNIT', col_src='UNIT'),
    RemapCB(lut={}, col_remap='LAB', col_src='NUCLIDE', default_val=345),
    RemapCB(lut={}, col_remap='AREA', col_src='NUCLIDE', default_val=4256),
    SanitizeLonLatCB(),
    EncodeTimeCB(),
    AddSampleIDCB(col_provider='SMP_ID_PROVIDER'),
])
tfm()
out = tfm.dfs['SEAWATER']
print(f"Final shape: {out.shape}")
print("Columns:", out.columns.tolist())
print(out[['SMP_ID', 'SMP_ID_PROVIDER', 'NUCLIDE', 'UNIT', 'LAB', 'AREA']].head(4).to_string())

# %%
#|eval: false
print("Final data summary (uppercase columns only):")
upper_cols = [c for c in out.columns if c.isupper()]
print(out[upper_cols].describe().to_string())

# %% [markdown]
# ## NetCDF encoder
#
# The encoder wraps the full pipeline and writes the standardised data to a NetCDF4 file. Global attributes are assembled via `GlobAttrsFeeder` with `BboxCB`, `DepthRangeCB`, `TimeRangeCB`, plus keywords and processing logs.
#
# We do not yet have an INIS entry for the JOIS datasets, so `INISCB` is commented out. The [IAEA INIS repository](https://www.iaea.org/resources/databases/inis) will be used for bibliographic metadata once the record is created. A placeholder line is included for future use.

# %%
#| exports
# NetCDF global attributes
JOIS_KEYWORDS = ['Beaufort Sea', 'JOIS', 'I-129', 'U-236', 'U-238', 'radionuclides', 'seawater', 'Arctic']

def get_attrs(tfm):
    "Retrieve global attributes for the JOIS handler."
    return GlobAttrsFeeder(tfm.dfs, cbs=[
        BboxCB(),
        DepthRangeCB(),
        TimeRangeCB(),
        #INISCB('XXXXXXXX'),  # TODO: add INIS record id when available
        KeyValuePairCB('keywords', ', '.join(JOIS_KEYWORDS)),
        KeyValuePairCB('publisher_postprocess_logs', ', '.join(tfm.logs)),
    ])()


# %%
#| exports
def encode(fname_out=None  # Output NetCDF file path; defaults to fname_out
            ):
    "Encode JOIS data to NetCDF4."
    fname_out = fname_out or globals().get('fname_out', 'JOIS_Beaufort_Sea.nc')
    dfs = load_data()
    tfm = Transformer(dfs, cbs=[
        RenameNucColsCB(), RenameColsCB(), ParseDateTimeCB(),
        MeltJOISCB(META_COLS, VAL_COLS),
        ConvertU238CB(),
        RemapCB(lut=NUCLIDE_LUT, col_remap='NUCLIDE', col_src='NUCLIDE'),
        RemapCB(lut=UNIT_LUT, col_remap='UNIT', col_src='UNIT'),
        RemapCB(lut={}, col_remap='LAB', col_src='NUCLIDE', default_val=345),
        RemapCB(lut={}, col_remap='AREA', col_src='NUCLIDE', default_val=4256),
        SanitizeLonLatCB(),
        EncodeTimeCB(),
        AddSampleIDCB(col_provider='SMP_ID_PROVIDER'),
    ])
    tfm()
    encoder = NetCDFEncoder(tfm.dfs, dest_fname=fname_out,
                            global_attrs=get_attrs(tfm))
    encoder.encode()



# %%
#|eval: false
# Encode to NetCDF
encode('../../_data/output/jois.nc')
print("JOIS NetCDF written.")
