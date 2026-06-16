#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

import nbformat


def strip_notebook(path: Path) -> bool:
    nb = nbformat.read(path, as_version=nbformat.NO_CONVERT)
    changed = False
    for cell in nb.cells:
        if cell.get("cell_type") != "code":
            continue
        if cell.get("outputs"):
            cell["outputs"] = []
            changed = True
        if cell.get("execution_count") is not None:
            cell["execution_count"] = None
            changed = True
    if changed:
        nbformat.write(nb, path)
    return changed


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        return 0
    for raw_path in argv[1:]:
        path = Path(raw_path)
        if not path.exists():
            print(f"[strip-notebook-outputs] missing file: {path}", file=sys.stderr)
            return 1
        if path.suffix != ".ipynb":
            print(f"[strip-notebook-outputs] not a notebook: {path}", file=sys.stderr)
            return 1
        strip_notebook(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
