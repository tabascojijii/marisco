"""
NetCDF regression-test comparison helpers.

Provides ``assert_netcdf_regression`` to compare two ``.nc`` files
for structural, attribute, and value equality, using ``xarray``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import xarray as xr

# ---------------------------------------------------------------------------
# Default set of global attributes that are allowed to differ between runs
# (timestamps, local paths, etc.)
# ---------------------------------------------------------------------------
DEFAULT_IGNORE_GLOBAL_ATTRS: frozenset[str] = frozenset(
    {
        "date_created",
        "date_modified",
        "history",
        "source",
        "publisher_postprocess_logs",
    }
)

DEFAULT_IGNORE_VARIABLE_ATTRS: frozenset[str] = frozenset(
    {
        "ancillary_variables",
    }
)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def assert_netcdf_regression(
    actual_path: str | Path,
    golden_path: str | Path,
    *,
    rtol: float = 1e-7,
    atol: float = 1e-12,
    ignore_global_attrs: set[str] | None = None,
    ignore_variable_attrs: set[str] | None = None,
    exclude_variables: set[str] | None = None,
    check_structure: bool = True,
    check_attrs: bool = True,
    check_values: bool = True,
) -> None:
    """
    Assert that two NetCDF files are structurally and numerically identical.

    Parameters
    ----------
    actual_path:
        Path to the file produced by the current code.
    golden_path:
        Path to the reference (golden) file.
    rtol, atol:
        Relative / absolute tolerance passed to ``np.allclose``
        for floating-point variables.
    ignore_global_attrs:
        Global attribute keys to skip during comparison.
    ignore_variable_attrs:
        Variable-level attribute keys to skip during comparison.
    exclude_variables:
        Variable names to skip entirely.
    check_structure:
        If True, check that groups, variables, dimensions and dtypes match.
    check_attrs:
        If True, check global and per-variable attributes.
    check_values:
        If True, check numerical equality.
    """
    if ignore_global_attrs is None:
        ignore_global_attrs = set(DEFAULT_IGNORE_GLOBAL_ATTRS)
    if ignore_variable_attrs is None:
        ignore_variable_attrs = set(DEFAULT_IGNORE_VARIABLE_ATTRS)
    if exclude_variables is None:
        exclude_variables = set()

    actual_path = Path(actual_path)
    golden_path = Path(golden_path)

    assert actual_path.exists(), f"Actual file not found: {actual_path}"
    assert golden_path.exists(), f"Golden file not found: {golden_path}"

    # -- collect all group names --
    actual_groups = _collect_groups(actual_path)
    golden_groups = _collect_groups(golden_path)

    if check_structure:
        _assert_groups_match(actual_groups, golden_groups)

    # -- compare each group --
    for grp in golden_groups:
        if grp not in actual_groups:
            if check_structure:
                continue
            raise AssertionError(f"Group '{grp}' missing in actual file")

        grp_arg = grp if grp else None  # None = root group
        grp_actual = xr.open_dataset(actual_path, group=grp_arg, engine="netcdf4")
        grp_golden = xr.open_dataset(golden_path, group=grp_arg, engine="netcdf4")
        try:
            _assert_group_regression(
                grp_actual,
                grp_golden,
                group_path=grp or "/",
                rtol=rtol,
                atol=atol,
                ignore_global_attrs=ignore_global_attrs,
                ignore_variable_attrs=ignore_variable_attrs,
                exclude_variables=exclude_variables,
                check_structure=check_structure,
                check_attrs=check_attrs,
                check_values=check_values,
            )
        finally:
            grp_actual.close()
            grp_golden.close()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _collect_groups(path: Path) -> list[str]:
    """Return list of group paths (empty string for root)."""
    from netCDF4 import Dataset

    groups: list[str] = [""]
    with Dataset(str(path), "r") as ds:
        stack = [("", ds.groups)]
        while stack:
            prefix, grp_dict = stack.pop()
            for name, grp in grp_dict.items():
                grp_path = f"{prefix}/{name}" if prefix else name
                groups.append(grp_path)
                stack.append((grp_path, grp.groups))
    return groups


def _assert_groups_match(
    actual: list[str],
    golden: list[str],
) -> None:
    """Check that both files contain the same set of groups."""
    actual_set = set(actual)
    golden_set = set(golden)
    missing = golden_set - actual_set
    extra = actual_set - golden_set
    msg_parts = []
    if missing:
        msg_parts.append(f"Missing groups (present in golden, absent in actual): {sorted(missing)}")
    if extra:
        msg_parts.append(f"Extra groups (present in actual, absent in golden): {sorted(extra)}")
    if msg_parts:
        raise AssertionError("Group mismatch:\n  " + "\n  ".join(msg_parts))


def _assert_group_regression(
    actual: xr.Dataset,
    golden: xr.Dataset,
    *,
    group_path: str,
    rtol: float,
    atol: float,
    ignore_global_attrs: set[str],
    ignore_variable_attrs: set[str],
    exclude_variables: set[str],
    check_structure: bool,
    check_attrs: bool,
    check_values: bool,
) -> None:
    """Compare a single group (or root) between actual and golden."""

    if check_structure:
        _assert_variable_structure(actual, golden, group_path, exclude_variables)
        _assert_dimension_sizes(actual, golden, group_path, exclude_variables)

    if check_attrs:
        _assert_attrs_match(
            actual.attrs,
            golden.attrs,
            label=f"[Group {group_path}] Global attributes",
            ignore_keys=ignore_global_attrs,
        )
        for var_name in actual.data_vars:
            if var_name in exclude_variables:
                continue
            if var_name not in golden.data_vars:
                continue
            _assert_attrs_match(
                actual[var_name].attrs,
                golden[var_name].attrs,
                label=f"[Group {group_path}:{var_name}] Attributes",
                ignore_keys=ignore_variable_attrs,
            )

    if check_values:
        for var_name in actual.data_vars:
            if var_name in exclude_variables:
                continue
            if var_name not in golden.data_vars:
                continue
            _assert_values_match(
                actual[var_name].values,
                golden[var_name].values,
                golden[var_name].dtype,
                label=f"[Group {group_path}:{var_name}]",
                rtol=rtol,
                atol=atol,
            )


def _assert_variable_structure(
    actual: xr.Dataset,
    golden: xr.Dataset,
    group_path: str,
    exclude_variables: set[str],
) -> None:
    """Check that the variable sets match."""
    actual_vars = set(actual.data_vars) | set(actual.coords)
    golden_vars = set(golden.data_vars) | set(golden.coords)
    missing_vars = golden_vars - actual_vars - exclude_variables
    extra_vars = actual_vars - golden_vars - exclude_variables
    msg_parts = []
    if missing_vars:
        msg_parts.append(f"  Missing variables: {sorted(missing_vars)}")
    if extra_vars:
        msg_parts.append(f"  Extra variables: {sorted(extra_vars)}")
    if msg_parts:
        raise AssertionError(
            f"[Group {group_path}] Variable structure mismatch:\n"
            + "\n".join(msg_parts)
        )


def _assert_dimension_sizes(
    actual: xr.Dataset,
    golden: xr.Dataset,
    group_path: str,
    exclude_variables: set[str],
) -> None:
    """Check that common variables have the same dimension sizes."""
    common = set(golden.data_vars) & set(actual.data_vars)
    for var_name in common:
        if var_name in exclude_variables:
            continue
        for dim in golden[var_name].dims:
            actual_size = actual.sizes.get(dim)
            golden_size = golden.sizes.get(dim)
            if actual_size != golden_size:
                raise AssertionError(
                    f"[Group {group_path}:{var_name}] "
                    f"Dimension '{dim}' size differs: "
                    f"actual={actual_size}, golden={golden_size}"
                )


def _assert_values_match(
    actual_values,
    golden_values,
    golden_dtype: np.dtype,
    *,
    label: str,
    rtol: float,
    atol: float,
) -> None:
    """Compare values of a single variable."""
    gv = golden_values
    av = actual_values

    # Handle masked arrays
    if isinstance(gv, np.ma.MaskedArray):
        gv = gv.filled(np.nan)
    if isinstance(av, np.ma.MaskedArray):
        av = av.filled(np.nan)

    if np.issubdtype(golden_dtype, np.floating):
        if not np.allclose(av, gv, rtol=rtol, atol=atol, equal_nan=True):
            diff = np.abs(av - gv)
            max_diff = float(np.nanmax(diff))
            raise AssertionError(
                f"{label} Values differ beyond tolerance "
                f"(rtol={rtol}, atol={atol}); max diff = {max_diff:.4e}"
            )
    else:
        equal = av == gv
        if hasattr(equal, "all") and not equal.all():
            raise AssertionError(
                f"{label} Non-float values differ"
            )


def _assert_attrs_match(
    actual: dict,
    golden: dict,
    *,
    label: str,
    ignore_keys: set[str],
) -> None:
    """Compare two attribute dictionaries, ignoring select keys."""
    actual_filtered = {k: v for k, v in actual.items() if k not in ignore_keys}
    golden_filtered = {k: v for k, v in golden.items() if k not in ignore_keys}

    if actual_filtered != golden_filtered:
        all_keys = set(actual_filtered) | set(golden_filtered)
        diffs = []
        for k in sorted(all_keys):
            a_val = actual_filtered.get(k, "<MISSING>")
            g_val = golden_filtered.get(k, "<MISSING>")
            if a_val != g_val:
                diffs.append(f"    {k}: actual={a_val!r}, golden={g_val!r}")
        msg = f"{label} differ:\n" + "\n".join(diffs)
        raise AssertionError(msg)
</｜｜DSML｜｜parameter>
<task_progress string="true">- [x] Create tests/ directory structure
- [x] Create nc_compare.py with assert_netcdf_regression
- [x] Create sample fixture data for HELCOM
- [ ] Create golden_generation.py helper script
- [ ] Generate helcom_golden.nc
- [ ] Create and run pytest test_regression_helcom.py -> PASSED</task_progress>
</｜｜DSML｜｜invoke>
</｜｜DSML｜｜tool_calls>