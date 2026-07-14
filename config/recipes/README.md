# config/recipes/ — chaos-data handling recipe pack

Encapsulated callback configuration snippets designed to be copy-pasted into
`pre_cbs: []` or `post_cbs: []` inside `config/handlers/template.yaml`.

---

## Diagnostic flowchart

```
You opened a wild CSV file
        │
        ├─ Are latitude and longitude combined in one column? (for example "45.5/135.2")
        │       └─ YES → recipe_split_lat_lon.yaml
        │
        ├─ Are latitude/longitude split into degree-minute-second + hemisphere columns?
        │       └─ YES → recipe_dms_to_decimal.yaml
        │
        ├─ Are measured values and units stored in the same cell? (for example "3.4 Bq/kg")
        │       └─ YES → recipe_extract_value_unit.yaml
        │
        └─ None of the above
                └─ columns: / melt.spec: in template.yaml should be sufficient
```

---

## Recipe index

| File | Target pattern | Callback(s) used |
|---|---|---|
| [recipe_split_lat_lon.yaml](recipe_split_lat_lon.yaml) | Combined coordinate column such as `"45.5/135.2"` | `SoftRegexTransformCB` |
| [recipe_dms_to_decimal.yaml](recipe_dms_to_decimal.yaml) | Degree/minute/second + hemisphere columns | `SoftDMStoDecimalCB` x 2 |
| [recipe_extract_value_unit.yaml](recipe_extract_value_unit.yaml) | Combined value+unit cells such as `"3.4 Bq/kg"` | `SoftRegexTransformCB` + `SoftExtractUnitFromColCB` |

---

## Paste workflow

1. Open the recipe file that matches the anomaly pattern.
2. Copy the entire block that starts with `pre_cbs:`.
3. Replace the `pre_cbs: []` line in `template.yaml` with that block.
4. Rename the placeholder column names (`src_col`, `col_deg`, etc.) to your real dataset columns.
5. Run `gap_check` and confirm that all required MARIS columns are now satisfied.

```python
from marisco.handlers.pipeline.loader import HandlerConfig, gap_check
cfg = HandlerConfig.from_yaml("config/handlers/my_dataset.yaml")
gap_check(cfg)   # no error -> safe to proceed with encode()
```

---

## Common pitfalls

| Pitfall | Trigger | Recommended fix |
|---|---|---|
| Writing combined coordinate columns directly into `columns:` as `LAT/LON` | A raw string lands in `LAT`, then `SanitizeLonLatCB` fails on float conversion | Do not map combined columns into `LAT/LON`; generate them in `pre_cbs` first |
| Passing `col_dir=None` | `df[None]` triggers an immediate `KeyError` | Create a constant hemisphere column first if the source file has no direction column |
| Extracting float + string in one `SoftRegexTransformCB` | One `cast` is applied to every destination column | Split VALUE and UNIT extraction into separate callbacks |

---

## Adding a new recipe

1. Create `config/recipes/recipe_<pattern>.yaml`.
2. Add one line to the diagnostic flow and one row to the recipe index above.
3. Leave `template.yaml` stable as the canonical starter skeleton.
