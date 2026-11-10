# Image exemplar and no-timeout refinement

## Decision

The professional environment will use the exemplar image as an observation and
dense learning signal, not only as a terminal evaluator. The full A4 raster is
cropped to the writing box and reduced to a fixed 16x16 thumbnail. A 5x5 target
patch and a 5x5 current-ink patch, sampled around the moving brush in its local
tangent frame, provide fine detail. These 306 image-derived values extend the
existing 65 physical and trajectory values without adding a CNN or a GPU
dependency.

KanjiVG remains responsible for stroke count, order, and type. AnimCJK supplies
Japanese stroke medians and outline widths. The Aoyagi Kouzan glyph supplies
the professional finished-form image. A robust low-order per-stroke fit may
move a median toward the glyph, but cannot reorder strokes or snap individual
points across intersections.

## Episode lifecycle

The environment has no time-limit failure. `step()` returns `truncated=False`;
episodes end only on completion, a serious collision, excessive force, or a
hard joint limit. PPO rollout length remains a batching parameter and does not
reset an unfinished character. Evaluation and Viewer playback continue until a
physical terminal condition.

## Learning and evaluation

Dense reward includes local exemplar occupancy and reduction in normalized
image error after ink transfer. The terminal 14-part score remains visible:
glyph shape, stroke placement, length and angle, line width, trajectory, stroke
order, smoothness, brushwork, ink quality, loading, drip control, collision
safety, and balance. A new observation version prevents an old 65-value policy
from being loaded silently.

The PPO curriculum is retrained on the image-conditioned observation, then all
2,136 joyo kanji are replayed. README status distinguishes completed facts,
currently running work, measured limitations, and future real-hardware work.
