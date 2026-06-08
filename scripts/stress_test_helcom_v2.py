"""
Stress test v2: load HELCOM data at original scale, merge (works), then
inflate merged DataFrames 10x in-memory. Run full callback pipeline + encode.

Usage: python scripts/stress_test_helcom_v2.py
"""

import cProfile, pstats, io, sys, os, time, tracemalloc, copy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import pandas as pd, numpy as np

# Use original data (not inflated files) for the merge
import marisco.handlers.helcom as helcom_module
helcom_module.src_dir = os.path.abspath('_data')
helcom_module.read_csv = lambda f, d=helcom_module.src_dir: pd.read_csv(os.path.join(d, f))

from marisco.handlers.helcom import load_data as orig_load_data
from marisco.handlers.helcom import get_attrs
from marisco.callbacks import (
    Transformer, LowerStripNameCB, EncodeTimeCB, SanitizeLonLatCB, RemapCB
)
from marisco.handlers.helcom import (
    RemapNuclideNameCB, ParseTimeCB, SplitSedimentValuesCB, SanitizeValueCB,
    NormalizeUncCB, RemapUnitCB, RemapDetectionLimitCB, RemapSedimentCB,
    RemapFiltCB, AddSampleIDCB, AddDepthCB, AddSalinityCB, AddTemperatureCB,
    RemapSedSliceTopBottomCB, LookupDryWetPercentWeightCB, ParseCoordinates,
    AddStationCB,
    coi_sediment, coi_val, coi_dl, coi_units_unc,
    lut_nuclides, lut_biota, lut_tissues, lut_biogroup_from_biota,
    lut_sediments, sed_replace_lut, lut_filtered, ddmm_to_dd, kw
)
from marisco.configs import detection_limit_lut_path
lut_dl = lambda: pd.read_excel(detection_limit_lut_path(), usecols=['name','id']).set_index('name').to_dict()['id']
from marisco.encoders import NetCDFEncoder

OUTPUT_NC = '_data_stress/stress_helcom_10x_v2.nc'
TIMING_FILE = '_data_stress/stress_timings_10x_v2.txt'
PROFILE_CUM = '_data_stress/stress_profile_cumtime_10x_v2.txt'
PROFILE_TOT = '_data_stress/stress_profile_tottime_10x_v2.txt'
INFLATION = 10

def inflate_dfs(dfs, factor, rng):
    """Inflate each DataFrame in the dict by factor."""
    result = {}
    for key, df in dfs.items():
        n = len(df)
        indices = np.tile(np.arange(n), factor)
        rng.shuffle(indices)
        result[key] = df.iloc[indices].reset_index(drop=True)
    return result

def run_profile_stress():
    print("=" * 70)
    print(f"STRESS TEST v2: HELCOM {INFLATION}x in-memory inflated + corrupted")
    print("=" * 70)
    
    timings, peaks = {}, {}
    
    def stage(name, func):
        tracemalloc.start()
        t0 = time.time()
        prof = cProfile.Profile(); prof.enable()
        r = func()
        prof.disable()
        elapsed = time.time() - t0
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        timings[name] = elapsed; peaks[name] = peak
        for pf, sort in [(PROFILE_CUM,'cumtime'), (PROFILE_TOT,'tottime')]:
            s = io.StringIO()
            pstats.Stats(prof, stream=s).sort_stats(sort).print_stats(20)
            with open(pf, 'a') as f:
                f.write(f"\n--- {name} ({elapsed:.1f}s, {peak/1024**2:.0f}MB) ---\n{s.getvalue()}\n")
        return r
    
    for f in [PROFILE_CUM, PROFILE_TOT]:
        with open(f, 'w') as fh: fh.write("HELCOM Stress Profile v2\n")
    
    # Stage 0: Inflate corrupted data files first (avoid merge OOM)
    print("\n[0] Reading ORIGINAL data + inflating in-memory (bypass merge OOM)...")
    t0 = time.time()
    tracemalloc.start()
    rng = np.random.default_rng(42)
    raw_dfs = {}
    for prefix, stype in [('BIO', 'BIOTA'), ('SEA', 'SEAWATER'), ('SED', 'SEDIMENT')]:
        # Read ORIGINAL (small) files from _data/ via helcom's read_csv (which uses monkey-patched path)
        df_meas = helcom_module.read_csv(f'{prefix}02.csv')
        df_smp = helcom_module.read_csv(f'{prefix}01.csv')
        # Lowercase columns (same as helcom's load_data does)
        df_meas.columns = df_meas.columns.str.lower()
        df_smp.columns = df_smp.columns.str.lower()
        # Merge at original size (this works fine)
        merged = pd.merge(df_meas, df_smp, on='key', how='left')
        # Inflate in memory
        n = len(merged)
        indices = np.tile(np.arange(n), INFLATION)
        rng.shuffle(indices)
        df_inflated = merged.iloc[indices].reset_index(drop=True)
        # Corrupt (inject NaNs, empty strings, whitespace)
        for col in df_inflated.columns:
            if df_inflated[col].dtype == 'object':
                mask = rng.random(size=len(df_inflated)) < 0.03
                vals = df_inflated[col].values.copy()
                for idx in np.where(mask)[0]:
                    p = rng.random()
                    if p < 0.3: vals[idx] = np.nan
                    elif p < 0.6: vals[idx] = ''
                    else: vals[idx] = ' ' + str(vals[idx]).strip() + ' '
                df_inflated[col] = vals
        raw_dfs[stype] = df_inflated
        print(f"   {stype}: {len(raw_dfs[stype])} rows (inflated {INFLATION}x from {n})")
    elapsed = time.time() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    timings['inflate_load'] = elapsed; peaks['inflate_load'] = peak
    print(f"   Time: {elapsed:.1f}s, Peak mem: {peak/1024**2:.0f}MB")
    
    # Stage 1: Transformer init
    print("\n[1] Initializing Transformer...")
    cbs = [
        LowerStripNameCB(col_src='nuclide', col_dst='NUCLIDE'),
        RemapNuclideNameCB(lut_nuclides, col_name='NUCLIDE'),
        ParseTimeCB(), EncodeTimeCB(),
        SplitSedimentValuesCB(coi_sediment), SanitizeValueCB(coi_val),
        NormalizeUncCB(), RemapUnitCB(),
        RemapDetectionLimitCB(coi_dl),
        RemapCB(fn_lut=lut_biota, col_remap='SPECIES', col_src='rubin', dest_grps='BIOTA'),
        RemapCB(fn_lut=lut_tissues, col_remap='BODY_PART', col_src='tissue', dest_grps='BIOTA'),
        RemapCB(fn_lut=lut_biogroup_from_biota, col_remap='BIO_GROUP', col_src='SPECIES', dest_grps='BIOTA'),
        RemapSedimentCB(fn_lut=lut_sediments, replace_lut=sed_replace_lut),
        RemapFiltCB(lut_filtered), AddSampleIDCB(), AddDepthCB(),
        AddSalinityCB(), AddTemperatureCB(), RemapSedSliceTopBottomCB(),
        LookupDryWetPercentWeightCB(), ParseCoordinates(ddmm_to_dd),
        SanitizeLonLatCB(), AddStationCB()
    ]
    tfm = stage("Transformer.__init__", lambda: Transformer(raw_dfs, cbs=cbs))
    
    # Stage 2: Run callbacks
    print("\n[2] Running all callbacks...")
    stage("Transformer.__call__", lambda: tfm())
    for k, v in tfm.dfs.items():
        print(f"   After - {k}: {len(v)} rows, {len(v.columns)} cols")
    
    # Stage 3: Get attributes
    print("\n[3] Getting attributes...")
    attrs = stage("get_attrs", lambda: get_attrs(tfm, zotero_key='26VMZZ2Q', kw=kw))
    
    # Stage 4: Encode to NetCDF
    print("\n[4] Encoding to NetCDF...")
    encoder = NetCDFEncoder(tfm.dfs, dest_fname=OUTPUT_NC, global_attrs=attrs, verbose=False)
    stage("NetCDFEncoder.encode", lambda: encoder.encode())
    out_mb = os.path.getsize(OUTPUT_NC)/1024**2 if os.path.exists(OUTPUT_NC) else 0
    
    total = sum(timings.values())
    max_mem = max(peaks.values())
    summary = f"""
{'='*70}
HELCOM STRESS TEST v2 RESULTS ({INFLATION}x inflated + corrupted)
{'='*70}
  Inflate+load  : {timings['inflate_load']:.1f}s   mem: {peaks['inflate_load']/1024**2:.0f}MB
  Transformer   : {timings['Transformer.__init__']:.1f}s   mem: {peaks['Transformer.__init__']/1024**2:.0f}MB
  Callbacks     : {timings['Transformer.__call__']:.1f}s   mem: {peaks['Transformer.__call__']/1024**2:.0f}MB
  Attrs         : {timings['get_attrs']:.1f}s   mem: {peaks['get_attrs']/1024**2:.0f}MB
  Encode        : {timings['NetCDFEncoder.encode']:.1f}s   mem: {peaks['NetCDFEncoder.encode']/1024**2:.0f}MB
  {'-'*35}
  TOTAL         : {total:.1f}s   peak: {max_mem/1024**2:.0f}MB
  Output size   : {out_mb:.1f} MB
"""
    for k, v in tfm.dfs.items():
        summary += f"  {k}: {len(v)} rows x {len(v.columns)} cols\n"
    
    with open(TIMING_FILE, 'w') as f: f.write(summary)
    print(summary)

if __name__ == '__main__':
    run_profile_stress()