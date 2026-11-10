# KanjiVG Stroke and Radical Curriculum Design

## Decision

Use KanjiVG release `r20250816` as the external source for real Japanese
stroke order, CJK stroke types, and radical/component groups. Download only
the SVG files required by a run and keep them outside Git. This avoids
duplicating KanjiVG while preserving its attribution and CC BY-SA 3.0 terms.

## Minimal integration

Extend the existing SVG loader with an optional element filter. A small
KanjiVG adapter uses that filter to select either one numbered stroke, a
`kvg:radical` group, or the complete character. The resulting `Trajectory`
continues through the existing waypoint, Gymnasium, PPO, logging, and Viewer
code without a second environment or trainer.

The Python standard library downloads pinned raw SVG files from GitHub into
`data/kanjivg/`. No HTTP dependency or KanjiVG database copy is added.

## Curricula

The technique curriculum uses KanjiVG's actual `kvg:type` values:

- 横画 `㇐` from 一
- 縦画 `㇑` from 十
- 点 `㇔` from 主
- 左払い `㇒` and 右払い `㇏` from 人
- 折れ `㇕` from 口
- はね `㇚` from 小

The radical curriculum extracts groups marked `kvg:radical="general"`:

- 亻 from 休
- 氵 from 海
- 忄 from 情
- 扌 from 持
- 艹 from 花
- ⻌ from 道
- 言 from 語

`foundations` runs techniques followed by radicals. A separate character
option trains every ordered stroke in any one KanjiVG glyph.

## CLI and validation

`so101-train` gains mutually exclusive KanjiVG curriculum and character
inputs plus a cache-path option. Replay accepts a curriculum-stage slug or a
character. Downloads validate XML before replacing cache files. Technique
stages validate the expected `kvg:type`, and radical stages fail when no
marked radical paths are present.

Tests use small inline KanjiVG-shaped XML fixtures, so the normal test suite
does not require network access. One live smoke check uses the pinned public
KanjiVG release before push.
