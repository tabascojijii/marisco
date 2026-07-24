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
#| default_exp callbacks

# %% [markdown]
# # Callbacks
#
# > Callbacks used by handlers to transform raw provider dataframes through an ordered pipeline of transformations.

# %%
#| export
from __future__ import annotations
import copy
from fastcore.all import *
from operator import attrgetter
from cftime import date2num ,num2date
import numpy as np
import pandas as pd
from typing import List, Dict, Callable, Any, Optional, Union
from collections import defaultdict
from marisco.configs import get_lut, get_time_units, NC_GROUPS, SMP_TYPE_LUT

# %%
#| hide
#from marisco.utils import test_dfs
# %load_ext autoreload
# %autoreload 2

# %%
#| eval: false
from nbdev.showdoc import show_doc


# %% [markdown]
# ## Foundation

# %% [markdown]
# The `Transformer` class coordinates an ordered pipeline of `Callback` objects applied to a `dict` of DataFrames (one per sample type group) or a single DataFrame.
#
# Each callback modifies its group's DataFrame in sequence. This is how provider-specific conventions are gradually normalised to the MARIS schema.

# %%
#| export
class Callback(): 
    "Base class for callbacks."
    order = 0
    def __init__(self): pass


# %%
#| export
class PerGroupCB(Callback):
    "Calls `each_grp` for each group in `tfm.dfs`; set `grps` to restrict to specific groups."
    grps: list = None

    def __init__(self,
                 grps: list=None  # Groups to process; None = all groups in `tfm.dfs`
                 ):
        if grps is not None: self.grps = grps

    def __call__(self, tfm):
        for grp in (self.grps or tfm.dfs):
            if grp in tfm.dfs: self.each_grp(grp, tfm.dfs[grp], tfm)


# %%
#| export
@patch
def each_grp(self:PerGroupCB,
             grp: str,          # Group key e.g. `'SEAWATER'`, `'BIOTA'`
             df: pd.DataFrame,  # DataFrame for this group
             tfm,               # Parent `Transformer`
             ):
    "Override to implement per-group transformation logic."
    raise NotImplementedError


# %%
#| export
def run_cbs(
    cbs: List[Callback], # List of callbacks to run
    obj: Any # Object to pass to the callbacks
    ):
    "Run the callbacks in the order they are specified."
    for cb in sorted(cbs, key=attrgetter('order')):
        if cb.__doc__: obj.logs.append(cb.__doc__)
        cb(obj)


# %% [markdown]
# Testing that callbacks run in `order` and only those with docstrings get logged:

# %%
class DocCB(Callback):
    "Runs second."
    order = 1
    def __call__(self, obj): pass

class DocSecondCB(Callback):
    "Runs first."
    order = 0
    def __call__(self, obj): pass

class NoDocCB(Callback):
    def __call__(self, obj): pass

obj = type('Obj', (), {'logs': []})()
run_cbs([DocCB(), NoDocCB(), DocSecondCB()], obj)
test_eq(obj.logs, ['Runs first.', 'Runs second.'])


# %%
#| export
class Transformer():
    "Transform the dataframe(s) according to the specified callbacks."
    def __init__(self, 
                 data: Union[Dict[str, pd.DataFrame], pd.DataFrame], # Data to be transformed
                 cbs: Optional[List[Callback]]=None, # List of callbacks to run
                 custom_maps: Dict = None,
                 inplace: bool=False # Whether to modify the dataframe(s) in place
                 ): 
        store_attr()
        self.is_single_df = isinstance(data, pd.DataFrame)
        self.df, self.dfs = self._prepare_data(data, inplace)
        self.logs = []
        self.custom_maps = custom_maps or defaultdict(lambda: defaultdict(dict))
            
    def _prepare_data(self, data, inplace):
        if self.is_single_df:
            return (data if inplace else data.copy()), None
        else:
            return None, (data if inplace else {k: v.copy() for k, v in data.items()})
    
    def unique(self, col_name: str) -> np.ndarray:
        "Distinct values of a specific column present in all groups."
        if self.is_single_df:
            values = self.df.get(col_name, pd.Series()).dropna().values
        else:
            columns = [df.get(col_name) for df in self.dfs.values() if df.get(col_name) is not None]
            values = np.concatenate([col.dropna().values for col in columns]) if columns else []
        return np.unique(values)
        
    def __call__(self):
        "Transform the dataframe(s) according to the specified callbacks."
        if self.cbs: run_cbs(self.cbs, self)
        return self.df if self.dfs is None else self.dfs


# %% [markdown]
# Below, a few examples of how to use the `Transformer` class.
# Let's define first a test callback that adds `1` to the `depth`:

# %%
class TestCB(Callback):
    "A test callback to add 1 to the depth."
    def __call__(self, tfm: Transformer):
        for grp, df in tfm.dfs.items(): 
            df['depth'] = df['depth'].apply(lambda x: x+1)


# %% [markdown]
# And apply it to the following dataframes:

# %%
dfs = {'biota': pd.DataFrame({'id': [0, 1, 2], 'species': [0, 2, 0], 'depth': [2, 3, 4]}),
       'seawater': pd.DataFrame({'id': [0, 1, 2], 'depth': [3, 4, 5]})}

tfm = Transformer(dfs, cbs=[TestCB()])
dfs_test = tfm()

test_eq(dfs_test['biota']['depth'].to_list(), [3, 4, 5])
test_eq(dfs_test['seawater']['depth'].to_list(), [4, 5, 6])


# %% [markdown]
# `Transformer` also accepts a single `pd.DataFrame` (pre-split handlers like geotraces). In that case callbacks access `tfm.df` instead of `tfm.dfs`:

# %%
class TestCB(Callback):
    "A test callback to add 1 to the depth."
    def __call__(self, tfm: Transformer):
        tfm.df['depth'] = tfm.df['depth'].apply(lambda x: x+1)


# %%
df = pd.DataFrame({'id': [0, 1, 2], 'species': [0, 2, 0], 'depth': [2, 3, 4]})

tfm = Transformer(df, cbs=[TestCB()])
df_test = tfm()

test_eq(df_test['depth'].to_list(), [3, 4, 5])


# %% [markdown]
# Subclass `PerGroupCB` and override `each_grp`. The loop, missing-group guard, and optional scoping are inherited. Use `grps` to restrict to specific groups:

# %%
# All groups: stamp every group with a constant flag
class AddFlagCB(PerGroupCB):
    def __init__(self, col, val): store_attr()
    def each_grp(self, grp, df, tfm): df[self.col] = self.val

dfs = {'SEAWATER': pd.DataFrame({'depth': [1, 2]}),
       'BIOTA':    pd.DataFrame({'depth': [3, 4]})}

tfm = Transformer(dfs, cbs=[AddFlagCB(col='flag', val=1)])
dfs_result = tfm()
test_eq(dfs_result['SEAWATER']['flag'].to_list(), [1, 1])
test_eq(dfs_result['BIOTA']['flag'].to_list(), [1, 1])


# %%
# Scoped: only BIOTA gets the column; SEAWATER is untouched
class BiotaFlagCB(PerGroupCB):
    grps = ['BIOTA']
    def each_grp(self, grp, df, tfm): df['is_biota'] = True

tfm2 = Transformer(dfs, cbs=[BiotaFlagCB()])
dfs_result2 = tfm2()
test_eq('is_biota' in dfs_result2['BIOTA'].columns, True)
test_eq('is_biota' in dfs_result2['SEAWATER'].columns, False)


# %% [markdown]
# ## Cleaning & validation

# %% [markdown]
# Callbacks for cleaning and validating data: coordinate sanitisation (invalid lon/lat), and removal of rows with all-NA values in key columns.

# %%
#| export
class SanitizeLonLatCB(PerGroupCB):
    "Drop rows with invalid longitude & latitude values. Convert `,` separator to `.` separator."
    def __init__(self, 
                 lon_col: str='LON', # Longitude column name
                 lat_col: str='LAT', # Latitude column name
                 verbose: bool=False # Whether to print the number of invalid longitude & latitude values
                 ):
        store_attr()

    def each_grp(self, grp, df, tfm):
        df[self.lon_col] = df[self.lon_col].apply(lambda x: float(str(x).replace(',', '.')))
        df[self.lat_col] = df[self.lat_col].apply(lambda x: float(str(x).replace(',', '.')))
        mask_zeroes = (df[self.lon_col] == 0) & (df[self.lat_col] == 0)
        if mask_zeroes.sum() and self.verbose:
            print(f'The "{grp}" group contains {mask_zeroes.sum()} data points whose ({self.lon_col}, {self.lat_col}) = (0, 0)')
        mask_goob = (df[self.lon_col] < -180) | (df[self.lon_col] > 180) | (df[self.lat_col] < -90) | (df[self.lat_col] > 90)
        if mask_goob.sum() and self.verbose:
            print(f'The "{grp}" group contains {mask_goob.sum()} data points with unrealistic {self.lon_col} or {self.lat_col} values.')
        tfm.dfs[grp] = df.loc[~(mask_zeroes | mask_goob)]


# %%
# Check that measurements located at (0,0) get removed
dfs = {'BIOTA': pd.DataFrame({'LON': [0, 1, 0], 'LAT': [0, 2, 0]})}
tfm = Transformer(dfs, cbs=[SanitizeLonLatCB()])
tfm()['BIOTA']

expected = [1., 2.]
test_eq(tfm()['BIOTA'].iloc[0].to_list(), expected)

# %%
# Check that comma decimal separator get replaced by point instead
dfs = {'BIOTA': pd.DataFrame({'LON': ['45,2'], 'LAT': ['43,1']})}
tfm = Transformer(dfs, cbs=[SanitizeLonLatCB()])
tfm()['BIOTA']

expected = [45.2, 43.1]
test_eq(tfm()['BIOTA'].iloc[0].to_list(), expected)

# %%
# Check that out of bounds lon or lat get removed
dfs = {'BIOTA': pd.DataFrame({'LON': [-190, 190, 1, 2, 1.1], 'LAT': [1, 2, 91, -91, 2.2]})}
tfm = Transformer(dfs, cbs=[SanitizeLonLatCB()])
tfm()['BIOTA']

expected = [1.1, 2.2]
test_eq(tfm()['BIOTA'].iloc[0].to_list(), expected)


# %% [markdown]
# ## Value mapping

# %%
#| export
class RemapCB(PerGroupCB):
    "Remap source values to MARIS standard identifiers using a lookup table."
    def __init__(self,
                 lut: dict|Callable,  # Lookup: dict, or callable(dfs)->dict
                 col_remap: str,            # Destination column to create
                 col_src: str,              # Source column with provider values
                 default_val: int=0,        # Value assigned to unmapped source values
                 grps: list[str]=None,      # Groups to process (None = all)
                ):
        store_attr()
        grp_str = ', '.join(str(g) for g in grps) if grps else 'all'
        self.__doc__ = f"Remap values from '{col_src}' to '{col_remap}' for groups: {grp_str}."

    def _resolve_lut(self, tfm):
        "Resolve the LUT: if a callable, call it with tfm's dfs to produce a dict."
        spec = self.lut
        if callable(spec):
            dfs = tfm.dfs if not tfm.is_single_df else {'_': tfm.df}
            spec = spec(dfs)
        return spec

    def __call__(self, tfm):
        self._resolved_lut = self._resolve_lut(tfm)
        super().__call__(tfm)

    def each_grp(self, grp, df, tfm):
        df[self.col_remap] = (df[self.col_src]
            .map(self._resolved_lut).fillna(self.default_val).astype(int))


# %% [markdown]
# Here are tests demonstrating various `RemapCB` behaviours: basic mapping, default fallback, whitespace handling, group scoping, custom default values, and lazy LUT resolution via callable factories.

# %%
# Basic remapping: values present in the LUT get mapped correctly
lut_dict = {'Cs-137': 1, 'K-40': 2, 'Sr-90': 3}
dfs = {'SEAWATER': pd.DataFrame({'nuclide': ['Cs-137', 'K-40', 'Sr-90']})}
tfm = Transformer(dfs, cbs=[RemapCB(lut=lut_dict, col_remap='NUCLIDE_ID', col_src='nuclide')])
result = tfm()['SEAWATER']
test_eq(result['NUCLIDE_ID'].to_list(), [1, 2, 3])

# %%
# Default fallback: values NOT in the LUT get default_value (0)
dfs = {'SEAWATER': pd.DataFrame({'nuclide': ['Cs-137', 'Am-241']})}
tfm = Transformer(dfs, cbs=[RemapCB(lut=lut_dict, col_remap='NUCLIDE_ID', col_src='nuclide')])
result = tfm()['SEAWATER']
test_eq(result['NUCLIDE_ID'].to_list(), [1, 0])

# %%
# Group scoping: only BIOTA gets remapped, SEAWATER untouched
dfs = {'SEAWATER': pd.DataFrame({'nuclide': ['Cs-137']}),
       'BIOTA':    pd.DataFrame({'nuclide': ['K-40']})}
tfm = Transformer(dfs, cbs=[RemapCB(lut=lut_dict, col_remap='NUCLIDE_ID', col_src='nuclide',
                                     grps=['BIOTA'])])
result = tfm()
test_eq('NUCLIDE_ID' in result['SEAWATER'].columns, False)
test_eq(result['BIOTA']['NUCLIDE_ID'].to_list(), [2])

# %%
# Custom default_val
dfs = {'SEAWATER': pd.DataFrame({'nuclide': ['Am-241']})}
tfm = Transformer(dfs, cbs=[RemapCB(lut=lut_dict, col_remap='NUCLIDE_ID', col_src='nuclide',
                                     default_val=-1)])
result = tfm()['SEAWATER']
test_eq(result['NUCLIDE_ID'].to_list(), [-1])

# %%
from marisco.match import make_lut_from

# Provider supplies their own nuclide codes
prov_nomencl = pd.DataFrame({
    'code': ['h-3', 'k-40'],
    'maris_ref': ['h3', 'k40']
})

nuclide_lut = make_lut_from(prov_nomencl, key_col='code', match_col='maris_ref', lut_key='NUCLIDE')

dfs = {'SEAWATER': pd.DataFrame({'NUCLIDE': ['h-3', 'k-40']})}
tfm = Transformer(dfs, cbs=[RemapCB(lut=nuclide_lut, col_remap='NUCLIDE_ID', col_src='NUCLIDE')])
result = tfm()['SEAWATER']
# h-3 → h3 → nuclide_id=1, k-40 → k40 → nuclide_id=4
test_eq(result['NUCLIDE_ID'].to_list(), [1, 4])

# %%
# Only BIOTA gets remapped
dfs = {'SEAWATER': pd.DataFrame({'NUCLIDE': ['h-3']}),
       'BIOTA':    pd.DataFrame({'NUCLIDE': ['k-40']})}
       
tfm = Transformer(dfs, cbs=[RemapCB(lut=nuclide_lut, col_remap='NUCLIDE_ID', col_src='NUCLIDE',
                                     grps=['BIOTA'])])
result = tfm()
test_eq('NUCLIDE_ID' in result['SEAWATER'].columns, False)
test_eq(result['BIOTA']['NUCLIDE_ID'].to_list(), [4])

# %%
from marisco.match import make_lut
nuclide_lut = make_lut('NUCLIDE')

dfs = {'SEAWATER': pd.DataFrame({'NUCLIDE': ['h3']}),
       'BIOTA':    pd.DataFrame({'NUCLIDE': ['k40']})}
       
tfm = Transformer(dfs, cbs=[RemapCB(lut=nuclide_lut, col_remap='NUCLIDE_ID', col_src='NUCLIDE',
                                     grps=['BIOTA'])])
result = tfm()
test_eq('NUCLIDE_ID' in result['SEAWATER'].columns, False)
test_eq(result['BIOTA']['NUCLIDE_ID'].to_list(), [4])


# %%
#| export
class LowerStripNameCB(PerGroupCB):
    "Convert values to lowercase and strip any trailing spaces."
    def __init__(self, 
                 col_src: str, # Source column name e.g. 'Nuclide'
                 col_dst: str=None, # Destination column name
                 fn_transform: Callable=lambda x: x.lower().strip() # Transformation function
                 ):
        store_attr()
        self.__doc__ = f"Convert '{col_src}' column values to lowercase, strip spaces, and store in '{col_dst}' column."
        if not col_dst: self.col_dst = col_src
        
    def _safe_transform(self, value):
        "Ensure value is not NA and apply transformation function."
        return value if pd.isna(value) else self.fn_transform(str(value))

    def each_grp(self, grp, df, tfm): df[self.col_dst] = df[self.col_src].apply(self._safe_transform)


# %% [markdown]
# Let's test the callback:

# %%
dfs = {'seawater': pd.DataFrame({'Nuclide': ['CS137', '226RA']})}

tfm = Transformer(dfs, cbs=[LowerStripNameCB(col_src='Nuclide', col_dst='NUCLIDE')])
test_eq(tfm()['seawater']['NUCLIDE'].to_list(), ['cs137', '226ra'])


tfm = Transformer(dfs, cbs=[LowerStripNameCB(col_src='Nuclide')])
test_eq(tfm()['seawater']['Nuclide'].to_list(), ['cs137', '226ra'])


# %% [markdown]
# ## Schema alignment

# %%
#| export
class AddSampleTypeIdColumnCB(PerGroupCB):
    "Add a column with the sample type as defined in the CDL."
    def __init__(self, 
                 lut: dict=SMP_TYPE_LUT, # Lookup table for sample type
                 col_name: str='SAMPLE_TYPE' # Column name to store the sample type id
                 ): 
        store_attr()
        
    def each_grp(self, grp, df, tfm): df[self.col_name] = self.lut[grp]


# %% [markdown]
# Let's test the callback:

# %%
dfs = {smp_type: pd.DataFrame({'col_test': [0, 1, 2]}) for smp_type in SMP_TYPE_LUT.keys()};

tfm = Transformer(dfs, cbs=[AddSampleTypeIdColumnCB()])
dfs_test = tfm()

for smp_type in SMP_TYPE_LUT.keys():
    test_eq(dfs_test[smp_type]['SAMPLE_TYPE'].unique().item(), SMP_TYPE_LUT[smp_type]) 


# %%
#| export
class RenameColumnsCB(PerGroupCB):
    "Rename variables to MARIS standard names, keeping only renamed columns."
    def __init__(self,
                 renaming_rules: dict # Renaming rules {old_name: new_name}
                 ): 
        store_attr()
        
    def each_grp(self, grp, df, tfm): tfm.dfs[grp] = df[self.renaming_rules.keys()].rename(columns=self.renaming_rules)



# %%
# RenameColumnsCB now also selects: only renamed columns survive
dfs = {'SEAWATER': pd.DataFrame({'a': [1, 2], 'b': [3, 4], 'c': [5, 6]})}
rules = {'a': 'ALPHA', 'b': 'BETA'}
tfm = Transformer(dfs, cbs=[RenameColumnsCB(rules)])
result = tfm()['SEAWATER']
test_eq(list(result.columns), ['ALPHA', 'BETA'])
test_eq(result['ALPHA'].to_list(), [1, 2])

# Column 'c' is dropped: not in the renaming rules
test_eq('c' in result.columns, False)

# Works across multiple groups
dfs = {'SEAWATER': pd.DataFrame({'a': [1], 'b': [2]}),
       'BIOTA':    pd.DataFrame({'a': [3], 'b': [4]})}
rules = {'a': 'VAL'}
tfm = Transformer(dfs, cbs=[RenameColumnsCB(rules)])
result = tfm()
test_eq(list(result['SEAWATER'].columns), ['VAL'])
test_eq(list(result['BIOTA'].columns), ['VAL'])
test_eq(result['SEAWATER']['VAL'].iloc[0], 1)
test_eq(result['BIOTA']['VAL'].iloc[0], 3)


# %%
#| export
class RemoveAllNAValuesCB(Callback):
    "Remove rows with all NA values in specified columns."
    def __init__(self, 
                 cols_to_check: Union[Dict[str, list], list],  # Dict or list of columns to check
                 how: str='all'  # How to handle NA values 'all' or 'any'
                ):
        store_attr()

    def __call__(self, tfm):
        # Convert list to dict if cols_to_check is a list
        cols_dict = (self.cols_to_check if isinstance(self.cols_to_check, dict) 
                    else {k: self.cols_to_check for k in tfm.dfs.keys()})
        
        for sample_type, columns in cols_dict.items():
            tfm.dfs[sample_type].dropna(
                subset=columns,
                how=self.how,
                inplace=True
            )


# %% [markdown]
# Tests for list and dict `cols_to_check` inputs: rows where all specified columns are NA are removed, per group.

# %%
result

# %%
# List input: only row 'c' has all NA in subset cols → it's dropped, row 'b' survives (uncertainty=0.2)
dfs = {'SEAWATER': pd.DataFrame({'value': [1.0, np.nan, np.nan, 4.0],
                                  'uncertainty': [0.1, 0.2, np.nan, 0.4],
                                  'meta': ['a', 'b', 'c', 'd']})}
tfm = Transformer(dfs, cbs=[RemoveAllNAValuesCB(cols_to_check=['value', 'uncertainty'], how='all')])
result = tfm()['SEAWATER']
test_eq(len(result), 3)
test_eq(result['meta'].to_list(), ['a', 'b', 'd'])

# Dict input: same behaviour, per-group column lists
dfs = {'SEAWATER': pd.DataFrame({'value': [1.0, np.nan], 'uncertainty': [0.1, np.nan]}),
       'SEDIMENT': pd.DataFrame({'value': [np.nan, 2.0], 'uncertainty': [np.nan, 0.2]})}
tfm2 = Transformer(dfs, cbs=[RemoveAllNAValuesCB(
    cols_to_check={'SEAWATER': ['value', 'uncertainty'], 'SEDIMENT': ['value', 'uncertainty']},
    how='all')])
result2 = tfm2()
test_eq(len(result2['SEAWATER']), 1)
test_eq(len(result2['SEDIMENT']), 1)


# %% [markdown]
# ## Wide-to-long reshaping
#
# `MeltWideNuclidesCB` converts a provider's wide format (one column per nuclide) to the MARIS long format (one row per measurement). The `spec` argument is a list of dicts—one per nuclide column group—each carrying the source column names **and** the MARIS IDs to stamp. Adding a new nuclide requires adding one dict entry; the CB itself never needs to change.

# %%
#| export
class MeltWideNuclidesCB(Callback):
    "Reshape wide nuclide columns to long format using a named-dict spec."
    def __init__(self,
                 spec: list,           # List of dicts with keys: val, unc, nuclide, unit, lab
                 grp:  str='SEAWATER', # Group in tfm.dfs to reshape
                 ):
        store_attr()

    def __call__(self, tfm):
        if self.grp not in tfm.dfs: return
        df = tfm.dfs[self.grp]
        frames = []
        for s in self.spec:
            sub = df.dropna(subset=[s['val']]).copy()
            sub['NUCLIDE'] = s['nuclide']
            sub['VALUE']   = sub[s['val']]
            sub['UNC']     = sub[s['unc']]
            sub['UNIT']    = s['unit']
            sub['LAB']     = s['lab']
            frames.append(sub)
        if frames:
            tfm.dfs[self.grp] = pd.concat(frames, ignore_index=True)


# %%
# MeltWideNuclidesCB: wide to long melt using named-dict spec
melt_spec = [
    {'val': 'cs137_bq_l', 'unc': 'unc_cs137_bq_l', 'nuclide': 1, 'unit': 3, 'lab': 0},
    {'val': 'k40_bq_l',   'unc': 'unc_k40_bq_l',   'nuclide': 4, 'unit': 3, 'lab': 0},
]
dfs = {'SEAWATER': pd.DataFrame({
    'LAT': [1.0, 2.0], 'LON': [10.0, 20.0],
    'cs137_bq_l':     [0.5, np.nan], 'unc_cs137_bq_l': [0.1, np.nan],
    'k40_bq_l':       [100.0, 200.0], 'unc_k40_bq_l':  [5.0, 10.0],
})}
tfm = Transformer(dfs, cbs=[MeltWideNuclidesCB(spec=melt_spec)])
result = tfm()['SEAWATER']

# cs137 has 1 non-NA row; k40 has 2 → 3 rows total
test_eq(len(result), 3)
test_eq(result['NUCLIDE'].to_list(), [1, 4, 4])
test_eq(result['VALUE'].to_list(), [0.5, 100.0, 200.0])
test_eq(result['LAB'].unique().tolist(), [0])

# Missing group is silently skipped
tfm_no_grp = Transformer({'BIOTA': pd.DataFrame({'x': [1]})},
                          cbs=[MeltWideNuclidesCB(spec=melt_spec, grp='SEAWATER')])
tfm_no_grp()  # must not raise


# %% [markdown]
# ### Sample ID assignment
#
# `AddSampleIDCB` consolidates the copy-pasted `AddSampleIDCB` variants found independently in the helcom, geotraces, ospar, and tepco handlers. It assigns a 1-based sequential `SMP_ID` (resetting after each melt/reshape) and optionally casts a provider-supplied ID column to `str` for NetCDF VLEN string compatibility.

# %%
#| export
class AddSampleIDCB(PerGroupCB):
    "Assign 1-based sequential SMP_ID; optionally cast a provider ID column to str for NetCDF VLEN compatibility."
    def __init__(self,
                 col_provider: str=None,  # Provider ID column to cast to str; None = skip
                 ):
        store_attr()

    def each_grp(self, grp, df, tfm):
        tfm.dfs[grp] = df.reset_index(drop=True)
        tfm.dfs[grp]['SMP_ID'] = tfm.dfs[grp].index + 1
        if self.col_provider and self.col_provider in tfm.dfs[grp].columns:
            tfm.dfs[grp][self.col_provider] = tfm.dfs[grp][self.col_provider].astype(str).astype(object)


# %%
# Default: 1-based SMP_ID assigned; no provider column cast
dfs = {'SEAWATER': pd.DataFrame({'val': [10, 20, 30]})}
tfm = Transformer(dfs, cbs=[AddSampleIDCB()])
result = tfm()['SEAWATER']
test_eq(result['SMP_ID'].to_list(), [1, 2, 3])

# col_provider casts that column to str (NetCDF VLEN compatibility)
dfs = {'SEAWATER': pd.DataFrame({'val': [1.0, 2.0], 'PROVIDER_ID': [101, 202]})}
tfm2 = Transformer(dfs, cbs=[AddSampleIDCB(col_provider='PROVIDER_ID')])
result2 = tfm2()['SEAWATER']
test_eq(result2['SMP_ID'].to_list(), [1, 2])
test_eq(result2['PROVIDER_ID'].dtype, object)  # cast to str

# Missing col_provider is silently skipped
dfs = {'SEAWATER': pd.DataFrame({'val': [1.0]})}
tfm3 = Transformer(dfs, cbs=[AddSampleIDCB(col_provider='NONEXISTENT')])
tfm3()  # must not raise


# %% [markdown]
# ## Comparison & audit

# %%
#| export
class CompareDfsAndTfmCB(Callback):
    "Create a dataframe of removed data and track changes in row counts due to transformations."  # TODO: refactor - too long
    def __init__(self, 
                 dfs: Dict[str, pd.DataFrame]  # Original dataframes
                 ): 
        store_attr()
        
    def __call__(self, tfm: Transformer) -> None:
        self._initialize_tfm_attributes(tfm)
        for grp in tfm.dfs.keys():
            self._compute_changes(grp, tfm)

    def _initialize_tfm_attributes(self, tfm: Transformer) -> None:
        tfm.dfs_removed = {}
        tfm.compare_stats = {}

    def _compute_changes(self, 
                         grp: str,  # The group key
                         tfm: Transformer  # The transformation object containing `dfs`
                        ) -> None:
        "Compute and store changes including data removed and created during transformation."
        original_df = self.dfs[grp]
        transformed_df = tfm.dfs[grp]

        # Calculate differences
        original_count = len(original_df.index)
        transformed_count = len(transformed_df.index)
        removed_count = len(original_df.index.difference(transformed_df.index))
        created_count = len(transformed_df.index.difference(original_df.index))

        # Store results
        tfm.dfs_removed[grp] = original_df.loc[original_df.index.difference(transformed_df.index)]
        tfm.compare_stats[grp] = {
            'Original row count (dfs)': original_count,
            'Transformed row count (tfm.dfs)': transformed_count,
            'Rows removed from original (tfm.dfs_removed)': removed_count,
            'Rows created in transformed (tfm.dfs_created)': created_count
        }


# %% [markdown]
# `CompareDfsAndTfmCB` compares original vs. transformed dataframes. It creates:
#
# - `tfm.dfs_removed`: data present in the original but absent after transformation
# - `tfm.compare_stats`: row count summary per group

# %%
#|hide
# Test CompareDfsAndTfmCB: track rows removed by a sanitisation step
dfs = {'SEAWATER': pd.DataFrame({'LON': [0, 1, 2], 'LAT': [0, 2, 3]}),
       'SEDIMENT': pd.DataFrame({'LON': [10, 20], 'LAT': [10, 20]})}
original = {k: v.copy() for k, v in dfs.items()}

tfm = Transformer(dfs, cbs=[SanitizeLonLatCB(verbose=False), CompareDfsAndTfmCB(original)])
result = tfm()

# SEAWATER row 0 at (0,0) was removed
test_eq(tfm.compare_stats['SEAWATER']['Rows removed from original (tfm.dfs_removed)'], 1)
test_eq(tfm.compare_stats['SEAWATER']['Original row count (dfs)'], 3)
test_eq(tfm.compare_stats['SEAWATER']['Transformed row count (tfm.dfs)'], 2)
test_eq(tfm.dfs_removed['SEAWATER'].iloc[0].to_list(), [0.0, 0.0])

# SEDIMENT unchanged
test_eq(tfm.compare_stats['SEDIMENT']['Rows removed from original (tfm.dfs_removed)'], 0)


# %%
#| export
class UniqueIndexCB(PerGroupCB):
    "Set unique index for each group."
    def __init__(self, index_name='ID'): store_attr()
        
    def each_grp(self, grp, df, tfm):
        tfm.dfs[grp] = df.reset_index(drop=True).reset_index(names=[self.index_name])


# %% [markdown]
# Test `UniqueIndexCB`: sequential IDs per group, starting from 0 independently for each group.

# %%
# Test UniqueIndexCB: check sequential ID per group, starting from
# 0 for each group independently
dfs = {'SEAWATER': pd.DataFrame({'val': [10, 20, 30]}),
       'SEDIMENT': pd.DataFrame({'val': [100, 200]})}

tfm = Transformer(dfs, cbs=[UniqueIndexCB()])
result = tfm()

test_eq(result['SEAWATER']['ID'].to_list(), [0, 1, 2])
test_eq(result['SEDIMENT']['ID'].to_list(), [0, 1])


# %% [markdown]
# ## Time
#
# Callbacks for parsing, encoding, and decoding time columns to/from NetCDF-compatible numeric values.

# %%
#| export
class ParseTimeCB(PerGroupCB):
    "Parse time column from ISO8601 string to datetime."
    def __init__(self, time_col_name: str='TIME'): store_attr()
    def each_grp(self, grp, df, tfm):
        df[self.time_col_name] = pd.to_datetime(df[self.time_col_name], format='ISO8601')


# %%
dfs_test = {
    'SEAWATER': pd.DataFrame({'TIME': ['2023-01-01T00:00:00', '2023-06-15T12:30:00']}),
    'BIOTA':    pd.DataFrame({'TIME': ['2010-03-22T08:00:00']}),
}
tfm = Transformer(dfs_test, cbs=[ParseTimeCB()])
dfs_result = tfm()
test_eq(dfs_result['SEAWATER']['TIME'].dtype.kind, 'M')
test_eq(dfs_result['BIOTA']['TIME'].dtype.kind, 'M')


# %%
#| export
class EncodeTimeCB(PerGroupCB):
    "Encode time as seconds since epoch."    
    def __init__(self, 
                   col_time: str='TIME',  # Time column name
                   verbose: bool=False,  # Print warning about missing time values
                   fn_units: Callable=get_time_units # Function returning the time units
                 ): 
        store_attr()
        self.units = fn_units()

    def each_grp(self, grp: str, df: pd.DataFrame, tfm):
        n_missing = df[self.col_time].isna().sum()
        if self.verbose and n_missing: print(f"Warning: {n_missing} missing time value(s) in {grp}")
        tfm.dfs[grp] = df[df[self.col_time].notna()]
        tfm.dfs[grp][self.col_time] = tfm.dfs[grp][self.col_time].apply(lambda x: date2num(x, units=self.units))


# %%
dfs_test = {
    'SEAWATER': pd.DataFrame({
        'TIME': [pd.Timestamp(f'2023-01-0{t}') for t in [1, 2]],
        'value': [1, 2]
        }),
    'SEDIMENT': pd.DataFrame({
        'TIME': [pd.Timestamp(f'2023-01-0{t}') for t in [3, 4]],
        'value': [3, 4]
        }),
}

units = 'seconds since 1970-01-01 00:00:00.0'
tfm = Transformer(dfs_test, cbs=[
    EncodeTimeCB(fn_units=lambda: units)
    ], inplace=False)
dfs_result = tfm()

test_eq(dfs_result['SEAWATER'].TIME.dtype, 'int64')
test_eq(dfs_result['SEDIMENT'].TIME.dtype, 'int64')


test_eq(dfs_result['SEAWATER'].TIME, dfs_test['SEAWATER'].TIME.apply(lambda x: date2num(x, units=units)))
test_eq(dfs_result['SEDIMENT'].TIME, dfs_test['SEDIMENT'].TIME.apply(lambda x: date2num(x, units=units)))


# %%
#| export
class DecodeTimeCB(PerGroupCB):
    "Decode time from seconds since epoch to datetime format."    
    def __init__(self, 
                 col_time: str='TIME',
                 fn_units: Callable=get_time_units # Function returning the time units
                 ): 
        store_attr()
        self.units = fn_units()

    def each_grp(self, grp, df, tfm):
        n_missing = df[self.col_time].isna().sum()
        if n_missing: print(f"Warning: {n_missing} missing time value(s) in {grp}.")
        tfm.dfs[grp] = df[df[self.col_time].notna()]
        tfm.dfs[grp][self.col_time] = tfm.dfs[grp][self.col_time].apply(
            lambda x: num2date(x, units=self.units, only_use_cftime_datetimes=False)
        )


# %%
dfs_test = {
    'SEAWATER': pd.DataFrame({
        'TIME': [1672531200, 1672617600],  # 2023-01-01, 2023-01-02 in seconds since epoch
        'value': [1, 2]
        }),
    'SEDIMENT': pd.DataFrame({
        'TIME': [1672704000, 1672790400],  # 2023-01-03, 2023-01-04 in seconds since epoch
        'value': [3, 4]
        }),
}

units = 'seconds since 1970-01-01 00:00:00.0'
tfm = Transformer(dfs_test, cbs=[
    DecodeTimeCB(fn_units=lambda: units)
    ], inplace=False)
dfs_result = tfm()

# Test that times were converted to datetime
test_eq(dfs_result['SEAWATER'].TIME.dtype.kind, 'M')
test_eq(dfs_result['SEDIMENT'].TIME.dtype.kind, 'M')

# Test specific datetime values
expected_times_seawater = pd.to_datetime(['2023-01-01', '2023-01-02'])
expected_times_sediment = pd.to_datetime(['2023-01-03', '2023-01-04'])

test_eq(dfs_result['SEAWATER'].TIME.dt.date, expected_times_seawater.date)
test_eq(dfs_result['SEDIMENT'].TIME.dt.date, expected_times_sediment.date)
