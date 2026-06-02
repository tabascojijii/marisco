# Pydantic導入提案書

## 1. 提案の要旨

本リポジトリでは、CLI入力、設定ファイル、外部API応答、各handlerへの表データ入力に対する事前検証が限定的であり、異常系の多くが「処理途中で落ちる」「空のDataFrameのまま進む」「`print`のみで原因が曖昧になる」という形で現れている。

このため、デバッグ時に以下のようなコストが発生しやすい。

- 失敗箇所が入口ではなく後段のcallbackで初めて顕在化する
- ユーザー入力ミスとデータ構造不整合の区別がつきにくい
- Zotero応答の欠損や設定不備が、辞書アクセス失敗として遅れて現れる
- handlerごとに入力期待値が暗黙的で、保守時の認知負荷が高い

これを改善するため、**Pydanticを「境界」に限定導入**し、あわせて**DataFrame検証はPydanticではなく別手段で補完**することを提案する。

## 2. 現状の課題

### 2.1 CLI入力の検証が最小限

`maris_to_nc` は `ds` の値だけを検証し、`src` や `dest` の妥当性は見ていない。

- 許可される `ds` は `helcom`, `geotraces`, `tepco`, `ospar` の4つのみ
- `src` はコード上ほぼ `geotraces` のみで使用
- `dest` の拡張子や出力先ルールは未検証

根拠:

- `marisco/cli/to_nc.py:23`
- `marisco/cli/to_nc.py:34`
- `marisco/handlers/geotraces.py:283`
- `marisco/handlers/helcom.py:667`
- `marisco/handlers/ospar.py:520`
- `marisco/handlers/tepco.py:455`

### 2.2 設定値が辞書でそのまま流通している

設定は `CONFIGS` からTOMLに書き出され、`cfg()` でそのまま辞書として読み戻される。構造保証、必須値検証、型保証がない。

代表項目:

- `gh.owner`
- `gh.repo`
- `dirs.lut`, `dirs.cache`, `dirs.tmp`
- `paths.nc_template`, `paths.luts`
- `zotero.api_key`, `zotero.lib_id`

根拠:

- `marisco/configs.py:264`
- `marisco/configs.py:279`
- `marisco/inout.py:39`

### 2.3 Zotero応答への依存が強いが、応答スキーマが未定義

Zotero関連処理では、以下の項目に直接アクセスしている。

- `item['data']['title']`
- `item['data']['abstractNote']`
- `item['data']['creators']`
- `item['data']['archiveLocation']`
- `item['key']`

`ResourceNotFound` は一部捕捉しているが、`api_key` 未設定、ネットワーク異常、レスポンス項目欠損などは構造化されていない。

根拠:

- `marisco/metadata.py:97`
- `marisco/metadata.py:105`
- `marisco/metadata.py:108`
- `marisco/metadata.py:111`
- `marisco/metadata.py:125`
- `marisco/netcdf2csv.py:205`

### 2.4 DataFrame入力の期待構造が暗黙的

各handlerは `pd.read_csv()` や `pd.read_excel()` の後、想定列が存在する前提でcallbackを実行している。

例:

- `geotraces` は読込直後に列選択と列名パターン抽出へ進む
- `helcom` は `key` による2CSV結合を前提にする
- `ospar` は読込失敗時に空DataFrameを返しうる
- `tepco` はCSV/Excelのレイアウト依存が強い

根拠:

- `marisco/handlers/geotraces.py:284`
- `marisco/handlers/helcom.py:121`
- `marisco/handlers/ospar.py:107`
- `marisco/handlers/tepco.py:78`
- `marisco/handlers/tepco.py:112`

### 2.5 例外の品質が均一でない

現状は、失敗時に `print` のみ、あるいは空DataFrame返却で処理継続する箇所がある。

代表例:

- handler import失敗時に `print` のみ
- OSPAR読込失敗時に空DataFrame返却
- HELCOM座標変換失敗時に値をそのまま返す

根拠:

- `marisco/cli/to_nc.py:14`
- `marisco/handlers/ospar.py:113`
- `marisco/handlers/helcom.py:624`

## 3. 導入方針

### 3.1 基本方針

Pydanticは本リポジトリ全体に一律適用するのではなく、**入力境界と外部境界に限定導入**する。

対象:

- CLI引数
- `configs.toml`
- 環境変数
- Zotero API応答

対象外または別手段推奨:

- `pandas.DataFrame` 本体の列スキーマ検証

### 3.2 なぜ境界限定導入か

このリポジトリの中心はDataFrame変換パイプラインであり、そこを全面Pydantic化するのは効果に対してコストが高い。

一方で、入口の値と外部依存の値は構造が比較的安定しており、Pydanticの効果が出やすい。

期待できる改善:

- 失敗をcallback内部ではなく入口で検出できる
- エラーメッセージをユーザー向けに具体化できる
- 設定構造の変更影響を見つけやすくなる
- Zotero応答欠損時の原因切り分けが容易になる

## 4. Pydantic適用候補

### 4.1 第一優先: 設定モデル

#### 対象

- `CONFIGS`
- `cfg()` が返すTOML内容
- `ZOTERO_API_KEY`

#### モデル候補

- `GitHubConfig`
- `DirectoryConfig`
- `PathConfig`
- `ZoteroConfig`
- `AppConfig`

#### 導入効果

- 必須キー不足の早期検出
- 文字列/パス/空値の判定明確化
- 設定の利用側での辞書アクセス削減

#### 想定例

```python
class ZoteroConfig(BaseModel):
    api_key: str
    lib_id: str

class AppConfig(BaseModel):
    gh: GitHubConfig
    dirs: DirectoryConfig
    paths: PathConfig
    zotero: ZoteroConfig
```

### 4.2 第二優先: CLI入力モデル

#### 対象

- `maris_to_nc`
- `maris_db_to_nc`

#### 検証したい内容

- `ds` は許可値のみ
- `geotraces` の場合は `src` 必須
- `helcom/ospar/tepco` の場合は `src` 無視または警告
- `dest` は `.nc` 推奨または必須
- `ref_ids` は整数配列に正規化

#### 導入効果

- 利用者の入力ミスを即時検出
- README記載ルールと実装ルールの一致
- handler側の前提を簡潔化

### 4.3 第三優先: Zotero応答モデル

#### 対象

- `ZoteroItem`
- `ZoteroCB`
- `AddZoteroArchiveLocationCB`

#### 検証したい内容

- `key`
- `data.title`
- `data.abstractNote`
- `data.creators`
- `data.archiveLocation`

#### 導入効果

- 辞書アクセス由来の曖昧な失敗を減らせる
- 欠損項目を明示的に扱える
- `archiveLocation` の整数変換失敗を局所化できる

## 5. DataFrame検証は別手段を推奨

### 5.1 理由

Pydanticは辞書やオブジェクトの検証には強いが、DataFrameの列構造・列型・空値割合・列名集合の検証には最適ではない。

### 5.2 推奨手段

候補は2つ。

#### A. `pandera` 導入

用途:

- 必須列確認
- 列型確認
- nullable制約
- 日付/数値列のチェック

向いているケース:

- handlerごとに明確な入力表スキーマがある場合

#### B. 自前の軽量検証関数

用途:

- `validate_required_columns(df, cols, context)`
- `validate_non_empty_df(df, context)`
- `validate_merge_key(df, key, context)`

向いているケース:

- まず低コストで改善したい場合

### 5.3 本リポジトリでの適用候補

- `geotraces`: 必須列・日時列・経度列
- `helcom`: `key` と各CSVペアの存在
- `ospar`: 空DataFrame禁止、主要列確認
- `tepco`: sheet構造、セクション境界、必須列確認

## 6. 想定アーキテクチャ

### 6.1 設定読込

現状:

- `read_toml()` → 辞書

提案:

- `read_toml()` → `AppConfig.model_validate(...)`

### 6.2 CLI実行

現状:

- `@call_parse` で受け取って、そのままhandlerへ渡す

提案:

- 受け取り後に `CliArgsModel` で検証
- 正規化済み値のみhandlerへ渡す

### 6.3 Zotero応答

現状:

- `zot.item()` の辞書を直接利用

提案:

- 取得辞書を `ZoteroRecordModel` で検証
- 必須項目欠損時は意味のある例外に変換

## 7. 導入優先順位

### フェーズ1: 最小導入

- 設定モデル
- CLI入力モデル

目的:

- 入口の失敗をすぐ分かる形にする

### フェーズ2: 外部依存の安定化

- Zotero応答モデル
- `archiveLocation` 変換の明示化

目的:

- 外部API起因の不具合切り分け改善

### フェーズ3: 表データの品質向上

- `pandera` または軽量検証関数の導入

目的:

- handlerごとの暗黙前提を明文化

## 8. 期待効果

### 8.1 デバッグ効率

- 失敗位置が入口に寄る
- メッセージが具体化する
- 再現条件が説明しやすくなる

### 8.2 保守性

- 設定構造変更時の影響範囲を把握しやすい
- 外部API仕様変更を検知しやすい
- handler前提を文書化しやすい

### 8.3 ユーザー体験

- CLIエラーが分かりやすくなる
- 初期設定ミスにすぐ気づける
- 不正入力時の修正案を出しやすい

## 9. リスクと注意点

### 9.1 Python互換性

本プロジェクトは `requires-python = ">=3.7"` である。Pydanticのバージョン選定には互換性確認が必要。

根拠:

- `pyproject.toml:10`

### 9.2 全面導入は過剰

DataFrame変換本体までPydantic化すると、実装負荷に対して効果が薄くなる可能性が高い。

### 9.3 notebook由来コードとの整合

本リポジトリは `nbdev` ベースで自動生成コードを含むため、導入箇所は notebook 側で管理できるかも確認が必要。

## 10. 提案内容の要約

本リポジトリに対する提案は、**Pydanticの全面導入ではなく、境界限定導入**である。

具体的には以下を推奨する。

1. `configs.toml` と環境変数をPydanticで検証する
2. `maris_to_nc` と `maris_db_to_nc` のCLI入力をPydanticで検証する
3. Zotero API応答をPydanticで検証する
4. DataFrame検証は `pandera` または軽量検証関数で補う

この順序で進めることで、導入コストを抑えつつ、デバッグ効率と保守性を高められる。

## 11. 次アクション案

- 方針合意後、まず `AppConfig` と `CliArgsModel` の試作を行う
- `geotraces` を対象に最小導入して、効果と実装量を確認する
- その結果を踏まえて、ZoteroモデルとDataFrame検証方針を決定する
