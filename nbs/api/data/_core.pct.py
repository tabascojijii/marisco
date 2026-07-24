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
#| default_exp data.core

# %% [markdown]
# # Data core
#
# > Core functionality to transform and gather data

# %%
#|export
from __future__ import annotations
from fastcore.basics import store_attr
import pandas as pd
import re
from pathlib import Path
from tqdm import tqdm


# %% [markdown]
# ## DumpExploder

# %%
#|export
class DumpExploder():
    """Exploding MARIS global .csv dump into distinct dataset-specific ones..."""
    def __init__(self, 
                 fname:str, # File name path and name
                 dst:str, # Path of folder that will receive created .csv
                 col_id:str='ref_id', # Name of the unique id column in loaded .csv
                 #cols_name:List[str]=['displaytext'] # Columns name as part of file name generated
                cols_name=['displaytext'] # Columns name as part of file name generated
                ):
        store_attr()
        self.df = self.load_data()
        self.dst = Path(dst)
        self.cols = [col_id] + cols_name
        
    def load_data(self):
        self.df = pd.read_csv(Path(self.fname))   
        return self.df
    
    def num_ds(self, verbose:Bool=False):
        if self.df is None:
            raise Exception('Run `.loadData() first: no data loaded yet')
        print(f'Number of distinct datasets: {len(self.df[self.col_id].unique())}')
        if verbose:
            print(self.df.drop_duplicates(subset=[self.col_id])[self.cols])     
    
    def explode(self):
        if self.df is None:
            self.loadData()
        grouped = self.df.groupby(self.col_id)
        print('Exploding MARIS global csv dump into distinct dataset-specific ones...')
        for _, group in tqdm(grouped):
            name = self._namer(group)
            group.to_csv(self.dst/name, index=False)

    def _namer(self, group):
        cols_name = group[self.cols].drop_duplicates().values[0]
        cols_name = [str(s) for s in cols_name]
        name = '-'.join(cols_name)
        return re.sub(r'\W+', '-', name).lower() + '.csv'


# %% [markdown]
# A bit of description ...

# %%
fname = '../files/csv/maris-dump-test.csv'
dst = 'files/exploded'

exploder = DumpExploder(fname, dst)

# %%
df = exploder.load_data()
print('Dataframe shape: ', df.shape)
print('Columns list', df.columns)

# %%
exploder.num_ds(verbose=True)

# %%
exploder.explode()

# %% [markdown]
# ## Rules

# %%
