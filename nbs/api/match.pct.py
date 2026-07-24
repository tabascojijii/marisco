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
#| default_exp match

# %% [markdown]
# # Match
#
# > Nomenclature reconciliation: fuzzy matching, lookup tables, and external API resolution.

# %%
#| export
import sys
from pathlib import Path
from dataclasses import dataclass
from math import modf
from fastcore.all import *
import pandas as pd
import numpy as np
from tqdm import tqdm
import requests
from jellyfish import levenshtein_distance, jaro_winkler_similarity
from typing import List, Dict, Callable, Tuple, Optional, Union
from marisco.configs import cache_path, lut_fname, NC_DTYPES, get_lut


# %%
#| export
def uniq_across_dfs(dfs:Dict[str,pd.DataFrame],  # Dict of group DataFrames
                    col:str,                      # Column to extract unique values from
                   )->list:                      # Unique values across all group DataFrames
    "Unique column values across all group DataFrames."
    return list(set().union(*(df[col].unique() for df in dfs.values() if col in df.columns)))


# %% [markdown]
# For instance:

# %%
dfs = {'SEAWATER': pd.DataFrame({'NUCLIDE': ['cs137', 'cs134_137_tot', 'cs134_137_tot']}),
       'BIOTA': pd.DataFrame({'NUCLIDE': ['cs137', 'cs134', 'cs134_137_tot']}),
       'SEDIMENT': pd.DataFrame({'NUCLIDE': ['cs134_137_tot', 'cs134_137_tot', 'cs134_137_tot']})}

test_eq(set(uniq_across_dfs(dfs, 'NUCLIDE')), {'cs134', 'cs137', 'cs134_137_tot'})

# %% [markdown]
# What if the column name is not in one of the dataframe?

# %%
dfs = {'SEAWATER': pd.DataFrame({'NUCLIDE': ['cs137', 'cs134_137_tot', 'cs134_137_tot']}),
       'BIOTA': pd.DataFrame({'NUCLIDE': ['cs137', 'cs134', 'cs134_137_tot']}),
       'SEDIMENT': pd.DataFrame({'NONUCLIDE': ['cs134_137_tot', 'cs134_137_tot', 'cs134_137_tot']})}

test_eq(set(uniq_across_dfs(dfs, 'NUCLIDE')), {'cs134', 'cs137', 'cs134_137_tot'})


# %% [markdown]
# When a data provider doesn't supply its own nomenclature, we can derive one from the data itself. `lut_from` wraps `uniq_across_dfs` in the format that `Remapper` expects.

# %%
#| export
def lut_from(
        dfs: Dict[str, pd.DataFrame], # Dict of group DataFrames
        col: str,                     # Column to extract unique values from
        incl_nchars: bool=False       # Include n_chars column?
        ) -> pd.DataFrame:            # Source lookup table
    "Build a source lookup table from unique values across all DataFrames."
    vals = sorted(uniq_across_dfs(dfs, col))
    df = pd.DataFrame(vals, columns=['value'])
    if incl_nchars: df['n_chars'] = df['value'].str.len()
    return df


# %%
# lut_from example
df_lut = lut_from(dfs, 'NUCLIDE')
test_eq(list(df_lut['value']), sorted(['cs134', 'cs137', 'cs134_137_tot']))


# %%
# lut_from with incl_nchars
df_lut = lut_from(dfs, 'NUCLIDE', incl_nchars=True)
test_eq(list(df_lut['n_chars']), [5, 13, 5])

# single group
single = {'SEAWATER': pd.DataFrame({'NUCLIDE': ['cs137', 'cs137']})}
test_eq(uniq_across_dfs(single, 'NUCLIDE'), ['cs137'])


# %% [markdown]
# ## Mapping provider codes to MARIS
#
# A semi-automated workflow for reconciling provider nomenclature against MARIS reference lookups.

# %% [markdown]
# This workflow is designed for the reality that mapping provider codes to MARIS is inherently imperfect. The computer can handle the bulk work with brute-force matching, but reliably getting the last mile right requires a domain expert in the loop.
#
# The idea is:
#
# 1. **Get familiar with the provider's codes**: inspect the raw data and list the unique terms that need mapping.
# 2. **Try an automatic mapping**: let the computer do fuzzy matching between provider codes and MARIS references.
# 3. **Fix what it got wrong**: apply expert overrides for cases the fuzzy match could not resolve correctly.
# 4. **Check the result**: verify the final mapping before using it in the pipeline.
#
# Handler authors should follow this pattern whenever they need to align provider nomenclature (species names, nuclide codes, units, etc.) to MARIS identifiers. The functions below give you the building blocks; steps 1 and 4 are manual review steps.

# %%
#| export
def fuzzy_merge(left: pd.DataFrame,        # Left DataFrame (provider codes)
                right: pd.DataFrame,       # Right DataFrame (MARIS references)
                left_on: str='value',      # Column in `left` to match on
                right_on: str='name',      # Column in `right` to match on
                dist_fn: Callable=levenshtein_distance,  # Distance/similarity function
                lowercase: bool=True,      # Normalise strings to lowercase before comparing?
               ) -> pd.DataFrame:          # Left rows augmented with best right match + score
    "For each row in left, find closest row in right by dist_fn."
    rows = []
    for _, lrow in left.iterrows():
        best_d = float('inf')
        best_rrow = None
        for _, rrow in right.iterrows():
            d = dist_fn(lrow[left_on].lower() if lowercase else lrow[left_on],
                        rrow[right_on].lower() if lowercase else rrow[right_on])
            if d < best_d:
                best_d = d
                best_rrow = rrow
        rows.append({**lrow.to_dict(), **best_rrow.to_dict(), 'score': best_d})
    return pd.DataFrame(rows)


# %% [markdown]
# Test `fuzzy_merge` exact matches, near-matches, and custom distance functions:

# %%
# fuzzy_merge: exact matches get score 0
left = pd.DataFrame({'value': ['cs137', 'k40']})
right = pd.DataFrame({'name': ['cs137', 'k40', 'sr90'], 'maris_id': [1, 2, 3]})
merged = fuzzy_merge(left, right, left_on='value', right_on='name')
test_eq(list(merged['score']), [0, 0])
test_eq(list(merged['maris_id']), [1, 2])

# fuzzy_merge: near-matches get a non-zero score
left = pd.DataFrame({'value': ['cs-137', 'cs134_137']})
merged = fuzzy_merge(left, right, left_on='value', right_on='name')
# 'cs-137' → 'cs137' (dist 1), 'cs134_137' → 'cs137' (dist 5)
test_eq(merged.loc[merged['value'] == 'cs-137', 'score'].iloc[0], 1)
test_eq(merged.loc[merged['value'] == 'cs134_137', 'score'].iloc[0], 4)

# %%
# fuzzy_merge: custom distance function
left = pd.DataFrame({'value': ['cs137', 'k40']})
merged_jw = fuzzy_merge(left, right, left_on='value', right_on='name',
                         dist_fn=lambda a, b: 1 - jaro_winkler_similarity(a, b))
test_eq(list(merged_jw['maris_id']), [1, 2])

# %%
# lowercase=True: case difference ignored
left = pd.DataFrame({'value': ['Cs137']})
right = pd.DataFrame({'name': ['cs137'], 'maris_id': [1]})
merged = fuzzy_merge(left, right, left_on='value', right_on='name', lowercase=True)
test_eq(merged.loc[0, 'score'], 0.0)
test_eq(merged.loc[0, 'maris_id'], 1)

# lowercase=False: case difference counts as distance 1
merged2 = fuzzy_merge(left, right, left_on='value', right_on='name', lowercase=False)
test_eq(merged2.loc[0, 'score'], 1)
test_eq(merged2.loc[0, 'maris_id'], 1)


# %% [markdown]
# For more details on jellyfish distance/similarity functions, see the [official documentation](https://www.jpt.sh/projects/jellyfish/functions/).

# %%
#| export
def fix_lut(merged: pd.DataFrame,
            overrides: dict,
            maris: pd.DataFrame,
            left_on: str,
            right_on: str,
            id_col: str,
           ) -> pd.DataFrame:
    "Replace matched entries with expert overrides by name."
    merged = merged.copy()
    for src_val, target_name in overrides.items():
        mask_ref = maris[right_on] == target_name
        if not mask_ref.any():
            print(f"Warning: '{target_name}' not found in MARIS {right_on} table — skipping override for '{src_val}'", file=sys.stderr, flush=True)
            continue
        mid = maris.loc[mask_ref, id_col].iloc[0]
        mask = merged[left_on] == src_val
        merged.loc[mask, [id_col, right_on, 'score']] = [mid, target_name, 0]
    return merged


# %% [markdown]
# `fix_lut` replaces fuzzy-matched entries with expert overrides and resets their score to 0:

# %%
# fix_lut: override a fuzzy match with the correct MARIS name
maris = pd.DataFrame({'name': ['cs137', 'k40', 'cs134_137_tot'], 'maris_id': [1, 2, 33]})
left = pd.DataFrame({'value': ['cs134_137']})
merged = fuzzy_merge(left, maris, left_on='value', right_on='name')
# cs134_137 matched to cs137 (score 4) — wrong!
test_eq(merged['maris_id'].iloc[0], 1)
test_eq(merged['score'].iloc[0], 4)
print(merged)

# %%
# Fix it with an expert override
overrides = {'cs134_137': 'cs134_137_tot'}
fixed = fix_lut(merged, overrides, maris,
                left_on='value', right_on='name', id_col='maris_id')
test_eq(fixed['maris_id'].iloc[0], 33)
test_eq(fixed['score'].iloc[0], 0)
print(fixed)

# %%
# Empty overrides: no changes
fixed2 = fix_lut(merged, {}, maris,
                 left_on='value', right_on='name', id_col='maris_id')
test_eq(fixed2['maris_id'].iloc[0], 1)
test_eq(fixed2['score'].iloc[0], 4)
print(fixed)

# %%
import io
import contextlib

# %%
# fix_lut: unknown target in overrides prints warning and skips
left2 = pd.DataFrame({'value': ['cs137', 'k40']})
merged2 = fuzzy_merge(left2, maris, left_on='value', right_on='name')
# 'nonexistent' is not in the maris table
overrides2 = {'cs137': 'nonexistent'}

stderr = io.StringIO()
with contextlib.redirect_stderr(stderr):
    fixed2 = fix_lut(merged2, overrides2, maris,
                     left_on='value', right_on='name', id_col='maris_id')

# Warning was printed
assert "Warning: 'nonexistent' not found" in stderr.getvalue()
# cs137 was not changed (still points to maris_id 1)
test_eq(fixed2.loc[fixed2['value'] == 'cs137', 'maris_id'].iloc[0], 1)

# %% [markdown]
# ### Usage examples

# %% [markdown]
# #### Case 1: Provider has explicit nomenclature (like HELCOM RUBIN_NAME.csv)

# %%
provider_df = pd.DataFrame({
    'RUBIN': ['GADU MOR', 'FUCU VES', 'MYTI EDU'],
    'SCIENTIFIC NAME': ['GADUS MORHUA', 'FUCUS VESICULOSUS', 'MYTILUS EDULIS'],
})

maris_species = pd.DataFrame({
    'species_id': [11, 22, 33],
    'species_name': ['Gadus morhua', 'Fucus vesiculosus', 'Mytilus edulis'],
})

overwrite_cache = False
path = cache_path() / 'species_helcom.pkl'
if path.exists() and not overwrite_cache:
    merged = pd.read_pickle(path)
else:
    merged = fuzzy_merge(provider_df, maris_species,
                         left_on='SCIENTIFIC NAME', right_on='species_name')
    merged.to_pickle(path)

merged.query('score > 0')  # inspect non-exact matches

merged = fix_lut(merged, {}, maris_species,
                 left_on='SCIENTIFIC NAME', right_on='species_name', id_col='species_id')
lut = dict(zip(merged['SCIENTIFIC NAME'], merged['species_id']))

print(lut['GADUS MORHUA'])  # 11

# %% [markdown]
# #### Case 2: Provider without explicit nomenclature
#
# Here the provider does not supply a nomenclature lookup table. We infer the unique values directly from the data using `lut_from`, then follow the same matching workflow.

# %%
# Case 2 — Provider without explicit nomenclature (use lut_from to infer from data)
provider_data = {
    'SEAWATER': pd.DataFrame({'NUCLIDE': ['cs137', 'cs134', 'cs137', 'k40']}),
    'BIOTA':    pd.DataFrame({'NUCLIDE': ['cs137', 'k40', 'sr90', 'cs134_137_tot']}),
}

# Inspect: build a LUT from the data itself
provider_lut = lut_from(provider_data, 'NUCLIDE')

maris_nuclides = pd.DataFrame({
    'maris_id': [1, 2, 3, 33],
    'name': ['cs137', 'k40', 'sr90', 'cs134_137_tot'],
})

# Match: brute-force fuzzy matching
merged = fuzzy_merge(provider_lut, maris_nuclides, left_on='value', right_on='name')
# Uncomment to inspect borderline matches: merged.query('score > 0')

# Fix: override anything the fuzzy match got wrong
overrides = {'cs134_137_tot': 'cs134_137_tot'}
fixed = fix_lut(merged, overrides, maris_nuclides,
                left_on='value', right_on='name', id_col='maris_id')

# Apply: use as a plain dict
lut = dict(zip(fixed['value'], fixed['maris_id']))
test_eq(lut['cs137'], 1)
test_eq(lut['cs134_137_tot'], 33)


# %% [markdown]
# ## Assembling the mappings

# %% [markdown]
# When you need to defer the entire mapping pipeline (for example, because the runtime data (`dfs`) isn't available at module load time) the functions below wrap the pipeline into a single lazy callable.
#
# **`make_lut_from`** is the general builder. You provide a callable (or a static DataFrame), and it returns a function that, given the full `dfs` dict, runs the matching and fixing pipeline and returns a `dict`.
#
# **`make_lut`** is a convenience wrapper for the common case (Case 2) where the provider has no explicit nomenclature table. It infers unique values from the data using `lut_from`, then follows the same matching and fixing pipeline.
#
# This pattern lets handler notebooks export the *configuration* (fixes, cache tag, key) without eagerly computing against data that may not exist yet.

# %%
#| export
def make_lut_from(
    mk_prov,           # Callable(dict->DataFrame) or static provider DataFrame
    key_col:str,        # Column name for the Lut key (source value to look up)
    match_col:str,      # Column in provider LUT to fuzzy-match against MARIS ref
    lut_key:str,        # NC_DTYPES key for the MARIS ref LUT to reconcile against, e.g. 'NUCLIDE' or 'SPECIES'
    fixes:dict=None,    # Expert overrides: {source_value: maris_name}
    cache_tag:str=None, # If set, cache `merged` as `{cache_tag}.pkl` under cache_path()
    ) -> Callable:       # Function dict->dict: takes dfs, returns lookup dict
    "Factory: returns a callable that builds a lookup dict from provider data at call time."
    cfg, maris = NC_DTYPES[lut_key], get_lut(lut_key, as_df=True)
    def _lut(dfs):
        cf = cache_path() / f'{cache_tag}.pkl' if cache_tag else None
        if cf and cf.exists(): return pd.read_pickle(cf)
        prov = mk_prov(dfs) if callable(mk_prov) else mk_prov
        m = fuzzy_merge(prov, maris, left_on=match_col, right_on=cfg['key'])
        if fixes: m = fix_lut(m, fixes, maris, left_on=match_col, right_on=cfg['key'], id_col=cfg['value'])
        return dict(zip(m[key_col], m[cfg['value']]))
    return _lut


# %%
#| export
def make_lut(
        lut_key:str, # NC_DTYPES key for the MARIS ref. LUT to reconcile against, e.g. 'NUCLIDE' or 'SPECIES'
        fixes:dict=None, # Expert overrides: {source_value: maris_name}
        cache_tag:str=None, # If set, cache `merged` as `{cache_tag}.pkl`
        ) -> Callable: # Function dict->dict: takes dfs, returns lookup dict
    "Convenience: derives provider LUT from dfs dict via lut_from, then wraps in make_lut_from."
    return make_lut_from(lambda dfs: lut_from(dfs, lut_key), 'value', 'value', lut_key, fixes, cache_tag)


# %%
# Flavor A — minimal example, no fixes, no cache
nuclide_lut = make_lut('NUCLIDE')

# Use with some test data
test_dfs = {
    'SEAWATER': pd.DataFrame({'NUCLIDE': ['cs137', 'cs134', 'k40']}),
    'BIOTA': pd.DataFrame({'NUCLIDE': ['cs137', 'k40', 'sr90', 'cs134_137']}),
}

lut = nuclide_lut(test_dfs)
# cs137 maps to maris_id 33 (from the database LUT)
test_eq(lut['cs137'], 33)

# %%
# Flavor A — with fixes derived from what's in the notebook
fixes_nuclide_names = {'cs134_137': 'cs134_137_tot'}
nuclide_lut = make_lut('NUCLIDE', fixes=fixes_nuclide_names)
lut = nuclide_lut(test_dfs)
# The fix ensures 'cs134_137' resolves correctly
test_eq(lut['cs134_137'], 76) # maris_id for cs134_137_tot

# %%
maris = get_lut('NUCLIDE', as_df=True)
maris.head(10)


# %%
# Flavor B — explicit provider LUT (e.g. from a nomenclature file)
provider_species = pd.DataFrame({
    'code': ['GADU MOR', 'MYTI EDU'],
    'sci_name': ['Gadus morhua', 'Mytilus edulis'],
})
species_lut = make_lut_from(lambda _: provider_species,
                            key_col='code', match_col='sci_name',
                            lut_key='SPECIES')

# %%
# GADU MOR maps to species_id 99 (from the database LUT)
test_eq(species_lut(None)['GADU MOR'], 99)

# %%
# Flavor B — with fix overrides
species_lut = make_lut_from(lambda _: provider_species,
                            key_col='code', match_col='sci_name',
                            lut_key='SPECIES', fixes={'GADU MOR': 'Gadus morhua'})

# %%
# Same result: fix confirms what fuzzy matching already got right
test_eq(species_lut(None)['GADU MOR'], 99)
