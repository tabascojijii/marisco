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
# # Data curation rules

# %% [markdown]
# > What are the data curation rules applied to MARIS data compilation?

# %% [markdown]
# This document outlines the rules and guidelines followed when curating data in the MARIS database, including:
# - Data validation criteria
# - Quality control measures
# - Standardization procedures
# - Handling of duplicate measurements
# - Treatment of missing values

# %% [markdown]
# ## Sample preparation methods

# %% [markdown]
# At some occasions, `biota` samples measurements are reported both in dry and wet weight for a given `sample` and `nuclide`.
#
# When for a given `sample` and `nuclide`, sample preparation methods are reported, MARIS will follow the following rules:
#
# 1. if sample preparation method is reported as `wet` only, then report measurement on a wet basis (in `Bq/kg wet`)
# 2. if sample preparation method is reported as `dry` only, then report measurement on a dry basis (in `Bq/kg dry`   )
# 3. if sample preparation method is reported as both `wet` and `dry`, then report measurement on a wet basis (in `Bq/kg wet`) but also calculate and report `percent wet weight`.

# %% [markdown]
# WIP ...
