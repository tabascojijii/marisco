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
#| default_exp decoders

# %% [markdown]
# # Decoders
# > Various utilities to decode MARIS dataset from `NetCDF`.

# %%
#| hide
# %load_ext autoreload
# %autoreload 2

# %%
#| export
from pathlib import Path
from netCDF4 import Dataset
import pandas as pd
import numpy as np
from fastcore.basics import patch, store_attr
import fastcore.all as fc
from typing import Dict, Callable

from marisco.configs import (
    NC_DTYPES, 
    NC_VARS, 
    CSV_VARS,
    NC_DIM,
    NC_GROUPS,
    SMP_TYPE_LUT,
    lut_path, 
    Enums,
    nc_tpl_path,
    get_time_units
)

from marisco.callbacks import (
    DecodeTimeCB
    )


# %% [markdown]
# ## Convert NetCDF to OpenRefine CSV
#

# %% [markdown]
# MARIS NetCDF files can be converted to OpenRefine CSV files. The OpenRefine CSV files are compatible with the [OpenRefine](https://openrefine.org/) data cleaning tool which are used during the MARIS data cleaning process before loading into the MARIS database.
#

# %%
#| exports
class NetCDFDecoder:
    """Decode MARIS NetCDF files to human readable formats."""
    def __init__(self, 
                 dfs: Dict[str, pd.DataFrame], 
                 fname_in: str,  # Path to NetCDF file
                 dest_out: str, 
                 output_format:str, 
                 remap_vars: Dict[str, str],
                 verbose: bool=False
                ):
        fc.store_attr()        


# %%
#| exports
@patch
def process_groups(self: NetCDFDecoder):
    """Process all groups in the dataset."""
    for group_name, df in self.dfs.items():
        self.process_group(group_name, df, self.remap_vars)


# %%
#| exports
@patch
def process_group(self: NetCDFDecoder, group_name: str, df: pd.DataFrame, remap_vars: Dict[str, str]):
    """Process a single group, mapping column names using remap_vars."""
    # Map column names using remap_vars
    df.columns = [remap_vars.get(col, col) for col in df.columns]



# %%
#| exports
@patch
def save_dataframes(self: NetCDFDecoder):
    """
    Save DataFrames to CSV files.
    
    Each group in the DataFrame dictionary will be saved as a separate CSV file
    with the naming pattern: {base_path}_{group_name}.csv
    
    Raises:
        ValueError: If no destination path is provided or if output format is not CSV
    """
    # Validate destination path
    if self.dest_out is None:
        self.dest_out  = str(Path(self.fname_in).with_suffix(''))
    
    # Validate output format
    if self.output_format != 'csv':
        raise ValueError("Only CSV format is supported")
    
    # Get base path without extension
    base_path = str(Path(self.dest_out).with_suffix(''))
    
    # Save each DataFrame to a CSV file
    for group_name, df in self.dfs.items():
        output_path = f"{base_path}_{group_name}.csv"
        df.to_csv(output_path, index=False)
        
        if self.verbose:
            print(f"Saved {group_name} to {output_path}")


# %%
#| exports
@patch
def decode(self: NetCDFDecoder):
    "Decode NetCDF to Human readable files."
    # Function to rename the columns. 
    self.process_groups()
    self.save_dataframes()
    return self.dfs    


# %%
#|eval: false
df_seawater = pd.DataFrame({
    'ID': [0, 1, 2], 
    'LON': [141, 142, 143], 
    'LAT': [37.3, 38.3, 39.3], 
    'TIME': [1234, 1235, 1236], 
    'NUCLIDE': [1, 2, 3],
    'VALUE': [0.1, 1.1, 2.1], 
    'AREA': [2374, 2379, 2401],
    })

df_biota = pd.DataFrame({
    'ID': [0, 1, 2, 3], 
    'LON': [141, 142, 143, 144], 
    'LAT': [37.3, 38.3, 39.3, 40.3], 
    'TIME': [1234, 1235, 1236, 1237], 
    'NUCLIDE': [1, 2, 3, 3],
    'VALUE': [0.1, 1.1, 2.1, 3.1], 
    'SPECIES': [1, 2, 3, 3]
    })
dfs = {'SEAWATER': df_seawater, 'BIOTA': df_biota}


# %%
#|eval: false
fname = Path('../../_data/output/100-HELCOM-MORS-2024.nc')

decoder = NetCDFDecoder( 
                        dfs=dfs,
                        fname_in=fname,  
                        dest_out=fname.with_suffix(''),
                        output_format='csv',
                        remap_vars=CSV_VARS,
                        verbose=True
                 )
decoder.decode()

