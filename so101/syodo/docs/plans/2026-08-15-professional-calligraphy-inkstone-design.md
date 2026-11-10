# Professional kaisho, inkstone, and modular brush design

> Superseded on 2026-08-15 by
> `2026-08-15-motoya-brushwork-curriculum-design.md`. The Aoyagi exemplar and
> contour-fitting portions below are historical and are not present in v0.4.

## Goal

Extend the existing CPU-only SO-101 MuJoCo environment from a competent
variable-width tracer into a complete calligraphy episode: load ink at an
inkstone, remove excess ink, carry the upright brush without dripping, execute
traditional kaisho brushwork, and return a transparent quality breakdown. The
target repertoire is all 2,136 joyo kanji.

The implementation remains usable on Apple Silicon without CUDA or Isaac Sim.
Heavier CPU training is acceptable, but every new physical or exemplar feature
must be independently switchable so an ablation can identify regressions.

## Reference sources

- The Agency for Cultural Affairs joyo table defines the 2,136-character
  target set.
- KanjiVG supplies ordered stroke medians and stroke types.
- AnimCJK supplies per-stroke Japanese kaisho outlines and medians.
- Aoyagi Kouzan's freely usable brush font supplies a professional
  calligrapher's final glyph silhouette. The font is cached, never silently
  substituted, and its source and checksum are recorded per run.
- CalliRewrite supplies the tool-calibration and image-to-motion design
  precedent. Its dependency-heavy training stack is not imported; small,
  attributable ideas are reimplemented against the current MuJoCo/Gymnasium
  API.
- Published motion-capture studies of expert Japanese calligraphers motivate
  low vertical variation, low jerk, and smooth time warping.

## Modular architecture

Three independently configured modules sit behind stable interfaces.

### `brush_physics.py`

`BrushPhysics` reads MuJoCo sites and contacts and returns a `BrushState`:

- multi-segment bend and bend rate;
- shaft and terminal tuft axes;
- compression and contact force;
- footprint length, width, opening, and roll;
- stored elastic energy and slip.

The high-fidelity MJCF uses three tapered passive bristle segments. Each has
two spring-damped bend joints, producing six passive degrees of freedom and an
S-shaped tuft. A legacy adapter exposes the old one-segment measurements when
`brush_physics="legacy"`. The rest of the environment only consumes
`BrushState`, so the high-fidelity model can be disabled without changing
rewards or trajectories.

### `ink_model.py`

`InkModel` owns the brush reservoirs and paper transfer:

- core ink, surface ink, and water;
- capillary flow from core to surface;
- absorption while the tuft is inside the inkstone;
- removal of excess surface ink at the inkstone lip;
- gravity/acceleration-dependent drip risk and discrete drips;
- pressure-, roll-, bend-, and speed-dependent multi-bundle paper transfer;
- paper absorption, feathering, dry-brush gaps, and optical accumulation.

The raster renderer is kept behind the same protocol. `ink_model="legacy"`
selects the previous single-reservoir elliptical stamp model. A deterministic
seed controls every stochastic-looking texture or drip, permitting exact
ablation comparisons.

### `brushwork.py`

`BrushworkPlanner` transforms ordered stroke geometry into phase-labelled,
time-parameterized targets:

- `gyakunyuu` or direct entry;
- `shihitsu` onset and settling;
- `souhitsu` transport with curvature-aware speed;
- `teian` lift/press modulation;
- `ten折` corner preparation and rotation;
- `shuu筆` with tome, hane, or harai;
- pen-up recovery with the tuft upright.

The professional planner combines AnimCJK stroke widths, curvature, stroke
type, neighboring stroke balance, and the Aoyagi Kouzan final silhouette. Its
time law minimizes jerk and vertical oscillation. `brushwork="legacy"` selects
the existing deterministic profiles.

## Complete episode and inkstone

The MJCF adds a reachable suzuri beside the A4 paper: a dark ink pool, sloped
well, and wiping lip. Every episode begins with these ordered phases:

1. approach the inkstone upright;
2. lower the tuft into the ink pool;
3. dwell and gently roll until core and surface reservoirs meet their target;
4. lift and wipe both sides on the lip until excess ink and drip risk fall;
5. carry the brush above a protected transfer corridor;
6. settle over the first stroke and write;
7. re-ink between strokes only when the predicted remaining ink is inadequate.

Inkstone contact is legal only for the tuft. Arm-inkstone collision, skipping
required loading, overloading, dripping, and wiping the tuft dry are penalized.
Drips are rendered and counted even outside the paper. The transfer controller
must keep the shaft upright, limit acceleration, and arrive with sufficient but
not excessive ink.

## Professional exemplar and all joyo kanji

KANJIDIC2 grade values 1 through 6 and 8 are intersected with the official joyo
set and must total exactly 2,136 characters. Training aborts on a mismatch.
Each character combines:

- KanjiVG stroke order and type;
- AnimCJK per-stroke outline and median;
- the professional font's whole-glyph mask;
- inferred pressure, roll, and speed targets from width and curvature.

The font mask is an image-level target, not a replacement for valid stroke
order. It is normalized to the same A4 writing box and compared at multiple
scales so the policy cannot gain a high score by merely making every stroke
thicker.

## Observation and action

The action remains six SO-101 joint target commands. New observation fields
include episode phase, inkstone-relative tip position, core/surface ink, water,
drip risk, bend rates, footprint orientation, target roll, and target phase.
Observation layouts are versioned. Old models fail with an explicit version
message rather than an opaque tensor-size error.

## Reward and transparent evaluation

The aggregate score is accompanied by normalized 0–100 components:

- `glyph_shape`: multiscale mask overlap, centroid, scale, and negative space;
- `line_width`: width time-series and final raster width agreement;
- `trajectory`: Chamfer, discrete Frechet, tangent, and endpoint agreement;
- `stroke_order`: ordered completion with no skipped or reversed stroke;
- `smoothness`: low joint/tip jerk and expert-like vertical variation;
- `brushwork`: entry, teian, corner, tome, hane, and harai quality;
- `ink_quality`: density continuity, controlled kasure, and feathering;
- `ink_loading`: correct absorption, wiping, and usable starting saturation;
- `drip_control`: no airborne or off-target drips;
- `collision_safety`: no arm, self, paper, or inkstone collision;
- `balance`: whole-character center, size, tilt, margins, and stroke spacing.

JSON, Monitor CSV, terminal replay, and per-character evaluation CSV retain
every component. The aggregate is a fixed weighted sum recorded in run
metadata. Raw measurements are also saved so weights can be changed without
rerunning the simulator.

## Training and ablations

The curriculum uses residual PPO with behavior cloning from the analytical
brushwork controller:

1. ink loading and symmetrical lip wiping;
2. no-drip carrying under randomized acceleration and delay;
3. entry, press/lift, corners, tome, hane, and harai;
4. radicals and spatial balance;
5. joyo kanji by grade and stroke count;
6. hard-example mining on the weakest component, not only total score.

Train and evaluate four matched seeds: legacy baseline, brush only, brush plus
ink, and all modules. Automatic checkpoint selection uses a robust score that
includes the mean, lower percentile, minimum, drip count, and collisions. A
module is not enabled in the shipped model if its matched-seed result regresses
the acceptance score.

## Acceptance and output

- All unit, Gymnasium, packaging, and deterministic replay tests pass.
- Ink loading, wiping, transfer, writing, and optional re-inking are visible in
  MuJoCo Viewer.
- Evaluation covers all 2,136 joyo kanji with per-component results.
- Completion, drip, and collision targets are 100%, zero, and zero.
- Engineering beauty target is mean at least 75 and minimum at least 60, with
  no component silently omitted. If the hardware or available exemplar cannot
  reach that threshold, the report remains explicitly incomplete rather than
  redefining the score.
- Representative easy, medium, hard, hane, harai, and dense kanji ink images
  are committed with the selected model, reward curves, checksums, and ablation
  report.

Human expert judgement is still required before claiming professional artistic
quality. The engineering score measures similarity and motion discipline; it
does not assert that an RL policy is itself a professional calligrapher.
