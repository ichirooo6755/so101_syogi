from dataclasses import replace
from pathlib import Path

import numpy as np

from so101_calligraphy.envs.calligraphy_env import CalligraphyEnv
from so101_calligraphy.training.professional import IndexedTrajectories, professional_config
from so101_calligraphy.trajectory.education import lazy_joyo_trajectories, load_joyo_kanji
from so101_calligraphy.trajectory.layout import frame_paper


entries = load_joyo_kanji(Path("data/kanjidic2"))
index = next(i for i, entry in enumerate(entries) if entry.character == "一")
source = professional_config("all")
dataset = lazy_joyo_trajectories(
    entries,
    kanjivg_cache=Path("data/kanjivg"),
    animcjk_cache=Path("data/animcjk"),
    use_animcjk_medians=True,
    paper=frame_paper(source.paper, source.writing_layout, 0),
)
font = Path(Path("runs/selected-exemplar-font.txt").read_text().strip())
base_config = professional_config("all", motoya_font_path=font)
config = replace(
    base_config,
    hardware=replace(
        base_config.hardware,
        base_position_xy_m=(-0.035, 0.0),
    ),
)
for layout in range(6):
        env = CalligraphyEnv(
            task="professional-evaluation-all",
            trajectories=IndexedTrajectories(dataset, (index,)),
            config=config,
        )
        try:
            env.reset(
                seed=17 + index * 6 + layout,
                options={"trajectory_index": 0, "layout_index": layout},
            )
        except RuntimeError as error:
            print(layout, "RESET FAILED", error)
            env.close()
            continue
        for wanted in ("entry", "send", "finish"):
            target_index = next(
                i
                for i, phase in enumerate(env.waypoints.brushwork_phases)
                if env.waypoints.pen_down[i] and phase == wanted
            )
            env._target_index = target_index
            env._set_target_marker()
            try:
                env._solve_position_ik(env.target_position)
            except RuntimeError as error:
                print(layout, wanted, "FAILED", error)
                continue
            q = env.data.qpos[env._qpos_indices]
            desired = env._desired_brush_axis()
            axis_error = np.degrees(
                np.arccos(np.clip(env.brush_mount_axis @ desired, -1.0, 1.0))
            )
            print(
                layout,
                wanted,
                "q_deg=", np.round(np.degrees(q), 2).tolist(),
                "position_mm=", round(
                    1000 * np.linalg.norm(env.target_position - env.brush_position), 3
                ),
                "axis_deg=", round(float(axis_error), 3),
            )
        env.close()
