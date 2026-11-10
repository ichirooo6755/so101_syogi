# S Motoya Seikaisho 5 ProN brushwork curriculum

Date: 2026-08-15

## Goal

Teach SO-101 to reproduce Japanese kaisho with human-like brush handling. The
licensed **S Motoya Seikaisho 5 ProN** font is used only as the normalized final
image exemplar. KanjiVG owns stroke count, order, grouping, and stroke type;
Japanese AnimCJK medians own executable centre lines and reference widths.
Font contours must never alter robot waypoints.

## Data boundary

- `SO101_MOTOYA_FONT` or `--motoya-font` points to a locally licensed font.
- The loader verifies the name table contains Motoya, Seikaisho, weight 5, and
  ProN-compatible naming. The repository never downloads or redistributes it.
- Missing or incorrect fonts fail before professional training starts. There is
  no silent teacher substitution.
- KanjiVG/AnimCJK revisions remain pinned and recorded in run metadata.
- A test asserts that enabling the image exemplar leaves every trajectory point,
  stroke order, technique label, and width profile unchanged.

## Human-like curriculum

Training progresses through cumulative, gated stages:

1. brush handling: load, wipe, upright carry, landing, and lift;
2. basic stroke phases: gyakunyu start, controlled send, and finish;
3. technique drills: tome, hane, harai, sori, mage, and ore;
4. radicals/components in real characters;
5. elementary-school transfer;
6. all 2,136 joyo kanji.

Each stage is evaluated before promotion. Required gates cover completion,
trajectory, width, brushwork, placement, angle, smoothness, zero drips, and zero
collisions. Failed characters are replayed as hard examples in the following
attempt instead of being hidden by a mean score.

## Brush and ink

The independent `brush_physics`, `ink_model`, and `brushwork` switches remain
the rollback boundary. The professional ink model uses multiple virtual hair
bundles over the segmented MuJoCo brush: bundle spread follows pressure,
deflection, and roll; surface ink and water affect transfer; start and finish
phases shape the bundle footprint. Gyakunyu creates a directional head, tome
retains a full settled end, and hane/harai converge and taper while pressure is
released. Loading, lip wiping, acceleration, tilt, excess ink, and dripping stay
explicitly measurable.

## Evaluation

Both generated and Motoya masks are cropped and normalized to a common canvas
for final-image comparison. The complete score exposes, at minimum:

- glyph silhouette agreement;
- per-stroke placement, length, and angle against ordered motion data;
- line-width profile and centre-line trajectory;
- centroid, scale, tilt, and negative-space balance;
- stroke order, pressure/speed technique, and smoothness;
- ink loading/quality, unintended ink, drips, collisions, and joint safety.

The final-image score is a critic only. Gradients or fitted contours from the
font cannot produce target waypoints.

## Outputs and acceptance

Every run saves configuration and provenance, reward traces, per-character CSV,
component summaries, raw ink PNGs, normalized Motoya comparisons, and the model.
The default location is `runs/<timestamp>-motoya-brushwork/`, with final images
under `final/ink/` and `final/comparisons/`.

Acceptance requires all tests, a working motion-only smoke run on Apple Silicon,
verified rejection of a missing/wrong font, and a professional run that starts
only when the licensed Motoya asset is available. Full aesthetic claims require
that exact asset and may not be inferred from another font.

## Technique-first refinement

The first motion smoke exposed two concrete defects: mean line-width agreement
was only 22.23/100, and dry bundle stamps became visibly discrete in dense
characters. The next iteration keeps the same module boundary and fixes these
at their shared sources:

- pressure is derived from the requested physical footprint, so target pressure
  and AnimCJK width cannot contradict one another;
- tome, hane, left harai, and right harai receive distinct finish time laws based
  on published school brush instruction (settle/return, aligned-tip release,
  gradual release, and stop-then-release respectively);
- bundle transfer is swept continuously between MuJoCo samples and replenished
  coherently from the surface reservoir, rather than appearing as isolated dots;
- curriculum promotion additionally requires per-technique finish and width
  scores, not only a mean across mixed characters.

The fixed comparison set remains 一, 十, 水, 永, 書, 道, 飛. The refinement must
improve line-width and brushwork scores without losing completion, zero-drip, or
zero-collision status. Motoya image similarity remains unavailable until the
licensed font is installed.
