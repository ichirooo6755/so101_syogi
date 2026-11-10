"""Measured brush state behind legacy and segmented physics adapters."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

from so101_calligraphy.config import BrushConfig, PaperConfig


STOCK_TUFT_M = 0.038


def brush_model_xml(
    *,
    total_length_m: float = STOCK_TUFT_M,
    tuft_length_m: float = STOCK_TUFT_M,
    distributed_contact: bool = False,
) -> str:
    """Compile a rigid holder followed by the measured flexible tuft.

    ``total_length_m`` is grip to tip. ``tuft_length_m`` is only the hair;
    the difference is the rigid brush shaft. This distinction is essential on
    the hardware brush: 80 mm rigid holder + 40 mm hair, not 120 mm hair.
    """
    values = np.asarray([total_length_m, tuft_length_m], dtype=np.float64)
    if not np.isfinite(values).all() or tuft_length_m <= 0 or total_length_m < tuft_length_m:
        raise ValueError("Brush lengths must be finite and total length must include the tuft")
    root = ET.fromstring(files("so101_calligraphy").joinpath(
        "assets/so101_calligraphy.xml"
    ).read_text(encoding="utf-8"))
    tuft = root.find(".//body[@name='brush_bristle_link']")
    assert tuft is not None
    mount = np.asarray([float(value) for value in tuft.get("pos").split()])
    rigid_length_m = float(total_length_m - tuft_length_m)
    tuft.set("pos", " ".join(format(value, ".17g") for value in mount + [0, 0, -rigid_length_m]))
    rest = root.find(".//site[@name='brush_rest_tip_site']")
    shaft = root.find(".//geom[@name='brush_shaft']")
    assert rest is not None and shaft is not None
    rest.set("pos", " ".join(format(value, ".17g") for value in mount + [0, 0, -total_length_m]))
    if rigid_length_m > 0:
        # Keep the visible handle above the gripper and extend the same rigid
        # shaft down to the hair root. Only the 40 mm below that root bends.
        handle_end = np.asarray(
            [float(value) for value in shaft.get("fromto").split()][3:]
        )
        shaft.set("fromto", " ".join(
            format(value, ".17g")
            for value in (*(mount + [0, 0, -rigid_length_m]), *handle_end)
        ))
    if distributed_contact:
        for name in ("brush_bristles", "brush_bristles_mid", "brush_bristles_tip"):
            geom = tuft.find(f".//geom[@name='{name}']")
            assert geom is not None
            geom.set("contype", "2")
            geom.set("conaffinity", "1")
    scale = tuft_length_m / STOCK_TUFT_M
    for element in tuft.iter():
        # Root position is the rigid holder; distances within hair scale.
        if element is tuft:
            continue
        for name in ("pos", "fromto"):
            if name in element.attrib:
                element.set(name, " ".join(
                    format(float(value) * scale, ".17g")
                    for value in element.attrib[name].split()
                ))
    # Hair radii and material constants remain the stock hypotheses. Keep the
    # last capsule connected when the 40 mm measured hair is slightly longer.
    if scale > 1.0:
        terminal = tuft.find(".//geom[@name='brush_bristles_tip']")
        tip = tuft.find(".//geom[@name='brush_tip']")
        assert terminal is not None and tip is not None
        endpoint = float(tip.get("pos").split()[0]) - (0.01382 - 0.01036)
        terminal.set("fromto", f"0 0 0 {endpoint:.17g} 0 0")
    return ET.tostring(root, encoding="unicode")


@lru_cache(maxsize=16)
def _world_geometry_model(geometry: tuple) -> mujoco.MjModel:
    root = ET.fromstring(brush_model_xml())
    for name, position, quaternion, size in geometry:
        geom = root.find(f"./worldbody/geom[@name='{name}']")
        assert geom is not None
        for key, values in (("pos", position), ("quat", quaternion), ("size", size)):
            geom.set(key, " ".join(format(value, ".17g") for value in values))
    return mujoco.MjModel.from_xml_string(ET.tostring(root, encoding="unicode"))


def refresh_world_collision_bounds(model: mujoco.MjModel) -> None:
    """Copy compiler-derived bounds after moving/resizing paper and inkstone.

    mj_setConst does not rebuild the static collision tree. Updating geom_pos
    alone left the new paper visible but contact culled at its old position.
    Only the world body's unchanged set of primitive geoms is handled here.
    """
    geoms = np.flatnonzero(model.geom_bodyid == 0)
    geometry = tuple((mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, int(g)),
                      tuple(model.geom_pos[g]), tuple(model.geom_quat[g]), tuple(model.geom_size[g])) for g in geoms)
    source = _world_geometry_model(geometry)
    begin, count = int(model.body_bvhadr[0]), int(model.body_bvhnum[0])
    other = int(source.body_bvhadr[0])
    if count != int(source.body_bvhnum[0]):
        raise ValueError("World collision topology changed unexpectedly")
    for field in ("bvh_aabb", "bvh_child", "bvh_nodeid", "bvh_depth"):
        getattr(model, field)[begin:begin + count] = getattr(source, field)[other:other + count]
    for geom in geoms:
        for field in ("geom_aabb", "geom_rbound"):
            getattr(model, field)[geom] = getattr(source, field)[geom]


@dataclass(frozen=True)
class BrushState:
    tip_position: np.ndarray
    shaft_axis: np.ndarray
    terminal_axis: np.ndarray
    deflection: np.ndarray
    bend: np.ndarray
    bend_rate: np.ndarray
    compression: float
    contact_force: float
    opening: float
    roll: float
    slip_speed: float
    elastic_energy: float


class BrushPhysics:
    """Read high-fidelity or legacy-equivalent tuft state from one MJCF."""

    def __init__(
        self,
        model: mujoco.MjModel,
        *,
        mode: str,
        brush: BrushConfig,
        paper: PaperConfig,
    ) -> None:
        if mode not in ("legacy", "professional"):
            raise ValueError(f"Unknown brush physics mode: {mode!r}")
        self.model = model
        self.mode = mode
        self.brush = brush
        self.paper = paper
        self.mount_site = self._id(mujoco.mjtObj.mjOBJ_SITE, "brush_mount_site")
        self.rest_site = self._id(mujoco.mjtObj.mjOBJ_SITE, "brush_rest_tip_site")
        self.tip_site = self._id(mujoco.mjtObj.mjOBJ_SITE, "brush_tip_site")
        self.terminal_site = self._id(
            mujoco.mjtObj.mjOBJ_SITE, "brush_terminal_root_site"
        )
        joint_names = (
            "brush_bend_y",
            "brush_bend_z",
            "brush_mid_bend_y",
            "brush_mid_bend_z",
            "brush_tip_bend_y",
            "brush_tip_bend_z",
        )
        self.joint_ids = np.asarray(
            [self._id(mujoco.mjtObj.mjOBJ_JOINT, name) for name in joint_names]
        )
        self.qpos_indices = np.asarray(
            [model.jnt_qposadr[joint_id] for joint_id in self.joint_ids]
        )
        self.qvel_indices = np.asarray(
            [model.jnt_dofadr[joint_id] for joint_id in self.joint_ids]
        )
        self._base_stiffness = model.jnt_stiffness[self.joint_ids].copy()
        self._base_damping = model.dof_damping[self.qvel_indices].copy()
        self.configure(mode)

    def _id(self, object_type: mujoco.mjtObj, name: str) -> int:
        value = mujoco.mj_name2id(self.model, object_type, name)
        if value < 0:
            raise RuntimeError(f"Brush MJCF is missing {name!r}.")
        return value

    def configure(self, mode: str) -> None:
        self.model.jnt_stiffness[self.joint_ids] = self._base_stiffness
        self.model.dof_damping[self.qvel_indices] = self._base_damping
        if mode == "legacy":
            # Preserve the old two-axis root compliance while making the two
            # distal segments behave as one rigid continuation.
            self.model.jnt_stiffness[self.joint_ids[2:]] = 4.0
            self.model.dof_damping[self.qvel_indices[2:]] = 0.08
        self.mode = mode

    @staticmethod
    def _unit(vector: np.ndarray) -> np.ndarray:
        return vector / max(float(np.linalg.norm(vector)), 1e-12)

    def observe(
        self,
        data: mujoco.MjData,
        *,
        contact_force: float,
        tip_velocity: np.ndarray,
    ) -> BrushState:
        tip = data.site_xpos[self.tip_site].copy()
        mount = data.site_xpos[self.mount_site]
        terminal_root = data.site_xpos[self.terminal_site]
        shaft_axis = self._unit(tip - mount)
        terminal_axis = self._unit(tip - terminal_root)
        deflection = tip - data.site_xpos[self.rest_site]
        bend = data.qpos[self.qpos_indices].copy()
        bend_rate = data.qvel[self.qvel_indices].copy()
        penetration = max(
            self.paper.surface_z + self.brush.tip_radius - float(tip[2]), 0.0
        )
        opening_span = 0.12 if self.mode == "professional" else 0.32
        opening = float(
            1.0
            + opening_span
            * np.clip(
                np.linalg.norm(bend) / (self.brush.bend_limit * np.sqrt(len(bend))),
                0.0,
                1.0,
            )
        )
        mount_matrix = data.site_xmat[self.mount_site].reshape(3, 3)
        local_y = mount_matrix[:, 1]
        roll = float(np.arctan2(local_y[2], max(abs(local_y[1]), 1e-9)))
        stiffness = self.model.jnt_stiffness[self.joint_ids]
        elastic_energy = float(0.5 * np.sum(stiffness * np.square(bend)))
        return BrushState(
            tip_position=tip,
            shaft_axis=shaft_axis,
            terminal_axis=terminal_axis,
            deflection=deflection,
            bend=bend,
            bend_rate=bend_rate,
            compression=penetration,
            contact_force=float(contact_force),
            opening=opening,
            roll=roll,
            slip_speed=float(np.linalg.norm(tip_velocity[:2])) if contact_force > 0 else 0.0,
            elastic_energy=elastic_energy,
        )
