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

# %% [markdown]
# # Enum rules

# %% [markdown]
# Enums are created from a lookup table (LUT) to map the values in the source data to the values in the NetCDF file. An Enum can be created using the ``nc.createEnumType`` method. The createEnumType(self, datatype, datatype_name, enum_dict) method requires three arguments:
#
# - ``datatype``: The data type of the enum, e.g. ``np.int64``.
# - ``datatype_name``: The name of the enum, e.g. ``'sed_type_t'``.
# - ``enum_dict``: A dictionary that maps the values in the source data to the values in the NetCDF file, e.g. ``{'Not applicable': -1, 'Not available': 0, 'Clay': 1, 'Gravel': 2, ...}``.
#
# The key of the enum_dict dictionary cannot contain illegal characters. 

# %% [markdown]
# Illegal Characters and Constraints:
#
# Special Characters:
#
#      Names cannot include the characters:
#           / (forward slash)
#          \ (backslash)
#         - . (dot) at the beginning of a name
#         - @ (at symbol)
#         - : (colon)
#         - Control characters (ASCII codes 0–31 and 127)
#
# Reserved Characters:
#
#     Names starting with _ are reserved for system use in certain NetCDF conventions.

# %% [markdown]
# Lets write a function that checks if the key of the enum_dict dictionary contains illegal characters or reserved characters.

# %%
#| eval: false
import pandas as pd
from marisco.configs import NC_DTYPES, lut_path


# %%
#| eval: false
def check_lut_characters():
    illegal_chars = ['\\', '@', ':', '•', '"'] + [chr(i) for i in range(32)] + [chr(127)]
    reserved_start_char = '_'
    print('illegal_chars', illegal_chars)
    for lut_name, lut_details in NC_DTYPES.items():
        print(lut_name)
        # Construct the file path
        file_path = lut_path() / lut_details['fname']
        
        # Read the Excel file into a DataFrame
        df = pd.read_excel(file_path)
        
        # Construct enum_dict using the specified columns for keys and values
        enum_dict = {df[lut_details['key']][i]: df[lut_details['value']][i] for i in df.index}
        # Check each key in the enum_dict
        for key in enum_dict.keys():
            
            key_str = str(key)  # Ensure the key is a string for checks
            if any(char in key_str for char in illegal_chars):
                print(f"Key '{key_str}' in LUT '{lut_name}' contains an illegal character.")
            if key_str.startswith(reserved_start_char):
                print(f"Key '{key_str}' in LUT '{lut_name}' starts with a reserved character.")


# %%
#| eval: false
check_lut_characters()

# %%
