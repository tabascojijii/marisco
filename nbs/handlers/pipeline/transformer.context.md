# Source Notebook: transformer.ipynb

### Cell [1] - Role: Module Declaration (default_exp)
```python
#| default_exp handlers.pipeline.transformer
```

# Transformer

Compatibility facade for `build_chain(cfg)` during the pipeline assembly modularization.

### Cell [3] - Role: Production Implementation (Exported)
```python
#| export
from __future__ import annotations
from marisco.handlers.pipeline.assembly import build_chain
```

## build_chain

Assembles the standard 11-CB pipeline from a `HandlerConfig`.
No `if` at runtime — empty YAML lists produce Null-Object no-op CBs.

### Cell [5] - Role: Production Implementation (Exported)
```python
#| export
from marisco.handlers.pipeline.assembly import build_chain
```

### Cell [6] - Role: Hidden Helper / Test Setup
```python
#| hide
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd
from netCDF4 import Dataset

from marisco.callbacks import EncodeTimeCB as _EncodeTimeCB, Transformer
from marisco.handlers.pipeline.contracts import HandlerConfig
import marisco.handlers.pipeline.assembly as _assembly

_TIME_UNITS = "seconds since 1970-01-01 00:00:00.0"
_REQUIRED = {"LAT", "LON", "TIME", "NUCLIDE", "VALUE", "UNC", "UNIT"}

with TemporaryDirectory() as _tmp_dir:
    _fixture_path = Path(_tmp_dir) / "transformer-input.nc"
    with Dataset(_fixture_path, "w", format="NETCDF4") as _fixture:
        _fixture.setncatts({
            "id": "transformer-fixture",
            "title": "Self-contained transformer fixture",
            "summary": "Minimal MARIS coordinate and measurement dataset",
            "Conventions": "CF-1.8",
        })
        _fixture.createDimension("obs", 3)
        _lat = _fixture.createVariable("LAT", np.float32, ("obs",))
        _lon = _fixture.createVariable("LON", np.float32, ("obs",))
        _time = _fixture.createVariable("TIME", np.float64, ("obs",))
        _nuclide = _fixture.createVariable("NUCLIDE", str, ("obs",))
        _value = _fixture.createVariable("VALUE", np.float64, ("obs",))
        _unc = _fixture.createVariable("UNC", np.float64, ("obs",))
        _unit = _fixture.createVariable("UNIT", str, ("obs",))

        _lat.setncatts({"standard_name": "latitude", "units": "degrees_north"})
        _lon.setncatts({"standard_name": "longitude", "units": "degrees_east"})
        _time.setncatts({"standard_name": "time", "units": _TIME_UNITS, "calendar": "standard"})
        _lat[:] = [79.5, 80.25, 95.0]
        _lon[:] = [4.2, 5.75, 6.0]
        _time[:] = [1577836800.0, 1577923200.0, 1578009600.0]
        _nuclide[:] = np.array(["Cs-137", "Co-60", "Cs-137"], dtype=object)
        _value[:] = [1.25, 2.50, 99.0]
        _unc[:] = [0.10, 0.20, 9.9]
        _unit[:] = np.array(["Bq/m3", "Bq/m3", "Bq/m3"], dtype=object)

    with Dataset(_fixture_path, "r") as _loaded:
        assert len(_loaded.dimensions["obs"]) == 3
        assert {"LAT", "LON", "TIME"}.issubset(_loaded.variables)
        assert _loaded.getncattr("id") == "transformer-fixture"
        _raw = pd.DataFrame({
            _name: _loaded.variables[_name][:]
            for _name in _REQUIRED
        })
        _raw["TIME"] = pd.to_datetime(_raw["TIME"], unit="s", utc=True)

    _cfg = HandlerConfig(
        module_name="tests.transformer_fixture",
        title="Transformer fixture",
        url="memory://transformer-fixture",
        fname_out=str(Path(_tmp_dir) / "unused.nc"),
        nuclide_lut={"Cs-137": 28, "Co-60": 29},
        unit_lut={"Bq/m3": 9},
    )

    _original_encode_time = _assembly.EncodeTimeCB
    _assembly.EncodeTimeCB = lambda: _EncodeTimeCB(fn_units=lambda: _TIME_UNITS)
    try:
        _chain = build_chain(_cfg)
        _tfm = Transformer({"SEAWATER": _raw}, cbs=_chain)
        _transformed = _tfm()["SEAWATER"]
    finally:
        _assembly.EncodeTimeCB = _original_encode_time

    assert type(_chain[0]).__name__ == "RenameColsCB"
    assert type(_chain[-1]).__name__ == "AddSampleIDCB"
    assert _REQUIRED.issubset(_transformed.columns)
    assert _transformed.shape[0] == 2  # invalid LAT=95 fixture row is rejected
    assert _transformed.index.tolist() == [0, 1]
    np.testing.assert_allclose(_transformed["LAT"], [79.5, 80.25])
    np.testing.assert_allclose(_transformed["LON"], [4.2, 5.75], rtol=1e-6)
    np.testing.assert_allclose(_transformed["TIME"], [1577836800.0, 1577923200.0])
    np.testing.assert_array_equal(_transformed["NUCLIDE"], [28, 29])
    np.testing.assert_array_equal(_transformed["UNIT"], [9, 9])
    np.testing.assert_array_equal(_transformed["SMP_ID"], [1, 2])

    assert _transformed["LAT"].dtype == np.dtype("float64")
    assert _transformed["LON"].dtype == np.dtype("float64")
    assert _transformed["TIME"].dtype.kind in "fi"
    assert _transformed["VALUE"].dtype == np.dtype("float64")
    assert _transformed["UNC"].dtype == np.dtype("float64")
    assert _transformed["NUCLIDE"].dtype.kind in "iu"
    assert _transformed["UNIT"].dtype.kind in "iu"
    assert _transformed["SMP_ID"].dtype.kind in "iu"
```

