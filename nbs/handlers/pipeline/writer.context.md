# Source Notebook: writer.ipynb

### Cell [1] - Role: Module Declaration (default_exp)
```python
#| default_exp handlers.pipeline.writer
```

# Writer

Compatibility facade for `write_netcdf(tfm, cfg)` during the output modularization.

### Cell [3] - Role: Production Implementation (Exported)
```python
#| export
from __future__ import annotations
from marisco.handlers.pipeline.output import (
    _SimpleBboxCB,
    build_global_attrs,
    project_netcdf_columns,
    validate_required_columns,
    write_netcdf,
)
```

## write_netcdf

Two-phase Strict guard → GlobAttrsFeeder → NetCDFEncoder:

| Phase | What | Fails with |
|-------|------|-----------|
| Guard 1 | `_MARIS_REQUIRED` ⊆ columns | `KeyError` |
| Guard 2 | `RenameColumnsCB` drops non-NC noise columns | silent |
| GlobAttrs | `BboxCB`, `DepthRangeCB`, `TimeRangeCB`, keywords, logs | `KeyError` on unknown attrs |
| Encode | `NetCDFEncoder.encode()` writes `.nc` | framework error |

### Cell [5] - Role: Production Implementation (Exported)
```python
#| export
from marisco.handlers.pipeline.output import (
    _SimpleBboxCB,
    build_global_attrs,
    project_netcdf_columns,
    validate_required_columns,
    write_netcdf,
)
```

### Cell [6] - Role: Hidden Helper / Test Setup
```python
#| hide
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd
from netCDF4 import Dataset

from marisco.callbacks import Transformer
from marisco.configs import NC_DTYPES
from marisco.encoders import NetCDFEncoder as _NetCDFEncoder
from marisco.handlers.pipeline.contracts import HandlerConfig
from marisco.metadata import TimeRangeCB as _TimeRangeCB
import marisco.handlers.pipeline.output as _output

_TIME_UNITS = "seconds since 1970-01-01 00:00:00.0"

def _build_template(path):
    with Dataset(path, "w", format="NETCDF4") as _nc:
        _nc.setncatts({
            "id": "template-fixture",
            "title": "Generated MARIS template",
            "summary": "Self-contained writer fixture",
            "Conventions": "CF-1.8",
        })
        _grp = _nc.createGroup("seawater")
        _grp.createDimension("id", None)
        _nuclide_t = _nc.createEnumType(np.int64, "nuclide_t", {"Cs_137": 28, "Co_60": 29})
        _unit_t = _nc.createEnumType(np.int64, "unit_t", {"Bq_m3": 9})
        _variables = {
            "lat": _grp.createVariable("lat", np.float64, ("id",)),
            "lon": _grp.createVariable("lon", np.float64, ("id",)),
            "time": _grp.createVariable("time", np.float64, ("id",)),
            "nuclide": _grp.createVariable("nuclide", _nuclide_t, ("id",)),
            "value": _grp.createVariable("value", np.float64, ("id",)),
            "unc": _grp.createVariable("unc", np.float64, ("id",)),
            "unit": _grp.createVariable("unit", _unit_t, ("id",)),
            "smp_depth": _grp.createVariable("smp_depth", np.float64, ("id",)),
            "id": _grp.createVariable("id", np.int64, ("id",)),
            "station": _grp.createVariable("station", str, ("id",)),
        }
        _variables["lat"].setncatts({"standard_name": "latitude", "units": "degrees_north"})
        _variables["lon"].setncatts({"standard_name": "longitude", "units": "degrees_east"})
        _variables["time"].setncatts({"standard_name": "time", "units": _TIME_UNITS, "calendar": "standard"})
        _variables["value"].units = "Bq m-3"
        _variables["unc"].units = "Bq m-3"
        _variables["smp_depth"].units = "m"

with TemporaryDirectory() as _tmp_dir:
    _template_path = Path(_tmp_dir) / "generated-template.nc"
    _target_path = Path(_tmp_dir) / "writer-output.nc"
    _build_template(_template_path)

    _df = pd.DataFrame({
        "LAT": np.array([79.5, 80.25], dtype=np.float64),
        "LON": np.array([4.2, 5.75], dtype=np.float64),
        "TIME": np.array([1577836800.0, 1577923200.0], dtype=np.float64),
        "NUCLIDE": np.array([28, 29], dtype=np.int64),
        "VALUE": np.array([1.25, 2.50], dtype=np.float64),
        "UNC": np.array([0.10, 0.20], dtype=np.float64),
        "UNIT": np.array([9, 9], dtype=np.int64),
        "SMP_DEPTH": np.array([10.0, 20.0], dtype=np.float64),
        "SMP_ID": np.array([1, 2], dtype=np.int64),
        "STATION": np.array(["FRAM_001", "FRAM_002"], dtype=object),
        "PROVIDER_JUNK": ["drop-me", "drop-me-too"],
    })
    _tfm = Transformer({"SEAWATER": _df}, cbs=[])
    _tfm()
    _cfg = HandlerConfig(
        module_name="tests.writer_fixture",
        title="Writer fixture",
        url="memory://writer-fixture",
        fname_out=str(_target_path),
        keywords=["MARIS", "self-contained-test"],
        global_attrs={
            "id": "writer-fixture",
            "title": "Writer integration fixture",
            "summary": "Generated without static NetCDF fixtures",
            "Conventions": "CF-1.8",
        },
    )

    class _FixtureEncoder(_NetCDFEncoder):
        def __init__(self, dfs, dest_fname, global_attrs):
            super().__init__(
                dfs, dest_fname, global_attrs, fn_src_fname=lambda: _template_path
            )

        def create_enums(self):
            for _column in (col for col in self.all_cols if col in NC_DTYPES):
                _values = sorted({
                    int(value)
                    for _frame in self.dfs.values()
                    for value in _frame[_column].dropna()
                })
                _name = NC_DTYPES[_column]["name"]
                _members = {f"{_column.lower()}_{value}": value for value in _values}
                self.enum_dtypes[_name] = self.dest.createEnumType(np.int64, _name, _members)

    _original_encoder = _output.NetCDFEncoder
    _original_time_range = _output.TimeRangeCB
    _output.NetCDFEncoder = _FixtureEncoder
    _output.TimeRangeCB = lambda: _TimeRangeCB(fn_time_unit=lambda: _TIME_UNITS)
    try:
        write_netcdf(_tfm, _cfg)
    finally:
        _output.NetCDFEncoder = _original_encoder
        _output.TimeRangeCB = _original_time_range

    assert _target_path.is_file() and _target_path.stat().st_size > 0
    with Dataset(_target_path, "r") as _nc:
        assert _nc.data_model == "NETCDF4"
        assert set(_nc.groups) == {"seawater"}
        assert _nc.getncattr("id") == "writer-fixture"
        assert _nc.getncattr("keywords") == "MARIS, self-contained-test"
        assert _nc.getncattr("geospatial_lat_min") == "79.5"
        assert _nc.getncattr("geospatial_lat_max") == "80.25"
        assert _nc.getncattr("time_coverage_start").startswith("2020-01-01T00:00:00")
        assert _nc.getncattr("time_coverage_end").startswith("2020-01-02T00:00:00")

        _grp = _nc.groups["seawater"]
        _expected_vars = {"lat", "lon", "time", "nuclide", "value", "unc", "unit", "smp_depth", "id", "station"}
        assert set(_grp.variables) == _expected_vars
        assert len(_grp.dimensions["id"]) == 2
        assert _grp.dimensions["id"].isunlimited()
        assert _grp.variables["lat"].dtype == np.dtype("float64")
        assert _grp.variables["time"].dtype == np.dtype("float64")
        assert _grp.variables["id"].dtype == np.dtype("int64")
        assert _grp.variables["nuclide"].datatype.name == "nuclide_t"
        assert _grp.variables["unit"].datatype.name == "unit_t"
        assert _grp.variables["lat"].units == "degrees_north"
        assert _grp.variables["time"].units == _TIME_UNITS
        np.testing.assert_allclose(_grp.variables["lat"][:], [79.5, 80.25])
        np.testing.assert_allclose(_grp.variables["lon"][:], [4.2, 5.75])
        np.testing.assert_allclose(_grp.variables["time"][:], [1577836800.0, 1577923200.0])
        np.testing.assert_array_equal(_grp.variables["nuclide"][:], [28, 29])
        np.testing.assert_array_equal(_grp.variables["unit"][:], [9, 9])
        np.testing.assert_array_equal(_grp.variables["id"][:], [1, 2])
        assert _grp.variables["station"][:].tolist() == ["FRAM_001", "FRAM_002"]

    try:
        validate_required_columns(Transformer({"SEAWATER": _df.drop(columns=["LAT"])}))
    except KeyError as _error:
        assert "LAT" in str(_error)
    else:
        raise AssertionError("validate_required_columns accepted a group without LAT")
```

