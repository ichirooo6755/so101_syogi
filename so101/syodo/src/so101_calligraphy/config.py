"""Shared physical and learning-environment configuration."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


JOINT_NAMES = (
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll",
    "gripper",
)

# Ranges from TheRobotStudio SO-101 calibrated URDF.
JOINT_LIMITS = np.asarray(
    [
        (-1.91986, 1.91986),
        (-1.74533, 1.74533),
        (-1.69, 1.69),
        (-1.65806, 1.65806),
        (-2.74385, 2.84121),
        (-0.174533, 1.74533),
    ],
    dtype=np.float64,
)


@dataclass(frozen=True)
class PaperConfig:
    """A4 paper placement in the MuJoCo world, in metres."""

    width: float = 0.210
    height: float = 0.297
    center_x: float = 0.200
    center_y: float = 0.0
    surface_z: float = 0.012
    margin: float = 0.015


@dataclass(frozen=True)
class WritingLayoutConfig:
    """Fixed A4 frames sized for the 38 mm brush."""

    two_by_two_size: float = 0.085
    two_character_size: float = 0.110
    # None keeps the six A4 frames. Set for one historical page-centre glyph.
    single_center_size: float | None = None

    @classmethod
    def legacy_sixty_mm(cls) -> "WritingLayoutConfig":
        return cls(two_by_two_size=0.060, two_character_size=0.060)

    @classmethod
    def brushmark_center(cls) -> "WritingLayoutConfig":
        return cls(single_center_size=0.110)


@dataclass(frozen=True)
class RewardConfig:
    """Reward terms; deliberately explicit for experiment reproducibility."""

    tracking: float = 1.0
    height_tracking: float = 0.35
    progress: float = 4.0
    completion: float = 30.0
    pressure_tracking: float = 1.30
    speed_tracking: float = 0.48
    width_tracking: float = 1.60
    orientation_tracking: float = 0.30
    ink_transfer: float = 0.20
    unintended_ink_penalty: float = 1.5
    stroke_quality: float = 25.0
    character_balance: float = 12.0
    smoothness_bonus: float = 0.08
    action_penalty: float = 0.015
    velocity_penalty: float = 0.002
    acceleration_penalty: float = 0.00005
    gripper_motion_penalty: float = 0.0
    joint_limit_penalty: float = 0.6
    collision_penalty: float = 30.0
    hard_limit_penalty: float = 40.0
    ink_loading: float = 2.0
    drip_penalty: float = 18.0
    professional_shape: float = 28.0
    # Emphasize finish/release (tome/hane/harai) after radicals still miss brushwork gate.
    brushwork_quality: float = 30.0
    harai_finish_bonus: float = 2.5
    tome_finish_penalty: float = 1.0
    endpoint_shape: float = 12.0
    exemplar_tracking: float = 1.1
    exemplar_image_improvement: float = 40.0


@dataclass(frozen=True)
class BrushConfig:
    """Calibratable virtual brush constants."""

    tip_radius: float = 0.0025
    # Opt-in contact on the whole segmented tuft for hardware diagnostics.
    # Existing learned-policy evaluations retain terminal-only contact.
    distributed_contact: bool = False
    nominal_compression: float = 0.00035
    release_clearance: float = 0.0008
    # The 38mm tuft reaches the same opening at less normal force than the old
    # 22mm brush. Tip-only A4 calibration uses the compliant terminal third;
    # its effective load is 0.60 N rather than the full-tuft 0.90 N estimate.
    nominal_force: float = 0.60
    large_frame_nominal_force: float = 0.60
    pressure_slew_per_step: float = 0.12
    pressure_response: float = 1.0
    horizontal_pressure_response: float = 1.0
    maximum_force: float = 8.0
    nominal_speed: float = 0.10
    minimum_width: float = 0.0018
    maximum_width: float = 0.013
    bristle_length: float = 0.038
    bend_limit: float = 0.45
    # 用筆プランナが目標幅を見積もるときに仮定する穂先の開き。
    # 墨モデル (ink.InkPaper.deposit) は筆の曲がりに応じて 1.0〜1.25 まで開く
    # ので、定数 1.12 では実際に置かれる墨より細く見積もってしまい、
    # The new profile stays on the terminal third of the tuft. Opening remains
    # a calibration knob, but no longer multiplies a sqrt-pressure footprint.
    tuft_opening: float = 1.05
    tip_pressure_scale: float = 0.52
    tip_pressure_floor: float = 0.01
    tip_pressure_ceiling: float = 0.45
    # Tangents of the physical lean angles used by the analytical controller.
    desired_lean: float = 0.1405408347  # 8 degrees
    sweep_lean: float = 0.2125565617  # 12 degrees
    corner_lean: float = 0.3639702343  # 20 degrees
    release_lean: float = 0.0699268119  # 4 degrees
    # Optional fixed physical lean while touching paper. None keeps the
    # phase-varying analytical tilt; tan(45deg)=1 holds a fixed oblique brush.
    fixed_contact_lean: float | None = None
    # The short airborne approach/retreat uses the 25-degree posture verified
    # around the whole A4 workspace. Contact then changes to the phase angle.
    airborne_lean: float = 0.4663076582  # 25 degrees
    # 起筆・収筆で穂を寝かせる量と向き。
    # 30-degree entry returns to the sending angle within the first 5%.
    entry_lean: float = 0.5773502692
    large_frame_entry_lean: float = 0.5773502692
    entry_lean_angle: float = -0.611
    entry_lean_end: float = 0.05
    # Exposed horizontal tome ends return into the stroke at 30 degrees.
    # A/B on 一三十 across 85/110 mm frames: +11.26 endpoint points versus
    # upright (22°: +3.94, 35°: +10.53) without incomplete strokes.
    finish_lean: float = 0.5773502692
    # Repeated safe-height waypoints give the offset attachment time to turn
    # before the tuft can touch paper.
    tilt_prepare_steps: int = 12


@dataclass(frozen=True)
class HardwareCalibrationConfig:
    """Measured SO-101 brush grip and inkstone pose for sim↔real transfer.

    Gripper frame matches the MJCF: +X along the brush shaft toward the tip.
    Set offsets from calliper measurements before sending policies to hardware.
    """

    # Added to the stock brush_mount / bristle-root pose (metres).
    brush_mount_offset_m: tuple[float, float, float] = (0.0, 0.0, 0.0)
    # Grip-to-tip reach relative to stock 38 mm. Hardware: 120/38.
    brush_tip_length_scale: float = 1.0
    # Only the flexible hair. Hardware: 40 mm, following an 80 mm rigid shaft.
    brush_tuft_length_m: float = 0.038
    # The MJCF gripper span is the stock servo's. A real arm's usable travel is
    # measured per unit and sits elsewhere, so the desk path overrides it; None
    # keeps the bundled range and leaves training untouched.
    gripper_range_rad: tuple[float, float] | None = None
    # Optional measured qpos limits for the complete physical arm. Keeping
    # this separate from JOINT_LIMITS preserves the stock training model.
    joint_ranges_rad: tuple[tuple[float, float], ...] | None = None
    # Reset IK seeds are elbow-up postures that reach down from the 150 mm
    # pedestal. A desk that sits above the base needs the opposite fold, so the
    # taught poses are offered first: (lift, elbow, wrist_flex, roll, gripper).
    reset_ik_seed_folds_rad: tuple[tuple[float, float, float, float, float], ...] = ()
    # Electrical 45deg is the upright home (`ref` in the MJCF). Legacy replay
    # locks at electrical 0deg (physical 45deg forward lean): upright lock
    # cannot reach A4 `lower` with five axes, while this pose can write.
    fixed_attachment_servo_angle_rad: float = 0.0
    # PLAN.md asked for a 100 mm pedestal. At that height, multi-start IK
    # still meets the 3 mm position gate but misses the 5° orientation gate
    # on A4 frames. 150 mm high / 30 mm forward is the pose that satisfies
    # the plan's own reachability numbers.
    base_riser_height_m: float = 0.150
    base_position_xy_m: tuple[float, float] = (0.030, 0.0)
    # Keep the proven loading/wiping path base-relative: the inkstone moves
    # with the base in X and is raised by the extra 50 mm spacer.
    inkstone_offset_m: tuple[float, float, float] = (0.030, 0.0, 0.050)
    # The upright attachment cannot reach the whole A4 rectangle. Long pen-up
    # transfers therefore use this collision-free circle, with posture changes
    # performed at the higher point before a 25-degree low approach/retreat.
    shoulder_pivot_offset_x_m: float = 0.0388353
    upright_transport_radius_m: float = 0.225
    upright_transport_height_m: float = 0.072
    # Domain-randomization amplitudes when EnvConfig.domain_randomization is on.
    mount_offset_randomization_m: float = 0.003
    tip_length_randomization: float = 0.08
    inkstone_offset_randomization_m: float = 0.012

    def __post_init__(self) -> None:
        if not JOINT_LIMITS[-1, 0] <= self.fixed_attachment_servo_angle_rad <= JOINT_LIMITS[-1, 1]:
            raise ValueError("fixed_attachment_servo_angle_rad is outside gripper limits")
        if self.upright_transport_radius_m <= 0.0:
            raise ValueError("upright_transport_radius_m must be positive")
        if self.upright_transport_height_m <= 0.0:
            raise ValueError("upright_transport_height_m must be positive")


@dataclass(frozen=True)
class InkConfig:
    """Lightweight ink-transfer and paper-absorption constants."""

    pixel_size: float = 0.001
    initial_ink: float = 0.95
    initial_water: float = 0.65
    transfer_rate: float = 0.0012
    water_loss_rate: float = 0.00055
    absorption: float = 0.22
    water_spread: float = 0.35
    dry_brush_threshold: float = 0.28
    viewer_deposit_limit: int = 700
    core_capacity: float = 1.35
    surface_capacity: float = 0.72
    capillary_rate: float = 0.030
    loading_rate: float = 0.140
    wiping_rate: float = 0.045
    target_surface_ink: float = 0.62
    drip_surface_threshold: float = 0.69
    drip_mass_threshold: float = 0.006
    airborne_evaporation: float = 0.00008
    professional_footprint_scale: float = 1.0
    # "soft" = Gaussian core + water halo (legacy). "hard" = crisp ellipse for kaisho.
    stamp_edge: str = "soft"

    def __post_init__(self) -> None:
        if self.stamp_edge not in ("soft", "hard"):
            raise ValueError(
                f"stamp_edge must be soft or hard, got {self.stamp_edge!r}."
            )


@dataclass(frozen=True)
class InkstoneConfig:
    """Reachable suzuri targets and dwell lengths, in metres and control steps.

    Positions are world-frame defaults for the bundled MJCF. Override via
    ``HardwareCalibrationConfig.inkstone_offset_m`` after measuring the real
    desk layout so the same policy can approach the physical inkstone.
    """

    center_x: float = 0.205
    center_y: float = -0.205
    pool_surface_z: float = 0.024
    lip_y: float = -0.161
    lip_surface_z: float = 0.027
    safe_height: float = 0.072
    pool_half_width: float = 0.038
    loading_steps: int = 28
    wiping_points: int = 10
    reink_interval_strokes: int = 7


@dataclass(frozen=True)
class ModuleConfig:
    """Independent, ablation-friendly model selections."""

    brush_physics: str = "legacy"
    ink_model: str = "legacy"
    brushwork: str = "legacy"
    inkstone: bool = False
    professional_exemplar: bool = False

    def __post_init__(self) -> None:
        for name in ("brush_physics", "ink_model", "brushwork"):
            value = getattr(self, name)
            if value not in ("legacy", "professional"):
                raise ValueError(f"{name} must be legacy or professional, got {value!r}.")

    @classmethod
    def professional(cls) -> "ModuleConfig":
        return cls(
            brush_physics="professional",
            ink_model="professional",
            brushwork="professional",
            inkstone=True,
            professional_exemplar=True,
        )


@dataclass(frozen=True)
class EnvConfig:
    """Numerical parameters for control and trajectory following."""

    paper: PaperConfig = field(default_factory=PaperConfig)
    writing_layout: WritingLayoutConfig = field(default_factory=WritingLayoutConfig)
    reward: RewardConfig = field(default_factory=RewardConfig)
    brush: BrushConfig = field(default_factory=BrushConfig)
    ink: InkConfig = field(default_factory=InkConfig)
    inkstone: InkstoneConfig = field(default_factory=InkstoneConfig)
    hardware: HardwareCalibrationConfig = field(
        default_factory=HardwareCalibrationConfig
    )
    modules: ModuleConfig = field(default_factory=ModuleConfig)
    motoya_font_path: str | None = None
    observation_version: int | None = None
    frame_skip: int = 4
    action_delta: float = 0.045
    ik_assist: bool = False
    residual_action_scale: float = 0.05
    tilt_residual_scale: float = 0.25
    tilt_residual_limit: float = np.deg2rad(8.0)
    target_tolerance_xy: float = 0.012
    target_tolerance_z: float = 0.005
    path_spacing: float = 0.008
    transition_spacing: float = 0.012
    # The 25-degree approach is reachable across the whole A4 frame at 58 mm.
    # It also leaves at least 8 mm while the wrist changes IK branch; long
    # upright transport happens separately at the calibrated 72 mm circle.
    safe_height: float = 0.058
    limit_margin_fraction: float = 0.06
    reset_noise: float = 0.01
    servo_latency_steps: int = 1
    max_joint_speed: float = 2.2
    # Rotate the offset attachment slowly on paper so the arm can compensate
    # its 30 mm pivot motion without driving the tuft through the sheet.
    contact_tilt_max_speed: float = 2.2
    orientation_ik_weight: float = 0.004
    contact_orientation_ik_weight: float = 0.120
    # Keep the analytical controller in sole charge of the offset tilt hinge.
    # The six-dimensional action stays unchanged so historical PPO models load.
    attachment_pose_control: bool = True
    # Replay historical five-axis policies with the servo locked. MuJoCo FK
    # on brush_tip_site already includes the 30mm pivot, 7.76mm offset, and
    # current tuft bend; driving the rigid rest tip left ink 12-15mm off path.
    legacy_attachment_compensation: bool = False
    # The analytical target owns the servo; the policy may use at most the
    # explicitly allowed eight-degree contact residual around it.
    attachment_orientation_tolerance: float = np.deg2rad(8.0)
    attachment_max_dwell: int = 160
    # 接地中は位置だけでなく筆圧でも高さを閉ループにする。位置サーボだけだと
    # 接触抗力とのつり合いで穂先が目標より 0.3-0.5mm 沈み込み、線が太くなり、
    # 払いの抜き（空中の最終ウェイポイント）に到達できず末端で墨が溜まる。
    # The tilted 38mm tuft needs more Z authority than the upright calibration.
    contact_pressure_gain: float = 0.0140
    large_frame_contact_pressure_gain: float = 0.0140
    horizontal_contact_pressure_gain: float = 0.0140
    harai_pressure_gain_scale: float = 1.6
    hane_release_pressure_gain_scale: float = 1.0
    contact_pressure_limit: float = 0.0045
    horizontal_contact_pressure_limit: float = 0.0045
    pressure_calibration_path: str | None = None
    require_pressure_calibration: bool = False
    residual_pressure_integral_scale: float = 1.0
    # Open-loop calibration only: fixed Z correction with all feedback disabled.
    pressure_probe_offset_m: float | None = None
    # 1.0 disables rejection; physical gates may set a stricter candidate limit.
    pressure_calibration_clip_rate_limit: float = 1.0
    # 到達判定が成立しないまま同一ウェイポイントで擦り続けるのを防ぐ上限。
    # 0 は無効（従来どおり到達するまで待つ）。
    max_pen_down_dwell: int = 0
    # 画間クリアランス。接続しない画同士のあいだに残す白の幅 [m] と、
    # 「設計上つながっている」とみなす端点接合の許容距離 [m]。
    # 用筆プランナは一画ずつ独立に計画するため隣の画を知らず、画数の多い字で
    # 線が太いまま重なって癒着する。お手本フォントは密な字ほど細いので、
    # 混み合った箇所だけ筆圧を落として白を残す。0 で無効。
    # 起筆の保持を「同じ点の繰り返し」ではなく「浅→深への沈み込み」にする比率。
    # 従来は 8 点すべて同一の XY・Z だったため、Z 許容の内側にいる限り 8 点とも
    # 即座に到達判定され、穂が座る前に送筆へ移っていた（起筆の目標圧 0.67 に
    # 対し実測 0.365、起筆幅 13.6mm の計画に対し実測 9.8mm）。
    # 開始圧をこの比率まで下げ、実際に降りないと進めない行程を作る。
    # 1.0 で従来どおり。0.20 まで下げると線幅が崩れる（IK 天井 82.4）。
    entry_descent_ratio: float = 0.55
    stroke_minimum_gap: float = 0.0015
    # 85mm frame calibration: close endpoints are intentional joins.
    stroke_junction_tolerance: float = 0.007
    # 細めすぎて画が消えないための下限（計画幅に対する比）。
    stroke_clearance_floor: float = 0.45
    # 指令ターゲットを可動域の端から内側に離しておくマージン [rad]。
    # 境界ちょうどへの指令を許すとサーボが実関節を限界まで駆動し、
    # hard_limit 終了（余裕 1e-4 以下）が発火する（事・串・荒の未完筆の原因）。
    # リセット時 ±0.005 / IK ソルバ ±0.01 と同水準の内側マージン。
    command_limit_margin: float = 0.005
    domain_randomization: bool = False
    # Optional training-only layout subset; evaluation still passes explicit layouts.
    training_layout_indices: tuple[int, ...] | None = None
    latency_randomization: int = 2
    friction_randomization: float = 0.18
    actuator_randomization: float = 0.10
    brush_stiffness_randomization: float = 0.15
    exemplar_motion_strength: float = 0.72
    # 字の外形比をお手本字形に合わせる強さ（大域アフィン）。0 で無効。
    # 骨格 bbox を書き枠に目一杯フィットさせる従来方式では、平たい字は横に
    # 27-39%、縦長の字は縦に 32-65% 伸び、IoU が画数の少ない字ほど悪化していた。
    exemplar_shape_fit: float = 1.0
    # The old 60mm mode amplified pressure up to 1.8x to match font ink mass.
    # That cancels the 0.52 tip-only profile on the larger A4 frames, so the
    # A4 recovery keeps the authored low-pressure curve unchanged.
    exemplar_density_fit: float = 0.0
    # 字の大きさに対して線が太すぎると布白が潰れる。字幅がこの値より小さいとき、
    # 比例して筆圧を下げる [m]。実際の書で小さい字に細い筆を使うのと同じ。
    # 0 で無効。11mm の線幅では、内部に線が入る字は 60mm 程度が下限。
    small_glyph_reference: float = 0.085
    # 小さい字での筆圧倍率の下限。これ以下には細めない。
    small_glyph_floor: float = 0.30

    def __post_init__(self) -> None:
        if self.observation_version not in (None, 1, 2, 3):
            raise ValueError("observation_version must be None, 1, 2, or 3")
        if not 0.0 <= self.exemplar_motion_strength <= 1.0:
            raise ValueError("exemplar_motion_strength must be in [0, 1]")
        if self.training_layout_indices is not None and (
            not self.training_layout_indices
            or len(set(self.training_layout_indices)) != len(self.training_layout_indices)
            or any(not 0 <= index < 6 for index in self.training_layout_indices)
        ):
            raise ValueError("training_layout_indices must contain unique values in 0..5")
        if self.brush.tilt_prepare_steps < 0:
            raise ValueError("tilt_prepare_steps cannot be negative")
        if (
            self.brush.fixed_contact_lean is not None
            and self.brush.fixed_contact_lean < 0.0
        ):
            raise ValueError("fixed_contact_lean cannot be negative")
        if self.attachment_orientation_tolerance <= 0.0:
            raise ValueError("attachment_orientation_tolerance must be positive")
        if self.contact_orientation_ik_weight <= 0.0:
            raise ValueError("contact_orientation_ik_weight must be positive")
        if self.harai_pressure_gain_scale <= 0.0:
            raise ValueError("harai_pressure_gain_scale must be positive")
        if self.hane_release_pressure_gain_scale <= 0.0:
            raise ValueError("hane_release_pressure_gain_scale must be positive")
        if (
            self.pressure_probe_offset_m is not None
            and (
                not np.isfinite(self.pressure_probe_offset_m)
                or abs(self.pressure_probe_offset_m)
                > max(self.contact_pressure_limit, self.horizontal_contact_pressure_limit)
                + 1e-12
            )
        ):
            raise ValueError("pressure_probe_offset_m exceeds contact pressure travel")
        if self.attachment_max_dwell <= 0:
            raise ValueError("attachment_max_dwell must be positive")
        if self.contact_tilt_max_speed <= 0.0:
            raise ValueError("contact_tilt_max_speed must be positive")
        if not 0.0 <= self.tilt_residual_scale <= 1.0:
            raise ValueError("tilt_residual_scale must be in [0, 1]")
        if self.tilt_residual_limit < 0.0:
            raise ValueError("tilt_residual_limit cannot be negative")
        if self.brush.tip_pressure_ceiling <= 0.0:
            raise ValueError("tip_pressure_ceiling must be positive")
        if not 0.0 < self.brush.tip_pressure_floor <= self.brush.tip_pressure_ceiling:
            raise ValueError("tip_pressure_floor must be in (0, tip_pressure_ceiling]")
        if self.brush.pressure_slew_per_step <= 0.0:
            raise ValueError("pressure_slew_per_step must be positive")
        if not 0.0 < self.brush.pressure_response <= 1.0:
            raise ValueError("pressure_response must be in (0, 1]")
        if not 0.0 < self.brush.horizontal_pressure_response <= 1.0:
            raise ValueError("horizontal_pressure_response must be in (0, 1]")
        if min(self.brush.nominal_force, self.brush.large_frame_nominal_force) <= 0.0:
            raise ValueError("nominal forces must be positive")
        if min(
            self.contact_pressure_gain,
            self.large_frame_contact_pressure_gain,
            self.horizontal_contact_pressure_gain,
        ) < 0.0:
            raise ValueError("contact pressure gains cannot be negative")
        if min(self.contact_pressure_limit, self.horizontal_contact_pressure_limit) < 0.0:
            raise ValueError("contact pressure limits cannot be negative")
        if self.hardware.upright_transport_height_m <= self.safe_height:
            raise ValueError("upright transport height must exceed safe_height")

    @property
    def pen_down_z(self) -> float:
        return (
            self.paper.surface_z
            + self.brush.tip_radius
            - self.brush.nominal_compression
        )
