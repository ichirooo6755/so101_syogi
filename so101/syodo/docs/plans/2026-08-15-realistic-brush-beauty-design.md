# SO-101 realistic brush and calligraphic beauty design

## Goal

Turn the existing centre-line tracer into a CPU-trainable calligraphy environment
whose visible ink and reward distinguish `tome` (stop), `hane` (hook), and
`harai` (sweep). It must stay practical on Apple Silicon and keep the six SO-101
joint commands as the action.

## Chosen design

Use a hybrid brush. MuJoCo supplies robot dynamics, paper contact, friction, and a
two-axis compliant bristle. A deterministic NumPy ink model converts compression,
lateral bristle deflection, speed, ink load, and water into an elliptical paper
deposit. This avoids a large flexible-body or fluid simulation in every PPO step
while retaining the physical signals that affect brush marks.

### Brush and robot physics

- Replace the rigid tip with a short bristle body on two spring-damped hinge
  joints. Its contact sphere is the physical tip and its lateral displacement is
  the bristle bend signal.
- Read normal contact force from MuJoCo. Brush pressure is a calibrated,
  normalized combination of contact force and bristle compression.
- Use the ferrule-to-tip vector as the brush orientation. Reward near-vertical
  posture while allowing a small directional lean.
- Model actuator command latency with a short FIFO and enforce per-step joint
  target velocity limits.
- Randomize paper friction, joint damping/friction, actuator gain, latency, ink
  load, water, and brush stiffness at reset when domain randomization is enabled.
  All ranges live in configuration so they can be calibrated to a real SO-101.

### Ink and paper

Each pen-down control step deposits one elliptical stamp on a fixed A4 raster.

- contact area and bristle opening set major/minor radius;
- velocity and bend orient and elongate the stamp;
- ink load controls density and is depleted by transfer;
- water increases spread and paper absorption, then decreases over time;
- low ink or excessive speed produces deterministic edge gaps (dry-brush
  texture) from a seeded spatial hash;
- repeated deposits combine optically and create the visible stroke.

The raster is part of evaluation and RGB rendering, not the policy observation.
The Viewer receives a bounded set of dark MuJoCo sites generated from recent ink
deposits, so native replay shows the written mark without a new rendering
dependency.

### Pressure-aware exemplar

`Stroke` retains the source `kvg:type` and a finish-technique label. KanjiVG path
order remains the centre-line source. A profile generator adds normalized arc
progress, tangent, target speed, target pressure, target width, and finish phase
to every drawing waypoint.

When available, the pinned Japanese `graphicsJa.txt` from AnimCJK supplies a
filled kaisho outline and median for every stroke. Distance from the median to
the outline becomes the target width time series; the pressure target is then
inferred through the calibrated brush footprint. Generated profiles remain the
fallback for arbitrary SVGs. The upstream data stays in the ignored cache and
its Arphic Public License attribution is recorded in `THIRD_PARTY.md`.

- `tome`: ease down, keep pressure and terminal width, pause, then lift mainly in
  Z;
- `hane`: decelerate and press before the hook, turn along the actual final path,
  then accelerate while pressure and width taper;
- `harai`: keep the outgoing tangent, smoothly accelerate, and release pressure
  over the final part to form a pointed end;
- unclassified finishes use a conservative stop profile.

SVG authors may override automatic classification with
`data-technique="tome|hane|harai"`. KanjiVG `kvg:type` is preserved and mapped
without changing the pinned dataset.

### Observation and action

The action remains `Box(-1, 1, (6,))`: six joint target increments.

The observation adds to the existing joint/position/progress signals:

- tip linear velocity;
- brush axis and lateral bristle deflection;
- measured pressure, ink load, and water;
- target tangent, pressure, speed, and width;
- within-stroke progress and one-hot technique;
- delayed-command fraction.

Changing the observation makes the realistic-brush policy intentionally
incompatible with the old 20-value centre-line model. The old model remains
reproducible from its tagged commit and report.

### Reward and evaluation

Dense reward terms cover centre-line distance, pressure, speed, width, brush
orientation, stroke-order progress, smooth commands, low acceleration, and safe
pen-up motion. Hard collisions and limits keep their large penalties.

At every completed stroke, delayed quality terms compare the rendered mark and
exemplar:

- symmetric Chamfer distance between ink and target centre-line;
- discrete Fréchet distance between executed and target tip paths;
- target-versus-measured width profile error;
- endpoint score specific to `tome`, `hane`, or `harai`;
- unintended ink outside the target band;
- whole-character centroid, scale, tilt, and occupied-space balance.

`beauty_score` is a transparent 0–100 engineering metric assembled from these
terms. It is not presented as a human aesthetic judgement. Episode metrics and
technique subscores are saved to Monitor output and JSON evaluation reports.

## Training

Train one PPO policy with DLS nominal control plus learned residual commands:

1. pressure/width calibration strokes;
2. `tome`, `hane`, and left/right `harai` exemplars;
3. the existing KanjiVG basic strokes;
4. radicals;
5. education kanji.

Behaviour cloning from a pressure-aware DLS expert provides a warm start. PPO
then optimizes the residual for line quality under randomized dynamics. A
bounded smoke curriculum is run and saved in this change; long education-kanji
training uses the same resumable command.

## Acceptance

- Gymnasium checker and all unit tests pass on CPU-only macOS.
- A zero-residual expert completes the three finish-technique exemplars without
  collision and produces non-empty, varying-width ink.
- A real PPO run saves a model, Monitor reward history, ink/technique metrics,
  beauty report, and reward curve.
- Native MuJoCo replay displays the accumulating ink and prints the final beauty
  score.
