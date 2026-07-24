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
#| default_exp metadata

# %% [markdown]
# # Metadata
# > Callbacks to populate NetCDF global attributes.

# %% [markdown]
# Covers four concerns:
#
# - **Spatial/temporal coverage** — bounding box and time range derived from the data
# - **Zotero** — bibliographic metadata fetched from the IAEA Zotero group library
# - **INIS** — bibliographic metadata fetched from the IAEA InvenioRDM-based INIS API
# - **Static key-value pairs** — arbitrary fixed attributes (e.g. `keywords`, `publisher`)

# %%
#| export
import os
import shutil
import subprocess, json
import pandas as pd
from fastcore.all import *
from cftime import num2date
from pyzotero import zotero, zotero_errors

from urllib.error import HTTPError, URLError
from urllib.request import urlopen
import subprocess

import json
from typing import Dict, List, Callable
from marisco.geo import get_bbox 
from marisco.configs import get_time_units, ZOTERO_LIB_ID, NC_GLOBAL_ATTRS
from marisco.callbacks import run_cbs, Callback

# %%
#| eval: false
from nbdev.showdoc import show_doc


# %% [markdown]
# ## Global attributes feeder

# %% [markdown]
# `GlobAttrsFeeder` follows the same callback pattern as `marisco.callbacks.Transformer`: it takes a list of `Callback` objects, runs them in order, and collects their results into an `attrs` dict. Each callback below contributes one piece of the NetCDF global metadata.

# %%
#| export
class GlobAttrsFeeder:
    "Produce NetCDF global attributes as specified by the callbacks."
    def __init__(self, 
                 dfs: Dict[str, pd.DataFrame], # Dictionary of NetCDF group DataFrames
                 cbs: List[Callback]=None, # Callbacks
                 logs: List[str]=None # List of preprocessing steps taken
                 ) -> None:
        store_attr()
        if self.cbs is None: self.cbs = []
        if self.logs is None: self.logs = []
        self.attrs = {}
        
    def callback(self):
        run_cbs(self.cbs, self)
        
    def __call__(self):
        self.callback()
        unknown = set(self.attrs.keys()) - NC_GLOBAL_ATTRS
        if unknown: raise KeyError(
            f"Unknown NetCDF global attribute(s): {', '.join(sorted(unknown))}. "
            f"Add to NC_GLOBAL_ATTRS in configs if intentional.")
        return self.attrs



# %% [markdown]
# ## Spatial and temporal coverage

# %%
#| export
class BboxCB(Callback):
    "Compute dataset geographical bounding box"
    def __call__(self, obj):
        bbox = get_bbox(pd.concat(obj.dfs))
        lon_min, lat_min, lon_max, lat_max = [str(bound) for bound in bbox.bounds]
        obj.attrs.update({
            'geospatial_lat_min': lat_min, 
            'geospatial_lat_max': lat_max,
            'geospatial_lon_min': lon_min,
            'geospatial_lon_max': lon_max,
            'geospatial_bounds': bbox.wkt})


# %%
mock_dfs = {
    'SEAWATER': pd.DataFrame({'LON': [10.0, 20.0], 'LAT': [30.0, 40.0]})
}
feed = GlobAttrsFeeder(mock_dfs, cbs=[BboxCB()])
attrs = feed()

test_eq(attrs['geospatial_lat_min'], '30.0')
test_eq(attrs['geospatial_lat_max'], '40.0')
test_eq(attrs['geospatial_lon_min'], '10.0')
test_eq(attrs['geospatial_lon_max'], '20.0')
test_eq(attrs['geospatial_bounds'], 'POLYGON ((10 30, 20 30, 20 40, 10 40, 10 30))')


# %%
#| export
class DepthRangeCB(Callback):
    "Compute minimum and maximum depth values"
    def __init__(self, 
                 depth_col: str='SMP_DEPTH' # Column name for sampling depth values
                ): 
        store_attr()
    def __call__(self, obj):
        depths = pd.concat(obj.dfs).get(self.depth_col, default=pd.Series([]))
        if not depths.empty:
            obj.attrs.update({
                'geospatial_vertical_max': str(depths.max()),
                'geospatial_vertical_min': str(depths.min())})


# %%
mock_dfs = {'SEDIMENT': pd.DataFrame({'SMP_DEPTH': [5.0, 200.0]})}
feed = GlobAttrsFeeder(mock_dfs, cbs=[DepthRangeCB()])
test_eq(feed()['geospatial_vertical_min'], '5.0')
test_eq(feed()['geospatial_vertical_max'], '200.0')


# %%
#| export
class TimeRangeCB(Callback):
    "Decode the min/max of the NetCDF-encoded TIME column into ISO date strings for global attributes"
    def __init__(self, 
                 time_col: str='TIME',         # Column name for time values
                 fn_time_unit: Callable=get_time_units  # Function returning the NetCDF time unit string
                ): 
        store_attr()
        self.time_unit = fn_time_unit()
    
    def __call__(self, obj):
        time = pd.concat(obj.dfs)[self.time_col]
        start, end = [num2date(t, units=self.time_unit).isoformat() 
                      for t in (time.min(), time.max())]
        obj.attrs.update({
            'time_coverage_start': start,
            'time_coverage_end': end})


# %%
mock_dfs = {'SEAWATER': pd.DataFrame({'TIME': [1.0, 365.0]})}
feed = GlobAttrsFeeder(mock_dfs, cbs=[TimeRangeCB()])
attrs = feed()
test_eq(attrs['time_coverage_start'], '1970-01-01T00:00:01')  # 1 s after Unix epoch
test_eq(attrs['time_coverage_end'], '1970-01-01T00:06:05')   # 365 s after Unix epoch


# %% [markdown]
# ## Bibliographic metadata
#
# Every curated dataset in MARIS needs bibliographic metadata (title, abstract, creators, DOI, ...) stored as global attributes in the NetCDF file produced by each dataset handler (e.g. the [Geotraces handler](https://fr.anckalbi.net/marisco/handlers/geotraces.html)). MARIS previously managed this metadata through the IAEA's Zotero group library, but the IAEA's own [INIS](https://inis.iaea.org) bibliographic database is now the target single source of truth; migration is ongoing.
#
# Both `ZoteroCB` and `InisCB` below produce the same core set of global attributes (`id`, `title`, `summary`, `creator_name`), making them interchangeable in a handler's callback pipeline. `InisCB` additionally injects `references` (DOI) and `metadata_link` (record URL). The attribute set is not locked; additional bibliographic fields can be added as future needs arise.

# %% [markdown]
# ### Zotero

# %% [markdown]
# Bibliographic metadata for each dataset is managed in the IAEA's Zotero group library. `ZoteroClient` is a lightweight client to fetch individual records; `ZoteroCB` wraps it into a callback that populates `id`, `title`, `summary`, and `creator_name` global attributes.

# %%
#| export
class ZoteroClient:
    "Zotero API client to fetch a bibliographic record."
    def __init__(self, 
                 item_id: str, # Zotero item key to retrieve
                 lib_id: str,  # Zotero library ID
                 api_key: str  # Zotero API key
                ) -> None:
        store_attr()
        try: self.item = self.get_item(item_id)
        except Exception: self.item = None
    
    def exist(self) -> bool: return self.item is not None
    
    def get_item(self, item_id:str  # Zotero item key to retrieve
               ) -> dict|None:      # Zotero item dict, or None if not found
        zot = zotero.Zotero(self.lib_id, 'group', self.api_key)
        try:
            return zot.item(item_id)
        except zotero_errors.ResourceNotFoundError:
            print(f'Item {item_id} does not exist in Zotero library')
            return None
            
    def _get(self, key:str  # Zotero data key to retrieve
            ) -> str:       # Value for that key, or '' if item not loaded
        return self.item['data'][key] if self.item else ''

    @property
    def title(self) -> str: return self._get('title')

    @property
    def summary(self) -> str: return self._get('abstractNote')

    @property
    def creator_name(self) -> str: return json.dumps(self._get('creators'))

    def __repr__(self): return json.dumps(self.item, indent=4)


# %% [markdown]
# Read-only properties (all return `str`): `title`, `summary`, `creator_name` (JSON-encoded list) — derived from the fetched Zotero record.

# %%
#|eval: false
item = ZoteroClient('26VMZZ2Q', ZOTERO_LIB_ID, os.getenv('ZOTERO_API_KEY'))
test_eq(item.title, 'Environmental database - Helsinki Commission Monitoring of Radioactive Substances')

# %%
#|eval: false
test_eq(item.summary[:30], 'MORS Environment database has ') 

# %%
#|eval: false
creators = json.loads(item.creator_name)
test_eq(len(creators), 1)
test_eq(creators[0]['creatorType'], 'author')


# %%
#| export
class ZoteroCB(Callback):
    "Populate global attributes from Zotero bibliographic metadata."
    def __init__(self, 
                 itemId,   # Zotero item key to retrieve
                ): store_attr()
    def __call__(self, obj):
        item = ZoteroClient(self.itemId, ZOTERO_LIB_ID, os.getenv('ZOTERO_API_KEY'))
        if item.exist(): 
            obj.attrs['id'] = item.item['key']
            for attr in ['title','summary', 'creator_name']:
                obj.attrs[attr] = getattr(item, attr)


# %%
#|eval: false
attrs = GlobAttrsFeeder(None, cbs=[
    ZoteroCB('26VMZZ2Q')
    ])()
    
test_eq(attrs['id'], '26VMZZ2Q')
test_eq(attrs['title'], 'Environmental database - Helsinki Commission Monitoring of Radioactive Substances')

# %%
#|eval: false
attrs = GlobAttrsFeeder(None, cbs=[
    ZoteroCB('3W354SQG')
    ])()
    
test_eq(attrs['id'], '3W354SQG')

# %%
#|eval: false
attrs = GlobAttrsFeeder(None, cbs=[
    ZoteroCB('x')
    ])()
    
test_eq(attrs, {})

# %% [markdown]
# ### INIS

# %% [markdown]
# Bibliographic metadata can also be fetched from the IAEA's InvenioRDM-based INIS API. `INISClient` is a lightweight client to fetch individual records; `InisCB` wraps it into a callback that populates `id`, `title`, `summary`, and `creator_name` global attributes, and can also inject `references` and `metadata_link` from the record's DOI and web URL.

# %%
#| exports
INIS_QA_API = "https://inis-qa.iaea.org/api/records"
INIS_API = "https://inis.iaea.org/api/records"


# %%
#| export
def fetch_inis(
    inis_id:str,   # INIS record identifier (e.g. 'vq0ha-86k24')
    base_url:str=INIS_API # API base URL
    ) -> dict:    # Raw INIS record payload
    "Fetch an INIS record from the InvenioRDM API via curl."
    url = f"{base_url}/{inis_id}"
    r = subprocess.run([find_curl(), '-sS', '-H', 'Accept: application/json', url],
                       capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


# %%
#| export
def find_curl() -> str:
    "Return path to curl, or raise FileNotFoundError."
    path = shutil.which('curl')
    if not path: raise FileNotFoundError(
        "curl not found. Install curl (https://curl.se) — it's required to fetch INIS records.")
    return path


# %%
#| export
class INISClient:
    "Retrieve INIS metadata from the InvenioRDM API."
    def __init__(self,
                 inis_id:str,   # INIS record identifier (e.g. 'vq0ha-86k24')
                 base_url:str=INIS_API # API base URL
                 ) -> None:
        store_attr()
        try: self.item = fetch_inis(inis_id, base_url)
        except Exception: self.item = None

    def exist(self) -> bool:
        "Does the record exist? The API returns {'status': 404, ...} (not an HTTP 404) for missing IDs, so check for a top-level 'id' key rather than relying on an exception."
        return self.item is not None and 'id' in self.item

    @property
    def title(self) -> str:
        if not self.item: return ''
        t = self.item.get('metadata', {}).get('title', '') or ''
        if isinstance(t, str): return t
        return t.get('en') or next((v for v in t.values() if v), '')

    @property
    def summary(self) -> str:
        if not self.item: return ''
        d = self.item.get('metadata', {}).get('description', '') or ''
        if isinstance(d, str): return d
        return d.get('en') or next((v for v in d.values() if v), '')

    @property
    def doi(self) -> str:
        if not self.item: return ''
        doi = self.item.get('pids', {}).get('doi', {})
        if isinstance(doi, dict): doi = doi.get('identifier') or ''
        if doi: return doi
        for ident in self.item.get('metadata', {}).get('identifiers', []):
            if ident.get('scheme') == 'doi': return ident.get('identifier', '')
        return ''

    @property
    def creator_name(self) -> str:
        if not self.item: return ''
        return json.dumps(self.item.get('metadata', {}).get('creators', []), ensure_ascii=True)

    @property
    def url(self) -> str:
        if not self.item: return ''
        links = self.item.get('links', {})
        return links.get('self_html') or links.get('latest_html') or links.get('self', '')


# %% [markdown]
# Read-only properties (all return `str`): `title`, `summary`, `doi`, `creator_name` (JSON-encoded list), `url` — derived from the fetched INIS record; return `''` when the record does not exist.

# %%
#|eval: false
inis = INISClient('5smfm-0a377')
test_eq(inis.title, 'The GEOTRACES Intermediate Data Product 2017')
test_eq(inis.exist(), True)

# %%
#|eval: false
test_eq(inis.summary[:30], 'The GEOTRACES Intermediate Dat')

# %%
#|eval: false
test_eq(inis.doi, '10.1016/j.chemgeo.2018.05.040')

# %%
#|eval: false
# Test a record without DOI (g7wwp-fcc77 is a test record with no DOI) on QA instance
no_doi = INISClient('g7wwp-fcc77', base_url=INIS_QA_API)
test_eq(no_doi.doi, '')
test_eq(no_doi.exist(), True)

# %%
#|eval: false
creators = json.loads(inis.creator_name)
test_eq(len(creators), 286)
test_eq(creators[0]['person_or_org']['family_name'], 'Schlitzer')

# %%
#|eval: false
test_eq(inis.url, 'https://inis.iaea.org/records/5smfm-0a377')

# %%
#|eval: false
# Test non-existent record
nonexistent = INISClient('this-does-not-exist')
test_eq(nonexistent.exist(), False)
test_eq(nonexistent.title, '')
test_eq(nonexistent.doi, '')


# %%
#| export
class InisCB(Callback):
    "Populate global attributes from INIS metadata."
    def __init__(self,
                 inis_id:str, # INIS record identifier to retrieve
                 base_url:str=INIS_API # API base URL
                ): store_attr()
    def __call__(self, obj):
        item = INISClient(self.inis_id, self.base_url)
        if item.exist():
            obj.attrs['id'] = self.inis_id
            for attr in ['title', 'summary', 'creator_name']:
                obj.attrs[attr] = getattr(item, attr)
            if item.doi: obj.attrs['references'] = item.doi
            if item.url: obj.attrs['metadata_link'] = item.url


# %%
#|eval: false
# Integration test: InisCB fills correct attrs
class AttrSink:
    def __init__(self): self.attrs = {}

sink = AttrSink()
InisCB('5smfm-0a377')(sink)
test_eq(sink.attrs['id'], '5smfm-0a377')
test_eq(sink.attrs['title'], 'The GEOTRACES Intermediate Data Product 2017')
test_eq(sink.attrs['references'], '10.1016/j.chemgeo.2018.05.040')
test_eq(sink.attrs['metadata_link'], 'https://inis.iaea.org/records/5smfm-0a377')
creators = json.loads(sink.attrs['creator_name'])
test_eq(len(creators), 286)
test_eq(set(sink.attrs.keys()), {'id', 'title', 'summary', 'creator_name', 'references', 'metadata_link'})


# %%
#|eval: false
# Test InisCB handles non-existent records gracefully
sink2 = AttrSink()
InisCB('this-does-not-exist')(sink2)
test_eq(sink2.attrs, {})


# %% [markdown]
# ## Static global attributes

# %%
#| export
class KeyValuePairCB(Callback):
    "Add a single key-value pair as a NetCDF global attribute."
    def __init__(self, 
                 k, # NetCDF global attribute key name
                 v  # NetCDF global attribute value
                ): store_attr()
    def __call__(self, obj): obj.attrs[self.k] = self.v


# %% [markdown]
# For static global attributes that don't derive from data — like a `keywords` string or a `publisher` name — `KeyValuePairCB` wraps a simple key-value pair into a callback, keeping the interface uniform.

# %% [markdown]
# ## Usage

# %%
#|eval: false
dfs = pd.read_pickle('../files/pkl/dfs_test.pkl')

# %%
#|eval: false
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
#|eval: false
feed = GlobAttrsFeeder(dfs, cbs=[
    BboxCB(),
    DepthRangeCB(),
    TimeRangeCB(),
    ZoteroCB('26VMZZ2Q'),
    KeyValuePairCB('keywords', ', '.join(kw))
    ])
attrs = feed()
attrs
