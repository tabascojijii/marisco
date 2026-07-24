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
#| default_exp configs

# %% [markdown]
# # Configs
# > Central constants and utilities for MARIS NetCDF encoding: variable and group mappings, lookup-table loading, enumeration types, and path helpers.
#

# %%
#| export
from pathlib import Path
import os
import re
from typing import Any, Dict, Union
import pandas as pd
from fastcore.all import *
from netCDF4 import Dataset
from importlib.resources import files as _pkg_files

# %%
#| eval: false
from nbdev.showdoc import show_doc

# %%
#| exports
AVOGADRO = 6.02214076e23

# %%
#| exports
NA = 'Not available'

# %%

# %%
#| exports
NC_DIM = 'id'

# %% [markdown]
# `NC_CSV` maps handler column names (ALLCAPS keys) to their output names in both NetCDF and CSV formats. Each entry is `KEY: (nc_name, csv_name)`. A `None` value means that key isn't used in that format: if it lacks an NC name, it's CSV-only; if it lacks a CSV name, it's NC-only.
#
# `NC_VARS` and `CSV_VARS` are derived automatically from this single source.
#

# %%
#| exports
NC_CSV = {
    'AREA':            ('area',          'area'),
    'BIO_GROUP':       ('bio_group',     None),
    'BODY_PART':       ('body_part',     'bodypar_id'),
    'BOTTOM':          ('bottom',        'slicedown'),
    'COUNT_MET':       ('count_met',     'counmet_id'),
    'DL':              ('dl',            'detection'),
    'DLV':             ('dlv',           'detection_lim'),
    'DRYWT':           ('drywt',         'drywt'),
    'FILT':            ('filt',          'filtered'),
    'LAB':             ('lab',           'lab_id'),
    'LAT':             ('lat',           'latitude'),
    'LON':             ('lon',           'longitude'),
    'NUCLIDE':         ('nuclide',       'nuclide_id'),
    'PERCENTWT':       ('percentwt',     'percentwt'),
    'PH':              ('ph',            None),
    'PREP_MET':        ('prep_met',      'prepmet_id'),
    'PROFILE_ID':      ('profile_id',    'profile_id'),
    'REF_ID':          (None,            'ref_id'),
    'SAL':             ('sal',           'salinity'),
    'SAMP_MET':        ('samp_met',      'sampmet_id'),
    'SAMPLE_TYPE':     (None,            'samptype_id'),
    'SED_TYPE':        ('sed_type',      'sedtype_id'),
    'SMP_DEPTH':       ('smp_depth',     'sampdepth'),
    'SMP_ID':          ('id',            None),
    'SMP_ID_PROVIDER': ('id_provider',   'samplabcode'),
    'SPECIES':         ('species',       'species_id'),
    'STATION':         ('station',       'station'),
    'TAXONDB':         (None,            'taxondb'),
    'TAXONDBID':       (None,            'taxondb_id'),
    'TAXONDBURL':      (None,            'taxondb_url'),
    'TAXONNAME':       (None,            'taxonname'),
    'TAXONRANK':       (None,            'taxonrank'),
    'TAXONREPNAME':    (None,            'taxonrepname'),
    'TEMP':            ('temp',          'temperatur'),
    'TIME':            ('time',          'begperiod'),
    'TOP':             ('top',           'sliceup'),
    'TOT_DEPTH':       ('tot_depth',     'totdepth'),
    'UNC':             ('unc',           'uncertaint'),
    'UNIT':            ('unit',          'unit_id'),
    'VALUE':           ('value',         'activity'),
    'VOL':             ('vol',           'volume'),
    'WETWT':           ('wetwt',         'wetwt'),
}

NC_VARS  = {k: v[0] for k,v in NC_CSV.items() if v[0] is not None}
CSV_VARS = {k: v[1] for k,v in NC_CSV.items() if v[1] is not None}

# %% [markdown]
# **TODO**: Fields documented in the OpenRefine CSV format but not yet integrated into the pipeline:
# - `SAMPLE_LAB_CODE`: sample lab code (relationship with `SMP_ID`/`SMP_ID_PROVIDER` TBD)
# - `SED_REPNAME`: sediment replicate name
# - `MEASURE_NOTE`: measurement notes
# - `REFERENCE_NOTE`: reference notes
# - `SAMPLE_NOTE`: sample notes
# - `PH`: documented in `NC_VARS` but missing from `field-definition.ipynb`
#
# Not yet in `NC_CSV`: need to decide if/how they map to NC variables before adding.

# %%
#| exports
NC_GROUPS = {'BIOTA': 'biota',
             'SEAWATER': 'seawater',
             'SEDIMENT': 'sediment',
             'SUSPENDED_MATTER': 'suspended_matter'}

# %% [markdown]
# **Two parallel group mappings:** `NC_GROUPS` maps each sample-type group to its lowercase NetCDF group name (used when writing to the file). `SMP_TYPE_LUT` maps the same groups to the MARIS database integer IDs (used when encoding `samptype_id` in CSV export). Both are needed because the NetCDF schema and the legacy CSV schema identify groups differently.

# %%
#| exports
SMP_TYPE_LUT = {
    'SEAWATER': 1,
    'BIOTA': 2,
    'SEDIMENT': 3,
    'SUSPENDED_MATTER': 4
}

# %% [markdown]
# **`NC_DTYPES`** defines every variable that uses a NetCDF enumeration type. Each entry maps a handler column key to `{name, fname, key, value}`:
# - `name` — the NetCDF4 enumeration type name (e.g. `'nuclide_t'`)
# - `fname` — the Excel file bundled in `marisco/files/lut/`
# - `key` — the Excel column used as dictionary keys
# - `value` — the Excel column used as integer IDs

# %%
#| exports
NC_DTYPES = {
    'AREA': {
        'name': 'area_t', 
        'fname': 'dbo_area.xlsx',
        'key': 'displayName', 
        'value':'areaId'
    },
    'BIO_GROUP': {
        'name': 'bio_group_t', 
        'fname': 'dbo_biogroup.xlsx',
        'key': 'biogroup', 
        'value':'biogroup_id'
    },
    'BODY_PART': {
        'name': 'body_part_t', 
        'fname': 'dbo_bodypar.xlsx',
        'key': 'bodypar', 
        'value':'bodypar_id'
    },
    'COUNT_MET': {
        'name': 'count_met_t', 
        'fname': 'dbo_counmet.xlsx',
        'key': 'counmet',
        'value':'counmet_id'
    },
    'DL': {
        'name': 'dl_t', 
        'fname': 'dbo_detectlimit.xlsx',
        'key': 'name_sanitized', 
        'value':'id'
    },
    'FILT': {
        'name': 'filt_t', 
        'fname': 'dbo_filtered.xlsx',
        'key': 'name',
        'value':'id'
    },
    'NUCLIDE': {
        'name': 'nuclide_t', 
        'fname': 'dbo_nuclide.xlsx',
        'key': 'nc_name',
        'value':'nuclide_id'
    },
    'PREP_MET': {
        'name': 'prep_met_t', 
        'fname': 'dbo_prepmet.xlsx', 
        'key': 'prepmet',
        'value':'prepmet_id'
    },
    'SAMP_MET': {
        'name': 'samp_met_t', 
        'fname': 'dbo_sampmet.xlsx', 
        'key': 'sampmet',
        'value':'sampmet_id'
    },
    'SED_TYPE': {
        'name': 'sed_type_t', 
        'fname': 'dbo_sedtype.xlsx', 
        'key': 'sedtype', 
        'value':'sedtype_id'
    },
    'SPECIES': {
        'name': 'species_t', 
        # 'fname': 'dbo_species_cleaned.xlsx',
        'fname': 'dbo_species_2024_11_19.xlsx',
        'key': 'species', 
        'value':'species_id'
    },
    'UNIT': {
        'name': 'unit_t', 
        'fname': 'dbo_unit.xlsx', 
        'key': 'unit_sanitized', 
        'value':'unit_id'
    },
    'LAB': {
        'name': 'lab_t', 
        #'fname': 'dbo_lab.xlsx', 
        'fname': 'dbo_lab_cleaned.xlsx', 
        'key': 'lab', 
        'value':'lab_id'
    }
}

# %%
#| exports
CSV_DTYPES = {
    'AREA': {'state': 'decoded'},
    'NUCLIDE': {'state': 'encoded'},  # encoded nuclide_id
    'UNIT': {'state': 'encoded'},  # encoded unit_id
    'DL': {'state': 'decoded'},
    'FILT': {'state': 'decoded'},
    'COUNT_MET': {'state': 'encoded'},  # encoded counmet_id
    'SAMP_MET': {'state': 'encoded'},  # encoded sampmet_id
    'PREP_MET': {'state': 'encoded'},  # encoded prepmet_id
    'SPECIES': {'state': 'encoded'},  # encoded species_id
    'BODY_PART': {'state': 'encoded'},  # encoded bodypar_id
    'SED_TYPE': {'state': 'encoded'},  # encoded sedtype_id
    'LAB': {'state': 'encoded'},  # encoded lab_id
}

# %% [markdown]
# **`CSV_DTYPES`** controls whether a column is written as human-readable names (`'decoded'`) or as integer IDs (`'encoded'`) in CSV export. For example, `'AREA'` uses `'decoded'` so the CSV contains area names, while `'NUCLIDE'` uses `'encoded'` so it contains `nuclide_id` values matching the MARIS database.

# %%
#| exports
ZOTERO_LIB_ID = '2432820'

# %% [markdown]
# ## NetCDF global attributes
#
# The set of valid global attribute names, extracted from the template CDL. Any key written to the NetCDF global attrs dict during encoding must belong to this set; otherwise a misspelled name would be silently injected into the output file.

# %%
#| exports
NC_GLOBAL_ATTRS = {
    'id', 'title', 'summary', 'keywords', 'history',
    'keywords_vocabulary', 'keywords_vocabulary_url',
    'record', 'featureType', 'cdm_data_type', 'Conventions',
    'publisher_name', 'publisher_email', 'publisher_url', 'publisher_institution',
    'creator_name', 'institution', 'metadata_link', 'creator_email', 'creator_url',
    'references', 'license', 'comment',
    'geospatial_lat_min', 'geospatial_lat_max', 'geospatial_lon_min', 'geospatial_lon_max',
    'geospatial_vertical_min', 'geospatial_vertical_max', 'geospatial_bounds', 'geospatial_bounds_crs',
    'time_coverage_start', 'time_coverage_end', 'local_time_zone',
    'date_created', 'date_modified', 'publisher_postprocess_logs',
}


# %% [markdown]
# ## Path helpers

# %%
#| export
def lut_path() -> Path:              # Path to LUTs directory
    "Return the path to the lookup tables directory."
    return _pkg_files('marisco') / 'files/lut'


# %%
#| export
def lut_fname(key: str               # NC_DTYPES key, e.g. 'SPECIES', 'UNIT', 'DL'
              ) -> Path:             # Full path to the lookup table Excel file
    "Return the full path to a lookup table file by its NC_DTYPES key."
    return lut_path() / NC_DTYPES[key]['fname']


# %%
#| export
def nc_tpl_path() -> Path:           # Path to MARIS NetCDF template
    "Return the path to the MARIS NetCDF template file."
    return _pkg_files('marisco') / 'files/nc/maris-template.nc'


# %%
_pkg_files('marisco')

# %%
nc_tpl_path()


# %%
#| export
def cache_path() -> Path: # Path to cache directory
    "Return the path to the cache directory, creating it if needed."
    p = Path.home() / '.cache' / 'marisco'
    p.mkdir(parents=True, exist_ok=True)
    return p


# %% [markdown]
# ## Utilities function

# %%
#| exports
NETCDF_TO_PYTHON_TYPE = {
    'u8': int,
    'f4': float
    }


# %%
#| export
def get_time_units() -> str:
    "Get the units attribute of the time variable from a NetCDF file."
    with Dataset(nc_tpl_path(), 'r') as nc:
        for group in nc.groups.values():
            if 'time' in group.variables:
                return group.variables['time'].units
    raise ValueError("Time variable not found in NetCDF file")


# %% [markdown]
# Usage example:

# %%
#| eval: false
time_units = get_time_units(); time_units


# %% [markdown]
# ## Enumeration types
#
# Enumeration types are used to avoid using strings as NetCDF4 variable values. Instead, enumeration types (lookup tables) such as `{'Crustaceans': 2, 'Echinoderms': 3, ...}` are prepended to the NetCDF file template and associated ids (integers) are used as values.

# %%
#| export
def sanitize(
    s: str|float # String or float to sanitize
    ) -> str|float:  # Sanitized string or original float
    """
    Sanitize dictionary key to comply with NetCDF enumeration type:
    
    - Remove `(`, `)`, `.`, `/`, `-`
    - Strip the string
    - Return original value if it's not a string (e.g., NaN)
    """
    if isinstance(s, str):
        s = re.sub(r'[().]', '', s)
        return re.sub(r'[/-]', ' ', s).strip()
    elif pd.isna(s):  # This covers np.nan, None, and pandas NaT
        return s
    else:
        return str(s).strip()


# %% [markdown]
# For example:

# %%
test_eq(sanitize('key (sanitized)'), 'key sanitized')
test_eq(sanitize('key san.itized'), 'key sanitized')
test_eq(sanitize('key-sanitized'), 'key sanitized')
test_eq(sanitize('key/sanitized'), 'key sanitized')


# %% [markdown]
# NetCDF4 enumeration type seems to not accept keys containing non alphanumeric characters like parentheses, dots, slash, ... As a result, MARIS lookup table needs to be sanitized.

# %%
#| export
def try_int(x:Any         # Value to attempt integer conversion on
            )->int|Any:   # Integer if successful, or the original value
    "Try to convert `x` to an integer."
    try:
        return int(x)
    except (ValueError, TypeError):
        return x


# %% [markdown]
# **Sanitised keys are then coerced to integers where possible** — some lookup-table keys (e.g. area codes) come as numeric strings like `"1"`, which NetCDF4 enums interpret more reliably as integers. The `try_int` helper handles this conversion without breaking on genuinely non-numeric string keys.

# %%
#| export
# too long for our coding standard - NEED REFACTORING
def get_lut(
    key_or_fname: str, # NC_DTYPES key (e.g. 'NUCLIDE') or Excel filename
    key: Optional[str]=None, # Column for dict keys; inferred from NC_DTYPES if applicable
    value: Optional[str]=None, # Column for dict values; inferred from NC_DTYPES if applicable
    src_dir: Optional[str]=None, # Directory containing lookup tables (default: lut_path())
    do_sanitize: bool=True, # Sanitization required?
    reverse: bool=False, # Reverse lookup table (value, key)
    check_duplicates: bool=False, # Check for duplicates in lookup table
    as_df: bool=False # Return DataFrame instead of dict (for fuzzy_merge etc.)
    ) -> Union[Dict[str, int], pd.DataFrame]: # MARIS lookup table (key, value) or (key, value) DataFrame
    "Convert MARIS db lookup table excel file to dictionary or DataFrame."
    if src_dir is None: src_dir = lut_path()
    
    # Resolve from NC_DTYPES if the first arg is a known key
    if key_or_fname in NC_DTYPES:
        cfg = NC_DTYPES[key_or_fname]
        fname = cfg['fname']
        if key is None: key = cfg['key']
        if value is None: value = cfg['value']
    else:
        fname = key_or_fname
    
    fname = Path(src_dir) / fname
    df = pd.read_excel(fname, usecols=[key, value]).dropna(subset=value)
    
    if check_duplicates:
        duplicates = df[key][df[key].duplicated()].tolist()
        if duplicates: print(f"Warning: {fname.name}: found duplicate keys: {duplicates}")
        
    df[value] = df[value].astype('int')
    if as_df: return df
    
    df = df.set_index(key)
    lut = df[value].to_dict()
    if do_sanitize: lut = {sanitize(k): v for k, v in lut.items()}
    lut = {try_int(k): try_int(v) for k, v in lut.items()}    
    return {v: k for k, v in lut.items()} if reverse else lut


# %% [markdown]
# For example:

# %%
#|eval: false
get_lut('BIO_GROUP', reverse=False)


# %%
#| export
class Enums():
    "Hold and filter MARIS NetCDF enumeration types loaded from lookup tables."
    def __init__(self,
                 lut_src_dir: str,                         # Directory containing lookup tables
                 dtypes: Dict[str, Dict[str, str]] = NC_DTYPES  # Dict keyed by NC_DTYPES key, each is {name, fname, key, value}
                ):
        store_attr()
        self.types = self.lookup()


# %%
#| export
@patch
def lookup(self: Enums) -> Dict[str, Dict[str, int]]:
    "Load all enumeration types defined in `NC_DTYPES` as `{name: id}` dictionaries, available via `self.types[var_name]`."
    types = {}
    for var_name in self.dtypes:
        lut = get_lut(var_name, src_dir=self.lut_src_dir)
        types[var_name] = lut
    return types


# %%
#| eval: false
show_doc(Enums.lookup)


# %%
#| export
@patch
def filter(self: Enums,
           var_name: str,      # NC_DTYPES key for the enumeration, e.g. 'SPECIES'
           values: list        # Enumeration IDs to keep
          ) -> Dict[str, int]:
    "Return a subset of an enumeration keeping only entries whose id is in `values`."
    return {name: id for name, id in self.types[var_name].items() if id in values}


# %%
#| eval: false
show_doc(Enums.filter)

# %%
#|eval: false
lut_src_dir_test = lut_path()
enums = Enums(lut_src_dir=lut_src_dir_test)

# %%
#|eval: false
# Keep only 'Detected value' (id=1) and 'Not detected' (id=3) from the DL enumeration
enums.filter('DL', values=[1, 3])

# %%
#|eval: false
enums.types['DL']
