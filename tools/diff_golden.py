#!/usr/bin/env python
"""Regression safety net for handler refactoring.

Encodes a handler's real pipeline output, summarizes it (row counts, key nomenclature
value sets, lat/lon bounding box), and diffs that summary against a stored golden
snapshot. Catches unintended behavioural drift when a handler is refactored or
regenerated -- the manual check this replaces was done by hand throughout the
fram_strait2025 inplace=True fix (row count, STATION values, etc. compared before/after).

Usage:
    python tools/diff_golden.py helcom --save     # create/update tests/golden/helcom.json
    python tools/diff_golden.py helcom            # compare current encode() output against it
"""
import argparse
import importlib
import json
import sys
import tempfile
from pathlib import Path

import netCDF4
import numpy as np

GOLDEN_DIR = Path(__file__).resolve().parent.parent / 'tests' / 'golden'

# NetCDF variable names worth tracking as a value-set fingerprint, if present in a group.
TRACKED_VARS = ('nuclide', 'unit', 'dl', 'species', 'sed_type', 'bio_group', 'station')


def summarize(nc_path: Path) -> dict:
    "Row count, tracked-variable value sets, and lat/lon bbox per group."
    summary = {}
    with netCDF4.Dataset(nc_path, 'r') as ds:
        for grp_name, grp in ds.groups.items():
            row_count = next((len(d) for d in grp.dimensions.values()), 0)
            values: dict[str, list] = {}
            for var_name in TRACKED_VARS:
                if var_name not in grp.variables: continue
                data = grp.variables[var_name][:]
                if data.dtype.kind in 'USO':  # string, unicode, or netCDF4 VLEN-str object dtype
                    values[var_name] = sorted(set(str(v) for v in np.asarray(data).tolist() if v is not None))
                    continue
                raw = np.ma.filled(data, np.nan)
                values[var_name] = sorted(set(float(v) for v in raw.tolist() if v == v))  # drop NaN
            bbox = {}
            for coord in ('lat', 'lon'):
                if coord not in grp.variables: continue
                raw = np.ma.filled(grp.variables[coord][:], np.nan)
                valid = raw[~np.isnan(raw)]
                if len(valid): bbox[coord] = [float(valid.min()), float(valid.max())]
            summary[grp_name] = {'row_count': row_count, 'values': values, 'bbox': bbox}
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('handler', help='Handler module name under marisco.handlers, e.g. helcom')
    p.add_argument('--save', action='store_true', help='Write/overwrite the golden snapshot instead of comparing')
    args = p.parse_args()

    mod = importlib.import_module(f'marisco.handlers.{args.handler}')
    golden_path = GOLDEN_DIR / f'{args.handler}.json'

    with tempfile.TemporaryDirectory() as tmp:
        out_nc = Path(tmp) / f'{args.handler}.nc'
        mod.encode(str(out_nc))
        current = summarize(out_nc)

    if args.save:
        GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
        golden_path.write_text(json.dumps(current, indent=2, sort_keys=True))
        print(f"Saved golden snapshot: {golden_path}")
        return

    if not golden_path.exists():
        print(f"No golden snapshot at {golden_path}. Run with --save first.")
        sys.exit(1)

    golden = json.loads(golden_path.read_text())
    if current == golden:
        print(f"{args.handler}: matches golden snapshot ({golden_path}). ✓")
        return

    print(f"{args.handler}: DIFFERS from golden snapshot ({golden_path}):")
    for grp in sorted(set(current) | set(golden)):
        if current.get(grp) != golden.get(grp):
            print(f"  [{grp}]")
            print(f"    golden:  {golden.get(grp)}")
            print(f"    current: {current.get(grp)}")
    sys.exit(1)


if __name__ == '__main__':
    main()
