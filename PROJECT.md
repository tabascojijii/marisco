# PROJECT

## 概要

`marisco` は、IAEA の MARIS (Marine Radioactivity Information System) 向けデータ変換ツール群を提供する Python パッケージです。主な役割は、海洋放射能データをデータ提供者ごとの形式から MARIS 標準の NetCDF4 形式へ変換し、必要に応じて CSV へ再変換することです。

このリポジトリは `nbdev` ベースで構成されており、Jupyter Notebook を実装の正本として管理し、そこから Python モジュールを自動生成します。そのため、`marisco/` 配下は配布・実行用コード、`nbs/` 配下は設計説明と実装の正本、という役割分担になっています。

## 目的

- データ提供者ごとに異なる海洋放射能データを MARIS 標準へ正規化する
- MARIS 互換の NetCDF4 ファイルを生成する
- MARIS の既存運用で必要な CSV 形式へ再出力する
- 変換処理とその背景説明を notebook とコードで一体管理する

## 主要ユースケース

- `HELCOM`、`OSPAR`、`TEPCO`、`GEOTRACES` の各データセットを NetCDF4 に変換する
- MARIS Master Database のダンプを一括または参照 ID 単位で NetCDF4 に変換する
- 生成済み NetCDF4 を MARIS Standard / OpenRefine 系 CSV に変換する
- lookup table、NetCDF テンプレート、設定ファイルをローカルに初期配置する

## アーキテクチャ

### 1. notebook 正本

`nbs/` 配下の notebook が実装の正本です。

- `nbs/index.ipynb`: プロジェクト全体の説明
- `nbs/handlers/*.ipynb`: データ提供者ごとの変換ロジック
- `nbs/api/*.ipynb`: 共通 API、エンコーダ、デコーダ、設定、メタデータ処理
- `nbs/cli/*.ipynb`: CLI 実装

### 2. 自動生成された配布コード

`marisco/` 配下の Python ファイルは notebook から自動生成されています。

- `marisco/cli/`: CLI エントリポイント
- `marisco/handlers/`: ハンドラ実装
- `marisco/encoders.py`: DataFrame 群から NetCDF4 を生成
- `marisco/netcdf2csv.py`: NetCDF4 から CSV を生成
- `marisco/configs.py`: 変数名、列名、enum LUT、ローカル設定の定義
- `marisco/metadata.py`: NetCDF グローバル属性や Zotero メタデータの付与
- `marisco/utils.py`: LUT 変換、ダウンロード、NetCDF 内容抽出などの共通処理

### 3. テンプレートと参照データ

`nbs/files/` には NetCDF 生成や変換処理に必要な参照データが含まれます。

- `nbs/files/cdl/maris.cdl`: MARIS NetCDF テンプレートの元定義
- `nbs/files/nc/maris-template.nc`: NetCDF テンプレート
- `nbs/files/lut/*.xlsx`: lookup table 群
- `nbs/files/csv/`, `nbs/files/exploded/`, `nbs/files/pkl/`: サンプル・検証用データ

## データフロー

### 初期化

`maris_init` はユーザー環境のホーム配下に `.marisco/` ディレクトリを作成し、以下を配置します。

- `configs.toml`
- lookup table 一式
- `maris-template.nc`

初期化後の実行時設定や LUT 参照は、この `.marisco/` を基準に行われます。

### エンコード

`maris_to_nc` または `maris_db_to_nc` は、各ハンドラを通して入力データを DataFrame 群へ正規化し、`NetCDFEncoder` に渡して NetCDF4 を生成します。

典型的な流れは次のとおりです。

1. 入力データ読込
2. 列名正規化
3. 単位・核種・生物種・検出限界などの lookup remap
4. 時刻、緯度経度、深度、サンプル ID の整形
5. Zotero と内部計算に基づくグローバル属性生成
6. NetCDF テンプレートに従った group / variable / enum の書き込み

### デコード

`maris_nc_to_csv` は NetCDF から各 group を DataFrame として抽出し、必要な enum デコード、サンプル種別列追加、分類情報付与、Zotero 由来の参照 ID 付与を行ったうえで CSV を出力します。

## CLI コマンド

- `maris_init`
  - 設定、LUT、NetCDF テンプレートをローカルへ配置
- `maris_to_nc`
  - `helcom` / `geotraces` / `tepco` / `ospar` を NetCDF4 化
- `maris_db_to_nc`
  - MARIS legacy dump を NetCDF4 化
- `maris_nc_to_csv`
  - NetCDF4 を MARIS 向け CSV に変換

CLI 定義は `pyproject.toml` の `project.scripts` と `marisco/cli/*.py` にあります。

## ハンドラ一覧

現時点で確認できるハンドラは以下です。

- `marisco.handlers.helcom`
  - HELCOM データを MARIS 標準へ整形
- `marisco.handlers.ospar`
  - OSPAR データを MARIS 標準へ整形
- `marisco.handlers.tepco`
  - TEPCO Fukushima 監視データを MARIS 標準へ整形
- `marisco.handlers.geotraces`
  - GEOTRACES データを MARIS 標準へ整形
- `marisco.handlers.maris_legacy`
  - MARIS Master Database ダンプをバッチ変換

各ハンドラは notebook 冒頭に「対象データ」「変換意図」「主要処理」を説明しており、コードとドキュメントを兼ねています。

## 主要ディレクトリ

- `marisco/`
  - 実行される本体パッケージ
- `marisco/cli/`
  - CLI エントリポイント
- `marisco/handlers/`
  - データ提供者別の変換処理
- `nbs/`
  - notebook 正本
- `nbs/files/`
  - テンプレート、LUT、サンプルデータ
- `install_configure_guide/`
  - 開発・利用環境のセットアップ補助資料
- `.github/workflows/`
  - CI / GitHub Pages デプロイ
- `docs/`
  - このリポジトリでは主に監査・運用系の補助文書

## 外部依存

### Python 依存

`pyproject.toml` では、主に以下へ依存しています。

- `pandas`
- `openpyxl`
- `fastcore`
- `rich`
- `tqdm`
- `netcdf4`
- `tomli`, `tomli-w`
- `shapely`
- `pyzotero`
- `jellyfish`
- `requests`
- `pyarrow`
- `gevent`

### 外部サービス・外部データ

- GitHub raw / contents API
  - LUT や `maris-template.nc` のダウンロードに利用
- Zotero
  - データセットの書誌メタデータ取得に利用
- データソース別の外部 CSV / dump
  - ハンドラごとに取得元や入力形式が異なる

## 開発・ビルドの前提

- 実装変更は原則として `nbs/` 側 notebook を正本として行うのが自然です
- `marisco/` 側は nbdev により生成されるため、直接編集より notebook 更新が本筋です
- NetCDF テンプレートは `nbs/files/cdl/maris.cdl` から `ncgen` で再生成できます
- ドキュメントサイトは Quarto / nbdev 構成で GitHub Pages へデプロイされます

## 運用上の注意

- `ZOTERO_API_KEY` が未設定だと Zotero メタデータ取得を伴う処理に影響します
- 実行前に `maris_init` による `.marisco/` 初期化が前提です
- ハンドラの一部は外部 URL やキャッシュ済みファイルに依存します
- `README.md` は概説として有用ですが、生成途中の会話断片が混入しているため、厳密な参照元としては `nbs/index.ipynb` と実装コードの方が信頼できます
- `docs/` 配下はプロダクト仕様より監査・補助文書寄りなので、機能把握の主資料には向きません

## まず読むべきファイル

新しくこのリポジトリを把握する人向けの推奨順です。

1. `README.md`
2. `pyproject.toml`
3. `nbs/index.ipynb`
4. `marisco/cli/*.py`
5. `marisco/configs.py`
6. `marisco/encoders.py`
7. `marisco/netcdf2csv.py`
8. `marisco/handlers/*.py`
9. 必要に応じて対応する `nbs/handlers/*.ipynb`

## 現時点の理解

このリポジトリは単なる変換スクリプト集ではなく、MARIS 標準化パイプラインを notebook 主導で管理するためのパッケージです。中心概念は「ハンドラ」であり、各ハンドラがデータ提供者固有の差異を吸収し、共通の NetCDF / CSV ワークフローに接続しています。
