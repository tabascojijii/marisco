# ══ cell[01] code[00] ══
#| default_exp handlers.fram_strait

# ══ cell[02] code[01] ══
#| export
from fastcore.all import *
import pandas as pd
import numpy as np
import io
import requests

from marisco.callbacks import (PerGroupCB, Callback, Transformer, EncodeTimeCB,
                                MeltWideNuclidesCB, SanitizeLonLatCB, RemapCB,
                                AddSampleIDCB)
from marisco.metadata import GlobAttrsFeeder, BboxCB, DepthRangeCB, TimeRangeCB, KeyValuePairCB
from marisco.encoders import NetCDFEncoder

# ══ cell[03] code[02] ══
#| export
CSV_URL   = 'https://zenodo.org/records/19387002/files/FramStrait_2020_2021_radionuclides.csv?download=1'
fname_out = 'FramStrait_2020_2021.nc'
ZENODO_ID = '19387002'

# ══ cell[07] code[03] ══
#| export
def load_data(
    url=None  # CSV download URL; defaults to CSV_URL
) -> dict:
    "Fetch Fram Strait radionuclide CSV from Zenodo and return a single SEAWATER DataFrame."
    url = url or CSV_URL
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return {'SEAWATER': pd.read_csv(io.BytesIO(r.content))}

# ══ cell[08] code[04] ══
#|eval: false
dfs = load_data()

# ══ cell[09] code[05] ══
#|eval: false
print(f"Shape: {dfs['SEAWATER'].shape}")
print("\nColumn types:\n", dfs['SEAWATER'].dtypes.to_string())
print(f"\nDate range: {dfs['SEAWATER']['Date'].dropna().iloc[0]} ... {dfs['SEAWATER']['Date'].dropna().iloc[-1]}")

# ══ cell[11] code[06] ══
#| export
class RenameColsCB(PerGroupCB):
    "Map Fram Strait CTD and sample columns to MARIS standard names."
    grps = ['SEAWATER']
    def each_grp(self, grp, df, tfm):
        df.rename(columns={
            'Latitude_degN': 'LAT', 'Longitude_degE': 'LON',
            'Depth_m': 'SMP_DEPTH', 'Temperature_degC_ctd': 'TEMP',
            'Salinity_ctd': 'SAL', 'Station': 'STATION',
            'Sample_ID': 'SMP_ID_PROVIDER',
        }, inplace=True)
        df['STATION'] = df['STATION'].astype(str)
        df['SMP_ID_PROVIDER'] = df['SMP_ID_PROVIDER'].astype(str)

# ══ cell[12] code[07] ══
# Verify RenameColsCB maps provider columns to MARIS names and casts string columns
        dfs_mock = {'SEAWATER': pd.DataFrame({
            'Latitude_degN': [79.5],
'Longitude_degE': [5.1],
'Depth_m': [100.0],
'Temperature_degC_ctd': [-1.2],
'Salinity_ctd': [34.8],
'Station': [301],
'Sample_ID': [42],
        })}
        tfm = Transformer(dfs_mock, cbs=[RenameColsCB()])
        tfm()
        df_out = tfm.dfs['SEAWATER']
        test_eq('LAT' in df_out.columns, True)
        test_eq('SMP_ID_PROVIDER' in df_out.columns, True)
        test_eq('Latitude_degN' not in df_out.columns, True)
        test_eq(df_out['STATION'].dtype, object)        # vlen str expected by NetCDF encoder
        test_eq(df_out['SMP_ID_PROVIDER'].dtype, object)
        print("RenameColsCB: provider columns mapped to MARIS names, string columns cast. ✓")

# ══ cell[13] code[08] ══
#|eval: false
tfm = Transformer(dfs, cbs=[RenameColsCB()])
tfm()
print("Renamed columns:", [c for c in tfm.dfs['SEAWATER'].columns if c.isupper()])

# ══ cell[15] code[09] ══
#| export
class ParseDateTimeCB(PerGroupCB):
    "Combine Fram Strait Date and Time columns into a single UTC-aware TIME column."
    grps = ['SEAWATER']
    def __init__(self, col_date='Date',  # Source date column (DD/MM/YYYY)
                 col_time='Time'):       # Source time column (HH:MM:SS)
        store_attr()
    def each_grp(self, grp, df, tfm):
        df['TIME'] = pd.to_datetime(
            df[self.col_date].astype(str) + ' ' + df[self.col_time].astype(str),
            format='%d/%m/%Y %H:%M:%S', utc=True)
        df.drop(columns=[self.col_date, self.col_time], inplace=True)

# ══ cell[16] code[10] ══
# Verify ParseDateTimeCB parses DD/MM/YYYY and produces UTC-aware TIME
dfs_mock = {'SEAWATER': pd.DataFrame({'Date': ['27/08/2020', '09/08/2021'], 'Time': ['14:30:00', '08:00:00']})}
tfm = Transformer(dfs_mock, cbs=[ParseDateTimeCB()])
tfm()
test_eq('TIME' in tfm.dfs['SEAWATER'].columns, True)
test_eq('Date' not in tfm.dfs['SEAWATER'].columns, True)
test_eq(str(tfm.dfs['SEAWATER']['TIME'].dt.tz), 'UTC')
test_eq(tfm.dfs['SEAWATER']['TIME'].iloc[0].month, 8)   # 27 Aug — not 8 Jul
test_eq(tfm.dfs['SEAWATER']['TIME'].iloc[0].day, 27)
print(f"ParseDateTimeCB: TIME = {tfm.dfs['SEAWATER']['TIME'].iloc[0]}, tz=UTC. ✓")

# ══ cell[17] code[11] ══
#|eval: false
tfm = Transformer(dfs, cbs=[RenameColsCB(), ParseDateTimeCB()])
tfm()
print("First 3 TIME values:\n", tfm.dfs['SEAWATER']['TIME'].head(3).to_string())

# ══ cell[19] code[12] ══
#| export
# Columns kept as identifiers during the wide-to-long reshape
META_COLS = ['Cruise', 'STATION', 'SMP_ID_PROVIDER', 'LAT', 'LON',
             'TIME', 'SMP_DEPTH', 'TEMP', 'SAL']

# Hand-written spec: each entry maps one value column to its (unc, nuclide, unit, lab).
# NPI uncertainty columns follow unc_{col}; ETH follows ETH_unc_{nuc} — both captured here explicitly.
# U238_ppb is ingested directly with unit='at_ppb'; ConvertU238CB converts to at_kg post-melt.
MELT_SPEC = [
    {'val': 'I129_at_l',      'unc': 'unc_I129_at_l',      'nuclide': 'I129', 'unit': 'at_l',  'lab': 'NPI'},
    {'val': 'I129_at_kg',     'unc': 'unc_I129_at_kg',     'nuclide': 'I129', 'unit': 'at_kg', 'lab': 'NPI'},
    {'val': 'U236_at_l',      'unc': 'unc_U236_at_l',      'nuclide': 'U236', 'unit': 'at_l',  'lab': 'NPI'},
    {'val': 'U236_at_kg',     'unc': 'unc_U236_at_kg',     'nuclide': 'U236', 'unit': 'at_kg', 'lab': 'NPI'},
    {'val': 'U238_ppb',       'unc': 'unc_U238_ppb',       'nuclide': 'U238', 'unit': 'at_ppb','lab': 'NPI'},
    {'val': 'ETH_U236_at_l',  'unc': 'ETH_unc_U236_at_l',  'nuclide': 'U236', 'unit': 'at_l',  'lab': 'ETH'},
    {'val': 'ETH_U236_at_kg', 'unc': 'ETH_unc_U236_at_kg', 'nuclide': 'U236', 'unit': 'at_kg', 'lab': 'ETH'},
]

# ══ cell[20] code[13] ══
# Verify MeltWideNuclidesCB produces correct NUCLIDE, UNIT, VALUE, UNC, LAB columns
dfs_mock = {'SEAWATER': pd.DataFrame({
    'Cruise': ['2020'], 'STATION': [301], 'SMP_ID_PROVIDER': [42],
    'I129_at_l': [1.74e9], 'unc_I129_at_l': [5.2e7],
    'U238_ppb':  [3.1],    'unc_U238_ppb':  [0.2],
    'ETH_U236_at_l': [1.3e7], 'ETH_unc_U236_at_l': [4.5e5],
    'I129_at_kg': [np.nan], 'unc_I129_at_kg': [np.nan],
    'U236_at_l': [np.nan], 'unc_U236_at_l': [np.nan],
    'U236_at_kg': [np.nan], 'unc_U236_at_kg': [np.nan],
    'ETH_U236_at_kg': [np.nan], 'ETH_unc_U236_at_kg': [np.nan],
})}
MOCK_SPEC = [
    {'val': 'I129_at_l', 'unc': 'unc_I129_at_l', 'nuclide': 'I129', 'unit': 'at_l', 'lab': 'NPI'},
    {'val': 'U238_ppb', 'unc': 'unc_U238_ppb', 'nuclide': 'U238', 'unit': 'at_ppb', 'lab': 'NPI'},
    {'val': 'ETH_U236_at_l', 'unc': 'ETH_unc_U236_at_l', 'nuclide': 'U236', 'unit': 'at_l', 'lab': 'ETH'},
    {'val': 'I129_at_kg', 'unc': 'unc_I129_at_kg', 'nuclide': 'I129', 'unit': 'at_kg', 'lab': 'NPI'},
]
tfm = Transformer(dfs_mock, cbs=[MeltWideNuclidesCB(spec=MOCK_SPEC)])
tfm()
out = tfm.dfs['SEAWATER']
# Only 3 rows: I129_at_l, U238_ppb, ETH_U236_at_l (I129_at_kg is NaN, dropped)
test_eq(len(out), 3)
test_eq(sorted(out['NUCLIDE'].tolist()), ['I129', 'U236', 'U238'])
npi_rows = out[out['LAB'] == 'NPI']
eth_rows = out[out['LAB'] == 'ETH']
test_eq(len(eth_rows), 1)
test_eq(eth_rows['UNIT'].iloc[0], 'at_l')
test_eq(eth_rows['VALUE'].iloc[0], 1.3e7)
test_eq(eth_rows['UNC'].iloc[0], 4.5e5)
print("MeltWideNuclidesCB: NPI/ETH rows correctly split, ETH_unc_ col resolved as data. \u2713")

# ══ cell[21] code[14] ══
#|eval: false
tfm = Transformer(dfs, cbs=[RenameColsCB(), ParseDateTimeCB(),
                             MeltWideNuclidesCB(spec=MELT_SPEC)])
tfm()
out = tfm.dfs['SEAWATER']
print(f"Shape after melt: {out.shape}")
print("NUCLIDE values:", out['NUCLIDE'].unique())
print("UNIT values:",    out['UNIT'].unique())
print("LAB values:",     out['LAB'].unique())
print(out[['NUCLIDE', 'UNIT', 'LAB', 'VALUE', 'UNC']].head(6).to_string())

# ══ cell[23] code[15] ══
#| export
# Convert U-238 from ppb to atoms/kg: ppb * 1e-9 * (1/238.05) * 6.02214076e23
U238_PPB_TO_AT_KG = 2.529_697e12

# ══ cell[24] code[16] ══
#| export
class ConvertU238CB(PerGroupCB):
    "Convert U-238 VALUE and UNC from ppb to atoms/kg."
    grps = ['SEAWATER']
    def each_grp(self, grp, df, tfm):
        m = df['NUCLIDE'] == 'U238'
        df.loc[m, 'VALUE'] *= U238_PPB_TO_AT_KG
        df.loc[m, 'UNC']   *= U238_PPB_TO_AT_KG
        df.loc[m, 'UNIT']   = 'at_kg'

# ══ cell[25] code[17] ══
# Verify ConvertU238CB scales U-238 only; I-129 and U-236 unchanged
dfs_mock = {'SEAWATER': pd.DataFrame({
    'NUCLIDE': ['I129', 'U238', 'U236'],
    'UNIT':    ['at_l', 'at_ppb', 'at_l'],
    'VALUE':   [1.74e9, 3.1, 1.3e7],
    'UNC':     [5.2e7,  0.2, 4.5e5],
})}
tfm = Transformer(dfs_mock, cbs=[ConvertU238CB()])
tfm()
out = tfm.dfs['SEAWATER']
test_eq(out.loc[out['NUCLIDE']=='U238', 'VALUE'].iloc[0], 3.1 * U238_PPB_TO_AT_KG)
test_eq(out.loc[out['NUCLIDE']=='U238', 'UNC'].iloc[0],   0.2 * U238_PPB_TO_AT_KG)
test_eq(out.loc[out['NUCLIDE']=='U238', 'UNIT'].iloc[0],  'at_kg')
test_eq(out.loc[out['NUCLIDE']=='I129', 'VALUE'].iloc[0], 1.74e9)  # unchanged
test_eq(out.loc[out['NUCLIDE']=='U236', 'UNIT'].iloc[0],  'at_l')  # unchanged
print("ConvertU238CB: I-129 and U-236 unchanged, U-238 scaled to atoms/kg, UNIT updated. ✓")

# ══ cell[26] code[18] ══
#|eval: false
tfm = Transformer(dfs, cbs=[RenameColsCB(), ParseDateTimeCB(),
                             MeltWideNuclidesCB(spec=MELT_SPEC), ConvertU238CB()])
tfm()
out = tfm.dfs['SEAWATER']
u238 = out[out['NUCLIDE']=='U238']
print(f"U-238 rows: {len(u238)}, mean VALUE = {u238['VALUE'].mean():.3e} atoms/kg")

# ══ cell[28] code[19] ══
#| export
# MARIS nuclide IDs confirmed via dbo_nuclide.xlsx (nc_name column)
NUCLIDE_LUT = {'I129': 28, 'U236': 108, 'U238': 64}

# MARIS unit IDs confirmed via dbo_unit.xlsx (unit_sanitized column)
UNIT_LUT = {'at_kg': 9, 'at_l': 12}

LAB_NPI     = 281   # Norwegian Polar Institute — confirmed via dbo_lab.xlsx
LAB_ETH_LIP = 345   # ETH Zurich / LIP (Casacuberta group) — confirmed via JOIS handler
LAB_LUT     = {'NPI': LAB_NPI, 'ETH': LAB_ETH_LIP}

AREA_GREENLAND_SEA = 2356  # confirmed via dbo_area.xlsx (displayName: 'Greenland Sea')

# ══ cell[29] code[20] ══
# Verify all RemapCB steps: NUCLIDE, UNIT, LAB (NPI and ETH), AREA
dfs_mock = {'SEAWATER': pd.DataFrame({
    'NUCLIDE': ['I129', 'U236', 'U238', 'U236'],
    'UNIT':    ['at_l', 'at_l', 'at_kg', 'at_kg'],
    'LAB':     ['NPI',  'NPI',  'NPI',   'ETH'],
    'VALUE':   [1.0, 2.0, 3.0, 4.0],
})}
tfm = Transformer(dfs_mock, cbs=[
    RemapCB(lut=NUCLIDE_LUT, col_remap='NUCLIDE', col_src='NUCLIDE'),
    RemapCB(lut=UNIT_LUT,    col_remap='UNIT',    col_src='UNIT'),
    RemapCB(lut=LAB_LUT,     col_remap='LAB',     col_src='LAB'),
    RemapCB(lut={}, col_remap='AREA', col_src='NUCLIDE', default_val=AREA_GREENLAND_SEA),
])
tfm()
out = tfm.dfs['SEAWATER']
test_eq(out['NUCLIDE'].tolist(), [28, 108, 64, 108])
test_eq(out['UNIT'].tolist(),    [12, 12,   9,  9])
test_eq(out['LAB'].tolist(),     [LAB_NPI, LAB_NPI, LAB_NPI, LAB_ETH_LIP])
test_eq(out['AREA'].tolist(),    [AREA_GREENLAND_SEA] * 4)
print("RemapCB: NUCLIDE, UNIT, LAB (NPI/ETH), AREA all mapped to MARIS IDs. ✓")

# ══ cell[30] code[21] ══
#|eval: false
tfm = Transformer(dfs, cbs=[
    RenameColsCB(), ParseDateTimeCB(),
    MeltWideNuclidesCB(spec=MELT_SPEC), ConvertU238CB(),
    RemapCB(lut=NUCLIDE_LUT, col_remap='NUCLIDE', col_src='NUCLIDE'),
    RemapCB(lut=UNIT_LUT,    col_remap='UNIT',    col_src='UNIT'),
    RemapCB(lut=LAB_LUT,     col_remap='LAB',     col_src='LAB'),
    RemapCB(lut={}, col_remap='AREA', col_src='NUCLIDE', default_val=AREA_GREENLAND_SEA),
])
tfm()
out = tfm.dfs['SEAWATER']
print(out[['NUCLIDE', 'UNIT', 'LAB', 'AREA']].drop_duplicates().to_string())

# ══ cell[32] code[22] ══
#|eval: false
tfm = Transformer(dfs, cbs=[
    RenameColsCB(), ParseDateTimeCB(),
    MeltWideNuclidesCB(spec=MELT_SPEC), ConvertU238CB(),
    RemapCB(lut=NUCLIDE_LUT, col_remap='NUCLIDE', col_src='NUCLIDE'),
    RemapCB(lut=UNIT_LUT,    col_remap='UNIT',    col_src='UNIT'),
    RemapCB(lut=LAB_LUT,     col_remap='LAB',     col_src='LAB'),
    RemapCB(lut={}, col_remap='AREA', col_src='NUCLIDE', default_val=AREA_GREENLAND_SEA),
    SanitizeLonLatCB(),
    EncodeTimeCB(),
    AddSampleIDCB(col_provider='SMP_ID_PROVIDER'),
])
tfm()
out = tfm.dfs['SEAWATER']
print(f"Final shape: {out.shape}")
print("Columns:", out.columns.tolist())
print(out[['SMP_ID', 'SMP_ID_PROVIDER', 'NUCLIDE', 'UNIT', 'LAB', 'AREA']].head(6).to_string())

# ══ cell[33] code[23] ══
#|eval: false
upper_cols = [c for c in out.columns if c.isupper()]
print("Final data summary (MARIS uppercase columns):")
print(out[upper_cols].describe().to_string())

# ══ cell[35] code[24] ══
#| export
FRAM_KEYWORDS = ['Fram Strait', 'I-129', 'U-236', 'U-238', 'radionuclides',
                 'seawater', 'Arctic Ocean', 'Norwegian Polar Institute', 'ETH Zurich']

def get_attrs(tfm):
    "Retrieve global attributes for the Fram Strait handler."
    return GlobAttrsFeeder(tfm.dfs, cbs=[
        BboxCB(),
        DepthRangeCB(),
        TimeRangeCB(),
        #InisCB('XXXXXXXX'),  # TODO: add INIS record id when available
        KeyValuePairCB('keywords', ', '.join(FRAM_KEYWORDS)),
        KeyValuePairCB('publisher_postprocess_logs', ', '.join(tfm.logs)),
    ])()

# ══ cell[36] code[25] ══
#| export
def encode(
    fname_out=None  # Output NetCDF file path; defaults to fname_out
):
    "Encode Fram Strait 2020/2021 data to NetCDF4."
    fname_out = fname_out or globals().get('fname_out', 'FramStrait_2020_2021.nc')
    dfs = load_data()
    tfm = Transformer(dfs, cbs=[
        RenameColsCB(), ParseDateTimeCB(),
        MeltWideNuclidesCB(spec=MELT_SPEC), ConvertU238CB(),
        RemapCB(lut=NUCLIDE_LUT, col_remap='NUCLIDE', col_src='NUCLIDE'),
        RemapCB(lut=UNIT_LUT,    col_remap='UNIT',    col_src='UNIT'),
        RemapCB(lut=LAB_LUT,     col_remap='LAB',     col_src='LAB'),
        RemapCB(lut={}, col_remap='AREA', col_src='NUCLIDE', default_val=AREA_GREENLAND_SEA),
        SanitizeLonLatCB(),
        EncodeTimeCB(),
        AddSampleIDCB(col_provider='SMP_ID_PROVIDER'),
    ])
    tfm()
    encoder = NetCDFEncoder(tfm.dfs, dest_fname=fname_out, global_attrs=get_attrs(tfm))
    encoder.encode()

# ══ cell[37] code[26] ══
#|eval: false
encode('../../_data/output/fram_strait.nc')
print("Fram Strait NetCDF written.")
