# CLAUDE.md — marisco Agent Instructions

Pipeline: `raw data → Transformer (Callbacks) → GlobAttrsFeeder → NetCDFEncoder → .nc`

---

## The single most important rule

**Edit `nbs/**/*.pct.py` (Jupytext percent format, `# %%`) files only.** Never edit
`.ipynb` JSON directly, and never edit `marisco/*.py` directly (nbdev export output).
`.pct.py` and `.ipynb` are both git-tracked and kept in sync by Jupytext — the `.ipynb`
exists so anyone can open it straight from GitHub/GUI tools without needing the CLI.
After editing a `.pct.py` file, sync it back: `jupytext --sync <file>`.

Full workflow, sync points, and the `.pct.py` vs `.ipynb` vs `marisco/*.py` distinction:
[`CONTRIBUTING.md`](CONTRIBUTING.md).

Parameter docs use [`fastcore.docments`](https://fastcore.fast.ai/docments.html) —
inline `#` comment beside the type annotation, never in the docstring body.

---

## Key commands

```console
jupytext --sync **/*.ipynb                                       # resync all pairs (session start / branch switch)
jupytext --sync <file.pct.py>                                     # resync one pair (after editing)
nbdev_export                                                      # .ipynb -> marisco/*.py (still required, see CONTRIBUTING.md)
python tools/compile_notebook_context.py                         # before every notebook commit
python tools/test_harness.py --handler mock                      # smoke-test (no network)
python tools/test_harness.py --handler helcom                    # dry-run (no Zotero key)
python tools/test_harness.py --handler helcom --encode --audit   # full encode + structural audit
```

---

## AI brake protocol — 7 standing orders *(self-apply; no human prompt required)*

1. **Pre-implementation** — docstring needs "and/also/as well as" or ≥ 3 `if` branches → stop, slice, confirm.
2. **Existing-CB patch** — fixing by adding `if` to an existing CB → propose a new CB first.
3. **Test-report** — never "N PASS" alone; append concern-count per CB touched; flag ≥ 3 as `⚠`.
4. **Branch guardrail** — new branch without `CLAUDE.md` → merge from `main` immediately.
5. **Knowledge externalization** — any literal / hardcoded number inside `__call__`/`each_grp` → stop, extract to `*_LUT`.
6. **Fail-Fast** — `errors='coerce'`, `fillna()`, `try-except pass`, silent `if col in df`, `dropna()` inside CB → prohibited.
7. **Immutability** — `inplace=True` anywhere, or mutating a df the current CB doesn't own → prohibited. The `df` argument in `each_grp`/`__call__` *is* `tfm.dfs[grp]` (no copy) so direct column assignment on it is exempt; rebind via reassignment for everything else. Never repurpose a CB outside its declared job (e.g. `RemapCB(lut={})` as a constant-setter) — write a dedicated CB instead.

---

## Go deeper

| What | Where |
|------|-------|
| Jupytext workflow, sync points, `nbs/*.py` vs `marisco/*.py` | [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| Codebase structure & tool roles | [`docs/architecture.md`](docs/architecture.md) |
| Strict/Soft CB 設計思想・SRP 分離原則・CB 目的外流用禁止 | [`docs/developer/architecture_principles.md`](docs/developer/architecture_principles.md) |
| ZERO ast.If 原則・Pydantic 規約・Immutability/CoW 規約・Good/Bad 例 | [`docs/developer/code_style_guards.md`](docs/developer/code_style_guards.md) |
| AI 自律統治・認知バリア・ブレーキ詳細 | [`docs/developer/agent_guidelines.md`](docs/developer/agent_guidelines.md) |
| CB 設計 §§1–5 詳細・Fail-Fast 完全版 | [`nbs/reference/cb-design-rules.md`](nbs/reference/cb-design-rules.md) |
| Titanica 解剖・Aufheben 歴史 | [`nbs/reference/titanica-meltpattern-refactoring.md`](nbs/reference/titanica-meltpattern-refactoring.md) |
| Handler 執筆ガイド | [`nbs/how-to/writing-a-handler.ipynb`](nbs/how-to/writing-a-handler.ipynb) |
| GeneralHandler 2.0 全体構造・YAMLスキーマ・11本レイル・フェーズ分割 | [`docs/general-handler.md`](docs/general-handler.md) |
