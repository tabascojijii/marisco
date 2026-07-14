from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from marisco.callbacks.core import PerGroupCB, PipelineState


_LAT_LON_RE = re.compile(
    r"(?P<LAT>\d+(?:\.\d+)?)(?P<LAT_HEM>[NS])/(?P<LON>\d+(?:\.\d+)?)(?P<LON_HEM>[EW])"
)
_MEASURED_RE = re.compile(r"(?P<VALUE>\d+(?:\.\d+)?)\((?P<UNC>\d+(?:\.\d+)?)\)")


def load_chaos_mock(cfg, grp: str = "SEAWATER") -> dict[str, pd.DataFrame]:
    "Load the local chaos CSV fixture without changing shared pipeline code."
    csv_path = Path(cfg.url).resolve()
    return {grp: pd.read_csv(csv_path)}


class UltimateChaosPatchCB(PerGroupCB):
    "Straighten chaos cells into canonical MARIS columns before the shared core runs."
    grps = ["SEAWATER"]

    def each_grp(self, grp: str, df: pd.DataFrame, state: PipelineState):
        lat_lon = df["lat_lon"].str.extract(_LAT_LON_RE)
        measured = df["measured"].str.extract(_MEASURED_RE)

        df["LAT"] = lat_lon["LAT"].astype(float)
        df.loc[lat_lon["LAT_HEM"].eq("S"), "LAT"] *= -1
        df["LON"] = lat_lon["LON"].astype(float)
        df.loc[lat_lon["LON_HEM"].eq("W"), "LON"] *= -1

        df["VALUE"] = measured["VALUE"].astype(float)
        df["UNC"] = measured["UNC"].astype(float)
        df["TIME"] = pd.to_datetime(df["time_raw"], format="%Y/%m/%d_%H:%M", utc=True)
        df["LAB"] = "CHAOS_LAB"
        df["UNIT"] = "Bq_kg"
        df["NUCLIDE"] = "Cs137"

        state.dfs[grp] = df
