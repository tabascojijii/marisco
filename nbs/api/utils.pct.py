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
#| default_exp utils

# %% [markdown]
# # Utilities
# > Various utilities

# %%
#| export
from pathlib import Path
from netCDF4 import Dataset
from fastcore.all import *
import pandas as pd
import numpy as np
from ast import literal_eval

from marisco.configs import NC_VARS


# %% [markdown]
# We define below useful constants throughout the package.

# %% [markdown]
# ## NetCDF Utilities

# %% [markdown]
# Extract NetCDF contents

# %%
#| export
# way too long for our coding standard - REFACTORING NEEDED
class ExtractNetcdfContents:
    def __init__(self, filename: str, verbose: bool = False):
        "Initialize and extract data from a NetCDF file."
        self.filename = filename
        self.verbose = verbose
        self.dfs = {}  # DataFrames extracted from the NetCDF file
        self.enum_dicts = {}  # Enum dictionaries extracted from the NetCDF file
        self.global_attrs = {}  # Global attributes extracted from the NetCDF file
        self.custom_maps = {}  # Custom maps extracted from the NetCDF file
        self.extract_all()

    def extract_all(self):
        "Extract data, enums, and global attributes from the NetCDF file."
        if not Path(self.filename).exists():
            print(f'File {self.filename} not found.')
            return
        
        with Dataset(self.filename, 'r') as nc:
            self.global_attrs = self.extract_global_attributes(nc)
            for group_name in nc.groups:
                group = nc.groups[group_name]
                self.dfs[group_name.upper()] = self.extract_data(group)
                self.enum_dicts[group_name.upper()] = self.extract_enums(group, group_name)
                self.custom_maps[group_name.upper()] = self.extract_custom_maps(group, group_name)
                
            if self.verbose:
                print("Data extraction complete.")

    def extract_data(self, group) -> pd.DataFrame:
        "Extract data from a group and convert to DataFrame."
        data = {var_name: var[:] for var_name, var in group.variables.items() if var_name not in group.dimensions}
        df = pd.DataFrame(data)
        rename_map = {nc_var: col for col, nc_var in NC_VARS.items() if nc_var in df.columns}
        df = df.rename(columns=rename_map)
        return df

    def extract_enums(self, group, group_name: str) -> Dict:
        "Extract enum dictionaries for variables in a group."
        local_enum_dicts = {}
        for var_name, var in group.variables.items():
            if hasattr(var.datatype, 'enum_dict'):
                local_enum_dicts[var_name] = {str(k): str(v) for k, v in var.datatype.enum_dict.items()}
                if self.verbose:
                    print(f"Extracted enum_dict for {var_name} in {group_name}")
        return local_enum_dicts

    def extract_global_attributes(self, nc) -> Dict:
        "Extract global attributes from the NetCDF file."
        globattrs = {attr: getattr(nc, attr) for attr in nc.ncattrs()}
        return globattrs
    
    def extract_custom_maps(self, group, group_name: str) -> Dict:
        "Extract custom maps from the NetCDF file."
        reverse_nc_vars = {v: k for k, v in NC_VARS.items()}        
        custom_maps = {}
        for var_name, var in group.variables.items():
            attr=f"{var_name}_map"
            if hasattr(var, attr):
                custom_maps[reverse_nc_vars[var.name]] =  literal_eval(getattr(var, attr))
        return custom_maps

# %%
#| eval: false
# fname = Path('../../_data/output/190-geotraces-2021.nc')
#fname = Path('../../_data/output/tepco.nc')
#fname = Path('../../_data/output/tepco.nc')
#fname = Path('./files/nc/encoding-test.nc')
#contents= ExtractNetcdfContents(fname)
#print(contents.dfs)
#print(contents.enum_dicts)
#print(contents.global_attrs)
#print(contents.custom_maps)
