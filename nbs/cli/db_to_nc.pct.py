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
#| default_exp cli.db_to_nc

# %%
# %load_ext autoreload
# %autoreload 2

# %%
#| export
from fastcore.script import *
from typing import Optional
from fastcore.style import S
import sys
import importlib


# %%
#| export
def import_handler(handler_name, fn_name='encode'):
    try:
        handler = importlib.import_module(handler_name)
        return getattr(handler, fn_name)

    except (ImportError, AttributeError):
        print(f"Failed to import function: {fn_name}")


# %%
#| export
@call_parse
def main(
    src: str,  # Path to MARIS database dump as `.txt` file
    dest: str, # Output path for NetCDF file(s)
    ref_ids: str = '',  # Optional comma-separated reference IDs (e.g., "123,456,789")
) -> None:
    """Convert MARIS legacy database to NetCDF4 format.
    
    If ref_ids is provided as comma-separated values, only encodes those subsets.
    """
    print('Encoding MARIS legacy database...')
    
    ids = [int(id.strip()) for id in ref_ids.split(',')] if ref_ids else None
    if ids: print(f"Processing reference IDs: {', '.join(map(str, ids))}")
    encode = import_handler('marisco.handlers.maris_legacy')
    encode(fname_in=src, dir_dest=dest, ref_ids=ids)
