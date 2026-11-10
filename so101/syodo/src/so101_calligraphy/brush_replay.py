"""Offline, stateful tuft/contact replay of prescribed robot joint positions.

The material and ink parameters are hypotheses, not identified hardware values.
This module cannot send robot commands or certify physical writing quality.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace

import mujoco
import numpy as np

from so101_calligraphy.config import EnvConfig
from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv
from so101_calligraphy.ink import InkCanvas


@dataclass(frozen=True)
class ReplayParameters:
    timestep_s: float = 0.001
    sample_period_s: float = 0.01
    settle_s: float = 0.5
    stiffness_scale: float = 1.0
    friction_scale: float = 1.0
    distributed_contact: bool = True

    def __post_init__(self):
        values = np.asarray([self.timestep_s, self.sample_period_s, self.settle_s,
                             self.stiffness_scale, self.friction_scale])
        if not np.isfinite(values).all() or np.any(values <= 0):
            raise ValueError("Replay parameters must be finite and positive")
        if self.timestep_s > self.sample_period_s:
            raise ValueError("Physics timestep must not exceed the sampling period")


def replay_brush(
    config: EnvConfig,
    qpos: np.ndarray,
    expected: np.ndarray,
    pen_down: np.ndarray,
    period_s: float,
    *,
    parameters: ReplayParameters = ReplayParameters(),
) -> tuple[dict, dict[str, np.ndarray], np.ndarray]:
    """Advance passive hair joints continuously, including lifts and reversals.

    Large armature approximates prescribed arm motion while MuJoCo still sees
    the commanded arm velocity in contact friction. Arm positions are imposed
    each substep; only the tuft is free to respond. This deliberately excludes
    servo tracking error, which is logged separately by physical playback.
    """
    qpos = np.asarray(qpos, dtype=float)
    expected = np.asarray(expected, dtype=float)
    pen_down = np.asarray(pen_down, dtype=bool)
    if qpos.ndim != 2 or qpos.shape[1] != 6 or len(qpos) < 2:
        raise ValueError("Replay requires at least two six-joint waypoints")
    if expected.shape != (len(qpos), 3) or pen_down.shape != (len(qpos),):
        raise ValueError("Replay waypoint arrays differ in shape")
    if not np.isfinite(qpos).all() or not np.isfinite(expected).all():
        raise ValueError("Replay waypoints must be finite")
    if not np.isfinite(period_s) or period_s <= 0:
        raise ValueError("Replay period must be finite and positive")
    config = replace(config, brush=replace(config.brush, distributed_contact=parameters.distributed_contact))
    env = CalligraphyEnv("line", config=config)
    records: list[dict] = []
    canvas = InkCanvas(config.paper, config.brush, config.ink)
    try:
        model, data, physics = env.model, env.data, env.brush_physics
        model.opt.timestep = parameters.timestep_s
        model.jnt_stiffness[physics.joint_ids] *= parameters.stiffness_scale
        model.geom_friction[env._paper_geom_id] *= parameters.friction_scale
        model.geom_friction[env._brush_geom_id] *= parameters.friction_scale
        contact_geoms = {env._brush_geom_id}
        if parameters.distributed_contact:
            for name in ("brush_bristles", "brush_bristles_mid", "brush_bristles_tip"):
                geom = env._named_id(mujoco.mjtObj.mjOBJ_GEOM, name)
                model.geom_friction[geom] = model.geom_friction[env._brush_geom_id]
                contact_geoms.add(geom)
        model.dof_armature[env._qvel_indices] = 1e6
        mujoco.mj_setConst(model, data)
        mujoco.mj_resetData(model, data)
        data.qpos[env._qpos_indices] = qpos[0]
        data.ctrl[:] = qpos[0]
        mujoco.mj_forward(model, data)
        root_body = env._named_id(mujoco.mjtObj.mjOBJ_BODY, "brush_bristle_link")
        mount_position = data.site_xpos[physics.mount_site]
        root_position = data.xpos[root_body]
        unbent_gap = float(np.linalg.norm(env.brush_position - data.site_xpos[physics.rest_site]))
        physical_length = float(np.linalg.norm(env.brush_position - mount_position))
        rigid_length = float(np.linalg.norm(root_position - mount_position))
        tuft_length = float(np.linalg.norm(env.brush_position - root_position))
        if unbent_gap > 1e-8:
            raise ValueError("Deformable tip and IK reference differ at zero bend")
        # Settle at the first (normally airborne) waypoint, never at each point.
        for _ in range(int(np.ceil(parameters.settle_s / model.opt.timestep))):
            data.qpos[env._qpos_indices] = qpos[0]
            data.qvel[env._qvel_indices] = 0
            mujoco.mj_step(model, data)
        data.time = 0
        previous_tip = env.brush_position.copy()
        time_since_sample = 0.0
        stroke = -1
        was_down = False
        arm_error = 0.0
        contact_impulse = contact_time = missed_time = intended_time = 0.0
        unintended_contact_time = high_air_time = high_air_contact_time = 0.0
        force_peak = max_bend = max_deflection = 0.0
        start_warnings = data.warning.number.copy()
        normal = np.zeros(6)
        mid_body = env._named_id(mujoco.mjtObj.mjOBJ_BODY, "brush_mid_link")
        def contact_state():
            force = 0.0
            weighted = np.zeros(3)
            patches = []
            for ci in range(data.ncon):
                item = data.contact[ci]
                pair = {int(item.geom1), int(item.geom2)}
                if env._paper_geom_id in pair and pair.intersection(contact_geoms):
                    mujoco.mj_contactForce(model, data, ci, normal)
                    amount = max(0., float(normal[0]))
                    force += amount
                    weighted += item.pos * amount
                    if amount > 1e-6:
                        patches.append((item.pos.copy(), amount))
            return force, (weighted / force if force > 1e-6 else np.full(3, np.nan)), patches
        for index in range(1, len(qpos)):
            # Hardware moves toward this waypoint using its pen_down state.
            down = bool(pen_down[index])
            if down and not was_down:
                stroke += 1
            was_down = down
            steps = max(1, int(np.ceil(period_s / parameters.timestep_s)))
            h = period_s / steps
            model.opt.timestep = h
            velocity = (qpos[index] - qpos[index - 1]) / period_s
            for substep in range(steps):
                alpha = substep / steps
                command = qpos[index - 1] * (1 - alpha) + qpos[index] * alpha
                data.qpos[env._qpos_indices] = command
                data.qvel[env._qvel_indices] = velocity
                data.ctrl[:] = command
                mujoco.mj_step(model, data)
                next_alpha = (substep + 1) / steps
                next_command = qpos[index - 1] * (1 - next_alpha) + qpos[index] * next_alpha
                arm_error = max(arm_error, float(np.max(np.abs(data.qpos[env._qpos_indices] - next_command))))
                data.qpos[env._qpos_indices] = next_command
                mujoco.mj_forward(model, data)
                if not np.isfinite(data.qpos).all() or not np.isfinite(data.qvel).all():
                    raise ValueError("Non-finite dynamic brush state")
                target = expected[index - 1] * (1 - next_alpha) + expected[index] * next_alpha
                force, contact_point, patches = contact_state()
                contact = force > 1e-6
                high_air = bool(target[2] >= config.paper.surface_z + 0.015)
                force_peak = max(force_peak, force)
                contact_impulse += force * h
                contact_time += h if contact else 0
                intended_time += h if down else 0
                missed_time += h if down and not contact else 0
                unintended_contact_time += h if not down and contact else 0
                high_air_time += h if high_air else 0
                high_air_contact_time += h if high_air and contact else 0
                max_bend = max(max_bend, float(np.max(np.abs(data.qpos[physics.qpos_indices]))))
                max_deflection = max(max_deflection, float(np.linalg.norm(env.brush_deflection)))
                time_since_sample += h
                if time_since_sample + 1e-10 < parameters.sample_period_s and not (index == len(qpos) - 1 and substep == steps - 1):
                    continue
                tip = env.brush_position.copy()
                tip_velocity = (tip - previous_tip) / time_since_sample
                state = physics.observe(data, contact_force=force, tip_velocity=tip_velocity)
                if contact:
                    # Ink is placed at measured contact, oriented by the LAST
                    # hair segment; a straight handle does not imply straight hair.
                    for point, amount in patches:
                        pressure = float(1 - np.exp(-amount / config.brush.nominal_force))
                        canvas.deposit(
                            point, pressure=pressure,
                            speed=float(np.linalg.norm(tip_velocity[:2])),
                            deflection=state.deflection, tangent=tip_velocity[:2].copy(),
                            intended=down, stroke_index=stroke,
                            opening=state.opening,
                            shaft_direction=state.terminal_axis[:2].copy(),
                            lean=float(np.linalg.norm(state.terminal_axis[:2])),
                        )
                chain = np.stack((data.site_xpos[physics.mount_site],
                    data.xpos[root_body],
                    data.xpos[mid_body],
                    data.site_xpos[physics.terminal_site], tip))
                records.append(dict(time_s=float(data.time), waypoint=index, pen_down=down,
                    contact=contact, contact_count=len(patches), force_n=force, expected=target, rest=data.site_xpos[physics.rest_site].copy(),
                    tip=tip, contact_point=contact_point, bend=state.bend, chain=chain,
                    terminal_axis=state.terminal_axis, deflection=state.deflection,
                    energy_j=state.elastic_energy))
                previous_tip = tip
                time_since_sample = 0.0
        arrays = {key: np.asarray([row[key] for row in records]) for key in records[0]}
        hit = arrays["pen_down"] & arrays["contact"]
        xy_error = np.linalg.norm(arrays["contact_point"][hit, :2] - arrays["expected"][hit, :2], axis=1) * 1000
        warning_count = int(np.sum(data.warning.number - start_warnings))
        summary = {
            "model": "mujoco_rigid_holder_three_segment_tuft_v2", "mujoco_version": mujoco.__version__,
            "physical_writing_verified": False, "material_calibrated": False,
            "arm_motion": "prescribed_waypoints_with_large_armature",
            "material_parameters_source": "bundled_material_hypothesis_with_configured_tuft_length",
            "ink_model": "existing_force_width_mapping_at_simulated_contact",
            "parameters": asdict(parameters),
            "brush_total_length_mm": physical_length * 1000,
            "brush_rigid_length_mm": rigid_length * 1000,
            "brush_tuft_length_mm": tuft_length * 1000,
            "unbent_tip_reference_gap_mm": unbent_gap * 1000,
            "paper_surface_z_m": config.paper.surface_z,
            "paper_contact_solref": model.geom_solref[env._paper_geom_id].tolist(),
            "brush_joint_stiffness": model.jnt_stiffness[physics.joint_ids].tolist(),
            "brush_joint_damping": model.dof_damping[physics.qvel_indices].tolist(),
            "metrics": {
                "duration_s": float(data.time), "intended_contact_s": intended_time,
                "actual_contact_s": contact_time, "missed_contact_s": missed_time,
                "missed_contact_fraction": missed_time / intended_time if intended_time else None,
                "unintended_contact_s": unintended_contact_time,
                "high_air_s": high_air_time,
                "high_air_contact_s": high_air_contact_time,
                "high_air_contact_fraction": high_air_contact_time / high_air_time if high_air_time else None,
                "contact_xy_error_p90_mm": float(np.percentile(xy_error, 90)) if len(xy_error) else None,
                "contact_xy_error_max_mm": float(xy_error.max()) if len(xy_error) else None,
                "force_peak_n": force_peak, "contact_impulse_ns": contact_impulse,
                "deflection_max_mm": max_deflection * 1000,
                "bend_max_deg": float(np.rad2deg(max_bend)),
                "prescribed_arm_error_max_deg": float(np.rad2deg(arm_error)),
                "ink_area_mm2": float(np.sum(canvas.pigment > .12) * config.ink.pixel_size**2 * 1e6),
                "unintended_ink_fraction": float(canvas.unintended_fraction),
                "solver_warnings": warning_count,
            },
            "limitations": ["stiffness, friction, damping and tip cross section unmeasured",
                "ink pressure and width are not calibrated for the physical 40 mm tuft",
                "three capsule bundles and terminal sphere; individual and split hairs omitted",
                "capsule radius does not reproduce water-dependent hair opening",
                "no servo lag or closed-loop pressure correction replayed",
                "no hardware acceptance inferred from simulated contact"],
        }
        if warning_count:
            raise ValueError(f"MuJoCo reported {warning_count} warnings during replay")
        return summary, arrays, canvas.rgb_image()
    finally:
        env.close()
