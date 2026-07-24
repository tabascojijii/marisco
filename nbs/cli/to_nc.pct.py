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
#| default_exp cli.to_nc

# %%
# %load_ext autoreload
# %autoreload 2

# %%
#| export
from fastcore.script import *
from typing import Optional, Literal
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
available_handlers = ['helcom', 'geotraces', 'tepco', 'ospar']


# %%
#| export
@call_parse
def main(
    ds: str,  # Name of the dataset to encode as NetCDF4
    dest: str, # Output path and filename for NetCDF file
    src: Optional[str] = None,  # Optional input data path only required for the 'GEOTRACES' dataset
) -> None:
    "Convert 'helcom', 'geotraces', 'tepco' or 'ospar' marine radioactivity datasets to MARIS NetCDF4 format."
    # Validate input
    if ds not in available_handlers:
        print(S.red(f"Invalid handler name: {ds}. Available handlers: {available_handlers}"))
        sys.exit(1)
    
    print(f'Encoding: {ds} ...')
    
    encode = import_handler(f'marisco.handlers.{ds}')
    if src is None:
        encode(fname_out=dest)
    else:
        encode(fname_in=src, fname_out=dest)

# %%
