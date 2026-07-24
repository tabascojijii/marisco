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
#| default_exp handlers.ospar

# %% [markdown]
# # OSPAR 

# %% [markdown]
# > **Refactoring in progress.** This handler is being updated to use the new `marisco` API (fuzzy matching, `make_lut` / `make_lut_from`, `RemapCB`), following the approach used in the HELCOM and GEOTRACES handlers. Exports and execution are temporarily disabled.

# %% [markdown]
# > This data pipeline, known as a "handler" in Marisco terminology, is designed to clean, standardize, and encode [OSPAR data](https://odims.ospar.org/en/) into `NetCDF` format. The handler processes raw OSPAR data, applying various transformations and lookups to align it with `MARIS` data standards.
#
# Key functions of this handler:
#
# - **Cleans** and **normalizes** raw OSPAR data
# - **Applies standardized nomenclature** and units
# - **Encodes the processed data** into `NetCDF` format compatible with MARIS requirements
#
# This handler is a crucial component in the Marisco data processing workflow, ensuring OSPAR data is properly integrated into the MARIS database.

# %% [markdown]
# **[newer version in progress]**

# %% [markdown]
# ::: {.callout-tip}
# ## Getting Started
#
#
# For new MARIS users, please refer to [Understanding MARIS Data Formats (NetCDF and Open Refine)](https://github.com/franckalbinet/marisco/tree/main/install_configure_guide) for detailed information.
#
# :::

# %% [markdown]
# The present notebook pretends to be an instance of [Literate Programming](https://www.wikiwand.com/en/articles/Literate_programming) in the sense that it is a narrative that includes code snippets that are interspersed with explanations. When a function or a class needs to be exported in a dedicated python module (in our case `marisco/handlers/ospar.py`) the code snippet is added to the module using `#| export` as provided by the wonderful [nbdev](https://nbdev.fast.ai/getting_started.html) library.

# %%
#| hide
# %load_ext autoreload
# %autoreload 2

# %%
#| eval: false
import pandas as pd 
import numpy as np
import fastcore.all as fc 
from typing import  Dict, Callable 
from pathlib import Path 
import time
from rich import print

from marisco.configs import NA
from marisco.match import (
    Remapper,
    uniq_across_dfs, lut_from,
)

from marisco.callbacks import (
    Callback, 
    PerGroupCB,
    Transformer, 
    EncodeTimeCB, 
    LowerStripNameCB, 
    SanitizeLonLatCB, 
    CompareDfsAndTfmCB, 
    RemapCB,
    RemoveAllNAValuesCB
)

from marisco.metadata import (
    GlobAttrsFeeder, 
    BboxCB, 
    DepthRangeCB, 
    TimeRangeCB, 
    ZoteroCB, 
    KeyValuePairCB
)

from marisco.configs import (
    NC_DTYPES,
    lut_path,
    lut_fname,
    get_lut, 
    cache_path
)

from marisco.encoders import NetCDFEncoder
from marisco.netcdf2csv import decode
from marisco.utils import ExtractNetcdfContents

# %%
#| hide
from IPython.display import display, Markdown
import warnings
warnings.filterwarnings('ignore')

# %% [markdown]
# ## Configuration and File Paths

# %% [markdown]
# The handler requires several configuration parameters:
#
# 1. **src_dir**: path to the maris-crawlers folder containing the OSPAR data in CSV format
# 2. **fname_out**: Output path and filename for `NetCDF` file (relative paths supported) 
# 3. **zotero_key**: Key for retrieving dataset attributes from [Zotero](https://www.zotero.org/)

# %%
#| eval: false
src_dir = 'https://raw.githubusercontent.com/franckalbinet/maris-crawlers/refs/heads/main/data/processed/OSPAR'
fname_out = '../../_data/output/191-OSPAR-2024.nc'
zotero_key ='LQRA4MMK' # OSPAR MORS zotero key

# %% [markdown]
# ## Load data

# %% [markdown]
# [OSPAR data](https://odims.ospar.org/en/submissions/) is provided as a zipped Microsoft Access database. To facilitate easier access and integration, we process this dataset and convert it into `.csv` files. These processed files are then made available in the [maris-crawlers repository](https://github.com/franckalbinet/maris-crawlers/tree/main/data/processed/OSPAR) on GitHub.
# Once converted, the dataset is in a format that is readily compatible with the [marisco](https://github.com/franckalbinet/marisco) data pipeline, ensuring seamless data handling and analysis.

# %%
#| eval: false
default_smp_types = {  
    'Biota': 'BIOTA', 
    'Seawater': 'SEAWATER', 
}


# %%
#| eval: false
def read_csv(file_name, dir=src_dir):
    file_path = f'{dir}/{file_name}'
    return pd.read_csv(file_path)


# %%
#| eval: false
def load_data(src_url: str, 
              smp_types: dict = default_smp_types, # Sample types to load
              use_cache: bool = False, # Use cache
              save_to_cache: bool = False, # Save to cache
              verbose: bool = False # Verbose
              ) -> Dict[str, pd.DataFrame]:
    "Load OSPAR data and return the data in a dictionary of dataframes with the dictionary key as the sample type."
    
    def safe_file_path(url: str) -> str:
        "Safely encode spaces in a URL."
        return url.replace(" ", "%20")

    def get_file_path(dir_path: str, file_prefix: str) -> str:
        """Construct the full file path based on directory and file prefix."""
        file_path = f"{dir_path}/{file_prefix} data.csv"
        return safe_file_path(file_path) if not use_cache else file_path

    def load_and_process_csv(file_path: str) -> pd.DataFrame:
        """Load a CSV file and process it."""
        if use_cache and not Path(file_path).exists():
            if verbose:
                print(f"{file_path} not found in cache.")
            return pd.DataFrame()

        if verbose:
            start_time = time.time()

        try:
            df = pd.read_csv(file_path)
            df.columns = df.columns.str.lower()
            if verbose:
                print(f"Data loaded from {file_path} in {time.time() - start_time:.2f} seconds.")
            return df
        except Exception as e:
            if verbose:
                print(f"Failed to load {file_path}: {e}")
            return pd.DataFrame()

    def save_to_cache_dir(df: pd.DataFrame, file_prefix: str):
        """Save the DataFrame to the cache directory."""
        cache_dir = cache_path()
        cache_file_path = f"{cache_dir}/{file_prefix} data.csv"
        df.to_csv(cache_file_path, index=False)
        if verbose:
            print(f"Data saved to cache at {cache_file_path}")

    data = {}
    for file_prefix, smp_type in smp_types.items():
        dir_path = cache_path() if use_cache else src_url
        file_path = get_file_path(dir_path, file_prefix)
        df = load_and_process_csv(file_path)

        if save_to_cache and not df.empty:
            save_to_cache_dir(df, file_prefix)

        data[smp_type] = df

    return data


# %%
#| eval: false
dfs = load_data(src_dir, save_to_cache=True, verbose=False)

# %%
#| eval: false
dfs['SEAWATER'].columns

# %% [markdown]
# ## Remove Missing Values

# %% [markdown]
# :::{.callout-important}
# ## FEEDBACK TO DATA PROVIDER
#
# We consider records are incomplete if either the `activity or mda` field or the `sampling date` field is empty. These are the two key criteria we use to identify missing data. 
#
# As shown below: 10 rows are missing the `sampling date` and 10 rows are missing the `activity or mda` field.
# :::

# %%
#| eval: false
print(f'Missing sampling date: {dfs["SEAWATER"]["sampling date"].isnull().sum()}')
print(f'Missing activity or mda: {dfs["SEAWATER"]["activity or mda"].isnull().sum()}')
dfs['SEAWATER'][dfs['SEAWATER']['sampling date'].isnull()].sample(2)

# %% [markdown]
# To quickly remove all missing values, we can use the `RemoveAllNAValuesCB` callback.

# %%
#| eval: false
nan_cols_to_check = ['sampling date', 'activity or mda']

# %%
#| eval: false
dfs = load_data(src_dir)
tfm = Transformer(dfs, cbs = [
    RemoveAllNAValuesCB(nan_cols_to_check)])

dfs_out = tfm()

# %% [markdown]
# Now we can see that the `sampling date` and `activity or mda` columns have no missing values.

# %%
#| eval: false
len(dfs_out['SEAWATER'][dfs['SEAWATER']['sampling date'].isnull()])

# %% [markdown]
# ## Nuclide Name Normalization

# %% [markdown]
# We must standardize the nuclide names in the `OSPAR` dataset to align with the standardized names provided in the `MARISCO` lookup table.
# The lookup process utilizes three key columns:
# - `nuclide_id`: This serves as a unique identifier for each nuclide
# - `nuclide`: Represents the standardized name of the nuclide as per our conventions
# - `nc_name`: Denotes the corresponding name used in `NetCDF` files
#
# Below, we will examine the structure and contents of the lookup table:

# %%
#| eval: false
nuc_lut_df = pd.read_excel(nuc_lut_path())
nuc_lut_df.sample(5)

# %% [markdown]
# :::{.callout-important}
# ## FEEDBACK TO DATA PROVIDER
# In `OSPAR` dataset, the `nuclide` column has inconsistent naming:
#
# - `Cs-137`,  `137Cs` or `CS-137`
# - `239, 240 pu` or `239,240 pu`
# - `ra-226` and `226ra` 
# - duplicates due to the presence of trailing spaces
#
# See below:
#
# :::

# %%
#| eval: false
print(get_unique_across_dfs(dfs, 'nuclide', as_df=False))

# %% [markdown]
# Regardless of these inconsistencies, `OSPAR`'s `nuclide` column needs to be standardized accorsing to MARIS nomenclature.

# %% [markdown]
# ### Lower & strip nuclide names

# %% [markdown]
# To streamline the process of standardizing nuclide data, we employ the `LowerStripNameCB` callback. This function is applied to each DataFrame within our dictionary of DataFrames. Specifically, `LowerStripNameCB` simplifies the nuclide names by converting them to lowercase and removing any leading or trailing whitespace.
#

# %%
#| eval: false
dfs = load_data(src_dir, use_cache=True)
tfm = Transformer(dfs, cbs=[LowerStripNameCB(col_src='nuclide', col_dst='nuclide')])
dfs_output=tfm()
for key, df in dfs_output.items(): print(f'{key} nuclides: {df["nuclide"].unique()}')

# %% [markdown]
# ### Remap nuclide names to MARIS data formats

# %% [markdown]
# Next, we map nuclide names used by `OSPAR` to the `MARIS` standard nuclide names.

# %% [markdown]
# :::{.callout-note}
# ## The "IMFA" MARISCO PATTERN
#
# Remapping data provider nomenclatures to `MARIS` standards is a recurrent operation and is done in a semi-automated manner according to the following pattern:
#
# 1. **Inspect** data provider nomenclature
# 2. **Match** automatically against `MARIS` nomenclature (using a fuzzy matching algorithm)
# 3. **Fix** potential mismatches 
# 4. **Apply** the lookup table to the `DataFrame`
#
# We will refer to this process as **IMFA** (**I**nspect, **M**atch, **F**ix, **A**pply).
#
# :::

# %% [markdown]
# Let's now create an instance of a [fuzzy matching algorithm](https://www.wikiwand.com/en/articles/Approximate_string_matching) `Remapper`. This instance will align the nuclide names from the OSPAR dataset with the MARIS standard nuclide names, as defined in the lookup table located at `nuc_lut_path` and previously shown as `nuc_lut_df`.

# %%
#| eval: false
remapper = Remapper(
    provider_lut_df=get_unique_across_dfs(dfs_output, col_name='nuclide', as_df=True), 
    maris_lut_fn=nuc_lut_path,
    maris_col_id='nuclide_id',
    maris_col_name='nc_name',
    provider_col_to_match='value',
    provider_col_key='value',
    fname_cache='nuclides_ospar.pkl'
    )

# %% [markdown]
# Let's clarify the meaning of the `Remapper` parameters:
#
# - `provider_lut_df`: It is the nomenclature/lookup table used by the data provider for a certain attribute/variable. When the data provider does not provide such nomenclature, `lut_from` is used to derive the lookup table from the data provider data.
# - `maris_lut_fn`: The path to the lookup table containing the `MARIS` standard nuclide names
# - `maris_col_id`: The column name in the lookup table containing the `MARIS` standard nuclide names
# - `maris_col_name`: The column name in the lookup table containing the `MARIS` standard nuclide names
# - `provider_col_to_match`: The column name in the `OSPAR` dataset containing the nuclide names used for the remapping
# - `provider_col_key`: The column name in the `OSPAR` dataset containing the nuclide names to remap from
# - `fname_cache`: The filename for the cache file
#
# Both `provider_col_to_match` and `provider_col_key` are the same column name in the `OSPAR` dataset. In other cases, data providers provide an associated nomenclature such as below for instance (see HELCOM handler for instance).
#
# `data-provider-nuclide-lut` DataFrame:
#
# | nuclide_id | nuclide |
# |------------|---------|
# | 0   | Cs-137  |
# | 1      | Cs-134   |
# | 2      | I-131   |
#
# and uses the `nuclide_id` value in the data themselves. In such a case:
# - `provider_lut_df`: `data-provider-nuclide-lut`
# - `provider_col_to_match` would be `nuclide`
# - `provider_col_key` would be `nuclide_id`

# %% [markdown]
# Now, we can automatically match the OSPAR nuclide names to the MARIS standard. The match_score column helps us evaluate the results. 
#

# %% [markdown]
# ::: {.callout-note}
# ## Pay Attention
#
# Note that data provider's name to macth is always transformed to lowercase and stripped of any leading or trailing whitespace to streamline the matching process as mentionned above.
#
# :::

# %%
#| eval: false
remapper.generate_lookup_table(as_df=True)
remapper.select_match(match_score_threshold=0, verbose=True)

# %% [markdown]
# :::{.callout-note}
# ## Fuzzy Matching
#
# To try matching/reconciling two nomenclatures, we compute the [Levenshtein distance](https://www.wikiwand.com/en/Levenshtein_distance) between the `OSPAR` nuclide names and the `MARIS` standard nuclide names as indicated in the `match_score` column. A score of 0 indicates a perfect match.
#
# :::

# %% [markdown]
# We now manually review the unmatched nuclide names and construct a dictionary to map them to the `MARIS` standard. 

# %%
#| eval: false
fixes_nuclide_names = {
    '99tc': 'tc99',
    '238pu': 'pu238',
    '226ra': 'ra226',
    'ra-226': 'ra226',
    'ra-228': 'ra228',    
    '210pb': 'pb210',
    '241am': 'am241',
    '228ra': 'ra228',
    '137cs': 'cs137',
    '210po': 'po210',
    '239,240pu': 'pu239_240_tot',
    '239, 240 pu': 'pu239_240_tot',
    '3h': 'h3'
    }

# %% [markdown]
# The dictionary `fixes_nuclide_names` applies manual corrections to the nuclide names before the remapping process begins. Note that we did not remap `cs-137` to `cs137` as the fuzzy matching algorithm already matched `cs-137` to `cs137` (though the match score was 1).
#
# The `generate_lookup_table` function constructs a lookup table for this purpose and includes an `overwrite` parameter, set to `True` by default. When activated, this parameter enables the function to update the existing cache with a new pickle file containing the updated lookup table. We are now prepared to test the remapping process.

# %%
#| eval: false
remapper.generate_lookup_table(as_df=True, fixes=fixes_nuclide_names)

# %% [markdown]
# To view all remapped nuclides as a lookup table that will be later passed to our `RemapNuclideNameCB` callback:

# %%
#| eval: false
remapper.generate_lookup_table(as_df=False, fixes=fixes_nuclide_names, overwrite=True)

# %% [markdown]
# The nuclide names have been successfully remapped. We now create a callback named `RemapNuclideNameCB` to translate the OSPAR dataset's nuclide names into the standard `nuclide_id`s used by MARIS. This callback employs the `lut_nuclides` lambda function, which provides the required lookup table.
# Note that the `overwrite=False` parameter is specified in the `Remapper` constructor of the `lut_nuclides` lambda function to utilize the cached version.
#

# %%
#| eval: false
# Create a lookup table for nuclide names
lut_nuclides = lambda df: Remapper(provider_lut_df=df,
                                   maris_lut_fn=nuc_lut_path,
                                   maris_col_id='nuclide_id',
                                   maris_col_name='nc_name',
                                   provider_col_to_match='value',
                                   provider_col_key='value',
                                   fname_cache='nuclides_ospar.pkl').generate_lookup_table(fixes=fixes_nuclide_names, 
                                                                                            as_df=False, overwrite=True)


# %%
#| eval: false
class RemapNuclideNameCB(PerGroupCB):
    "Remap data provider nuclide names to standardized MARIS nuclide names."
    def __init__(self, 
                 fn_lut: Callable, # Function that returns the lookup table dictionary
                 col_name: str # Column name to remap
                ):
        fc.store_attr()

    def __call__(self, tfm):
        df_uniques = get_unique_across_dfs(tfm.dfs, col_name=self.col_name, as_df=True)
        self.lut = {k: v.matched_id for k, v in self.fn_lut(df_uniques).items()}
        super().__call__(tfm)

    def each_grp(self, grp, df, tfm):
        df['NUCLIDE'] = df[self.col_name].replace(self.lut)


# %% [markdown]
# Let's see it in action, along with the `LowerStripNameCB` callback:

# %%
#| eval: false
dfs = load_data(src_dir, use_cache=True)
tfm = Transformer(dfs, cbs=[
    RemoveAllNAValuesCB(nan_cols_to_check),
    LowerStripNameCB(col_src='nuclide', col_dst='nuclide'),
    RemapNuclideNameCB(lut_nuclides, col_name='nuclide')
    ])
dfs_out = tfm()

# For instance
for key in dfs_out.keys():
    print(f'Unique nuclide_ids for {key} NUCLIDE column: ', dfs_out[key]['NUCLIDE'].unique())

# %% [markdown]
# ## Standardize Time

# %% [markdown]
# We create a callback that remaps the date time format in the dictionary of DataFrames (i.e. `%m/%d/%y %H:%M:%S`) to a data time object and in the process handle missing date and times.

# %%
#| eval: false
time_cols = {'BIOTA': 'sampling date', 'SEAWATER': 'sampling date'}
time_format = '%m/%d/%y %H:%M:%S'


# %%
#| eval: false
class ParseTimeCB(PerGroupCB):
    "Parse the time format in the dataframe and check for inconsistencies."
    def __init__(self, 
                 col_src: dict=time_cols, # Column name to remap
                 col_dst: str='TIME', # Column name to remap
                 format: str=time_format # Time format
                 ):
        fc.store_attr()

    def each_grp(self, grp, df, tfm):
        df[self.col_dst] = pd.to_datetime(df[self.col_src.get(grp)], format=self.format, errors='coerce')


# %% [markdown]
# Apply the transformer for callback `ParseTimeCB`.

# %%
#|eval: false
dfs = load_data(src_dir, use_cache=True)
tfm = Transformer(dfs, cbs=[
    RemoveAllNAValuesCB(nan_cols_to_check),
    ParseTimeCB(),
    CompareDfsAndTfmCB(dfs)])
tfm()


display(Markdown("<b> Row Count Comparison Before and After Transformation:</b>"))
with pd.option_context('display.max_rows', None):
    display(pd.DataFrame.from_dict(tfm.compare_stats))

display(Markdown("<b> Example of parsed time column:</b>"))
with pd.option_context('display.max_rows', None):
    display(tfm.dfs['SEAWATER']['TIME'].head(2))

# %% [markdown]
# The NetCDF time format requires the time to be encoded as number of milliseconds since a time of origin. In our case the time of origin is `1970-01-01` as indicated in `configs.ipynb` `CONFIFS['units']['time']` dictionary.

# %% [markdown]
# `EncodeTimeCB` transforms the datetime object from `ParseTimeCB` into the MARIS NetCDF time format.

# %%
#| eval: false
dfs = load_data(src_dir, use_cache=True)
tfm = Transformer(dfs, cbs=[
    RemoveAllNAValuesCB(nan_cols_to_check),
    ParseTimeCB(),
    EncodeTimeCB(),
    CompareDfsAndTfmCB(dfs)
    ])

tfm()

display(Markdown("<b> Row Count Comparison Before and After Transformation:</b>"))
with pd.option_context('display.max_rows', None):
    display(pd.DataFrame.from_dict(tfm.compare_stats))


# %% [markdown]
# ## Sanitize value

# %% [markdown]
# We create a callback, `SanitizeValueCB`, to consolidate measurement values into a single column named `VALUE` and remove any NaN entries.

# %%
#| eval: false
value_cols = {'BIOTA': 'activity or mda', 'SEAWATER': 'activity or mda'}


# %%
#| eval: false
class SanitizeValueCB(PerGroupCB):
    "Sanitize value by removing blank entries and populating `value` column."
    def __init__(self, 
                 value_col: dict = value_cols # Column name to sanitize
                 ):
        fc.store_attr()

    def each_grp(self, grp, df, tfm):
        col = self.value_col.get(grp)
        n_invalid = df[col].isna().sum()
        if n_invalid: print(f"{n_invalid} invalid rows found in group '{grp}' during sanitize value callback.")
        tfm.dfs[grp] = df.dropna(subset=[col])
        tfm.dfs[grp]['VALUE'] = tfm.dfs[grp][col]


# %%
#|eval: false
dfs = load_data(src_dir, use_cache=True)
tfm = Transformer(dfs, cbs=[
    RemoveAllNAValuesCB(nan_cols_to_check),
    SanitizeValueCB(),
    CompareDfsAndTfmCB(dfs)])

tfm()

display(Markdown("<b> Example of VALUE column:</b>"))
with pd.option_context('display.max_rows', None):
    display(tfm.dfs['SEAWATER'][['VALUE']].head())

display(Markdown("<b> Row Count Comparison Before and After Transformation:</b>"))
with pd.option_context('display.max_rows', None):
    display(pd.DataFrame.from_dict(tfm.compare_stats))

display(Markdown("<b> Example of removed data:</b>"))
with pd.option_context('display.max_columns', None):
    display(tfm.dfs_removed['SEAWATER'].head(2))

# %% [markdown]
# ## Normalize uncertainty

# %% [markdown]
# We create a callback, `NormalizeUncCB`, to standardize the uncertainty value to the MARIS format. For each sample type in the OSPAR dataset, the reported uncertainty is given as an expanded uncertainty with a coverage factor `𝑘=2`. For further details, refer to the [OSPAR reporting guidelines](https://mcc.jrc.ec.europa.eu/documents/OSPAR/Guidelines_forestimationof_a_%20measurefor_uncertainty_in_OSPARmonitoring.pdf). In MARIS the uncertainty values are reported as standard uncertainty with a coverage factor
# `𝑘=1`.

# %% [markdown]
# `NormalizeUncCB` callback normalizes the uncertainty using the following `lambda` function:

# %%
#| eval: false
unc_exp2stan = lambda df, unc_col: df[unc_col] / 2

# %%
#| eval: false
unc_cols = {'BIOTA': 'uncertainty', 'SEAWATER': 'uncertainty'}


# %%
#| eval: false
class NormalizeUncCB(PerGroupCB):
    "Normalize uncertainty values in DataFrames."
    def __init__(self, 
                 col_unc: dict = unc_cols, # Column name to normalize
                 fn_convert_unc: Callable=unc_exp2stan, # Function correcting coverage factor
                 ): 
        fc.store_attr()

    def each_grp(self, grp, df, tfm):
        col = self.col_unc.get(grp)
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
        df['UNC'] = self.fn_convert_unc(df, col)


# %%
#|eval: false
dfs = load_data(src_dir, use_cache=True)
tfm = Transformer(dfs, cbs=[
    RemoveAllNAValuesCB(nan_cols_to_check),
    SanitizeValueCB(),               
    NormalizeUncCB()
    ])

tfm()

display(Markdown("<b> Example of VALUE and UNC columns:</b>"))  
for grp in ['SEAWATER', 'BIOTA']:
    print(f'\n{grp}:')
    print(tfm.dfs[grp][['VALUE', 'UNC']])

# %% [markdown]
# :::{.callout-important}
# ## FEEDBACK TO DATA PROVIDER
# The `SEAWATER` dataset includes instances where the uncertainty values significantly exceed the corresponding measurement values. While such occurrences are not inherently erroneous, they merit attention and may warrant further verification.
#
# :::

# %% [markdown]
# To demonstrate instances where the uncertainty significantly surpasses the measurement values, we will initially compute the 'relative uncertainty' as a percentage for the seawater dataset.

# %%
#| eval: false
dfs = load_data(src_dir, use_cache=True)
for grp in ['SEAWATER', 'BIOTA']:
    tfm.dfs[grp]['relative_uncertainty'] = (
    # Divide 'uncertainty' by 'value'
    (tfm.dfs[grp]['uncertainty'] / tfm.dfs[grp]['activity or mda'])
    # Multiply by 100 to convert to percentage
    * 100)

# %% [markdown]
# Now we will retrieve all rows where the relative uncertainty exceeds 100% for the seawater dataset.

# %%
#| eval: false
threshold = 100
grp = 'SEAWATER'
cols_to_show = ['id', 'contracting party', 'nuclide', 'value type', 'activity or mda', 'uncertainty', 'unit', 'relative_uncertainty']
df = tfm.dfs[grp][cols_to_show][tfm.dfs[grp]['relative_uncertainty'] > threshold]

print(f'Number of rows where relative uncertainty is greater than {threshold}%: \n {df.shape[0]} \n')

display(Markdown(f"<b> Example of data with relative uncertainty greater than {threshold}%:</b>"))
with pd.option_context('display.max_rows', None):
    display(df.head())


# %% [markdown]
# :::{.callout-important}
# ## FEEDBACK TO DATA PROVIDER
# The `BIOTA` dataset includes instances where the uncertainty values significantly exceed the corresponding measurement values. While such occurrences are not inherently erroneous, they merit attention and may warrant further verification.
#
# :::

# %% [markdown]
# Now we will retrieve all rows where the relative uncertainty exceeds 100% for the biota dataset.

# %%
#| eval: false
threshold = 100
grp = 'BIOTA' 
cols_to_show=['id', 'contracting party', 'nuclide', 'value type', 'activity or mda', 'uncertainty', 'unit', 'relative_uncertainty']
df=tfm.dfs[grp][cols_to_show][tfm.dfs[grp]['relative_uncertainty'] > threshold]

print(f'Number of rows where relative uncertainty is greater than {threshold}%: \n {df.shape[0]} \n')

display(Markdown(f"<b> Example of data with relative uncertainty greater than {threshold}%:</b>"))
with pd.option_context('display.max_rows', None):
    display(df.head())


# %% [markdown]
# ## Remap units

# %% [markdown]
# Let's inspect the unique units used by OSPAR:

# %%
#| eval: false
get_unique_across_dfs(dfs, col_name='unit', as_df=True)

# %% [markdown]
# :::{.callout-important}
# ## FEEDBACK TO DATA PROVIDER
# Standardizing the units would simplify data processing, as the units are not consistent across the dataset. For example, `BQ/L`, `Bq/l`, and `Bq/L` are used interchangeably.
#
# :::
#

# %% [markdown]
# We will establish unit renaming rules for the OSPAR dataset:

# %%
#| eval: false
# Define unit names renaming rules
renaming_unit_rules = {'Bq/l': 1, #'Bq/m3'
                       'Bq/L': 1,
                       'BQ/L': 1,
                       'Bq/kg f.w.': 5, # Bq/kgw
                       } 

# %% [markdown]
# Now we will create a callback, `RemapUnitCB`, to remap the units in the dataframes. For the `SEAWATER` dataset, we will set a default unit of `Bq/l`.

# %%
#| eval: false
default_units = {'SEAWATER': 'Bq/l',
                 'BIOTA': 'Bq/kg f.w.'}


# %%
#| eval: false
class RemapUnitCB(PerGroupCB):
    "Update DataFrame 'UNIT' columns based on a lookup table."

    def __init__(self,
                 lut: Dict[str, str],
                 default_units: Dict[str, str] = default_units,
                 ):
        fc.store_attr()

    def each_grp(self, grp, df, tfm):
        if grp == 'SEAWATER': df.loc[df['unit'].isnull(), 'unit'] = self.default_units.get(grp)
        df['UNIT'] = df['unit'].apply(lambda x: self.lut.get(x, 'Unknown'))


# %%
#|eval: false
dfs = load_data(src_dir, use_cache=True)
tfm = Transformer(dfs, cbs=[
    RemoveAllNAValuesCB(nan_cols_to_check),
    SanitizeValueCB(), # Remove blank value entries (also removes NaN values in Unit column) 
    RemapUnitCB(renaming_unit_rules),
    CompareDfsAndTfmCB(dfs)
    ])

tfm()

display(Markdown("<b> Row Count Comparison Before and After Transformation:</b>"))
with pd.option_context('display.max_rows', None):
    display(pd.DataFrame.from_dict(tfm.compare_stats))

print('Unique Unit values:')
for grp in ['BIOTA', 'SEAWATER']:
    print(f"{grp}: {tfm.dfs[grp]['UNIT'].unique()}")

# %% [markdown]
# ## Remap detection limit

# %% [markdown]
# :::{.callout-important}
# ## FEEDBACK TO DATA PROVIDER
# The `Value type` column contains numerous `nan` entries.
#
# :::

# %%
#| eval: false
# Count the number of NaN entries in the 'value type' column for 'SEAWATER'
na_count_seawater = dfs['SEAWATER']['value type'].isnull().sum()
print(f"Number of NaN 'Value type' entries in 'SEAWATER': {na_count_seawater}")

# Count the number of NaN entries in the 'value type' column for 'BIOTA'
na_count_biota = dfs['BIOTA']['value type'].isnull().sum()
print(f"Number of NaN 'Value type' entries in 'BIOTA': {na_count_biota}")


# %% [markdown]
# In the `OSPAR` dataset, the detection limit is denoted by `<` in the `Value type` column. When the `Value type` is `<`, the `Activity or MDA `column specifies the detection limit. Conversely, when the `Value type` is `=`, it indicates an actual measurement in the` Activity or MDA` column.
# Let’s review the entries in the `Value type` column for the OSPAR dataset:

# %%
#| eval: false
for grp in dfs.keys():
    print(f'{grp}:')
    print(tfm.dfs[grp]['value type'].unique())

# %% [markdown]
# In `MARIS` the Detection limits are encoded as follows:

# %%
#| eval: false
pd.read_excel(lut_fname('DL'))

# %% [markdown]
# We  can create a lambda function to retrieve the MARIS lookup table.

# %%
#| eval: false
lut_dl = lambda: pd.read_excel(detection_limit_lut_path(), usecols=['name','id']).set_index('name').to_dict()['id']

# %% [markdown]
# We can define the columns of interest in both the `SEAWATER` and `BIOTA` DataFrames for the detection limit column.

# %%
#| eval: false
coi_dl = {'SEAWATER' : {'DL' : 'value type'},
          'BIOTA':  {'DL' : 'value type'}
          }


# %% [markdown]
# We now create a callback `RemapDetectionLimitCB` to remap OSPAR detection limit values to MARIS formatted values using the lookup table. Since the dataset contains 'nan' entries for the detection limit column, we will create a condition to set the detection limit to '=' when the value and uncertainty columns are present and the current detection limit value is not in the lookup keys.

# %%
#| eval: false
class RemapDetectionLimitCB(PerGroupCB):
    "Remap detection limit values to MARIS format using a lookup table."

    def __init__(self, coi: dict, fn_lut: Callable): fc.store_attr()

    def __call__(self, tfm):
        self.lut = self.fn_lut()
        super().__call__(tfm)

    def each_grp(self, grp, df, tfm):
        df['DL'] = df[self.coi[grp]['DL']]
        condition_eq = df['VALUE'].notna() & df['UNC'].notna() & ~df['DL'].isin(self.lut.keys())
        df.loc[condition_eq, 'DL'] = '='
        df.loc[~df['DL'].isin(self.lut.keys()), 'DL'] = 'Not Available'
        df['DL'] = df['DL'].map(self.lut)


# %%
#| eval: false
dfs = load_data(src_dir, use_cache=True)
tfm = Transformer(dfs, cbs=[
    RemoveAllNAValuesCB(nan_cols_to_check),
    SanitizeValueCB(),
    NormalizeUncCB(),                  
    RemapUnitCB(renaming_unit_rules),
    RemapDetectionLimitCB(coi_dl, lut_dl)])

tfm()
for grp in ['BIOTA', 'SEAWATER']:
    print(f"{grp}: {tfm.dfs[grp]['DL'].unique()}")

# %% [markdown]
# ## Remap Biota species

# %% [markdown]
# The `OSPAR` dataset contains biota species information in the `Species` column of the biota DataFrame. To ensure consistency with MARIS standards,  it is necessary to remap these species names. We will employ a similar approach to that used for standardizing nuclide names, **IMFA** (**I**nspect, **M**atch, **F**ix, **A**pply).

# %% [markdown]
# We first **inspect** the unique `Species` values of the OSPAR Biota dataset:

# %%
#| eval: false
dfs = load_data(src_dir, use_cache=True)
with pd.option_context('display.max_columns', None):
    display(get_unique_across_dfs(dfs, col_name='species', as_df=True).T)

# %% [markdown]
# We attempt to **match** the OSPAR `species` column to the `species` column of the MARIS nomenclature using the `Remapper` . First, we initialize the `Remapper`:
#

# %%
#| eval: false
remapper = Remapper(provider_lut_df=get_unique_across_dfs(dfs, col_name='species', as_df=True),
                    maris_lut_fn=species_lut_path,
                    maris_col_id='species_id',
                    maris_col_name='species',
                    provider_col_to_match='value',
                    provider_col_key='value',
                    fname_cache='species_ospar.pkl')

# %% [markdown]
# Next, we perform the matching and generate a lookup table that includes the match score, which quantifies the degree of match accuracy:

# %%
#| eval: false
remapper.generate_lookup_table(as_df=True)
remapper.select_match(match_score_threshold=1, verbose=True)

# %% [markdown]
# Below, we **fix** the entries that are not properly matched by the `Remapper`:

# %%
#| eval: false
fixes_biota_species = {
    'RHODYMENIA PSEUDOPALAMATA & PALMARIA PALMATA': NA,  # Mix of species, no direct mapping
    'Mixture of green, red and brown algae': NA,  # Mix of species, no direct mapping
    'Solea solea (S.vulgaris)': 'Solea solea',
    'SOLEA SOLEA (S.VULGARIS)': 'Solea solea',
    'RAJIDAE/BATOIDEA': NA, #Mix of species, no direct mapping
    'PALMARIA PALMATA': NA,  # Not defined
    'Unknown': NA,
    'unknown': NA,
    'Flatfish': NA,
    'Gadus sp.': NA,  # Not defined
}

# %% [markdown]
# We can now review the remapping results, incorporating the adjustments from the `fixes_biota_species` dictionary:

# %%
#| eval: false
remapper.generate_lookup_table(fixes=fixes_biota_species)
remapper.select_match(match_score_threshold=1, verbose=True)

# %% [markdown]
# Visual inspection of the remaining imperfectly matched entries appears acceptable. We can now define a Remapper Lambda Function that instantiates the Remapper and returns the corrected lookup table.

# %%
#| eval: false
lut_biota = lambda: Remapper(provider_lut_df=lut_from(dfs, 'species'),
                             maris_lut_fn=species_lut_path,
                             maris_col_id='species_id',
                             maris_col_name='species',
                             provider_col_to_match='value',
                             provider_col_key='value',
                             fname_cache='species_ospar.pkl').generate_lookup_table(fixes=fixes_biota_species, 
                                                                                    as_df=False, overwrite=False)

# %% [markdown]
# Putting it all together, we now apply the `RemapCB` callback to our data. This process adds a `SPECIES` column to our `BIOTA` dataframe, which contains the standardized species IDs.

# %%
#| eval: false
dfs = load_data(src_dir, use_cache=True)
tfm = Transformer(dfs, cbs=[
    RemoveAllNAValuesCB(nan_cols_to_check),
    RemapCB(fn_lut=lut_biota, col_remap='SPECIES', col_src='species', dest_grps='BIOTA')    
    ])

tfm()['BIOTA']['SPECIES'].unique()

# %% [markdown]
# ## Enhance Species Data Using Biological group. 
# The `Biological group` column in the `OSPAR` dataset provides valuable insights related to species. We will leverage this information to enrich the `SPECIES` column. To achieve this, we will employ the generic `RemapCB` callback to create an `enhanced_species` column. Subsequently, this `enhanced_species` column will be used to further enrich the `SPECIES` column.

# %% [markdown]
# First we inspect the unique values in the `biological group` column.

# %%
#| eval: false
get_unique_across_dfs(dfs, col_name='biological group', as_df=True)

# %% [markdown]
# We will remap the `biological group` columns data to the `species` column of the MARIS nomenclature, again using a `Remapper` object:

# %%
#| eval: false
remapper = Remapper(provider_lut_df=lut_from(dfs, 'biological group'),
                    maris_lut_fn=species_lut_path,
                    maris_col_id='species_id',
                    maris_col_name='species',
                    provider_col_to_match='value',
                    provider_col_key='value',
                    fname_cache='enhance_species_ospar.pkl')

# %% [markdown]
# Like before we will **inspect** the data.

# %%
remapper.generate_lookup_table(as_df=True)
remapper.select_match(match_score_threshold=1)

# %% [markdown]
# We can see that some entries require manual **fixes**.

# %%
#| eval: false
fixes_enhanced_biota_species = {
    'fish': 'Pisces',
    'FISH': 'Pisces',
    'Fish': 'Pisces'    
}

# %% [markdown]
# Now we will apply the manual **fixes** to the lookup table and review.

# %%
#| eval: false
remapper.generate_lookup_table(fixes=fixes_enhanced_biota_species)
remapper.select_match(match_score_threshold=1)

# %% [markdown]
# Visual inspection of the remaining imperfectly matched entries appears acceptable. We can now define a Remapper Lambda Function that instantiates the Remapper and returns the corrected lookup table.

# %%
#| eval: false
lut_biota_enhanced = lambda: Remapper(provider_lut_df=get_unique_across_dfs(dfs, col_name='biological group', as_df=True),
                             maris_lut_fn=species_lut_path,
                             maris_col_id='species_id',
                             maris_col_name='species',
                             provider_col_to_match='value',
                             provider_col_key='value',
                             fname_cache='enhance_species_ospar.pkl').generate_lookup_table(
                                 fixes=fixes_enhanced_biota_species, 
                                 as_df=False, 
                                 overwrite=False)

# %% [markdown]
# Now we can apply `RemapCB` which results in the addition of an `enhanced_species` column in our `BIOTA` DataFrame.

# %%
#| eval: false
dfs = load_data(src_dir, use_cache=True)
tfm = Transformer(dfs, cbs=[
    RemoveAllNAValuesCB(nan_cols_to_check),
    RemapCB(fn_lut=lut_biota_enhanced, col_remap='enhanced_species', col_src='biological group', dest_grps='BIOTA')    
    ])

tfm()['BIOTA']['enhanced_species'].unique()


# %% [markdown]
# With the `enhanced_species` column, we can enrich the `SPECIES` column. We will use the value in `enhanced_species` column in the absence of a `SPECIES` match if the `enhanced_species` column is valid. 

# %%
#| eval: false
class EnhanceSpeciesCB(PerGroupCB):
    "Enhance the 'SPECIES' column using 'enhanced_species' if conditions are met."
    grps = ['BIOTA']

    def each_grp(self, grp, df, tfm):
        df['SPECIES'] = df.apply(
            lambda row: row['enhanced_species'] if row['SPECIES'] in [-1, 0] and pd.notnull(row['enhanced_species']) else row['SPECIES'],
            axis=1
        )


# %%
#| eval: false
dfs = load_data(src_dir, use_cache=True)
tfm = Transformer(dfs, cbs=[
    RemoveAllNAValuesCB(nan_cols_to_check),
    RemapCB(fn_lut=lut_biota, col_remap='SPECIES', col_src='species', dest_grps='BIOTA'),
    RemapCB(fn_lut=lut_biota_enhanced, col_remap='enhanced_species', col_src='biological group', dest_grps='BIOTA'),
    EnhanceSpeciesCB()
    ])

tfm()['BIOTA']['SPECIES'].unique()


# %% [markdown]
# All entries are matched for the `SPECIES` column.

# %% [markdown]
# ## Remap Biota tissues

# %% [markdown]
# The `OSPAR` dataset includes entries where the `Body Part` is labeled as `whole`. However, the `MARIS` data standard requires a more specific distinction for the `body_part` field, differentiating between `Whole animal` and `Whole plant`. Fortunately, the OSPAR dataset provides a `Biological group` field that allows us to make this distinction.
#
# To address this discrepancy and ensure compatibility with MARIS standards, we will:
# 1. Create a temporary column `body_part_temp` that combines information from both `Body Part` and `Biological group`.
# 2. Use this temporary column to perform the lookup using our `Remapper` object.

# %% [markdown]
# Lets create the temporary column, `body_part_temp`, that combines `Body Part` and `Biological group`.

# %%
#| eval: false
class AddBodypartTempCB(PerGroupCB):
    "Add a temporary column with the body part and biological group combined."
    grps = ['BIOTA']

    def each_grp(self, grp, df, tfm):
        df['body_part_temp'] = (df['body part'] + ' ' + df['biological group']).str.strip().str.lower()


# %%
#|eval: false
dfs = load_data(src_dir, use_cache=True)
tfm = Transformer(dfs, cbs=[  
                            AddBodypartTempCB(),
                            ])
dfs_test = tfm()
dfs_test['BIOTA']['body_part_temp'].unique()

# %% [markdown]
# To align the `body_part_temp` column with the `bodypar` column in the MARIS nomenclature, we will use the `Remapper`. However, since the OSPAR dataset lacks a predefined lookup table for the `body_part` column, we must first create one. This is accomplished by extracting unique values from the `body_part_temp` column.

# %%
#| eval: false
get_unique_across_dfs(dfs_test, col_name='body_part_temp', as_df=True).head()

# %% [markdown]
# We can now remap the `body_part_temp` column to the `bodypar` column in the MARIS nomenclature using the `Remapper`. Subsequently, we will **inspect** the results:

# %%
#| eval: false
remapper = Remapper(provider_lut_df=lut_from(dfs_test, 'body_part_temp'),
                    maris_lut_fn=bodyparts_lut_path,
                    maris_col_id='bodypar_id',
                    maris_col_name='bodypar',
                    provider_col_to_match='value',
                    provider_col_key='value',
                    fname_cache='tissues_ospar.pkl'
                    )

remapper.generate_lookup_table(as_df=True)
remapper.select_match(match_score_threshold=0, verbose=True)

# %% [markdown]
# Many of the lookup entries are sufficient for our needs. However, for values that don't find a match, we can use the `fixes_biota_bodyparts` dictionary to apply manual corrections. First we will create the dictionary.

# %%
#| eval: false
fixes_biota_tissues = {
    'whole seaweed' : 'Whole plant',
    'flesh fish': 'Flesh with bones', # We assume it as the category 'Flesh with bones' also exists
    'flesh fish' : 'Flesh with bones',
    'unknown fish' : NA,
    'unknown fish' : NA,
    'cod medallion fish' : NA, # TO BE DETERMINED
    'mix of muscle and whole fish without liver fish' : NA, # TO BE DETERMINED
    'whole without head fish' : NA, # TO BE DETERMINED
    'flesh without bones seaweed' : NA, # TO BE DETERMINED
    'tail and claws fish' : NA # TO BE DETERMINED
}

# %% [markdown]
# Now we will generate the lookup table and apply the manual *fixes*  defined in the ``fixes_biota_bodyparts`` dictionary.
#

# %%
#| eval: false
remapper.generate_lookup_table(fixes=fixes_biota_tissues)
remapper.select_match(match_score_threshold=1, verbose=True)

# %% [markdown]
# At this stage, the majority of entries have been successfully matched to the MARIS nomenclature. Entries that remain unmatched are appropriately marked as 'not available'. We are now ready to proceed with the final remapping process. We will define a lambda function to instantiate the `Remapper`, which will then generate and return the corrected lookup table.

# %%
#| eval: false
lut_bodyparts = lambda: Remapper(provider_lut_df=get_unique_across_dfs(tfm.dfs, col_name='body_part_temp', as_df=True),
                               maris_lut_key='BODY_PART',
                               maris_col_id='bodypar_id',
                               maris_col_name='bodypar',
                               provider_col_to_match='value',
                               provider_col_key='value',
                               fname_cache='tissues_ospar.pkl'
                               ).generate_lookup_table(fixes=fixes_biota_tissues, as_df=False, overwrite=False)

# %% [markdown]
# Putting it all together, we now apply the `RemapCB` callback. This process results in the addition of a `BODY_PART` column to our `BIOTA` DataFrame.

# %%
#|eval: false
dfs = load_data(src_dir, use_cache=True)
tfm = Transformer(dfs, cbs=[  
                            RemoveAllNAValuesCB(nan_cols_to_check),
                            AddBodypartTempCB(),
                            RemapCB(fn_lut=lut_bodyparts, col_remap='BODY_PART', col_src='body_part_temp' , dest_grps='BIOTA')
                            ])
tfm()
tfm.dfs['BIOTA']['BODY_PART'].unique()

# %% [markdown]
# ## Remap biogroup

# %% [markdown]
# The MARIS species lookup table contains a ``biogroup_id`` column that associates each species with its corresponding ``biogroup``. We will leverage this relationship to create a ``BIO_GROUP`` column in the ``BIOTA`` DataFrame.

# %%
#| eval: false
lut_biogroup_from_biota = lambda: get_lut('SPECIES', key='species_id', value='biogroup_id')

# %%
#| eval: false
dfs = load_data(src_dir, use_cache=True)
tfm = Transformer(dfs, cbs=[ 
    RemoveAllNAValuesCB(nan_cols_to_check),                            
    RemapCB(fn_lut=lut_biota, col_remap='SPECIES', col_src='species', dest_grps='BIOTA'),
    RemapCB(fn_lut=lut_biota_enhanced, col_remap='enhanced_species', col_src='biological group', dest_grps='BIOTA'),
    EnhanceSpeciesCB(),
    RemapCB(fn_lut=lut_biogroup_from_biota, col_remap='BIO_GROUP', col_src='SPECIES', dest_grps='BIOTA')
    ])

tfm()
print(tfm.dfs['BIOTA']['BIO_GROUP'].unique())


# %%
#| eval: false
tfm.dfs['BIOTA'].head()


# %% [markdown]
# ## Add Sample ID

# %% [markdown]
# - `SMP_ID` is a internal unique identifier for each sample
# - `SMP_ID_PROVIDER` is data provided by the data provider.

# %%
#| eval: false
class AddSampleIdCB(PerGroupCB):
    "Create incremental SMP_ID and store original sample id in SMP_ID_PROVIDER"
    def each_grp(self, grp, df, tfm):
        df['SMP_ID'] = range(1, len(df) + 1)
        df['SMP_ID_PROVIDER'] = df['sample id'].fillna('').astype(str)


# %%
#| eval: false
dfs = load_data(src_dir, use_cache=True)
tfm = Transformer(dfs, cbs=[RemoveAllNAValuesCB(nan_cols_to_check),
                            AddSampleIdCB(),
                            CompareDfsAndTfmCB(dfs)
                            ])
tfm()

tfm.dfs['BIOTA'].head()


# %% [markdown]
# ## Add depth

# %% [markdown]
# The OSPAR dataset features a `Sampling depth` column specifically for the `SEAWATER` dataset. In this section, we will develop a callback to integrate the sampling depth, denoted as `SMP_DEPTH`, into the MARIS dataset.

# %%
#| eval: false
class AddDepthCB(PerGroupCB):
    "Ensure depth values are floats and add 'SMP_DEPTH' columns."
    grps = ['SEAWATER']

    def each_grp(self, grp, df, tfm):
        if 'sampling depth' in df.columns: df['SMP_DEPTH'] = df['sampling depth'].astype(float)


# %%
#| eval: false
dfs = load_data(src_dir, use_cache=True)
tfm = Transformer(dfs, cbs=[
    AddDepthCB()
    ])
tfm()
for grp in tfm.dfs.keys():  
    if 'SMP_DEPTH' in tfm.dfs[grp].columns:
        print(f'{grp}:', tfm.dfs[grp][['SMP_DEPTH']].drop_duplicates())


# %% [markdown]
# ## Standardize Coordinates

# %% [markdown]
# The OSPAR dataset offers coordinates in degrees, minutes, and seconds (DMS). The following callback is designed to convert DMS to decimal degrees. 

# %%
#| eval: false
class ConvertLonLatCB(PerGroupCB):
    "Convert Coordinates to decimal degrees (DDD.DDDDD°)."

    def each_grp(self, grp, df, tfm):
        df['LAT'] = self._convert_lat(df)
        df['LON'] = self._convert_lon(df)

    def _dms_to_decimal(self, deg, m, s): return deg + m / 60 + s / 3600

    def _convert_lat(self, df):
        dec = self._dms_to_decimal(df['latd'], df['latm'], df['lats'])
        return np.where(df['latdir'].isin(['S']), -dec, dec)

    def _convert_lon(self, df):
        dec = self._dms_to_decimal(df['longd'], df['longm'], df['longs'])
        return np.where(df['longdir'].isin(['W']), -dec, dec)


# %%
#|eval: false
dfs = load_data(src_dir, use_cache=True)
tfm = Transformer(dfs, cbs=[
    RemoveAllNAValuesCB(nan_cols_to_check),
    ConvertLonLatCB()
    ])

tfm()

with pd.option_context('display.max_columns', None):
    display(tfm.dfs['SEAWATER'][['LAT','latd', 'latm', 'lats', 'LON', 'latdir', 'longd', 'longm','longs', 'longdir']])

# %% [markdown]
# Sanitize coordinates drops a row when both longitude & latitude equal 0 or data contains unrealistic longitude & latitude values. Converts longitude & latitude `,` separator to `.` separator."

# %%
#|eval: false
dfs = load_data(src_dir, use_cache=True)
tfm = Transformer(dfs, cbs=[
                            ConvertLonLatCB(),
                            SanitizeLonLatCB(),
                            CompareDfsAndTfmCB(dfs)
                            ])

tfm()

display(Markdown("<b> Row Count Comparison Before and After Transformation:</b>"))
with pd.option_context('display.max_rows', None):
    display(pd.DataFrame.from_dict(tfm.compare_stats))

with pd.option_context('display.max_columns', None):
    display(tfm.dfs['SEAWATER'][['LAT','LON']])


# %% [markdown]
# ## Add Station

# %%
#| eval: false
class AddStationCB(PerGroupCB):
    "Add STATION column to all DataFrames."
    def each_grp(self, grp, df, tfm): df['STATION'] = df['station id'].fillna('').astype(str)


# %% [markdown]
# ## Review all callbacks

# %%
#|eval: false
dfs = load_data(src_dir, use_cache=True)
tfm = Transformer(dfs, cbs=[
                            RemoveAllNAValuesCB(nan_cols_to_check),
                            LowerStripNameCB(col_src='nuclide', col_dst='nuclide'),
                            RemapNuclideNameCB(lut_nuclides, col_name='nuclide'),
                            ParseTimeCB(),
                            EncodeTimeCB(),
                            SanitizeValueCB(),
                            NormalizeUncCB(),
                            RemapUnitCB(renaming_unit_rules),
                            RemapDetectionLimitCB(coi_dl, lut_dl),
                            RemapCB(fn_lut=lut_biota, col_remap='SPECIES', col_src='species', dest_grps='BIOTA'),    
                            RemapCB(fn_lut=lut_biota_enhanced, col_remap='enhanced_species', col_src='biological group', dest_grps='BIOTA'),    
                            EnhanceSpeciesCB(),
                            AddBodypartTempCB(),
                            RemapCB(fn_lut=lut_bodyparts, col_remap='BODY_PART', col_src='body_part_temp' , dest_grps='BIOTA'),
                            AddSampleIdCB(),
                            AddDepthCB(),    
                            ConvertLonLatCB(),
                            SanitizeLonLatCB(),
                            AddStationCB(),
                            CompareDfsAndTfmCB(dfs)
                            ])

tfm()
print(pd.DataFrame.from_dict(tfm.compare_stats) , '\n')

# %%
#| eval: false
tfm.dfs['SEAWATER'].head()

# %% [markdown]
# ### Example change logs

# %% [markdown]
# Review the change logs for the netcdf encoding.

# %%
#|eval: false
dfs = load_data(src_dir, use_cache=True)
tfm = Transformer(dfs, cbs=[
                            RemoveAllNAValuesCB(nan_cols_to_check), 
                            LowerStripNameCB(col_src='nuclide', col_dst='nuclide'),
                            RemapNuclideNameCB(lut_nuclides, col_name='nuclide'),
                            ParseTimeCB(),
                            EncodeTimeCB(),
                            SanitizeValueCB(),
                            NormalizeUncCB(),
                            RemapUnitCB(renaming_unit_rules),
                            RemapDetectionLimitCB(coi_dl, lut_dl),
                            RemapCB(fn_lut=lut_biota, col_remap='SPECIES', col_src='species', dest_grps='BIOTA'),    
                            RemapCB(fn_lut=lut_biota_enhanced, col_remap='enhanced_species', col_src='biological group', dest_grps='BIOTA'),    
                            EnhanceSpeciesCB(),
                            AddBodypartTempCB(),
                            RemapCB(fn_lut=lut_bodyparts, col_remap='BODY_PART', col_src='body_part_temp' , dest_grps='BIOTA'),
                            AddSampleIdCB(),
                            AddDepthCB(),    
                            ConvertLonLatCB(),
                            SanitizeLonLatCB(),
                            AddStationCB(),
                            ])

# Transform
tfm()
# Check transformation logs
tfm.logs

# %% [markdown]
# ## Feed global attributes

# %%
#| eval: false
kw = ['oceanography', 'Earth Science > Oceans > Ocean Chemistry> Radionuclides',
      'Earth Science > Human Dimensions > Environmental Impacts > Nuclear Radiation Exposure',
      'Earth Science > Oceans > Ocean Chemistry > Ocean Tracers, Earth Science > Oceans > Marine Sediments',
      'Earth Science > Oceans > Ocean Chemistry, Earth Science > Oceans > Sea Ice > Isotopes',
      'Earth Science > Oceans > Water Quality > Ocean Contaminants',
      'Earth Science > Biological Classification > Animals/Vertebrates > Fish',
      'Earth Science > Biosphere > Ecosystems > Marine Ecosystems',
      'Earth Science > Biological Classification > Animals/Invertebrates > Mollusks',
      'Earth Science > Biological Classification > Animals/Invertebrates > Arthropods > Crustaceans',
      'Earth Science > Biological Classification > Plants > Macroalgae (Seaweeds)']


# %%
#| eval: false
def get_attrs(
    tfm: Transformer, # Transformer object
    zotero_key: str, # Zotero dataset record key
    kw: list = kw # List of keywords
    ) -> dict: # Global attributes
    "Retrieve all global attributes."
    return GlobAttrsFeeder(tfm.dfs, cbs=[
        BboxCB(),
        DepthRangeCB(),
        TimeRangeCB(),
        ZoteroCB(zotero_key),
        KeyValuePairCB('keywords', ', '.join(kw)),
        KeyValuePairCB('publisher_postprocess_logs', ', '.join(tfm.logs))
        ])()


# %%
#|eval: false
get_attrs(tfm, zotero_key=zotero_key, kw=kw)


# %% [markdown]
# ## Encoding NETCDF

# %%
#| eval: false
def encode(
    fname_out: str, # Output file name
    **kwargs # Additional arguments
    ) -> None:
    "Encode data to NetCDF."
    dfs = load_data(src_dir, use_cache=True)
    tfm = Transformer(dfs, cbs=[
                            RemoveAllNAValuesCB(nan_cols_to_check),
                            LowerStripNameCB(col_src='nuclide', col_dst='nuclide'),
                            RemapNuclideNameCB(lut_nuclides, col_name='nuclide'),
                            ParseTimeCB(),
                            EncodeTimeCB(),
                            SanitizeValueCB(),
                            NormalizeUncCB(),
                            RemapUnitCB(renaming_unit_rules),
                            RemapDetectionLimitCB(coi_dl, lut_dl),
                            RemapCB(fn_lut=lut_biota, col_remap='SPECIES', col_src='species', dest_grps='BIOTA'),    
                            RemapCB(fn_lut=lut_biota_enhanced, col_remap='enhanced_species', col_src='biological group', dest_grps='BIOTA'),    
                            EnhanceSpeciesCB(),
                            AddBodypartTempCB(),
                            RemapCB(fn_lut=lut_bodyparts, col_remap='BODY_PART', col_src='body_part_temp' , dest_grps='BIOTA'),
                            AddSampleIdCB(),
                            AddDepthCB(),    
                            ConvertLonLatCB(),
                            SanitizeLonLatCB(),
                            AddStationCB()
                                ])
    tfm()
    encoder = NetCDFEncoder(tfm.dfs, 
                            dest_fname=fname_out, 
                            global_attrs=get_attrs(tfm, zotero_key=zotero_key, kw=kw),
                            verbose=kwargs.get('verbose', False),
                           )
    encoder.encode()


# %%
#|eval: false
encode(fname_out, verbose=False)

# %% [markdown]
# ## NetCDF Review

# %% [markdown]
# First lets review the global attributes of the NetCDF file:

# %%
#| eval: false
contents = ExtractNetcdfContents(fname_out)
print(contents.global_attrs)

# %% [markdown]
# Review the publisher_postprocess_logs.

# %%
#| eval: false
print(contents.global_attrs['publisher_postprocess_logs'])

# %% [markdown]
# Lets review the data of the NetCDF file:

# %%
#| eval: false
dfs = contents.dfs
dfs

# %% [markdown]
# Lets review the biota data:

# %%
#| eval: false
nc_dfs_biota = dfs['BIOTA']
nc_dfs_biota

# %% [markdown]
# Lets review the seawater data:

# %%
#| eval: false
nc_dfs_seawater = dfs['SEAWATER']
nc_dfs_seawater

# %% [markdown]
# ## Data Format Conversion 
#
# The MARIS data processing workflow involves two key steps:
#
# 1. **NetCDF to Standardized CSV Compatible with OpenRefine Pipeline**
#    - Convert standardized NetCDF files to CSV formats compatible with OpenRefine using the `NetCDFDecoder`.
#    - Preserve data integrity and variable relationships.
#    - Maintain standardized nomenclature and units.
#
# 2. **Database Integration**
#    - Process the converted CSV files using OpenRefine.
#    - Apply data cleaning and standardization rules.
#    - Export validated data to the MARIS master database.
#
# This section focuses on the first step: converting NetCDF files to a format suitable for OpenRefine processing using the `NetCDFDecoder` class.

# %%
#|eval: false
decode(fname_in=fname_out, verbose=True)
