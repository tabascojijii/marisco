"""
Stress test: run the HELCOM encode pipeline on 10x inflated + corrupted data
with cProfile and memory usage profiling.

Usage: python scripts/stress_test_helcom.py
"""

import cProfile, pstats, io, sys, os, time, tracemalloc
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import pandas as pd, numpy as np

import marisco.handlers.helcom as helcom_module
helcom_module.src_dir = os.path.abspath('_data_stress')
helcom_module.read_csv = lambda f, d=helcom_module.src_dir: pd.read_csv(os.path.join(d, f))

from marisco.handlers.helcom import load_data, get_attrs
from marisco.callbacks import Transformer
from marisco.handlers.helcom import *
from marisco.configs import detection_limit_lut_path
lut_dl = lambda: pd.read_excel(detection_limit_lut_path(), usecols=['name','id']).set_index('name').to_dict()['id']
from marisco.encoders import NetCDFEncoder

OUTPUT_NC = '_data_stress/stress_helcom_10x.nc'
TIMING_FILE = '_data_stress/stress_timings_10x.txt'
PROFILE_CUM = '_data_stress/stress_profile_cumtime_10x.txt'
PROFILE_TOT = '_data_stress/stress_profile_tottime_10x.txt'

def run_profile_stress():
    print("=" * 70)
    print("STRESS TEST: HELCOM 10x inflated + corrupted data")
    print("=" * 70)
    
    timings, peaks = {}, {}
    
    def stage(name, func):
        tracemalloc.start(); t0 = time.time()
        prof = cProfile.Profile(); prof.enable()
        r = func()
        prof.disable()
        elapsed, _, peak = time.time()-t0, tracemalloc.get_traced_memory()
        tracemalloc.stop()
        timings[name] = elapsed; peaks[name] = peak
        for pf, sort in [(PROFILE_CUM,'cumtime'), (PROFILE_TOT,'tottime')]:
            s = io.StringIO()
            pstats.Stats(prof, stream=s).sort_stats(sort).print_stats(20)
            with open(pf, 'a') as f:
                f.write(f"\n--- {name} ({elapsed:.1f}s, {peak/1024**2:.0f}MB) ---\n{s.getvalue()}\n")
        return r
    
    # Clear profile files
    for f in [PROFILE_CUM, PROFILE_TOT]:
        with open(f, 'w') as fh: fh.write("HELCOM Stress Profile\n")
    
    print("\n[1] Loading stress data...")
    dfs = stage("load_data", lambda: load_data(helcom_module.src_dir))
    for k, v in dfs.items(): print(f"   {k}: {len(v)} rows, {len(v.columns)} cols")
    
    print("\n[2] Initializing Transformer...")
    cbs = [
        LowerStripNameCB(col_src='nuclide', col_dst='NUCLIDE'),
        RemapNuclideNameCB(lut_nuclides, col_name='NUCLIDE'),
        ParseTimeCB(), EncodeTimeCB(),
        SplitSedimentValuesCB(coi_sediment), SanitizeValueCB(coi_val),
        NormalizeUncCB(), RemapUnitCB(),
        RemapDetectionLimitCB(coi_dl, lut_dl),
        RemapCB(fn_lut=lut_biota, col_remap='SPECIES', col_src='rubin', dest_grps='BIOTA'),
        RemapCB(fn_lut=lut_tissues, col_remap='BODY_PART', col_src='tissue', dest_grps='BIOTA'),
        RemapCB(fn_lut=lut_biogroup_from_biota, col_remap='BIO_GROUP', col_src='SPECIES', dest_grps='BIOTA'),
        RemapSedimentCB(fn_lut=lut_sediments, replace_lut=sed_replace_lut),
        RemapFiltCB(lut_filtered), AddSampleIDCB(), AddDepthCB(),
        AddSalinityCB(), AddTemperatureCB(), RemapSedSliceTopBottomCB(),
        LookupDryWetPercentWeightCB(), ParseCoordinates(ddmm_to_dd),
        SanitizeLonLatCB(), AddStationCB()
    ]
    tfm = stage("Transformer.__init__", lambda: Transformer(dfs, cbs=cbs))
    
    print("\n[3] Running all callbacks...")
    stage("Transformer.__call__", lambda: tfm())
    for k, v in tfm.dfs.items(): print(f"   After - {k}: {len(v)} rows, {len(v.columns)} cols")
    
    print("\n[4] Getting attributes...")
    attrs = stage("get_attrs", lambda: get_attrs(tfm, zotero_key='26VMZZ2Q', kw=kw))
    
    print("\n[5] Encoding to NetCDF...")
    encoder = NetCDFEncoder(tfm.dfs, dest_fname=OUTPUT_NC, global_attrs=attrs, verbose=False)
    stage("NetCDFEncoder.encode", lambda: encoder.encode())
    out_mb = os.path.getsize(OUTPUT_NC)/1024**2 if os.path.exists(OUTPUT_NC) else 0
    
    total = sum(timings.values())
    max_mem = max(peaks.values())
    summary = f"""
{'='*70}
HELCOM STRESS TEST RESULTS (10x inflated + corrupted)
{'='*70}
  Load data         : {timings['load_data']:.1f}s   mem: {peaks['load_data']/1024**2:.0f}MB
  Transformer init  : {timings['Transformer.__init__']:.1f}s   mem: {peaks['Transformer.__init__']/1024**2:.0f}MB
  Callbacks (all)   : {timings['Transformer.__call__']:.1f}s   mem: {peaks['Transformer.__call__']/1024**2:.0f}MB
  Get attributes    : {timings['get_attrs']:.1f}s   mem: {peaks['get_attrs']/1024**2:.0f}MB
  Encode to NetCDF  : {timings['NetCDFEncoder.encode']:.1f}s   mem: {peaks['NetCDFEncoder.encode']/1024**2:.0f}MB
  {'-'*35}
  TOTAL             : {total:.1f}s   peak: {max_mem/1024**2:.0f}MB
  Output size       : {out_mb:.1f} MB
"""
    for k, v in tfm.dfs.items():
        summary += f"  {k}: {len(v)} rows x {len(v.columns)} cols\n"
    
    with open(TIMING_FILE, 'w') as f: f.write(summary)
    print(summary)

if __name__ == '__main__':
    run_profile_stress()