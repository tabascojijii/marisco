#!/usr/bin/env python
"""Profile a raw provider file for handler development.

Automates the "derive unique values -> fuzzy-match against MARIS reference" steps that
every handler notebook currently hand-writes at the start of nomenclature reconciliation
(see nbs/how-to/reconcile-nomenclature.pct.py). Pure orchestration around the existing
marisco.match / marisco.configs primitives -- no new matching logic.

Usage:
    python tools/profile_source.py data.csv
    python tools/profile_source.py data.csv --lut nuclide=NUCLIDE --lut rubin=SPECIES
"""
import argparse
from pathlib import Path

import pandas as pd

from marisco.configs import NC_DTYPES, get_lut
from marisco.match import fuzzy_merge, lut_from


def load(path: Path) -> pd.DataFrame:
    "Load a provider file by extension (csv or excel)."
    suffix = path.suffix.lower()
    if suffix == '.csv': return pd.read_csv(path)
    if suffix in ('.xlsx', '.xls'): return pd.read_excel(path)
    raise ValueError(f"Unsupported file type: {suffix} (expected .csv/.xlsx)")


def profile_columns(df: pd.DataFrame) -> None:
    "Print per-column dtype, null rate, cardinality, and a sample of values."
    print(f"\n{len(df)} rows, {len(df.columns)} columns\n")
    for col in df.columns:
        s = df[col]
        n_null = int(s.isna().sum())
        n_uniq = int(s.nunique(dropna=True))
        sample = s.dropna().unique()[:8].tolist()
        pct = 100 * n_null / len(df) if len(df) else 0
        print(f"  {col!s:<30} dtype={str(s.dtype):<10} null={n_null:>6} ({pct:4.1f}%) "
              f"unique={n_uniq:>6}  sample={sample}")


def profile_nomenclature(df: pd.DataFrame, col: str, lut_name: str) -> None:
    "Fuzzy-match a column's unique values against a MARIS reference LUT; report borderline cases."
    if lut_name not in NC_DTYPES:
        print(f"  Unknown LUT '{lut_name}'. Known: {sorted(NC_DTYPES)}")
        return
    right_on = NC_DTYPES[lut_name]['key']
    maris_ref = get_lut(lut_name, as_df=True)
    provider_lut = lut_from({'_': df}, col)
    merged = fuzzy_merge(provider_lut, maris_ref, left_on='value', right_on=right_on)
    non_exact = merged[merged.score > 0].sort_values('score', ascending=False)
    n_exact = len(merged) - len(non_exact)
    print(f"\n  '{col}' -> {lut_name} ({right_on}): {n_exact}/{len(merged)} exact matches")
    if len(non_exact):
        print(f"  {len(non_exact)} borderline match(es) needing review (add to a fixes_* dict if wrong):")
        print(non_exact[['value', right_on, 'score']].to_string(index=False))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('path', type=Path, help='CSV or Excel file to profile')
    p.add_argument('--lut', action='append', default=[], metavar='COLUMN=LUT_NAME',
                   help='Fuzzy-match COLUMN against a MARIS reference LUT (e.g. nuclide=NUCLIDE). Repeatable.')
    args = p.parse_args()

    df = load(args.path)
    profile_columns(df)

    for spec in args.lut:
        if '=' not in spec:
            print(f"Skipping malformed --lut '{spec}', expected COLUMN=LUT_NAME")
            continue
        col, lut_name = spec.split('=', 1)
        if col not in df.columns:
            print(f"Skipping --lut '{spec}': column '{col}' not in {args.path}")
            continue
        profile_nomenclature(df, col, lut_name)


if __name__ == '__main__':
    main()
