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
#| default_exp netcdf2csv

# %% [markdown]
# # NetCDF2CSV

# %% [markdown]
# > A data pipeline that converts MARIS NetCDF files into MARIS Standard OpenRefine CSV format.

# %% [markdown]
# This module converts NetCDF files into CSV files that follow the MARIS Standard [OpenRefine](https://openrefine.org/) format. While MARISCO has replaced OpenRefine in the data cleaning and preparation pipeline, the MARIS master database still requires input files to conform to this CSV format specification. The conversion is performed using the marisco library.
#

# %% [markdown]
# :::{.callout-tip}
#
# For new MARIS users, please refer to [field definitions
# ](https://github.com/franckalbinet/marisco/blob/main/nbs/reference/field-definition.ipynb) for detailed information about Maris fields.
#
# :::

# %% [markdown]
# # Dependencies
# > Required packages and internal modules for data format transformations

# %%
#| export
from pathlib import Path
# from netCDF4 import Dataset
import os
import pandas as pd
import fastcore.all as fc
from typing import Dict,Callable

from marisco.configs import (
    NC_VARS,
    CSV_VARS,
    CSV_DTYPES,
    Enums,
    lut_path,
    lut_fname,
    ZOTERO_LIB_ID
)

from marisco.utils import (
    ExtractNetcdfContents,
)

from marisco.callbacks import (
    Callback,
    Transformer,
    DecodeTimeCB,
    AddSampleTypeIdColumnCB
)  
    
from marisco.decoders import (
    NetCDFDecoder
    )
from marisco.metadata import (
    ZoteroClient
)

# %%
#| eval: false
from IPython.display import display, Markdown

# %% [markdown]
# ## Configuration and File Paths

# %%
#| eval: false
# fname_in =  Path('../../_data/output/tepco.nc')
fname_in =  Path('../../_data/output/100-HELCOM-MORS-2024.nc')
fname_out = fname_in.with_suffix('.csv')
output_format = 'openrefine_csv'

# %% [markdown]
# ## Data Loading

# %% [markdown]
# Load data from standardized MARIS NetCDF files using ExtractNetcdfContents. The NetCDF files follow CF conventions and include standardized variable names and metadata according to MARIS specifications.

# %%
#| eval: false
contents = ExtractNetcdfContents(fname_in)

# %% [markdown]
# Show the dictionary of dataframes extracted from the NetCDF file. 

# %%
#| eval: false
contents.dfs.keys()

# %% [markdown]
# Show an example of the DataFrame extracted from the NetCDF file. 

# %%
#| eval: false
with pd.option_context('display.max_columns', None):
    display(contents.dfs['SEAWATER'].head())

# %% [markdown]
# Show an example of the dictionary of enums extracted from the NetCDF file as a DataFrame. 

# %%
#| eval: false
grp='SEAWATER'
print(f'Variables in {grp} group: {contents.enum_dicts[grp].keys()}')
var='dl'
with pd.option_context('display.max_columns', None):
    display(pd.DataFrame.from_dict(contents.enum_dicts[grp][var], orient='index').T)

# %% [markdown]
# Show the global attributes extracted from the NetCDF file. 

# %%
#| eval: false
print("First few attributes from global attributes:", list(contents.global_attrs.items())[:5])

# %% [markdown]
# Show the custom maps extracted from the NetCDF file. 

# %%
#| eval: false
grp='SEAWATER'
print(f'Custom maps in {grp} group: {contents.custom_maps[grp].keys()}')
with pd.option_context('display.max_columns', None):
    display(pd.DataFrame.from_dict(contents.custom_maps[grp], orient='index'))   

# %% [markdown]
# ## Validate NetCDF Enumerations

# %% [markdown]
# Verify that enumerated values in the NetCDF file match current MARIS lookup tables.

# %% [markdown]
# :::{.callout-important}
# ## FEEDBACK TO DATA PROVIDERS
#
# The enumeration validation process is a diagnostic step that identifies inconsistencies between NetCDF enumerations and MARIS lookup tables. While this validation does not modify the dataset, it generates detailed feedback about any mismatches or undefined values. 
#
#
# :::

# %%
NC_VARS


# %%
#| export
class ValidateEnumsCB(Callback):
    "Validate enumeration mappings between NetCDF file and MARIS lookup tables."

    def __init__(self, contents, maris_enums, verbose=False):
        fc.store_attr()

    def __call__(self, tfm):
        for group_name, enum_dict in self.contents.enum_dicts.items():
            self._validate_group(group_name, enum_dict)

    def _validate_group(self, group_name, enum_dict):
        
        for var_name, nc_enum_dict in enum_dict.items():
            if self.verbose:
                print(f"Validating variable {var_name} from NetCDF group {group_name}.")
            var_name = self._get_original_var_name(var_name)
            if self.verbose:
                print(f"Standardized variable name to MARISCO naming convention: {var_name}")

            if var_name not in self.maris_enums.types:
                if self.verbose:
                    print(f"Variable {var_name} not found in MARISCO enums.")
                continue

            self._compare_mappings(nc_enum_dict, self.maris_enums.types[var_name], group_name, var_name)

    def _get_original_var_name(self, var_name):
        return next((var for var, nc_var in NC_VARS.items() if nc_var == var_name), var_name)

    def _compare_mappings(self, nc_dict, maris_enum, group_name, var_name):        
        for key, value in nc_dict.items():
            value=int(value)
            if key not in maris_enum or maris_enum[key] != value:
                print(f"\nWarning: Enum mismatch: {var_name} in {group_name}.")
                print(f"   NetCDF value: {key} -> {value}")
                print(f"   MARISCO standard enum lookup value: {key} -> {maris_enum.get(key, 'Not found')}")
            


# %%
#| eval: false
contents = ExtractNetcdfContents(fname_in)
tfm = Transformer(
    data= contents.dfs,
    custom_maps=contents.custom_maps,
    cbs=[
        ValidateEnumsCB(
            contents = contents,
            maris_enums=Enums(lut_src_dir=lut_path())
        ),
    ]
)
tfm()


# %% [markdown]
# ## Remove Non Compatible Columns 

# %% [markdown]
# The ``RemoveNonCompatibleVariablesCB`` callback filters out variables from the NetCDF format that are not listed in the VARS configuration. 

# %%
#| export
class RemoveNonCompatibleVariablesCB(Callback):
    "Remove variables not listed in VARS configuration."
    def __init__(self, 
                vars: Dict[str, str] = CSV_VARS,  # Dictionary mapping OR vars to NC vars
                verbose: bool = False,
                ):
        fc.store_attr()
        
    def __call__(self, tfm: Transformer):
        """Remove non-OR variables fro  m all dataframes."""
        for group_name in tfm.dfs:
            tfm.dfs[group_name] = self._remove_non_vars(tfm.dfs[group_name], group_name)
            
    def _remove_non_vars(self, df: pd.DataFrame, group_name:str ) -> pd.DataFrame:
        """Remove variables not in vars and print removed columns if verbose."""
        current_cols = set(df.columns)
        vars_cols = set(self.vars.keys())
        cols_to_remove = current_cols - vars_cols
        
        if self.verbose and cols_to_remove:
            print(f"Removing variables that are not compatible with vars provided. \nRemoving {', '.join(cols_to_remove)} from {group_name} dataset.")           
        return df.drop(columns=cols_to_remove)



# %%
#| eval: false
contents = ExtractNetcdfContents(fname_in)
tfm = Transformer(
    data=contents.dfs,
    custom_maps=contents.custom_maps,
    cbs=[
        RemoveNonCompatibleVariablesCB(vars=CSV_VARS, verbose=True),
    ]
)
tfm()
print(tfm.dfs['BIOTA'].head())


# %% [markdown]
# ## Sample ID Handling
#
# The MARISCO NetCDF encoding pipeline uses `SMP_ID` to store unique identifiers for each sample measurement. These IDs can come from two sources:
#
# 1. Directly from data providers who supply their own unique identifiers
# 2. Auto-generated by MARISCO as incremented integers when providers don't supply IDs
#
# The Maris database ingestion pipeline expects:
#
# - The original `SMP_ID` if provided by the data source
# - `None` if the ID was auto-generated by MARISCO
#
# *Note: When writing to CSV, `SMP_ID` is renamed to `samplabcode` as defined in the `CSV_VARS` mapping in `configs.ipynb`.*
#
# The callback below implements this logic by providing an option to convert auto-generated `SMP_ID` values to `None` while preserving original provider-supplied IDs.

# %%
#| export
class SampleIDConversionCB(Callback):
    "Convert auto-generated `SMP_ID` values to `None` while preserving original provider-supplied IDs."
    def __init__(self, 
                 nonify: bool = False, # If True, convert auto-generated `SMP_ID` values to `None`
                ):
        fc.store_attr()
        
    def __call__(self, tfm: Transformer):
        for group_name in tfm.dfs:
            if self.nonify: 
                tfm.dfs[group_name]['SMP_ID'] = None


# %%
#| eval: false
contents = ExtractNetcdfContents(fname_in)
tfm = Transformer(
    data=contents.dfs,
    custom_maps=contents.custom_maps,
    cbs=[
        RemoveNonCompatibleVariablesCB(vars=CSV_VARS, verbose=True),
        # SampleIDConversionCB(nonify=True)
    ]
)
tfm()
print(tfm.dfs['BIOTA'].head())

# %% [markdown]
# ## Add Taxon Information

# %%
#| export
TAXON_MAP = {
    'Taxonname': 'TAXONNAME',
    'Taxonrank': 'TAXONRANK',
    'TaxonDB': 'TAXONDB',
    'TaxonDBID': 'TAXONDBID',
    'TaxonDBURL': 'TAXONDBURL'
}


# %%
#| export
def get_taxon_info_lut(maris_lut: str, key_names: dict = TAXON_MAP) -> dict:
    "Create lookup dictionary for taxon information from MARIS species lookup table."
    species = pd.read_excel(maris_lut)
    # Select columns and rename them to standardized format
    columns = ['species_id'] + list(key_names.keys())
    df = species[columns].rename(columns=key_names)
    return df.set_index('species_id').to_dict()

lut_taxon = lambda: get_taxon_info_lut(maris_lut=lut_fname('SPECIES'), key_names=TAXON_MAP)


# %%
#| export
class AddTaxonInformationCB(Callback):
    """Add taxon information to BIOTA group based on species lookup table."""
    
    def __init__(self, 
                fn_lut: Callable = lut_taxon,  # Function that returns taxon lookup dictionary
                verbose: bool = False
                ):
        fc.store_attr()
        
    def __call__(self, tfm: Transformer):
        """Delegate tasks to add taxon information to the BIOTA group."""
        if not self.check_biota_group_exists(tfm):
            return
        
        df = tfm.dfs['BIOTA']
        if not self.check_species_column_exists(df):
            return
        
        self.add_taxon_columns(df)

    def check_biota_group_exists(self, tfm: Transformer) -> bool:
        """Check if 'BIOTA' group exists in the dataframes."""
        if 'BIOTA' not in tfm.dfs:
            if self.verbose:
                print("No BIOTA group found, skipping taxon information")
            return False
        return True

    def check_species_column_exists(self, df: pd.DataFrame) -> bool:
        """Check if 'SPECIES' column exists in the BIOTA dataframe."""
        if 'SPECIES' not in df.columns:
            if self.verbose:
                print("No SPECIES column found in BIOTA dataframe, skipping taxon information")
            return False
        return True

    def add_taxon_columns(self, df: pd.DataFrame):
        """Add taxon information columns to the BIOTA dataframe."""
        lut = self.fn_lut()
        
        # Add each column from the lookup table
        for col in lut.keys():
            df[col] = df['SPECIES'].map(lut[col]).fillna('Unknown')
        
        self.report_unmatched_species(df)

    def report_unmatched_species(self, df: pd.DataFrame):
        """Report any species IDs not found in the lookup table."""
        unmatched = df[df['TAXONNAME'] == 'Unknown']['SPECIES'].unique()
        if self.verbose and len(unmatched) > 0:
            print(f"Warning: Species IDs not found in lookup table: {', '.join(map(str, unmatched))}")


# %%
#| eval: false
contents = ExtractNetcdfContents(fname_in)
tfm = Transformer(
    data=contents.dfs,
    custom_maps=contents.custom_maps,
    cbs=[
        AddTaxonInformationCB(
            fn_lut=lut_taxon
        ),
    ]
)

tfm()


# %% [markdown]
# ## Standardize Time

# %%
#| eval: false
contents = ExtractNetcdfContents(fname_in)
tfm = Transformer(
    data=contents.dfs,
    custom_maps=contents.custom_maps,
    cbs=[
        DecodeTimeCB(),
    ]
)

tfm()

print(tfm.dfs['SEAWATER']['TIME'])


# %% [markdown]
# ## Add Sample Type ID

# %%
#| eval: false
contents = ExtractNetcdfContents(fname_in)
tfm = Transformer(
    data=contents.dfs,
    custom_maps=contents.custom_maps,
    cbs=[
        AddSampleTypeIdColumnCB(),
    ]
)

tfm()
print(tfm.dfs['SEAWATER']['SAMPLE_TYPE'].unique())
# print(tfm.dfs['BIOTA']['SAMPLE_TYPE'].unique())
# print(tfm.dfs['SEDIMENT']['SAMPLE_TYPE'].unique())


# %% [markdown]
# ## Add Reference ID
#

# %% [markdown]
# Include the `ref_id` (i.e., Zotero Archive Location). The `ZoteroArchiveLocationCB` performs a lookup of the Zotero Archive Location based on the `Zotero key` defined in the global attributes of the MARIS NetCDF file as `id`.

# %%
#| eval: false
contents.global_attrs['id']


# %%
#| export
class AddZoteroArchiveLocationCB(Callback):
    "Fetch and append 'Loc. in Archive' from Zotero to DataFrame."
    def __init__(self, attrs: str):
        fc.store_attr()

    def __call__(self, tfm):
        zotero_key = self.attrs['id']
        item = ZoteroItem(zotero_key, ZOTERO_LIB_ID, os.getenv('ZOTERO_API_KEY'))
        if item.exist():
            loc_in_archive = item.item['data']['archiveLocation'] 
            for grp, df in tfm.dfs.items():
                df['REF_ID'] = int(loc_in_archive)
        else:
            print(f"Warning: Zotero item {zotero_key} does not exist.")


# %%
#| eval: false
contents = ExtractNetcdfContents(fname_in)
tfm = Transformer(
    data=contents.dfs,
    custom_maps=contents.custom_maps,
    cbs=[
        AddZoteroArchiveLocationCB(contents.global_attrs),
    ]
)
tfm()
print(tfm.dfs['SEAWATER']['REF_ID'].unique())

# %% [markdown]
# ## Remap to Open Refine specific mappings

# %% [markdown]
# :::{.callout-warning}
# ## FEEDBACK FOR NEXT VERSION 
#
# [To be further clarified]
#
# The current approach of remapping to OR-specific mappings should be reconsidered. Considering that we already utilize MARISCO lookup tables in NetCDF for creating enums, it would be beneficial to extend their use to OpenRefine data formats as well. By doing so, we could eliminate the need for OpenRefine-specific mappings, streamlining the data transformation process. Lets review the lookup tables used to create the enums for NetCDF:
#
# :::

# %%
#| eval: false
enums = Enums(lut_src_dir=lut_path())
print(f'DL enums: {enums.types["DL"]}')
print(f'FILT enums: {enums.types["FILT"]}')

# %% [markdown]
# For the detection limit lookup table (LUT), as shown below, the values required for the OpenRefine CSV format are listed under the 'name' column, whereas the enums utilize the 'name_sanitized' column. 
#
# Additionally, for the filtered LUT, also shown below, the values do not align consistently with the OpenRefine CSV format, which uses (`Y`, `N`, `NA`).

# %%
#| eval: false
dl_lut = pd.read_excel(detection_limit_lut_path())
dl_lut

# %%
#| eval: false
filtered_lut = pd.read_excel(lut_fname('FILT'))
filtered_lut

# %% [markdown]
# We will create OpenRefine specific mappings for the detection limit and filtered data:

# %%
#| export
or_mappings={'DL':
                {3:'ND',1:'=',2:'<'},
            'FILT':
                {0:'NA',1:'Y',2:'N'},
            }


# %% [markdown]
# RemapToORSpecificMappingsCB remaps the values of the detection limit and filtered data to the OpenRefine CSV format. 

# %%
#| export
class RemapToORSpecificMappingsCB(Callback):
    "Convert values using OR mappings if columns exist in dataframe."
    def __init__(self, 
                or_mappings: Dict[str, Dict] = or_mappings,  # Dictionary of column mappings, 
                output_format: str = 'openrefine_csv',
                verbose: bool = False
                ):
        fc.store_attr()
        
    def __call__(self, tfm: Transformer):
        """Apply OR mappings to all dataframes."""
        for group_name in tfm.dfs:
            if self.verbose:
                print(f"\nProcessing {group_name} group...")
            tfm.dfs[group_name] = self._apply_mappings(tfm.dfs[group_name])
            
    def _apply_mappings(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply OR mappings to columns that exist in the dataframe."""
        for col, mapping in self.or_mappings.items():
            if col in df.columns:
                if self.verbose:
                    print(f"    Mapping values for column: {col}")
                df[col] = df[col].map(mapping)
        return df



# %%
#| eval: false
contents = ExtractNetcdfContents(fname_in)
tfm = Transformer(
    data= contents.dfs,
    custom_maps=contents.custom_maps,
    cbs=[
        RemapToORSpecificMappingsCB(),
    ]
)

tfm()

# Loop through each group in the 'dfs' dictionary
for group_name, df in tfm.dfs.items():
    # Check if the group dataframe contains any of the columns specified in or_mappings.keys()
    relevant_columns = [col for col in or_mappings.keys() if col in df.columns]
    if relevant_columns:
        # Print the unique values from the relevant columns
        print(f"\nUnique values in {group_name} for columns {relevant_columns}:")
        for col in relevant_columns:
            print(f"{col}: {df[col].unique()}")
    else:
        print(f"No relevant columns found in {group_name} based on or_mappings keys.")

# %% [markdown]
# ## Remap to CSV data type format

# %% [markdown]
# `CSV_DTYPES` (defined in configs.ipynb) defines a state for each variable that contains a lookup table (i.e. enums). The state is either 'decoded' or 'encoded'. Lets review the variable states as a DataFrame:

# %%
#| eval: false
with pd.option_context('display.max_columns', None, 'display.max_colwidth', None):
    display(pd.DataFrame.from_dict(CSV_DTYPES, orient='index').T)

# %%
#| eval: false
enums = Enums(lut_src_dir=lut_path())
enums.types.keys()


# %%
#| export
def get_excluded_enums(output_format: str = 'openrefine_csv') -> dict:
    "Get excluded enums based on output format."
    return or_mappings if output_format == 'openrefine_csv' else {}


# %%
#| export
class DataFormatConversionCB(Callback):
    """
    A callback to convert DataFrame enum values between encoded and decoded formats based on specified settings.
    """

    def __init__(self, 
                 dtypes: Dict,  # Dictionary defining data types and states for each lookup table
                 excluded_mappings: Callable = get_excluded_enums,  # Dictionary of columns to exclude from conversion
                 output_format: str = 'openrefine_csv',
                 verbose: bool = False  # Flag for verbose output
                ):
        fc.store_attr()

    def __call__(self, tfm):
        """
        Apply the data format conversion to each DataFrame within the Transformer.
        """
        self.load_enums()
        
        for group_name, df in tfm.dfs.items():
            tfm.dfs[group_name] = self.process_dataframe(group_name, df)

    def load_enums(self):
        """
        Load enums from the lookup path.
        """
        self.enums = Enums(lut_path())
        if self.verbose:
            print(f"Loaded enums: {self.enums.types.keys()}")

    def process_dataframe(self, group_name: str, df: pd.DataFrame):
        """
        Process each DataFrame to convert columns to the target state.
        """
        for column in df.columns:
            if column in self.dtypes and column not in self.excluded_mappings(self.output_format):
                if self.dtypes[column]['state'] == 'decoded':
                    if self.verbose:
                        print(f"Decoding column: {column}")
                    if column in self.enums.types:
                        # Apply the mapping from encoded to decoded values
                        df[column] = df[column].map(self.enums.types[column])
                        if self.verbose:
                            print(f"Decoded column: {column}")
                    else:
                        if self.verbose:
                            print(f"No enum mapping found for column: {column}, skipping decoding.")
        return df


# %%
#| eval: false
contents = ExtractNetcdfContents(fname_in)
tfm = Transformer(
    contents.dfs,
    cbs=[
        RemoveNonCompatibleVariablesCB(vars=CSV_VARS, verbose=True),
        DataFormatConversionCB(
            dtypes=CSV_DTYPES,
            excluded_mappings = get_excluded_enums,
            output_format='openrefine_csv',
            verbose=True
        ),
    ]
)
tfm()

# %% [markdown]
# ## Review all callbacks

# %%
#| eval: false
contents = ExtractNetcdfContents(fname_in)
output_format = 'openrefine_csv'
tfm = Transformer(
    data=contents.dfs,
    custom_maps=contents.custom_maps,
    cbs=[
        ValidateEnumsCB(
            contents = contents,
            maris_enums=Enums(lut_src_dir=lut_path())
        ),
        RemoveNonCompatibleVariablesCB(vars=CSV_VARS),
        # SampleIDConversionCB(nonify=False),
        # RemapCustomMapsCB(),
        RemapToORSpecificMappingsCB(output_format=output_format),
        AddTaxonInformationCB(
            fn_lut=lut_taxon
        ),
        DecodeTimeCB(),
        AddSampleTypeIdColumnCB(),
        AddZoteroArchiveLocationCB(contents.global_attrs),
        DataFormatConversionCB(
            dtypes=CSV_DTYPES,
            excluded_mappings = get_excluded_enums,
            output_format=output_format,
        ) 
        ]
)
tfm()
for grp in ['SEAWATER', 'BIOTA']:
    display(Markdown(f"<b>Head of the transformed `{grp}` DataFrame:</b>"))
    with pd.option_context('display.max_rows', None):
        display(tfm.dfs[grp].head())


# %% [markdown]
# ## Decode   

# %%
#| export
def decode(
    fname_in: str, # Input file name
    dest_out: str | None = None, # Output file name (optional)
    output_format: str = 'openrefine_csv', # Output format
    remap_vars: Dict[str, str] = CSV_VARS, # Mapping of OR vars to NC vars
    remap_dtypes: Dict[str, str] = CSV_DTYPES, # Mapping of OR vars to NC dtypes
    # has_smp_id: bool = True, # If False, do not convert auto-generated `SMP_ID` values to `None`
    verbose: bool = False, # If True, print verbose output
    **kwargs # Additional arguments
    ) -> None:
    "Decode data from NetCDF."
    valid_output_formats=['openrefine_csv', 'decoded_csv']
    
    if output_format not in valid_output_formats:
        print (f'Invalid output format. Allowed formats: {valid_output_formats}')
        return 
    
    if output_format == 'decoded_csv':
        remap_dtypes = {k: {'state': 'decoded'} for k in remap_dtypes.keys()}
        
    contents = ExtractNetcdfContents(fname_in)
    tfm = Transformer(
        data=contents.dfs,
        custom_maps=contents.custom_maps,
        cbs=[
        ValidateEnumsCB(
            contents = contents,
            maris_enums=Enums(lut_src_dir=lut_path())
        ),
        RemoveNonCompatibleVariablesCB(vars=remap_vars),
        # SampleIDConversionCB(nonify=not has_smp_id),
        # RemapCustomMapsCB(),
        RemapToORSpecificMappingsCB(output_format=output_format),
        AddTaxonInformationCB(
            fn_lut=lut_taxon
        ),
        DecodeTimeCB(),
        AddSampleTypeIdColumnCB(),
        AddZoteroArchiveLocationCB(contents.global_attrs),
        DataFormatConversionCB(
            dtypes=remap_dtypes,
            excluded_mappings = get_excluded_enums,
            output_format=output_format
        ) 
        ]
    )    
    
    tfm()
    decoder = NetCDFDecoder( 
                            dfs=tfm.dfs,
                            fname_in=fname_in,  
                            dest_out=dest_out,                           
                            output_format='csv',
                            # remap_vars=CSV_VARS,
                            remap_vars=remap_vars,
                            verbose=verbose
                    )
    decoder.decode()


# %%
#|eval: false
fname = Path('../../_data/output/100-HELCOM-MORS-2024.nc')
decode(fname_in=fname, dest_out=fname.with_suffix(''), output_format='openrefine_csv')
