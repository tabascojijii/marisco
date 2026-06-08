"""Helper to produce HELCOM golden NetCDF from sample fixture data."""

from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def build_helcom_golden(
    tmp_path: Path,
    data_root: Path | None = None,
) -> Path:
    """Run the HELCOM handler on real data and return the output path.

    Uses the full HELCOM dataset from *data_root* (defaults to
    ``PROJECT_ROOT / "_data"``).
    """
    if data_root is None:
        data_root = PROJECT_ROOT / "_data"

    output_nc = tmp_path / "helcom_golden.nc"

    import pandas as pd
    from marisco.configs import detection_limit_lut_path

    import marisco.handlers.helcom as helcom_module

    # --- Patch 1: RemapDetectionLimitCB coi/lut_dl mismatch ---
    _orig_cls = helcom_module.RemapDetectionLimitCB

    class _PatchedRemapDL(_orig_cls):
        def __init__(self, coi, lut_dl=None):
            super().__init__(coi)

    helcom_module.RemapDetectionLimitCB = _PatchedRemapDL

    # --- Patch 2: add missing module-level lut_dl ---
    helcom_module.lut_dl = lambda: pd.read_excel(
        detection_limit_lut_path(), usecols=["name", "id"]
    ).set_index("name").to_dict()["id"]

    # --- Patch 3: replace get_attrs to skip Zotero (external API) ---
    def _patched_get_attrs(tfm, zotero_key, kw=helcom_module.kw):
        from marisco.metadata import GlobAttrsFeeder, BboxCB, DepthRangeCB, TimeRangeCB, KeyValuePairCB

        return GlobAttrsFeeder(tfm.dfs, cbs=[
            BboxCB(),
            DepthRangeCB(),
            TimeRangeCB(),
            KeyValuePairCB("keywords", ", ".join(kw)),
            KeyValuePairCB("publisher_postprocess_logs", ", ".join(tfm.logs)),
        ])()

    helcom_module.get_attrs = _patched_get_attrs

    # --- Patch 4: point handler to read CSV from our data dir ---
    original_src_dir = helcom_module.src_dir
    original_read_csv = helcom_module.read_csv

    helcom_module.src_dir = str(data_root)
    helcom_module.read_csv = lambda f, d=None: original_read_csv(f, dir=str(data_root))

    try:
        from marisco.handlers.helcom import encode
        encode(fname_out=str(output_nc))
    finally:
        helcom_module.src_dir = original_src_dir
        helcom_module.read_csv = original_read_csv

    assert output_nc.exists(), f"Output file was not created: {output_nc}"
    return output_nc


def build_helcom_golden_cli() -> None:
    """CLI entry point: python -m tests.helpers.golden_generation"""
    import shutil
    import tempfile

    golden_dir = PROJECT_ROOT / "tests" / "golden_data" / "helcom" / "expected"
    golden_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        actual = build_helcom_golden(Path(tmp))
        dest = golden_dir / "helcom_golden.nc"
        shutil.copy2(actual, dest)
        print(f"Golden file written to: {dest}")
        print(f"Size: {dest.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    build_helcom_golden_cli()