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

# %% [markdown]
# # Reconcile nomenclatures 
# > Aligning provider nomenclature with MARIS
#
# A repeatable workflow for mapping data provider names (nuclides, species, units, etc.) to MARIS standard identifiers.

# %% [markdown]
# **Why this needs a human in the loop?**

# %% [markdown]
#
# Matching provider codes to MARIS identifiers sounds like a string comparison problem, but in practice it is a data curation problem.
#
# There are many reasons the automatic matching can fail:
#
# - Spelling variations and typos in the source data
# - Inconsistent use of hyphens, spaces, or underscores (`Cs-137`, `cs137`, `CS 137`)
# - Composite or derived values that do not exist as a single MARIS reference (`cs134_137_tot`, `pu239+240`)
# - Provider-specific codes with no direct MARIS equivalent
# - Scientific names that have been updated (synonyms, reclassifications)
# - Units written in different notations (`Bq/m3` vs `Bq.m-3`)
#
# No fuzzy-matching algorithm can resolve these on its own. The distance score can flag the borderline cases, but deciding the correct mapping requires domain expertise.
#
# An LLM could take a first pass, but it would need the same careful human review afterwards. And some nomenclatures are large: the MARIS species reference has over 1500 entries and gets updated over time. Running an LLM on that scale for every handler would be disproportionate, especially when fuzzy matching handles the bulk cases well and the remaining ambiguous cases still need a domain expert to evaluate them anyway.
#
# Our experience has shown that the most reliable approach is: let the computer do brute-force fuzzy matching on the bulk cases, then bring a domain expert into the loop for the ambiguous ones.

# %% [markdown]
#

# %% [markdown]
# ## How it works
#
# The reconciliation workflow breaks down into four steps, each with a clear outcome:
#
# - **Try an automatic mapping**: Let the computer do brute-force fuzzy matching between provider values and MARIS references. The distance score tells you how far apart two strings are. A score of 0 means an exact match. The higher the score, the more the strings differ. This score is your signal for which cases need human attention.
#
# - **Fix what it got wrong**: Apply expert overrides for every case the fuzzy match could not resolve correctly. This is where domain knowledge enters.
#
# - **Check the result**: Verify the final mapping before using it in the pipeline.
#
# - **Use the mapping in a Transformer**: Package the resolved lookup table and pass it into a callback.

# %% [markdown]
# **Let's see it in action.**
#
# First try to ["fuzzy" match](https://www.jpt.sh/projects/jellyfish) data provider and maris nomenclature:

# %% [markdown]
# ### Try to map automatically

# %%
# Real-world HELCOM-style nuclide values (compound codes, typos, hyphen variants)
from marisco.match import fuzzy_merge
import pandas as pd

provider_lut = pd.DataFrame({'value': ['cs134137', 'cm243244', 'pu239240',
                                       'pu238240', 'cs143', 'cs145', 'cs144', 'k-40']})
maris_ref = pd.DataFrame({
    'maris_id': [1, 2, 3, 4, 5, 99, 33],
    'name': ['cs134', 'cs137', 'cm244', 'pu239', 'pu240', 'cs134_137_tot', 'k40'],
})

merged = fuzzy_merge(provider_lut, maris_ref, left_on='value', right_on='name')

# Inspect non-exact matches (score > 0)
print(merged[merged['score'] > 0][['value', 'name', 'maris_id', 'score']])

# %% [markdown]
# ### Fix what it got wrong
#
# Apply expert overrides for every case the fuzzy match got wrong. You write a dictionary that maps each problematic provider value to the correct MARIS name. The `fix_lut` function applies these overrides and resets the score to 0 for the fixed entries, so you can verify that no issues remain.
#
# There are two kinds of problems you will encounter:
#
# - **False matches**: The algorithm picked a MARIS name, but it is the wrong one. For example, `cs134_137_tot` was matched to `k40` because of some accidental string similarity. These need an override telling the system the correct target.
#
# - **Missing matches**: The provider uses a value that does not exist in the MARIS reference at all. For example, `cs134` and `cs144` are not standard MARIS nuclide names. You need to research what they actually represent and map them to the closest MARIS equivalent.

# %%
#| eval: false
from marisco.match import fix_lut

# Expert overrides: provider value -> correct MARIS name
overrides = {
    'cs134_137_tot': 'cs134_137_tot',  # correct match exists
    'cs144': 'cs137',                   # typo for cs137
    'cs134': 'cs134_137_tot',           # combined measurement
}

fixed = fix_lut(merged, overrides, maris_ref,
                left_on='value', right_on='name', id_col='maris_id')
print(fixed[fixed['score'] > 0])

# %% [markdown]
# ### Check the result
#
# If all entries now have a score of 0, the lookup table is complete and ready for use.
#
# ```python
# assert len(fixed[fixed['score'] > 0]) == 0, "Unresolved matches remain"
# ```

# %% [markdown]
# ## Common scenarios

# %% [markdown]
# ### When the match is correct but the score is not zero
#
# A non-zero score does not always mean something is wrong. The algorithm scores every pair by string distance, and sometimes a valid mapping produces a small positive score. For example, the HELCOM RUBIN code `ENCHINODERMATA CIM` fuzzy-matches to the MARIS species `Echinodermata` with a non-zero score, because the provider uses a more specific category name than the MARIS reference entry. The match is semantically correct, so you leave it as is and move on.
#
# The boundary of concern is not "score is zero" but "score is low enough to be clearly the same thing." If the best match is clearly the right one even with a non-zero score, no override is needed. You only need to override when the fuzzy match picked the wrong MARIS entry, or when you decide a value must map to a specific target that the algorithm did not rank first.

# %% [markdown]
# ### When the provider supplies a lookup table
#
# Some providers include a separate file that maps their codes to scientific names. For example, HELCOM ships a `RUBIN_NAME.csv` that maps RUBIN species codes to their full scientific names. In this case you load that file directly and run the workflow on it.
#
# ```python
# provider_df = pd.read_csv(f'{src_dir}/RUBIN_NAME.csv')
# maris_ref = get_lut('SPECIES', as_df=True)
#
# merged = fuzzy_merge(provider_df, maris_ref,
#                      left_on='SCIENTIFIC NAME', right_on='species')
#
# merged[merged.score > 0].sort_values('score', ascending=False)
# ```
#
# Review the borderline matches, write your overrides, and fix:
#
# ```python
# fixes = {
#     'LAMINARIA SACCHARINA': 'Saccharina latissima',
#     'CARDIUM EDULE': 'Cerastoderma edule',
# }
#
# fixed = fix_lut(merged, fixes, maris_ref,
#                 left_on='SCIENTIFIC NAME', right_on='species', id_col='species_id')
#
# assert len(fixed[fixed['score'] > 0]) == 0, "Unresolved matches remain"
# ```
#
# Package the result into a callable the Transformer can use:
#
# ```python
# species_lut = make_lut_from(provider_df, 'RUBIN', 'SCIENTIFIC NAME',
#                             'SPECIES', fixes=fixes)
# ```

# %% [markdown]
# ### When the provider does not supply a lookup table
#
# Many providers only share measurement data without a mapping table. In this case you derive the unique values directly from the data columns using `lut_from`, which collects all unique entries across every sample group (`SEAWATER`, `BIOTA`, `SEDIMENT`) into a single DataFrame.
#
# Once you have this derived lookup table, the workflow proceeds exactly as above: try an automatic match against the MARIS reference, inspect the borderline scores, fix with overrides, and check the result.
#
# Once the assertion passes, wrap it into a Transformer-ready callable with:
#
# ```python
# nuclide_lut = make_lut('NUCLIDE', fixes=fixes)
# ```

# %%
#| eval: false
from marisco.match import lut_from, fuzzy_merge, fix_lut, make_lut
import pandas as pd

# Derive unique values from the data itself
provider_data = {
    'SEAWATER': pd.DataFrame({'NUCLIDE': ['cs137', 'cs134', 'cs137', 'k40']}),
    'BIOTA': pd.DataFrame({'NUCLIDE': ['cs137', 'k40', 'sr90', 'cs134_137_tot']}),
}
provider_lut = lut_from(provider_data, 'NUCLIDE')

maris_ref = pd.DataFrame({
    'maris_id': [1, 2, 3, 33],
    'name': ['cs137', 'k40', 'sr90', 'cs134_137_tot'],
})

merged = fuzzy_merge(provider_lut, maris_ref, left_on='value', right_on='name')
fixes = {'cs134_137_tot': 'cs134_137_tot', 'cs134': 'cs134_137_tot'}
fixed = fix_lut(merged, fixes, maris_ref,
                left_on='value', right_on='name', id_col='maris_id')

assert len(fixed[fixed['score'] > 0]) == 0, "Unresolved matches remain" 

nuclide_lut = make_lut('NUCLIDE', fixes=fixes)

# %% [markdown]
# ## Using the result in a Transformer
#
# The lookup table (whether built by `make_lut`, `make_lut_from`, or a plain dict) goes into a `RemapCB` callback that the `Transformer` applies during encoding.

# %% [markdown]
# ### Self-contained reconciliation example
#
# This example creates a mock provider LUT, fuzzy-matches it against the MARIS NUCLIDE reference (loaded with `get_lut`), applies expert overrides, and packages the result into a `RemapCB` callback. This is the most explicit workflow, mapping directly to what you would do for a new provider.

# %%
#| eval: false
from marisco.configs import get_lut
from marisco.match import fuzzy_merge, fix_lut, make_lut_from
from marisco.callbacks import RemapCB
import pandas as pd


# Mock provider values
provider_lut = pd.DataFrame({'value': ['cs137', 'cs134', 'k-40', 'sr90', 'cs144', 'cs134_137_tot']})
maris_ref = get_lut('NUCLIDE', as_df=True)  # columns: nuclide_id, nc_name

merged = fuzzy_merge(provider_lut, maris_ref,
                     left_on='value', right_on='nc_name')
print("=== Non-zero scores ===")
print(merged[merged.score > 0][['value', 'nc_name', 'score']].to_string(index=False))

fixes = {'cs134': 'cs134_137_tot', 'cs144': 'cs137', 'k-40': 'k40'}
fixed = fix_lut(merged, fixes, maris_ref,
                left_on='value', right_on='nc_name', id_col='nuclide_id')

assert len(fixed[fixed.score > 0]) == 0, "Unresolved matches remain"
print("\n=== All resolved ===")

# Package for Transformer callback
nuclide_lut = make_lut_from(provider_lut, 'value', 'value', 'NUCLIDE', fixes=fixes)
cb = RemapCB(lut=nuclide_lut, col_remap='NUCLIDE', col_src='NUCLIDE')
print(f"Callback ready: {cb}")

# %% [markdown]
# ### Using `make_lut` as a shortcut
#
# When the provider only delivers measurement data without a separate lookup table, `make_lut` handles the entire workflow in one call: it derives unique values from the data, fuzzy-matches against the MARIS reference, applies your overrides, and returns a ready-to-use callable.

# %%
#| eval: false
from marisco.configs import get_lut
from marisco.match import make_lut
from marisco.callbacks import RemapCB


# What the provider actually delivers: measurement data in each group
dfs = {
    'SEAWATER': pd.DataFrame({'NUCLIDE': ['cs137', 'cs134', 'k-40', 'sr90']}),
    'BIOTA':    pd.DataFrame({'NUCLIDE': ['cs137', 'cs144', 'cs134_137_tot']}),
}

# Derive unique values across all groups
maris_ref = get_lut('NUCLIDE', as_df=True)
fixes = {'cs134': 'cs134_137_tot', 'cs144': 'cs137', 'k-40': 'k40'}

# make_lut does the derive + fuzzy-match + fix in one call
nuclide_lut = make_lut('NUCLIDE', fixes=fixes)

# Use in Transformer
cb = RemapCB(lut=nuclide_lut, col_remap='NUCLIDE', col_src='NUCLIDE')

# %% [markdown]
# ### Running the Transformer end-to-end
#
# Once the lut is built, you feed it into a `Transformer` along with your data. The `RemapCB` callback remaps every value in the specified column to its MARIS identifier during encoding. The output shows the remapped numeric ids.

# %%
#| eval: false
from marisco.match import make_lut
from marisco.callbacks import RemapCB, Transformer
import pandas as pd

# Complete end-to-end: build lut, run Transformer, inspect result
dfs = {
    'SEAWATER': pd.DataFrame({'NUCLIDE': ['cs137', 'cs134', 'k-40', 'sr90']}),
    'BIOTA':    pd.DataFrame({'NUCLIDE': ['cs137', 'cs144', 'cs134_137_tot']}),
}

fixes = {'cs134': 'cs134_137_tot', 'cs144': 'cs137', 'k-40': 'k40'}
nuclide_lut = make_lut('NUCLIDE', fixes=fixes)
cb = RemapCB(lut=nuclide_lut, col_remap='NUCLIDE', col_src='NUCLIDE')

tfm = Transformer(dfs, cbs=[cb])
result = tfm()

print(result['SEAWATER']['NUCLIDE'].unique())
print(result['BIOTA']['NUCLIDE'].unique())

# %% [markdown]
# ### Using a plain dict as a lut
#
# For simple mappings where the provider values already match MARIS codes exactly, you can pass a plain Python dict directly as the lut. No fuzzy matching or overrides needed.

# %%
#| eval: false
from marisco.callbacks import RemapCB, Transformer
import pandas as pd

# Plain dict for trivial mappings
filter_lut = {'N': 2, 'n': 2, 'F': 1}

dfs = {
    'SEAWATER': pd.DataFrame({'FILTERING': ['N', 'F', 'n', 'Y']}),
}

cb = RemapCB(lut=filter_lut, col_remap='FILTERING', col_src='FILTERING')
tfm = Transformer(dfs, cbs=[cb])
result = tfm()

print(result['SEAWATER']['FILTERING'].unique())

# %% [markdown]
# ## Recording decisions in the handler notebook
#
# Each handler should document the overrides dictionary and any data-quality issues discovered during inspection. The HELCOM handler shows this pattern with `FEEDBACK TO DATA PROVIDER` callout boxes.
#

# %% [markdown]
# For instance, the following markdown cell:
#
# ```
# :::{.callout-important}
# ## FEEDBACK TO DATA PROVIDER
#
# Some `rubin` codes in the HELCOM Biota dataset do not appear in the `RUBIN_NAME.csv` lookup table. This includes entries with trailing spaces (`FUCU VES `, `GADU MOR  `) and apparently missing codes (`FUCU SPP`, `FURC LUMB`, `STUC PECT`). Trailing spaces should be trimmed at source, and any valid RUBIN codes missing from the lookup table should be added.
# :::
# ```
#
# would be rendered as:

# %% [markdown]
# :::{.callout-important}
# ## FEEDBACK TO DATA PROVIDER
#
# Some `rubin` codes in the HELCOM Biota dataset do not appear in the `RUBIN_NAME.csv` lookup table. This includes entries with trailing spaces (`FUCU VES `, `GADU MOR  `) and apparently missing codes (`FUCU SPP`, `FURC LUMB`, `STUC PECT`). Trailing spaces should be trimmed at source, and any valid RUBIN codes missing from the lookup table should be added.
# :::
