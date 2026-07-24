.PHONY: install sync check test security complexity smoke profile diff-golden diff-golden-save ci

install:  ## Install package + dev tooling (ruff, mypy, vulture, bandit, pytest-cov, radon, ...)
	pip install -e ".[dev]"

sync:  ## Resync nbs/*.pct.py <-> nbs/*.ipynb, then regenerate marisco/*.py
	jupytext --sync "**/*.ipynb"
	nbdev_export

check:  ## Lint + type check + dead-code scan (see CONTRIBUTING.md before deleting on vulture's word)
	ruff check .
	mypy .
	vulture .

test:  ## pytest with coverage report (tests/ — see CONTRIBUTING.md: coverage is a signal, not a target)
	pytest --cov=marisco --cov-report=term-missing tests/

smoke:  ## Legacy handler smoke tests (no network)
	python tools/test_harness.py --handler mock

security:  ## Static security scan of the exported package (see CONTRIBUTING.md for false-positive handling)
	bandit -r marisco/ -ll

complexity:  ## Cyclomatic complexity, rank C (complexity > 10) and worse only
	radon cc . -n C -e ".venv/*,build/*,__pycache__/*"

profile:  ## Profile a raw provider file: column stats + fuzzy-match against MARIS LUTs
	@# Usage: make profile SRC=path/to/file.csv [LUT="nuclide=NUCLIDE rubin=SPECIES"]
	python tools/profile_source.py $(SRC) $(foreach l,$(LUT),--lut $(l))

diff-golden:  ## Compare a handler's encode() output against its stored golden snapshot
	@# Usage: make diff-golden HANDLER=helcom
	python tools/diff_golden.py $(HANDLER)

diff-golden-save:  ## (Re)create the golden snapshot for a handler after a reviewed, intentional change
	@# Usage: make diff-golden-save HANDLER=helcom
	python tools/diff_golden.py $(HANDLER) --save

ci: check security complexity test  ## Everything CI runs
