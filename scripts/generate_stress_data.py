"""
Generate 100x inflated + corrupted stress test data from original HELCOM CSV files.

Usage: python scripts/generate_stress_data.py
Output: Writes inflated CSVs to _data_stress/ directory
"""

import pandas as pd
import numpy as np
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

DATA_DIR = '_data'
OUT_DIR = '_data_stress'
REPLICATION_FACTOR = 100  # inflate 100x

os.makedirs(OUT_DIR, exist_ok=True)

def corrupt_value(val, rng):
    """Apply a corruption to a value with some probability."""
    if pd.isna(val):
        return val
    p = rng.random()
    if p < 0.02:
        # 2%: return NaN
        return np.nan
    elif p < 0.04:
        # 2%: return empty string
        return ''
    elif p < 0.06:
        # 2%: add/remove whitespace
        s = str(val)
        if rng.random() < 0.5:
            return ' ' + s.strip() + ' '
        else:
            return s.strip()
    elif p < 0.08:
        # 2%: case flip
        s = str(val)
        return s.swapcase() if len(s) > 0 else s
    elif p < 0.10:
        # 2%: add special characters
        s = str(val)
        chars = ['\u3000', '\u00a0', '\u200b', '\ufffd', '', '\t', '\n']
        return s + rng.choice(chars)
    else:
        return val

def inflate_and_corrupt(df, replication_factor, rng):
    """Inflate a DataFrame by replication_factor and corrupt some rows."""
    n = len(df)
    if n == 0:
        return df.copy()
    
    # Create replicated indices
    indices = np.tile(np.arange(n), replication_factor)
    # Shuffle to mix rows
    rng.shuffle(indices)
    
    df_inflated = df.iloc[indices].reset_index(drop=True)
    
    # Corrupt each column
    for col in df_inflated.columns:
        if df_inflated[col].dtype == 'object':
            # String columns: apply corruption
            df_inflated[col] = df_inflated[col].apply(lambda v: corrupt_value(v, rng))
        elif pd.api.types.is_numeric_dtype(df_inflated[col]):
            # Numeric columns: inject NaNs and outliers
            nan_mask = rng.random(size=len(df_inflated)) < 0.005  # 0.5% NaN
            outlier_mask = rng.random(size=len(df_inflated)) < 0.001  # 0.1% outliers
            df_inflated.loc[nan_mask, col] = np.nan
            if outlier_mask.any() and df_inflated[col].notna().any():
                std = df_inflated[col].std()
                mean = df_inflated[col].mean()
                if pd.notna(std) and std > 0:
                    df_inflated.loc[outlier_mask, col] = mean + 100 * std * rng.standard_normal(outlier_mask.sum())
    
    return df_inflated

def process_file_pair(prefix, replication_factor, rng):
    """Process a pair of 01.csv and 02.csv files."""
    for suffix in ['01', '02']:
        fname = f'{prefix}{suffix}.csv'
        src_path = os.path.join(DATA_DIR, fname)
        if not os.path.exists(src_path):
            print(f"  [SKIP] {src_path} not found")
            continue
        
        print(f"  Reading {src_path}...")
        df = pd.read_csv(src_path, low_memory=False)
        orig_rows = len(df)
        print(f"    Original rows: {orig_rows}")
        
        df_inflated = inflate_and_corrupt(df, replication_factor, rng)
        print(f"    Inflated rows: {len(df_inflated)}")
        
        dst_path = os.path.join(OUT_DIR, fname)
        df_inflated.to_csv(dst_path, index=False)
        print(f"    Written to {dst_path}")

def process_single_file(fname, replication_factor, rng):
    """Process a single nomenclature CSV file."""
    src_path = os.path.join(DATA_DIR, fname)
    if not os.path.exists(src_path):
        print(f"  [SKIP] {src_path} not found")
        return
    
    print(f"  Reading {src_path}...")
    df = pd.read_csv(src_path, low_memory=False)
    orig_rows = len(df)
    print(f"    Original rows: {orig_rows}")
    
    # For lookup tables, just copy (don't inflate since they're small lookups)
    df.to_csv(os.path.join(OUT_DIR, fname), index=False)
    print(f"    Copied (no inflation)")

if __name__ == '__main__':
    rng = np.random.default_rng(42)  # deterministic seed
    
    print(f"Generating stress test data with {REPLICATION_FACTOR}x inflation + corruption")
    print(f"Source: {DATA_DIR}/")
    print(f"Output: {OUT_DIR}/\n")
    
    # HELCOM data file pairs
    print("=== HELCOM measurement/sample files (100x inflation) ===")
    for prefix in ['BIO', 'SEA', 'SED']:
        print(f"\nProcessing {prefix}...")
        process_file_pair(prefix, REPLICATION_FACTOR, rng)
    
    # Nomenclature files (copy as-is)
    print("\n=== Nomenclature files (copied, no inflation) ===")
    for fname in ['RUBIN_NAME.csv', 'TISSUE.csv', 'SEDIMENT_TYPE.csv']:
        process_single_file(fname, REPLICATION_FACTOR, rng)
    
    # Verify output sizes
    print("\n=== Output file sizes ===")
    total_mb = 0
    for fname in sorted(os.listdir(OUT_DIR)):
        size_mb = os.path.getsize(os.path.join(OUT_DIR, fname)) / (1024 * 1024)
        total_mb += size_mb
        print(f"  {fname}: {size_mb:.2f} MB")
    print(f"\nTotal output size: {total_mb:.2f} MB")