# 幅の詳細評価が一度も動いていなかった（2026-08-20）

`line_width` の天井が 88.00 しかなく、方策がすでに 86.99 でほぼ張り付いていた
（差 1.01）。報酬を触っても伸びないので天井側を調べたところ、
**`width_metrics.py` 全体が実質的に死にコードだった**ことが分かった。

## 1. 症状

全数評価の `characters.csv` で `width_scale` / `width_contrast` / `taper` /
`width_smoothness` が**すべて同一値**（88.29）、`corner_width` は常に 100.00。

これは `metrics.stroke_quality` のフォールバックの形と完全に一致する:

```python
except ValueError:
    width_details = {
        "width_scale": profile_width_score,
        "width_contrast": profile_width_score,
        "taper": profile_width_score,
        "corner_width": 1.0,          # ← 常に 100
        "width_smoothness": profile_width_score,
        "score": profile_width_score,
    }
```

## 2. 確認

`evaluate_width_profile` を包んで数えた結果:

```
呼び出し 89 回 / 成功 0 回 / 失敗 89 回
  89 回: actual_width, target_width, and progress must have equal lengths.
```

**一度も成功していない。** 配列長を実測すると:

| 実測幅 | 目標幅 | 実測progress | curvature |
|---:|---:|---:|---:|
| 184 | 27 | 184 | 27 |
| 120 | 21 | 120 | 21 |
| 186 | 27 | 186 | 27 |

一致した組 0 / 16。実測は**制御ステップ単位**（1 画あたり 100-190 点）、目標は
**ウェイポイント単位**（20-28 点）で、構造的に一致しない。

## 3. なぜ気づかれなかったか

- `stroke_quality` の他の成分（shape / placement / pressure / speed）は
  `_profile_error` が進捗軸で内挿するので長さ違いを吸収する。
  `evaluate_width_profile` だけが同長を要求する設計だった。
- `try/except ValueError` で例外が握り潰され、フォールバックへ静かに落ちる。
- フォールバックは全項目に `profile_width_score` を入れるので、
  `line_width = 0.40 × profile_width_score + 0.60 × profile_width_score`
  = `profile_width_score` となり、**粗い単一指標に退化していた**。
- テストは `evaluate_width_profile` を直接呼ぶので通ってしまう。

## 4. 修正

`_resample_to` を追加し、他の成分と同じく進捗軸で実測を目標グリッドへ内挿してから
渡す。curvature は目標側の系列なので、これで 3 つの長さが揃う。

```
修正後: 呼び出し 89 回 / 成功 83 回 / 失敗 6 回
  6 回: progress must contain at least four distinct values.（正当な条件）
```

## 5. 初めて見えた内訳（IK 天井）

| 技法 | scale | contrast | **taper** | corner | smooth | 総合 |
|---|---:|---:|---:|---:|---:|---:|
| tome | 93.45 | 92.33 | 95.16 | 96.70 | 98.96 | 91.97 |
| hane | 98.15 | 73.24 | **53.32** | 83.86 | 96.46 | 83.88 |
| **harai** | 95.20 | **54.00** | **20.99** | 88.15 | 98.81 | 76.06 |

**払いの taper が 20.99。** taper は胴体に対する末端の細まり方（対数比）を見る
指標で、払いの本質そのもの。`scale`（全体の太さ）は 95.20 と良好なのに taper が
壊滅的、つまり**太さは合っているが細くなっていく形になっていない**。
はねも taper 53.32 / contrast 73.24 と低い。

これまで払いは `finish`（末端の幅・圧・速度）で追っていたが、
より鋭い指標がずっと隠れていた。

## 6. 評価値への影響

同一モデル（`shapefit-cont`）・同一 83 字で測り直し:

| 指標 | 修正前 | 修正後 |
|---|---:|---:|
| line_width | 86.99 | **87.78** |
| brushwork | 82.60 | 82.60 |
| beauty | 85.17 | **85.41** |

モデルは変えていない。**測り方が正しくなっただけ**で、以後の全数評価の値は
この修正の前後で直接比較できない点に注意（基準を取り直す必要がある）。

## 7. 次

払いの taper 20.99 / contrast 54.00 が最大の伸びしろ。
`_kaisho_pressure_speed` の `pie` / `na` の圧プロファイル（`press_finish=0.02`）は
細まる形を書いているのに実行で出ていない、という三折法と同じ構図の可能性がある。
