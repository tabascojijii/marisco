# DEPENDENCIES

## 概要

このドキュメントは、`marisco` リポジトリが依存する要素を、実行時・開発時・外部サービス・静的資産・Handler 個別前提に分けて整理したものです。

このリポジトリの依存は、単なる Python パッケージ一覧ではありません。実際には次の層に分かれています。

- Python runtime 依存
- Python 開発依存
- 外部 API / 外部サービス依存
- ローカル静的資産依存
- Handler ごとの入力データ依存
- CI / docs / notebook ベース開発依存

## Runtime Python Dependencies

`pyproject.toml` に宣言されている runtime 依存は以下です。

- `pandas`
- `openpyxl`
- `fastcore`
- `rich`
- `tqdm`
- `netcdf4`
- `tomli`
- `tomli-w`
- `shapely`
- `pyzotero`
- `jellyfish`
- `requests`
- `pyarrow`
- `gevent>=22.10.2`

## Observed Runtime Imports

コード上で実際に import されている主要な外部パッケージは以下です。

- `pandas`
- `numpy`
- `fastcore`
- `netCDF4`
- `tqdm`
- `requests`
- `shapely`
- `jellyfish`
- `pyzotero`
- `tomli`
- `tomli_w`
- `rich`
- `cftime`

## Declared vs Observed Gaps

依存宣言と実使用の間にはいくつか差分があります。

- `numpy`
  - 実コードで広く使用されているが、`pyproject.toml` には明示されていない
- `cftime`
  - `callbacks.py` と `metadata.py` で使用されているが、明示されていない
- `openpyxl`
  - 直接 import はされないが、`pandas.read_excel()` の実行に実質必要
- `pyarrow`
  - 宣言されているが、今回確認した主要 runtime コードでは直接使用箇所が見えない
- `gevent`
  - 宣言されているが、今回確認した主要 runtime コードでは直接使用箇所が見えない

`DEPENDENCIES.md` としては、「declared dependencies」と「observed runtime usage」を分けて記載するのが安全です。

## Development Dependencies

`pyproject.toml` の `optional-dependencies.dev` にある開発依存は以下です。

- `nbdev`
- `ipykernel`
- `twine`

加えて、build system として以下に依存します。

- `setuptools>=64`

## Development Tooling

このリポジトリは Jupyter Notebook 正本による開発を前提にしています。

- `nbdev`
  - notebook から Python モジュールを生成
  - notebook から docs を生成
- `Jupyter`
  - notebook 編集と実行の前提
- `ipykernel`
  - Jupyter kernel の前提
- `Quarto`
  - docs 公開パイプラインの基盤

`nbs/nbdev.yml` では docs 出力先が `_docs` に設定され、website 情報も定義されています。

## External Services and APIs

### GitHub

以下の用途で GitHub に依存します。

- `maris_init` による Lookup Table (LUT) ダウンロード
- `maris_init` による `maris-template.nc` ダウンロード
- 一部 Handler の raw データ取得
- docs / source metadata

実際のアクセス先:

- `https://api.github.com/repos/.../contents/...`
- `https://raw.githubusercontent.com/...`

### Zotero

以下の用途で Zotero に依存します。

- NetCDF global attributes 用の書誌メタデータ取得
- CSV 変換時の `REF_ID` 補完

前提:

- `ZOTERO_API_KEY`
- library id `2432820`

### WoRMS

補助的な種名マッチング用途で以下に依存します。

- `https://www.marinespecies.org/rest/AphiaRecordsByMatchNames`

これは主フローの絶対必須ではありませんが、MARIS lookup との照合補助としてコードに存在します。

## Repository-Managed Static Assets

リポジトリ内の静的資産は主に `nbs/files/` にあります。

- `nbs/files/cdl/maris.cdl`
  - NetCDF スキーマの正本
- `nbs/files/nc/maris-template.nc`
  - NetCDF template
- `nbs/files/lut/*.xlsx`
  - LUT 原本
- `nbs/files/csv/`
  - サンプル CSV
- `nbs/files/exploded/`
  - 展開済みサンプルデータ
- `nbs/files/pkl/`
  - 補助 pickle データ

## Runtime Local Assets

実行時には、リポジトリ直下の `nbs/files/` を直接参照するのではなく、`maris_init` が作成する `~/.marisco/` を主に参照します。

`~/.marisco/` に配置されるもの:

- `configs.toml`
- `lut/`
- `cache/`
- `tmp/`
- `maris-template.nc`

## Local Initialization Requirements

`maris_init` は以下を行います。

1. `~/.marisco/` 作成
2. `configs.toml` 作成
3. `lut/`, `cache/`, `tmp/` 作成
4. LUT 一式ダウンロード
5. `maris-template.nc` ダウンロード

実行時の多くのコードは、以下の関数を通じて `.marisco/` 配下を参照します。

- `cfg()`
- `lut_path()`
- `cache_path()`
- `nc_tpl_path()`

したがって、`maris_init` 未実行の状態は実質的に未初期化状態です。

## Lookup Table Dependencies

主に以下の LUT が runtime で参照されます。

- `dbo_area.xlsx`
- `dbo_biogroup.xlsx`
- `dbo_bodypar.xlsx`
- `dbo_counmet.xlsx`
- `dbo_detectlimit.xlsx`
- `dbo_filtered.xlsx`
- `dbo_lab_cleaned.xlsx`
- `dbo_nuclide.xlsx`
- `dbo_prepmet.xlsx`
- `dbo_sampmet.xlsx`
- `dbo_sedtype.xlsx`
- `dbo_species_2024_11_19.xlsx`
- `dbo_unit.xlsx`

これらは `Enums` や各種 `*_lut_path()` 関数を通じて、encoder / decoder / Handler 群に使われます。

## Template and CDL Dependencies

- `nbs/files/cdl/maris.cdl`
  - schema 正本
- `nbs/files/nc/maris-template.nc`
  - template の repository 版
- `~/.marisco/maris-template.nc`
  - 実行時 (runtime) 参照先

注意点:

- `get_time_units()` は NetCDF template を開いて time units を取得する
- つまり template は出力雛形だけでなく、時間変換の基準でもある

## Cache and Tmp Dependencies

### `cache/`

`cache/` は実際に利用されています。

- `Remapper` による pickle cache
- `HELCOM` データのローカル CSV cache
- `OSPAR` データのローカル CSV cache

特に `OSPAR` は `encode()` が `use_cache=True` で動くため、キャッシュ前提が強い設計です。

### `tmp/`

`tmp/` は初期化時に作られますが、今回確認した主要 runtime コードでは明確な直接利用は少なめです。現時点では、将来用途や運用補助のための予約領域とみなすのが妥当です。

## Handler-Specific Dependencies

### HELCOM

- 入力形式
  - sample CSV + measurement CSV を組にして読み込み
- 主入力元
  - `maris-crawlers` の raw GitHub CSV
- 追加前提条件
  - `.marisco/lut/` が必要
  - `cache/` を使ったローカル CSV キャッシュが可能
- 特記事項
  - `BIO` / `SEA` / `SED` を内部 group にマップ
  - unit, species, tissue, sediment, filtered, detection limit の LUT 依存が強い

### OSPAR

- 入力形式
  - sample type ごとの CSV
- 主入力元
  - `maris-crawlers` の raw GitHub CSV
- 追加前提条件
  - `.marisco/lut/` が必要
  - `cache/` 前提が強い
- 特記事項
  - `encode()` は `load_data(..., use_cache=True)` を使う
  - species 補正や tissue remap など BIOTA 向け補正が多い

### TEPCO

- 入力形式
  - 公開 CSV
  - 公開 Excel
  - station master CSV
- 主入力元
  - `radioactivity.nra.go.jp`
  - `raw.githubusercontent.com/RML-IAEA/iaea.orbs/...`
- 追加前提条件
  - `.marisco/lut/` と template が必要
  - 直接的な専用 cache 利用は薄い
- 特記事項
  - 複数外部ソースを突き合わせて georeference
  - `SEAWATER` のみ出力
  - `Bq/L` から `Bq/m3` に換算

### GEOTRACES

- 入力形式
  - ローカル CSV 1 本
- 主入力元
  - 実装上はローカルファイル前提
- 追加前提条件
  - GEOTRACES CSV をユーザーが事前に用意する必要がある
  - `.marisco/lut/` と template が必要
- 特記事項
  - wide -> long -> group dispatch の変形が中心
  - `SEAWATER` / `SUSPENDED_MATTER` に分配

### MARIS legacy

- 入力形式
  - タブ区切り dump (`.txt`)
- 主入力元
  - ローカル dump
- 追加前提条件
  - dump ファイルの事前用意
  - `.marisco/lut/` と template が必要
  - Zotero key を dump 中の `zoterourl` から抽出
- 特記事項
  - `ref_id` ごとに個別 NetCDF を出力
  - `samptype` を内部 group にマップ

## CI and Documentation Dependencies

### CI

GitHub Actions は以下の upstream workflow に依存します。

- `fastai/workflows/nbdev3-ci@master`
- `fastai/workflows/quarto-ghp3@master`

これは、このリポジトリの CI / deploy 挙動が repo 内 YAML だけで自己完結していないことを意味します。

### Documentation Publishing

docs 公開は以下に依存します。

- `nbdev`
- `Quarto`
- GitHub Pages

`deploy.yaml` は `main` / `master` への push と manual dispatch をトリガーにしています。

## Local Development Environment Requirements

ガイド類から読み取れるローカル開発前提は次のとおりです。

- Jupyter notebook 実行環境
- `ipykernel`
- editable install (`pip install -e '.[dev]'`)
- `maris_init`
- Windows では Anaconda Navigator ベース構成が案内されている
- WSL では VS Code Remote Development + Mambaforge ベース構成が案内されている

## System-Level Tooling Dependencies

NetCDF template を再生成する場合、Python パッケージだけでは不十分です。

必要なシステム依存:

- `ncgen`
- `netcdf-bin` または相当する NetCDF-C utilities

用途:

- `nbs/files/cdl/maris.cdl` から `nbs/files/nc/maris-template.nc` を再生成

これは runtime 必須ではなく、template 更新や低レベル開発時の依存です。

## Operational Notes

- `maris_init` 未実行だと `.marisco/` 前提コードが動かない
- `ZOTERO_API_KEY` がないと metadata 系フローに影響する
- `HELCOM` / `OSPAR` / `TEPCO` は外部公開 URL の可用性に左右される
- `OSPAR` は cache 前提が比較的強い
- `GEOTRACES` / `MARIS legacy` はローカル入力ファイル前提が強い
- `README` や install guide には古い前提が残っている可能性がある
- docs / CI は upstream `fastai/workflows` に依存する

## Current Assessment

このリポジトリの依存は、次の 3 つを同時に満たして初めて安定します。

1. Python パッケージがそろっていること
2. `~/.marisco/` が `maris_init` により初期化されていること
3. 対象 Handler に応じた外部またはローカル入力データが利用可能であること

特に `DEPENDENCIES.md` として重要なのは、`marisco` の依存が「pip install だけで完結しない」点です。runtime はローカル資産、外部メタデータ、場合によっては外部公開データ配信先にも依存しています。
