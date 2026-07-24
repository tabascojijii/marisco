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
#| default_exp geo

# %% [markdown]
# # Geo
#
# > Geoprocessing utilities: bounding boxes, coordinate conversions.

# %%
#| export
from math import modf
from fastcore.all import *
import numpy as np
import pandas as pd
from shapely import MultiPoint
from typing import Tuple


# %%
#| export
def get_bbox(df: pd.DataFrame,                                # DataFrame with coordinate columns
             coord_cols: Tuple[str, str] = ('LON', 'LAT')     # Column names for (longitude, latitude)
            ) -> MultiPoint:                                  # Bounding box as a shapely envelope
    "Bounding box of a DataFrame's coordinates as a shapely envelope (Polygon)."
    x, y = coord_cols        
    arr = [(row[x], row[y]) for _, row in df.iterrows()]
    return MultiPoint(arr).envelope



# %%
# Multiple distinct points — returns a rectangular envelope
df = pd.DataFrame({'LON': np.linspace(-10, 5, 20), 'LAT':  np.linspace(40, 50, 20)})
bbox = get_bbox(df)
test_eq(bbox.bounds, (-10.0, 40.0, 5.0, 50.0))


# %%
# The envelope is a Polygon — inspect its WKT representation
test_eq(bbox.wkt, 'POLYGON ((-10 40, 5 40, 5 50, -10 50, -10 40))')


# %%
# When all points share the same coordinate, envelope is a degenerate Polygon
df = pd.DataFrame({'LON': [0, 0], 'LAT':  [1, 1]})
bbox = get_bbox(df)
test_eq(bbox.bounds, (0.0, 1.0, 0.0, 1.0))


# %%
# Custom coordinate column names
df = pd.DataFrame({'X': [10, 20], 'Y': [30, 40]})
bbox = get_bbox(df, coord_cols=('X', 'Y'))
test_eq(bbox.bounds, (10.0, 30.0, 20.0, 40.0))


# %%
#| export
def ddmm_to_dd(ddmmmm:float  # Coord in DDMM.MMMM format (e.g. 45.34 → 45°34')
              )->float:      # Same coord in decimal degrees
    "Convert DDMM.MMMM to decimal degrees."
    mins, degs = modf(ddmmmm)
    return round(int(degs) + mins*100/60, 6)



# %%
test_close(ddmm_to_dd(45.34), 45.566667)
test_close(ddmm_to_dd(0.0), 0.0)
test_close(ddmm_to_dd(0.30), 0.5)
test_close(ddmm_to_dd(-45.34), -45.566667)
test_close(ddmm_to_dd(180.00), 180.0)

