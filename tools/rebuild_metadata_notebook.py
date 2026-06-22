"""
Rebuild nbs/api/metadata.ipynb cleanly:
  1. Load upstream/main baseline from git
  2. Adapt 3 cells to current codebase (imports, GlobAttrsFeeder, ZoteroCB)
  3. Insert Zenodo section additively after InisCB tests
  4. Write with source always as list[str]
"""
import json, subprocess, sys
sys.stdout.reconfigure(encoding='utf-8')

TARGET = 'nbs/api/metadata.ipynb'

# ── helpers ──────────────────────────────────────────────────────────────────

def lines(text):
    """Convert a multi-line string to list[str] with each line ending in \\n,
    except the last line. This is the standard nbformat source representation."""
    raw = text.split('\n')
    out = [l + '\n' for l in raw[:-1]] + ([raw[-1]] if raw[-1] else [])
    if out and out[-1] == '':
        out = out[:-1]
    return out

def code_cell(src, cell_id):
    return {'cell_type': 'code', 'execution_count': None,
            'id': cell_id, 'metadata': {}, 'outputs': [],
            'source': lines(src)}

def md_cell(src, cell_id):
    return {'cell_type': 'markdown', 'id': cell_id,
            'metadata': {}, 'source': lines(src)}

# ── load upstream baseline ────────────────────────────────────────────────────

result = subprocess.run(
    ['git', 'show', 'upstream/main:nbs/api/metadata.ipynb'],
    capture_output=True, check=True
)
nb = json.loads(result.stdout.decode('utf-8'))
cells = nb['cells']
print(f'Loaded upstream baseline: {len(cells)} cells')

# ── verify insertion point ────────────────────────────────────────────────────
for idx, expected in [(40, 'Test InisCB handles'), (41, '## Static global')]:
    src = ''.join(cells[idx]['source'])
    assert expected in src, f'Unexpected cell at [{idx}]: {src[:60]}'
print('Insertion point verified: [40]=InisCB test, [41]=Static global attrs')

# ── Cell [03]: adapt imports for current codebase ────────────────────────────
cells[3]['source'] = lines(
    '#| export\n'
    'import os\n'
    'import shutil\n'
    'import subprocess, json\n'
    'import pandas as pd\n'
    'from fastcore.all import *\n'
    'from cftime import num2date\n'
    'from pyzotero import zotero, zotero_errors\n'
    'import json\n'
    'from typing import Dict, List, Callable\n'
    'from marisco.utils import get_bbox\n'
    'from marisco.configs import get_time_units, cfg\n'
    'from marisco.callbacks import run_cbs, Callback'
)

# ── Cell [07]: GlobAttrsFeeder – drop NC_GLOBAL_ATTRS validation ──────────────
cells[7]['source'] = lines(
    '#| export\n'
    'class GlobAttrsFeeder:\n'
    '    "Produce NetCDF global attributes as specified by the callbacks."\n'
    '    def __init__(self, \n'
    '                 dfs: Dict[str, pd.DataFrame], # Dictionary of NetCDF group DataFrames\n'
    '                 cbs: List[Callback]=None, # Callbacks\n'
    '                 logs: List[str]=None # List of preprocessing steps taken\n'
    '                 ) -> None:\n'
    '        store_attr()\n'
    '        if self.cbs is None: self.cbs = []\n'
    '        if self.logs is None: self.logs = []\n'
    '        self.attrs = {}\n'
    '\n'
    '    def callback(self):\n'
    '        run_cbs(self.cbs, self)\n'
    '\n'
    '    def __call__(self):\n'
    '        self.callback()\n'
    '        return self.attrs'
)

# ── Cell [20]: ZoteroCB – source credentials from cfg() ──────────────────────
cells[20]['source'] = lines(
    '#| export\n'
    'class ZoteroCB(Callback):\n'
    '    "Populate global attributes from Zotero bibliographic metadata."\n'
    '    def __init__(self, \n'
    '                 itemId,   # Zotero item key to retrieve\n'
    '                ): store_attr()\n'
    '    def __call__(self, obj):\n'
    "        c = cfg()['zotero']\n"
    "        item = ZoteroClient(self.itemId, c['lib_id'], c['api_key'])\n"
    '        if item.exist(): \n'
    "            obj.attrs['id'] = item.item['key']\n"
    "            for attr in ['title','summary', 'creator_name']:\n"
    '                obj.attrs[attr] = getattr(item, attr)'
)

# ── Zenodo cells to insert at index 41 ───────────────────────────────────────

zenodo_cells = [
    md_cell(
        '### Zenodo\n'
        '\n'
        'Use this adapter only after upstream discovery has confirmed that the selected `record_id` belongs to the TITANICA community. '
        'It intentionally skips discovery and community validation, and instead performs stable single-record retrieval via '
        '`https://zenodo.org/api/records/{id}` because the community API is a listing/discovery surface rather than a stable single-record contract.\n'
        '\n'
        'The canonical `id` projected into `obj.attrs` remains the selected version-specific Zenodo record id; '
        'this adapter does not chase `conceptrecid` or latest-version redirects.',
        'zenodo-md'
    ),
    code_cell(
        '#| export\n'
        'import httpx\n'
        'from urllib.parse import urlencode\n'
        '\n'
        '# Stable single-record retrieval endpoint; TITANICA community discovery stays upstream.\n'
        "DEFAULT_ZENODO_RECORDS_URL = 'https://zenodo.org/api/records'\n"
        'DEFAULT_ZENODO_TIMEOUT = 10.0\n'
        '\n'
        'class _ZenodoMetadataError(Exception):\n'
        '    "Raised when Zenodo metadata retrieval fails."\n'
        '    pass\n'
        '\n'
        'class _ZenodoMissingRecordError(_ZenodoMetadataError):\n'
        '    "Raised when the selected Zenodo record does not exist."\n'
        '    pass\n'
        '\n'
        'class _ZenodoTransportError(_ZenodoMetadataError):\n'
        '    "Raised when Zenodo transport fails before a valid payload is received."\n'
        '    pass',
        'zenodo-constants'
    ),
    code_cell(
        '#| export\n'
        'def _zenodo_build_client(timeout:float=DEFAULT_ZENODO_TIMEOUT):\n'
        '    return httpx.Client(\n'
        '        timeout=timeout,\n'
        "        headers={'Accept': 'application/json'},\n"
        '        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),\n'
        '    )\n'
        '\n'
        'def _zenodo_find_curl() -> str:\n'
        "    path = shutil.which('curl') or shutil.which('curl.exe')\n"
        "    if not path: raise _ZenodoTransportError('Zenodo metadata retrieval failed: curl not found')\n"
        '    return path\n'
        '\n'
        'def _zenodo_httpx_json(client, url:str, params:dict=None):\n'
        '    try:\n'
        '        response = client.get(url, params=params)\n'
        '        response.raise_for_status()\n'
        '        return response.json()\n'
        '    except httpx.HTTPStatusError as exc:\n'
        "        status_code = exc.response.status_code if exc.response else 'unknown'\n"
        "        if status_code == 404: raise _ZenodoMissingRecordError('Zenodo metadata retrieval failed: record not found') from exc\n"
        "        raise _ZenodoMetadataError(f'Zenodo metadata retrieval failed: HTTP {status_code}') from exc\n"
        '    except (httpx.RequestError, TimeoutError) as exc:\n'
        "        raise _ZenodoTransportError(f'Zenodo metadata retrieval failed: {exc}') from exc\n"
        '    except ValueError as exc:\n'
        "        raise _ZenodoMetadataError('Zenodo metadata retrieval failed: invalid JSON payload') from exc\n"
        '\n'
        'def _zenodo_curl_json(url:str, timeout:float=DEFAULT_ZENODO_TIMEOUT, params:dict=None):\n'
        "    if params: url = f\"{url}?{urlencode(params, doseq=True)}\"\n"
        '    try:\n'
        '        response = subprocess.run(\n'
        "            [_zenodo_find_curl(), '-sS', '-H', 'Accept: application/json', '-w', r'\\n%{http_code}', url],\n"
        "            capture_output=True, text=True, encoding='utf-8', check=True,\n"
        '            timeout=max(1, int(timeout * 4)),\n'
        '        )\n'
        "        body, _, status_line = response.stdout.rstrip('\\n').rpartition('\\n')\n"
        '        status_code = int(status_line)\n'
        "        if status_code == 404: raise _ZenodoMissingRecordError('Zenodo metadata retrieval failed: record not found')\n"
        "        if status_code >= 400: raise _ZenodoMetadataError(f'Zenodo metadata retrieval failed: HTTP {status_code}')\n"
        '        return json.loads(body)\n'
        '    except subprocess.TimeoutExpired as exc:\n'
        "        raise _ZenodoTransportError(f'Zenodo metadata retrieval failed: {exc}') from exc\n"
        '    except subprocess.CalledProcessError as exc:\n'
        "        raise _ZenodoMetadataError('Zenodo metadata retrieval failed: curl returned a non-zero exit code') from exc\n"
        '    except ValueError as exc:\n'
        "        raise _ZenodoMetadataError('Zenodo metadata retrieval failed: invalid curl response payload') from exc\n"
        '\n'
        'def _zenodo_fetch_json(url:str, timeout:float=DEFAULT_ZENODO_TIMEOUT, params:dict=None, client=None):\n'
        '    if client is not None: return _zenodo_httpx_json(client, url, params=params)\n'
        '    httpx_client = _zenodo_build_client(timeout)\n'
        '    try: return _zenodo_httpx_json(httpx_client, url, params=params)\n'
        '    except _ZenodoTransportError: return _zenodo_curl_json(url, timeout=timeout, params=params)\n'
        '    finally: httpx_client.close()\n'
        '\n'
        'def _zenodo_fetch_record(record_id:str,\n'
        '                         record_base_url:str=DEFAULT_ZENODO_RECORDS_URL,\n'
        '                         timeout:float=DEFAULT_ZENODO_TIMEOUT, client=None):\n'
        "    url = f\"{record_base_url.rstrip('/')}/{record_id}\"\n"
        '    return _zenodo_fetch_json(url, timeout=timeout, client=client)',
        'zenodo-transport'
    ),
    code_cell(
        '#| export\n'
        'def _zenodo_as_dict(value): return value if isinstance(value, dict) else {}\n'
        'def _zenodo_as_list(value): return value if isinstance(value, list) else []\n'
        'def _zenodo_pick_text(value):\n'
        '    if isinstance(value, str): return value\n'
        '    if isinstance(value, dict):\n'
        "        if value.get('en'): return value.get('en')\n"
        "        return next((v for v in value.values() if isinstance(v, str) and v), '')\n"
        "    return '' if value is None else str(value)",
        'zenodo-shape-helpers'
    ),
    code_cell(
        '#| export\n'
        'def _zenodo_normalize_creator(creator):\n'
        '    creator = _zenodo_as_dict(creator)\n'
        "    person = _zenodo_as_dict(creator.get('person_or_org'))\n"
        "    name = _zenodo_pick_text(creator.get('name')) or _zenodo_pick_text(person.get('name'))\n"
        "    affiliation = _zenodo_pick_text(creator.get('affiliation')) or _zenodo_pick_text(person.get('affiliation'))\n"
        "    orcid = _zenodo_pick_text(creator.get('orcid'))\n"
        '    if not orcid:\n'
        "        identifiers = _zenodo_as_list(creator.get('identifiers')) or _zenodo_as_list(person.get('identifiers'))\n"
        '        for ident in identifiers:\n'
        '            ident = _zenodo_as_dict(ident)\n'
        "            if _zenodo_pick_text(ident.get('scheme')).lower() == 'orcid':\n"
        "                orcid = _zenodo_pick_text(ident.get('identifier'))\n"
        '                break\n'
        '    cleaned = {}\n'
        "    if name: cleaned['name'] = name\n"
        "    if affiliation: cleaned['affiliation'] = affiliation\n"
        "    if orcid: cleaned['orcid'] = orcid\n"
        '    return cleaned or None\n'
        '\n'
        'def _zenodo_creator_name(creators):\n'
        '    names, seen = [], set()\n'
        '    for creator in _zenodo_as_list(creators):\n'
        '        normalized = _zenodo_normalize_creator(creator)\n'
        '        if not normalized: continue\n'
        '        key = tuple(sorted(normalized.items()))\n'
        '        if key in seen: continue\n'
        '        seen.add(key)\n'
        '        names.append(normalized)\n'
        '    return json.dumps(names, ensure_ascii=True)\n'
        '\n'
        'def _zenodo_doi(record, metadata):\n'
        "    doi = _zenodo_pick_text(record.get('doi')) or _zenodo_pick_text(metadata.get('doi'))\n"
        '    if doi: return doi\n'
        "    pids = _zenodo_as_dict(record.get('pids'))\n"
        "    return _zenodo_pick_text(_zenodo_as_dict(pids.get('doi')).get('identifier'))\n"
        '\n'
        'def _zenodo_url(record):\n'
        "    links = _zenodo_as_dict(record.get('links'))\n"
        "    return (_zenodo_pick_text(links.get('self_html'))\n"
        "            or _zenodo_pick_text(links.get('latest_html'))\n"
        "            or _zenodo_pick_text(record.get('doi_url')))",
        'zenodo-parse-helpers'
    ),
    code_cell(
        '#| export\n'
        'class ZenodoItem:\n'
        '    "Retrieve and normalize a selected TITANICA-linked Zenodo record through the stable single-record endpoint."\n'
        '    def __init__(self,\n'
        '                 record_id:str, # Zenodo record id that upstream already confirmed belongs to the TITANICA community\n'
        '                 record_base_url:str=DEFAULT_ZENODO_RECORDS_URL, # Stable single-record retrieval endpoint\n'
        '                 timeout:float=DEFAULT_ZENODO_TIMEOUT # Request timeout in seconds\n'
        '                ):\n'
        '        store_attr()\n'
        '        try: self.item = _zenodo_fetch_record(self.record_id, self.record_base_url, self.timeout)\n'
        '        except _ZenodoMissingRecordError: self.item = None\n'
        '\n'
        "    def exist(self): return self.item is not None and bool(_zenodo_pick_text(_zenodo_as_dict(self.item).get('id')))\n"
        '\n'
        '    @property\n'
        '    def id(self) -> str:\n'
        "        return _zenodo_pick_text(_zenodo_as_dict(self.item).get('id')) if self.item else ''\n"
        '\n'
        '    @property\n'
        '    def title(self) -> str:\n'
        "        metadata = _zenodo_as_dict(_zenodo_as_dict(self.item).get('metadata'))\n"
        "        return _zenodo_pick_text(metadata.get('title')) if self.item else ''\n"
        '\n'
        '    @property\n'
        '    def summary(self) -> str:\n'
        "        metadata = _zenodo_as_dict(_zenodo_as_dict(self.item).get('metadata'))\n"
        "        return _zenodo_pick_text(metadata.get('description')) if self.item else ''\n"
        '\n'
        '    @property\n'
        '    def creator_name(self) -> str:\n'
        "        metadata = _zenodo_as_dict(_zenodo_as_dict(self.item).get('metadata'))\n"
        "        return _zenodo_creator_name(metadata.get('creators', [])) if self.item else '[]'\n"
        '\n'
        '    @property\n'
        '    def doi(self) -> str:\n'
        "        metadata = _zenodo_as_dict(_zenodo_as_dict(self.item).get('metadata'))\n"
        '        return _zenodo_doi(_zenodo_as_dict(self.item), metadata) if self.item else \'\'\n'
        '\n'
        '    @property\n'
        '    def url(self) -> str:\n'
        "        return _zenodo_url(_zenodo_as_dict(self.item)) if self.item else ''\n"
        '\n'
        '    def __repr__(self): return json.dumps(self.item, indent=4)',
        'zenodo-item'
    ),
    code_cell(
        '#| export\n'
        'class ZenodoCB(Callback):\n'
        '    "Project a selected TITANICA-linked Zenodo record into NetCDF global attrs without doing discovery or community validation."\n'
        '    def __init__(self,\n'
        '                 record_id:str, # Zenodo record id that upstream already confirmed belongs to the TITANICA community\n'
        '                 record_base_url:str=DEFAULT_ZENODO_RECORDS_URL, # Stable single-record retrieval endpoint\n'
        '                 timeout:float=DEFAULT_ZENODO_TIMEOUT # Request timeout in seconds\n'
        '                ): store_attr()\n'
        '    def __call__(self, obj):\n'
        '        item = ZenodoItem(self.record_id, record_base_url=self.record_base_url, timeout=self.timeout)\n'
        '        if item.exist():\n'
        "            obj.attrs['id'] = self.record_id\n"
        "            for attr in ['title', 'summary', 'creator_name']: obj.attrs[attr] = getattr(item, attr)\n"
        "            if item.doi: obj.attrs['references'] = item.doi\n"
        "            if item.url: obj.attrs['metadata_link'] = item.url",
        'zenodo-callback'
    ),
    md_cell(
        'Pass the selected Zenodo record id only after a handler, registry entry, or audit step has already confirmed TITANICA community membership. '
        '`ZenodoCB` then projects that single record into global attrs (`id`, `title`, `summary`, `creator_name`, and optionally `references`, `metadata_link`) without broad Zenodo discovery.',
        'zenodo-usage-md'
    ),
    code_cell(
        '#|eval: false\n'
        'import json, httpx, unittest\n'
        'from unittest.mock import patch\n'
        '\n'
        'class _FakeZenodoClient:\n'
        '    def __init__(self, response): self.response = response\n'
        '    def get(self, *args, **kwargs): return self.response\n'
        '    def close(self): pass\n'
        '\n'
        'class _AttrSink:\n'
        '    def __init__(self): self.attrs = {}\n'
        '\n'
        "globals().pop('TestZenodoCB', None)\n"
        '\n'
        'class TestZenodoCB(unittest.TestCase):\n'
        "    def _mock_resp(self, payload, status=200, record_id='rec-001'):\n"
        "        req = httpx.Request('GET', f'{DEFAULT_ZENODO_RECORDS_URL}/{record_id}')\n"
        '        return httpx.Response(status, json=payload, request=req)\n'
        '\n'
        '    def test_projects_titanica_linked_record(self):\n'
        "        payload = {'id': 'payload-rec-001', 'doi': '10.5281/zenodo.rec-001',\n"
        "                   'metadata': {'title': 'TITANICA record', 'description': 'desc',\n"
        "                                'creators': [{'name': 'Author One'}]},\n"
        "                   'links': {'self_html': 'https://zenodo.example/records/rec-001'}}\n"
        '        sink = _AttrSink()\n'
        "        with patch('httpx.Client', return_value=_FakeZenodoClient(self._mock_resp(payload))):\n"
        "            ZenodoCB(record_id='rec-001')(sink)\n"
        "        test_eq(sink.attrs['id'], 'rec-001')\n"
        "        test_eq(sink.attrs['title'], 'TITANICA record')\n"
        "        test_eq(sink.attrs['summary'], 'desc')\n"
        "        test_eq(sink.attrs['creator_name'], json.dumps([{'name': 'Author One'}], ensure_ascii=True))\n"
        "        test_eq(sink.attrs['references'], '10.5281/zenodo.rec-001')\n"
        "        test_eq(sink.attrs['metadata_link'], 'https://zenodo.example/records/rec-001')\n"
        '\n'
        '    def test_missing_record_leaves_attrs_empty(self):\n'
        "        req = httpx.Request('GET', f'{DEFAULT_ZENODO_RECORDS_URL}/missing')\n"
        '        sink = _AttrSink()\n'
        "        with patch('httpx.Client', return_value=_FakeZenodoClient(httpx.Response(404, json={}, request=req))):\n"
        "            ZenodoCB(record_id='missing')(sink)\n"
        '        test_eq(sink.attrs, {})\n'
        '\n'
        '    def test_http_500_surfaces_as_error(self):\n'
        "        req = httpx.Request('GET', f'{DEFAULT_ZENODO_RECORDS_URL}/srv')\n"
        '        sink = _AttrSink()\n'
        "        with patch('httpx.Client', return_value=_FakeZenodoClient(httpx.Response(500, json={}, request=req))):\n"
        '            try:\n'
        "                ZenodoCB(record_id='srv')(sink)\n"
        "                assert False, 'Expected _ZenodoMetadataError'\n"
        '            except _ZenodoMetadataError: pass\n'
        '        test_eq(sink.attrs, {})\n'
        '\n'
        'unittest.TextTestRunner(verbosity=2).run(\n'
        '    unittest.defaultTestLoader.loadTestsFromTestCase(TestZenodoCB))',
        'zenodo-tests'
    ),
]

# ── assemble ──────────────────────────────────────────────────────────────────

nb['cells'] = cells[:41] + zenodo_cells + cells[41:]
print(f'Assembled: {len(nb["cells"])} cells ({len(zenodo_cells)} Zenodo cells inserted)')

# ── sanity: every source must be list[str] ────────────────────────────────────
for i, cell in enumerate(nb['cells']):
    src = cell['source']
    assert isinstance(src, list), f'Cell [{i}] source is {type(src).__name__}, not list'
    for j, s in enumerate(src):
        assert isinstance(s, str), f'Cell [{i}] source[{j}] is {type(s).__name__}'
print('Sanity check passed: all source fields are list[str]')

# ── write ─────────────────────────────────────────────────────────────────────
with open(TARGET, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
print(f'Written: {TARGET}')

# ── verify round-trip ─────────────────────────────────────────────────────────
with open(TARGET, encoding='utf-8') as f:
    json.load(f)
print('Round-trip JSON parse: OK')
print()
print('Next step:')
print('  python -c "import nbdev.cli; nbdev.cli.nb_export(\'nbs/api/metadata.ipynb\', lib_path=\'marisco\')"')
