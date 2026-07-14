# config/recipes/ — カオスデータ対応レシピ集

`config/handlers/template.yaml` の `pre_cbs: []` / `post_cbs: []` にペーストして使う  
カプセル化された Callback 設定スニペット集。

---

## 診断フローチャート

```
野生の CSV を開いた
        │
        ├─ 緯度と経度が 1 列に入っている? ("45.5/135.2" 等)
        │       └─ YES → recipe_split_lat_lon.yaml
        │
        ├─ 緯度・経度が 度/分/秒/方位 の 4 列セットになっている?
        │       └─ YES → recipe_dms_to_decimal.yaml
        │
        ├─ 濃度値と単位が同じセルに入っている? ("3.4 Bq/kg" 等)
        │       └─ YES → recipe_extract_value_unit.yaml
        │
        └─ 上記に該当しない
                └─ template.yaml の columns: / melt.spec: だけで対応可能
```

---

## レシピ一覧

| ファイル | 対象パターン | 使用 CB |
|---|---|---|
| [recipe_split_lat_lon.yaml](recipe_split_lat_lon.yaml) | `"45.5/135.2"` 形式の合体列 | `SoftRegexTransformCB` |
| [recipe_dms_to_decimal.yaml](recipe_dms_to_decimal.yaml) | 度・分・秒・方位の 4 列 | `SoftDMStoDecimalCB` × 2 |
| [recipe_extract_value_unit.yaml](recipe_extract_value_unit.yaml) | `"3.4 Bq/kg"` 形式の値+単位合体列 | `SoftRegexTransformCB` + `SoftExtractUnitFromColCB` |

---

## ペーストの手順

1. 対象レシピファイルを開く
2. `pre_cbs:` から始まるブロック全体をコピー
3. `template.yaml` の `pre_cbs: []` の行を削除してペースト
4. `src_col` / `col_deg` 等の列名を実データに合わせて変更
5. `gap_check` を実行して必須列が揃っていることを確認

```python
from marisco.handlers.pipeline.loader import HandlerConfig, gap_check
cfg = HandlerConfig.from_yaml("config/handlers/my_dataset.yaml")
gap_check(cfg)   # エラーなし → encode() 実行可
```

---

## 共通の落とし穴

| 落とし穴 | 発生条件 | 対処 |
|---|---|---|
| `columns:` に合体列→LAT/LON を書く | 文字列が LAT 列に入り SanitizeLonLatCB が崩壊 | 合体列は columns: に追加しない |
| `col_dir=None` を渡す | `df[None]` → KeyError で即死 | 方位列が存在しない場合は事前に定数列を作成 |
| `SoftRegexTransformCB` で float+str を混在させる | 同一 cast が全 dst_cols に適用される仕様 | VALUE と UNIT は CB を 2 つに分割 |

---

## 新しいレシピの追加方法

1. `config/recipes/recipe_<pattern>.yaml` を作成
2. このファイルの診断フローとレシピ一覧に 1 行追加
3. `template.yaml` は触らない (骨格として固定)
