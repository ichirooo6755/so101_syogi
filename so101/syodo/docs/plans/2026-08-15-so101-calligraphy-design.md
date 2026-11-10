# SO-101 Calligraphy Learning Environment Design

## Goal

Build a CPU-only reinforcement-learning environment for Apple Silicon Macs in
which a lightweight SO-101 model traces ordered SVG strokes on A4 paper. The
environment uses MuJoCo, Gymnasium, Stable-Baselines3, and PPO. It has no CUDA
or Isaac Sim dependency.

## Robot and control

The bundled MJCF copies the SO-101 joint chain, axes, approximate link lengths,
and joint limits from the public SO-101 URDF. Primitive collision and visual
geometries keep simulation and training lightweight. A virtual brush is fixed
to the gripper frame.

The six-dimensional action is a normalized increment to joint position targets.
MuJoCo position actuators track those targets. This is more stable for an
initial CPU-trained PPO policy than direct torque control while preserving
joint-space actions.

## Trajectories

SVG elements and path subpaths are kept in document order and flattened into
approximately equal arc-length samples. SVG view-box coordinates are scaled
uniformly into a padded A4 writing area, with the SVG Y axis flipped into the
paper frame. Empty or malformed SVG inputs fail with actionable errors.

Line, circle, and cross are built-in tasks. The training curriculum transfers
the PPO model in that order. Arbitrary SVG files pass through the same stroke
representation.

Between strokes, the target state machine inserts lift, travel, and lower
segments. This makes pen-up motion explicit instead of treating it as an
unobserved teleport.

## Environment

The observation contains six joint positions, six joint velocities, brush-tip
position, relative position to the current target, normalized progress, and a
pen-down flag. The action contains one command per SO-101 joint.

The reward combines path proximity, ordered forward progress, smooth actions,
low joint velocity and acceleration, correct pen height, and a small time cost.
Joint-limit proximity, limit violations, self-collision, and non-brush contact
with the paper receive penalties. Severe violations terminate the episode.

A target advances only when the tip enters its tolerance. Therefore skipping
ahead does not earn stroke-order progress. Episodes end after successful
completion, a maximum step count, or a severe safety violation.

## Training and replay

Training is headless. Stable-Baselines3 Monitor data, checkpoints, evaluation
scores, final models, and reward plots are stored per curriculum stage. The
next stage starts from the preceding PPO parameters.

A replay command loads a saved policy and renders it with MuJoCo's passive
viewer. Target points are represented in the model so the intended character
is visible with the robot and paper.

## Validation

Unit tests cover SVG sampling and stroke order. Environment tests cover the
Gymnasium API, observation and action shapes, state progression, and pen-up
construction. An optional short PPO smoke test covers model creation, learning,
save, and reload.

The README documents Apple Silicon setup, tests, curriculum training, arbitrary
SVG training, replay, outputs, and the distinction between this research
simulation and hardware deployment.
