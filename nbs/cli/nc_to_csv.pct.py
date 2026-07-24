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
#| default_exp cli.nc_to_csv

# %%
# %load_ext autoreload
# %autoreload 2

# %%
#| export
from fastcore.script import *
from pathlib import Path
from marisco.netcdf2csv import decode


# %%
#| export
@call_parse
def main(
    src: str,  # Input path and filename for NetCDF file
    dest: str, # Output path and filename (without extension) for CSV file
) -> None:
    "Converts NetCDF files into CSV files that follow the MARIS Standard format."
    print(f'Decoding: {Path(src).name} ...')
    decode(fname_in=src, dest_out=dest, verbose=True)
