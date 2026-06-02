# Pydantic導入提案書

## 1. 提案の要旨

本リポジトリでは、CLI入力、設定ファイル、外部API応答、各handlerへの表データ入力に対する事前検証が限定的であり、異常系の多くが「処理途中で落ちる」「空のDataFrameのまま進む」「`print`のみで原因が曖昧になる」という形で現れている。

このため、デバッグ時に以下のようなコストが発生しやすい。

- 失敗箇所が入口ではなく後段のcallbackで初めて顕在化する
- ユーザー入力ミスとデータ構造不整合の区別がつきにくい
- Zotero応答の欠損や設定不備が、辞書アクセス失敗として遅れて現れる
- handlerごとに入力期待値が暗黙的で、保守時の認知負荷が高い

これを改善するため、**Pydanticを「境界」に限定導入**し、あわせて**DataFrame検証はPydanticではなく別手段で補完**することを提案する。

ここで重要なのは、**Pydanticは入力データをきれいにするためのものではない**という点である。  
Pydanticの役割は、**「この値は少なくともここまでは守ってほしい」**という境界契約を宣言することにある。

したがって本提案は、外部データの揺れを入口で一律排除するものではない。  
**汚いデータの補正・表記ゆれ吸収・変換ロジックは、引き続き handler / callback 側の責務として残す**ことを前提とする。

ただし、本リポジトリは `nbdev` を用いており、実装変更の正本は `marisco/*.py` ではなく **`nbs/` 以下の notebook** である。  
したがって本提案は、**生成コードを直接編集する方針ではなく、notebookを編集する方針**を前提に進める。

## 2. nbdev運用の監査結果

### 2.1 本リポジトリは notebook 正本の構成である

生成コードの先頭には、対応する notebook が明記されている。

例:

- `marisco/metadata.py` → `nbs/api/metadata.ipynb`
- `marisco/configs.py` → `nbs/api/configs.ipynb`
- `marisco/netcdf2csv.py` → `nbs/api/netcdf2csv.ipynb`
- `marisco/cli/to_nc.py` → `nbs/cli/to_nc.ipynb`
- `marisco/handlers/helcom.py` → `nbs/handlers/helcom.ipynb`

したがって、`.py` 直編集を前提にした改善案は、このリポジトリの基本運用と整合しない。

根拠:

- `marisco/metadata.py:5`
- `marisco/configs.py:5`
- `marisco/netcdf2csv.py:3`
- `marisco/cli/to_nc.py:1`
- `marisco/handlers/helcom.py:3`

### 2.2 notebook は責務ごとに整理されている

`nbs/` 配下には、責務ごとに notebook が分割されている。

- API層: `nbs/api/`
- CLI層: `nbs/cli/`
- handler層: `nbs/handlers/`
- 補助的な資料: `nbs/metadata/`

この構成は、Pydantic導入時の責務分離とも相性がよい。

### 2.3 変更方針は「生成コード修正」ではなく「notebook修正」で統一すべき

本件に関しては、次の方針を明示しておくべきである。

- `marisco/*.py` や `marisco/cli/*.py` を直接編集しない
- 変更は対応する `nbs/**/*.ipynb` に加える
- 生成コードは notebook から再生成する
- 提案・レビュー・実装タスクは notebook 単位で管理する

これは運用上の好みではなく、**自動生成ファイルの上書きリスクを避けるための必須方針**である。

## 3. 現状の課題

### 3.1 CLI入力の検証が最小限

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

### 3.2 設定値が辞書でそのまま流通している

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

### 3.3 Zotero応答への依存が強いが、応答スキーマが未定義

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

### 3.4 DataFrame入力の期待構造が暗黙的

各handlerは `pd.read_csv()` や `pd.read_excel()` の後、想定列が存在する前提でcallbackを実行している。

なお、この柔軟な変換設計そのものは、データ提供元ごとの差異を吸収する上で重要な価値である。  
課題は柔軟性そのものではなく、**柔軟性の責任範囲が明示されていないため、失敗検出が後段化していること**にある。

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

### 3.5 例外の品質が均一でない

現状は、失敗時に `print` のみ、あるいは空DataFrame返却で処理継続する箇所がある。

代表例:

- handler import失敗時に `print` のみ
- OSPAR読込失敗時に空DataFrame返却
- HELCOM座標変換失敗時に値をそのまま返す

根拠:

- `marisco/cli/to_nc.py:14`
- `marisco/handlers/ospar.py:113`
- `marisco/handlers/helcom.py:624`

## 4. 導入方針

### 4.1 基本方針

Pydanticは本リポジトリ全体に一律適用するのではなく、**入力境界と外部境界に限定導入**する。

ただし、実装はすべて **notebook正本に対して行う**。

対象:

- CLI引数
- `configs.toml`
- 環境変数
- Zotero API応答

対象外または別手段推奨:

- `pandas.DataFrame` 本体の列スキーマ検証

本方針の狙いは、柔軟性を削ることではない。  
**柔軟な変換パイプラインを維持したまま、曖昧な境界条件だけを明示化すること**にある。

### 4.2 なぜ境界限定導入か

このリポジトリの中心はDataFrame変換パイプラインであり、そこを全面Pydantic化するのは効果に対してコストが高い。

一方で、入口の値と外部依存の値は構造が比較的安定しており、Pydanticの効果が出やすい。

期待できる改善:

- 失敗をcallback内部ではなく入口で検出できる
- エラーメッセージをユーザー向けに具体化できる
- 設定構造の変更影響を見つけやすくなる
- Zotero応答欠損時の原因切り分けが容易になる
- notebook ごとの責務分離を保ったまま改善できる

言い換えると、Pydanticは**厳格化のための道具**ではなく、**柔軟性の責任範囲を整理するための道具**として使うべきである。

### 4.3 Pydanticとhandler / callbackの責務分担

本提案では、責務を次のように分ける。

#### Pydanticが担うもの

- `configs.toml` の構造保証
- 環境変数の最低限の存在保証
- CLI引数の制約保証
- Zotero API応答の最低限の必須項目保証

#### handler / callbackが担い続けるもの

- 列名ゆれの吸収
- 値の表記ゆれ補正
- 欠損補完
- provider固有レイアウトの解釈
- MARIS向けの正規化・変換ロジック

この分担により、**境界契約の明示**と**現実データへの耐性**を両立する。

### 4.4 notebook編集を前提にした実装原則

本提案を実装する際は、以下を原則とする。

1. 生成 `.py` ファイルを直接編集しない
2. Pydanticモデルは、その責務を持つ notebook に定義する
3. notebook 上で説明・実装・検証を一体で管理する
4. 再生成後の `.py` は成果物として扱う

この原則により、nbdevの開発フローとPydantic導入が衝突しない状態を保てる。

## 5. Pydantic適用候補

### 5.1 第一優先: 設定モデル

#### 対象 notebook

- `nbs/api/configs.ipynb`

#### 対象コード領域

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

### 5.2 第二優先: CLI入力モデル

#### 対象 notebook

- `nbs/cli/to_nc.ipynb`
- `nbs/cli/db_to_nc.ipynb`

#### 対象コード領域

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

### 5.3 第三優先: Zotero応答モデル

#### 対象 notebook

- `nbs/api/metadata.ipynb`
- `nbs/api/netcdf2csv.ipynb`

#### 対象コード領域

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

## 6. DataFrame検証は別手段を推奨

### 6.1 理由

Pydanticは辞書やオブジェクトの検証には強いが、DataFrameの列構造・列型・空値割合・列名集合の検証には最適ではない。

加えて、本プロジェクトではDataFrameに対して一定の柔軟性が必要である。  
そのため、表データ検証の目的は**すべての揺れを拒否すること**ではなく、**処理不能な欠落と、handlerで吸収可能な揺れを切り分けること**に置くべきである。

### 6.2 推奨手段

候補は2つ。

#### A. `pandera` 導入

用途:

- 必須列確認
- 列型確認
- nullable制約
- 日付/数値列のチェック

向いているケース:

- handlerごとに明確な入力表スキーマがある場合
- ただし「厳密拒否」を目的とするのではなく、「最低限の処理前提」を確認したい場合

#### B. 自前の軽量検証関数

用途:

- `validate_required_columns(df, cols, context)`
- `validate_non_empty_df(df, context)`
- `validate_merge_key(df, key, context)`

向いているケース:

- まず低コストで改善したい場合
- provider固有の柔軟な吸収ロジックを残したい場合

### 6.3 本リポジトリでの適用候補

- `geotraces`: 必須列・日時列・経度列
- `helcom`: `key` と各CSVペアの存在
- `ospar`: 空DataFrame禁止、主要列確認
- `tepco`: sheet構造、セクション境界、必須列確認

実装場所は以下の2案がある。

- 共通検証ヘルパとして `nbs/api/` に置く
- handler固有検証として `nbs/handlers/*.ipynb` に置く

まずは再利用性の高い検証だけを `nbs/api/` に寄せ、データセット固有の検証は各 handler notebook に置く方針が自然である。

実装時の判断基準は、次のように整理するのが望ましい。

- **止めるべきもの**
  - 必須列が存在しない
  - 設定が欠けている
  - CLI引数が契約を満たさない
  - Zotero応答に最低限必要な項目がない
- **handler / callback で吸収すべきもの**
  - 列名や値の表記ゆれ
  - 補正可能な欠損
  - providerごとのフォーマット差
  - MARIS標準への正規化

## 7. 想定アーキテクチャ

### 7.0 三層での責務整理

本提案の構造は、次の三層で捉えると分かりやすい。

- **Boundary layer**
  - Pydanticで扱う層
  - 設定、CLI、外部API応答の最低限の契約を定義する
- **Normalization layer**
  - handler / callback で扱う層
  - 汚いデータをMARIS処理可能な形へ寄せる
- **Encoding layer**
  - NetCDF/CSV生成層
  - 正規化済みデータを出力形式へ落とし込む

この整理により、Pydanticが変換ロジックの代替ではないことを明確にできる。

### 7.1 設定読込

現状:

- `read_toml()` → 辞書

提案:

- `read_toml()` → `AppConfig.model_validate(...)`

### 7.2 CLI実行

現状:

- `@call_parse` で受け取って、そのままhandlerへ渡す

提案:

- 受け取り後に `CliArgsModel` で検証
- 正規化済み値のみhandlerへ渡す

### 7.3 Zotero応答

現状:

- `zot.item()` の辞書を直接利用

提案:

- 取得辞書を `ZoteroRecordModel` で検証
- 必須項目欠損時は意味のある例外に変換

### 7.4 notebookから生成コードへの反映

現状:

- notebook が正本
- `.py` は export された成果物

提案:

- 設計レビューは notebook 単位で行う
- 実装修正は notebook に対して行う
- 生成 `.py` は差分確認対象ではあるが、修正対象ではない

これにより、将来の再生成で変更が失われるリスクを避けられる。

## 8. 導入優先順位

### フェーズ1: 最小導入

- `nbs/api/configs.ipynb` に設定モデル
- `nbs/cli/to_nc.ipynb` / `nbs/cli/db_to_nc.ipynb` にCLI入力モデル

目的:

- 入口の失敗をすぐ分かる形にする

### フェーズ2: 外部依存の安定化

- `nbs/api/metadata.ipynb` にZotero応答モデル
- `nbs/api/netcdf2csv.ipynb` に `archiveLocation` 変換の明示化

目的:

- 外部API起因の不具合切り分け改善

### フェーズ3: 表データの品質向上

- `nbs/api/` または `nbs/handlers/*.ipynb` に `pandera` または軽量検証関数を導入

目的:

- handlerごとの暗黙前提を明文化

## 9. 期待効果

### 9.1 デバッグ効率

- 失敗位置が入口に寄る
- メッセージが具体化する
- 再現条件が説明しやすくなる
- 「設定の問題」なのか「データ吸収ロジックの問題」なのかを切り分けやすくなる

### 9.2 保守性

- 設定構造変更時の影響範囲を把握しやすい
- 外部API仕様変更を検知しやすい
- handler前提を文書化しやすい
- notebook と生成コードの責務分離を維持できる
- 柔軟な変換ロジックを壊さずに、境界条件だけを改善できる

### 9.3 ユーザー体験

- CLIエラーが分かりやすくなる
- 初期設定ミスにすぐ気づける
- 不正入力時の修正案を出しやすい
- データの揺れを一律拒否しないため、現実の入力データに対する耐性を維持できる

## 10. リスクと注意点

### 10.1 Python互換性

本プロジェクトは `requires-python = ">=3.7"` である。Pydanticのバージョン選定には互換性確認が必要。

根拠:

- `pyproject.toml:10`

### 10.2 全面導入は過剰

DataFrame変換本体までPydantic化すると、実装負荷に対して効果が薄くなる可能性が高い。

また、Pydanticや表スキーマ検証を過度に厳格化すると、現実の外部データの揺れに耐えられなくなる恐れがある。  
そのため、拒否条件は**処理不能な欠落**に限定し、表記ゆれや補正可能な欠損は既存変換層で扱うべきである。

### 10.3 notebook由来コードとの整合

本リポジトリは `nbdev` ベースで自動生成コードを含むため、導入箇所は notebook 側で管理することを前提にすべきである。

注意点:

- `.py` 直修正は再生成で失われる
- notebook側のimport設計が複雑になると保守性を損なう
- モデル定義を1箇所に寄せすぎると、nbdev上の責務境界が曖昧になる

## 11. 変更方針の提案

本件の実装方針は、**「コード本体を編集する」のではなく、「対応する notebook を編集する」** に明確化すべきである。

### 11.1 推奨する変更単位

- CLI改善: `nbs/cli/*.ipynb`
- 設定改善: `nbs/api/configs.ipynb`
- Zotero改善: `nbs/api/metadata.ipynb`, `nbs/api/netcdf2csv.ipynb`
- DataFrame検証: `nbs/api/` または `nbs/handlers/*.ipynb`

### 11.2 推奨するレビュー単位

- notebook 単位で設計レビューする
- 生成 `.py` は反映結果として確認する
- 提案書・タスク分解も notebook 名を基準に記載する

### 11.3 推奨しない変更方法

- `marisco/*.py` の直接編集
- 生成コードだけを根拠にした実装計画
- notebook と生成コードで責務がずれる変更

## 12. 提案内容の要約

本リポジトリに対する提案は、**Pydanticの全面導入ではなく、境界限定導入**である。

加えて、実装方針は **「生成コード編集」ではなく「notebook編集」** とする。

ここでのPydanticは、データクレンジングのための仕組みではない。  
**柔軟なデータ変換パイプラインを維持したまま、設定・CLI・外部APIといった境界条件のみを明示化するための仕組み**として使う。

列名ゆれ、値の表記ぶれ、欠損補完、provider固有のレイアウト吸収といった処理は、従来どおり handler / callback に残す。

具体的には以下を推奨する。

1. `nbs/api/configs.ipynb` で `configs.toml` と環境変数をPydanticで検証する
2. `nbs/cli/to_nc.ipynb` と `nbs/cli/db_to_nc.ipynb` でCLI入力をPydanticで検証する
3. `nbs/api/metadata.ipynb` と `nbs/api/netcdf2csv.ipynb` で Zotero API応答をPydanticで検証する
4. DataFrame検証は `pandera` または軽量検証関数で補い、必要に応じて `nbs/api/` または `nbs/handlers/*.ipynb` に配置する

この順序で進めることで、導入コストを抑えつつ、デバッグ効率と保守性を高められる。

## 13. 次アクション案

- 方針合意後、まず `nbs/api/configs.ipynb` に `AppConfig` を試作する
- 次に `nbs/cli/to_nc.ipynb` で `CliArgsModel` を試作する
- `geotraces` を対象に、notebook編集 → 生成コード反映の流れで最小導入を検証する
- その結果を踏まえて、ZoteroモデルとDataFrame検証方針を決定する
