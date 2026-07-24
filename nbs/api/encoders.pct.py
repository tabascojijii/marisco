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

# %%
#| default_exp encoders

# %% [markdown]
# # Encoders
# > Handler-curated DataFrames → MARIS NetCDF

# %%
#| hide
# %load_ext autoreload
# %autoreload 2

# %%
#| export
import netCDF4
from netCDF4 import Dataset
import pandas as pd
from typing import Dict, Callable
import numpy as np
from fastcore.all import *
from marisco.configs import NC_DTYPES, NC_VARS, NC_DIM, NC_GROUPS, lut_path, Enums, nc_tpl_path

# %% [markdown]
# The test data below simulates what a handler might produce: two DataFrames (`SEAWATER` and `BIOTA`) with a handful of rows each, covering the key column types: identifiers, coordinates, timestamps, measurements, and controlled-vocabulary fields like `AREA`, `NUCLIDE`, and `SPECIES`.
#

# %%
import tempfile, os
from fastcore.test import test_eq

df_seawater = pd.DataFrame({
    'SMP_ID': [0, 1, 2],
    'SMP_ID_PROVIDER': ['1', '2', '3'],
    'LON': [141.0, 142.0, 143.0],
    'LAT': [37.3, 38.3, 39.3],
    'TIME': [1234, 1235, 1236],
    'NUCLIDE': [1, 2, 3],
    'VALUE': [0.1, 1.1, 2.1],
    'AREA': [2374, 2379, 2401],
    'STATION': ['A0', 'A11', 'B234']
    })

df_biota = pd.DataFrame({
    'SMP_ID': [0, 1, 2, 3],
    'SMP_ID_PROVIDER': ['ID1', 'ID2', 'ID3', 'ID4'],
    'LON': [141.0, 142.0, 143.0, 144.0],
    'LAT': [37.3, 38.3, 39.3, 40.3],
    'TIME': [1234, 1235, 1236, 1237],
    'NUCLIDE': [1, 2, 3, 3],
    'VALUE': [0.1, 1.1, 2.1, 3.1],
    'SPECIES': [1, 2, 3, 3]
    })

dfs = {'SEAWATER': df_seawater, 'BIOTA': df_biota}
attrs = {'id': '123', 'title': 'Test title', 'summary': 'Summary test'}
dest = tempfile.mktemp(suffix='.nc')


# %% [markdown]
# The `NetCDFEncoder` class is the workhorse of this module: it takes a dict of handler-curated DataFrames and writes them out as a single self-contained NetCDF4 file following the MARIS template.

# %%
#| export
class NetCDFEncoder:
    "MARIS NetCDF encoder: transforms handler-curated DataFrames into a self-contained NetCDF4 file."
    def __init__(self, 
                 dfs: Dict[str, pd.DataFrame], # {NC_GROUPS key → DataFrame}, e.g. {'SEAWATER': df_sw, 'BIOTA': df_bio}
                 dest_fname: str, # Name of output file to produce
                 global_attrs: Dict[str, str], # NetCDF global attributes (id, title, summary, keywords, ...)
                 fn_src_fname: Callable=nc_tpl_path, # Callable returning path to the MARIS NetCDF template
                 verbose: bool=False, # Print currently written NetCDF group and variable names
                 ):
        store_attr()
        self.src_fname = fn_src_fname()
        self.enum_dtypes = {}
        self.nc_to_cols = {v:k for k,v in NC_VARS.items()}


# %%
#| export
@patch 
def copy_global_attrs(self:NetCDFEncoder):
    "Update NetCDF template global attributes as specified by `global_attrs` argument."
    self.dest.setncatts(self.src.__dict__)
    for k, v in self.global_attrs.items(): self.dest.setncattr(k, v)


# %%
#| export
@patch
def copy_dims(
    self:NetCDFEncoder,
    grp_dest,  # Destination NetCDF group
    ):
    "Copy dimensions from template into a group."
    src_dim = self.src.groups[grp_dest.name].dimensions
    for name, dim in src_dim.items():
        grp_dest.createDimension(name, (len(dim) if not dim.isunlimited() else None))


# %%
#| export
@patch
def process_grps(self:NetCDFEncoder):
    "Iterate all groups in `dfs` and encode each one."
    for grp_name, df in self.dfs.items():
        self.process_grp(NC_GROUPS[grp_name], df)


# %%
#| export
@patch
def process_grp(
    self:NetCDFEncoder,
    grp_name:str,  # NC_GROUPS key, e.g. `'SEAWATER'`
    df:pd.DataFrame,  # Measurements for this group
    ):
    "Create a destination group, copy dimensions, then create and populate variables from the DataFrame."
    grp_dest = self.dest.createGroup(grp_name)
    self.copy_dims(grp_dest)
    self.copy_vars(grp_name, df, grp_dest)


# %%
#| export
@patch
def copy_vars(
    self:NetCDFEncoder,
    grp_name:str,  # NC_GROUPS key
    df:pd.DataFrame,  # Measurements for this group
    grp_dest,  # Destination NetCDF group
    ):
    "Copy variables from template into group, filling from df."
    cols = [NC_VARS[col] for col in df.columns if col in NC_VARS]
    for var_name, var_src in self.src.groups[grp_name].variables.items():
        if var_name in cols: self.copy_var(var_name, var_src, df, grp_dest)


# %%
#| export
@patch
def copy_var(
    self:NetCDFEncoder,
    var_name:str,  # NetCDF variable name
    var_src,  # Source template variable
    df:pd.DataFrame,  # DataFrame with the data
    grp_dest,  # Destination NetCDF group
    ):
    "Copy a single variable: create, populate, copy attrs."
    dtype_name = var_src.datatype.name
    if self.verbose:
        print(80*'-')
        print(f'Group: {grp_dest.name}, Variable: {var_name}')
    variable_type = self.var_type(dtype_name, var_src)
    self.create_var(grp_dest, var_name, variable_type)
    self.fill_var(grp_dest, var_name, variable_type, df)
    self.copy_var_attrs(var_name, var_src, grp_dest)


# %%
#| export
@patch
def var_type(
    self:NetCDFEncoder,
    dtype_name:str,  # Datatype name from template
    var_src,  # Source template variable
    ):
    "Pick enum type if available, else template datatype."
    if var_src.dtype == str: return str
    return self.enum_dtypes.get(dtype_name, var_src.datatype)


# %%
#| export
@patch
def create_var(
    self:NetCDFEncoder,
    grp_dest,  # Destination NetCDF group
    var_name:str,  # NetCDF variable name
    variable_type,  # NetCDF type (enum, str, or float)
    ):
    "Create a NetCDF variable with zlib compression."
    use_comp = variable_type == str
    grp_dest.createVariable(var_name, variable_type, (NC_DIM,),
                            **({'compression': None} if use_comp else {'compression': 'zlib', 'complevel': 9}))


# %%
#| export
@patch
def fill_var(
    self:NetCDFEncoder,
    grp_dest,  # Destination NetCDF group
    var_name:str,  # NetCDF variable name
    variable_type,  # NetCDF type (enum, str, or float)
    df:pd.DataFrame,  # DataFrame with the data
    ):
    "Populate a NetCDF variable from a DataFrame column."
    values = df[self.nc_to_cols[var_name]].values
    is_enum = hasattr(variable_type, '__class__') and 'EnumType' in str(type(variable_type))
    if is_enum: values = self.fillna_enum(values)
    if variable_type == str:
        for i,v in enumerate(values): grp_dest[var_name][i] = v
    else:
        grp_dest[var_name][:] = values


# %%
#| export
@patch
def fillna_enum(
    self:NetCDFEncoder,
    values,  # Array of values, possibly with NaN
    fill_value:int=-1,  # Sentinel for missing enum values
    ):
    "Replace NaN in enum-typed columns with a fill value."
    try: values = values.astype(float)
    except (ValueError, TypeError): values = np.array(values, dtype=float)
    values[np.isnan(values)] = fill_value
    return values.astype(np.int64)



# %% [markdown]
# NetCDF enum types store values as plain integers. They don't have a native concept of "missing." So when an enum column contains `NaN`, we replace them with a sentinel value (`-1`) before writing to disk.

# %%
enc = NetCDFEncoder(dfs, dest_fname=tempfile.mktemp(suffix='.nc'), global_attrs=attrs)

vals = np.array([1.0, np.nan, 3.0, np.nan])
res = enc.fillna_enum(vals)
test_eq(list(res), [1, -1, 3, -1])


# %%
#| export
@patch
def copy_var_attrs(
    self:NetCDFEncoder,
    var_name:str,  # NetCDF variable name
    var_src,  # Source template variable
    grp_dest,  # Destination NetCDF group
    ):
    "Copy attributes from template variable to destination."
    grp_dest[var_name].setncatts(var_src.__dict__)


# %%
#| export
@patch(as_prop=True)
def all_cols(self:NetCDFEncoder):
    "All unique NC columns present across all groups."
    return list(set(col for df in self.dfs.values() for col in df.columns if col in NC_VARS))



# %% [markdown]
# Before we create enum types, we need to know which columns we're dealing with across all groups. `all_cols` gathers them for us. It picks up `SPECIES` from BIOTA and `AREA`, `LAT`, `LON`, `NUCLIDE`, `SMP_ID`, `SMP_ID_PROVIDER`, `STATION`, `TIME`, and `VALUE` from both groups.

# %%
enc = NetCDFEncoder(dfs, dest_fname=tempfile.mktemp(suffix='.nc'), global_attrs=attrs)
test_eq(set(enc.all_cols), {'AREA', 'LAT', 'LON', 'NUCLIDE', 'SMP_ID',
                            'SMP_ID_PROVIDER', 'SPECIES', 'STATION', 'TIME', 'VALUE'})


# %%
#| export
@patch
def create_enums(self:NetCDFEncoder):
    "Create NetCDF enum types for all columns referenced in the data."
    cols = [col for col in self.all_cols if col in NC_DTYPES]
    enums = Enums(lut_src_dir=lut_path())
    for col in cols:
        name = NC_DTYPES[col]["name"]
        if self.verbose: print(f"Creating enum for {name} with values {enums.types[col]}.")
        dtype = self.dest.createEnumType(np.int64, name, enums.types[col])
        self.enum_dtypes[name] = dtype


# %%
#| export
@patch
def encode(self:NetCDFEncoder):
    "Encode MARIS NetCDF based on template and dataframes."
    with Dataset(self.src_fname, format='NETCDF4') as self.src, Dataset(self.dest_fname, 'w', format='NETCDF4') as self.dest:
        self.copy_global_attrs()
        self.create_enums()
        self.process_grps()


# %% [markdown]
# ## How it works
#
# Let's run the encoder on test data and inspect each step to see how the pieces fit together.

# %% [markdown]
# ### Global attributes
#
# We inherit the template's standard attributes, then layer on the ones unique to this dataset. Things like title, summary, and identifier.
#
#
# Let's encode our test dataframes and verify the global attributes made it through:

# %%
encoder = NetCDFEncoder(dfs, dest_fname=dest, global_attrs=attrs)
encoder.encode()

with Dataset(dest, 'r', format='NETCDF4') as nc:
    test_eq(nc.id, '123')
    test_eq(nc.title, 'Test title')
    test_eq(nc.summary, 'Summary test')

# %% [markdown]
# ### Dimensions
#
# Each group gets an `id` dimension from the template. It's an unlimited dimension, so rows can be appended later without restructuring the file. Its length matches the number of rows in the group's DataFrame.

# %%
with Dataset(dest, 'r', format='NETCDF4') as nc:
    for grp_name in ('seawater', 'biota'):
        grp = nc.groups[grp_name]
        test_eq('id' in grp.dimensions, True)
        test_eq(grp.dimensions['id'].isunlimited(), True)
        test_eq(len(grp.dimensions['id']), len(dfs[grp_name.upper()]))


# %% [markdown]
# ### Groups and variables
#
# Each key in `dfs` becomes a NetCDF group. Within each group, only the variables matching the DataFrame columns are created. So `biota` gets a `species` variable while `seawater` doesn't.

# %%
with Dataset(dest, 'r', format='NETCDF4') as nc:
    test_eq(list(nc.groups.keys()), ['seawater', 'biota'])

    sw_vars = list(nc['seawater'].variables.keys())
    bio_vars = list(nc['biota'].variables.keys())
    test_eq('species' in bio_vars, True)
    test_eq('species' in sw_vars, False)

# %% [markdown]
# ### Variable values
#
# Each DataFrame column becomes the corresponding NetCDF variable. The mapping goes through `NC_VARS`, so `VALUE` becomes `value`, `LAT` becomes `lat`, and so on.

# %%
with Dataset(dest, 'r', format='NETCDF4') as nc:
    sw = nc['seawater']
    test_eq(list(sw['id'][:]), [0, 1, 2])
    test_eq(list(sw['lon'][:]), [141.0, 142.0, 143.0])
    test_eq(list(sw['lat'][:]), [37.3, 38.3, 39.3])
    test_eq(list(sw['value'][:]), [0.1, 1.1, 2.1])

# %% [markdown]
# ### Enum types
#
# Columns backed by a controlled vocabulary (`area`, `nuclide`, `species`, …) use NetCDF enum types rather than plain integers.

# %% [markdown]
# NetCDF enums store values as plain integers (`int64`) on disk, with a human-readable label mapping attached as metadata. The file stores `[1, 2, 3, 3]` as `int64`, but `ncdump` or netCDF4-python display them as species names. You can inspect this directly:

# %%
with Dataset(dest, 'r', format='NETCDF4') as nc:
    species = nc['biota']['species']
    print("Enum name:    ", species.datatype.name)
    print("On-disk type: ", species.dtype)
    print("Raw values:   ", species[:])
    mapping = species.datatype.enum_dict
    for k, v in list(mapping.items())[:5]:
        print(f"  {v} → '{k}'")

# %% [markdown]
# The test confirms that `species` is a proper NetCDF enum type, coordinates like `lon` are stored as plain `float32`, and free-text fields like `station` use the NetCDF VLType (variable-length string).

# %%
with Dataset(dest, 'r', format='NETCDF4') as nc:
    biota = nc['biota']
    test_eq('EnumType' in str(type(biota['species'].datatype)), True)
    test_eq(biota['lon'].dtype, np.float32)
    sw = nc['seawater']
    test_eq(sw['station'].datatype.__class__.__name__, 'VLType')

