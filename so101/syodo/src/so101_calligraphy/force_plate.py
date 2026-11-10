"""Four independent vertical load cells: force and support reaction centre.

The result is not a camera measurement of the hair tip. Tangential brush force,
plate thickness, vibration and multiple contacts can bias the inferred centre.
No motor commands or automatic training promotion are performed here.
"""
from __future__ import annotations

from dataclasses import dataclass
import math


def _finite(values, count: int, name: str) -> tuple[float, ...]:
    result = tuple(float(v) for v in values)
    if len(result) != count or not all(math.isfinite(v) for v in result):
        raise ValueError(f"{name} requires {count} finite values")
    return result


@dataclass(frozen=True)
class ForcePlateCalibration:
    # Channel order: near-left, far-left, far-right, near-right. +X is far;
    # +Y is right. Distances are support spacing, not outer board dimensions.
    support_x_m: float
    support_y_m: float
    zero_counts: tuple[float, ...]
    newtons_per_count: tuple[float, ...]
    minimum_force_n: float
    maximum_force_n: float
    maximum_channel_skew_s: float

    def __post_init__(self):
        vals = _finite((self.support_x_m, self.support_y_m, self.minimum_force_n,
                        self.maximum_force_n, self.maximum_channel_skew_s), 5, "limits")
        if min(vals) <= 0 or self.maximum_force_n <= self.minimum_force_n:
            raise ValueError("Support dimensions and ordered force/time limits must be positive")
        object.__setattr__(self, "zero_counts", _finite(self.zero_counts, 4, "tare"))
        gains = _finite(self.newtons_per_count, 4, "gain")
        if any(g == 0 for g in gains):
            raise ValueError("Each channel needs a nonzero measured gain")
        object.__setattr__(self, "newtons_per_count", gains)

    def estimate(self, raw_counts, channel_time_s, *, saturated: bool = False,
                 hx711_ready=None, cell_ids=None) -> dict:
        raw = _finite(raw_counts, 4, "raw_counts")
        times = _finite(channel_time_s, 4, "channel_time_s")
        if min(times) < 0:
            raise ValueError("Acquisition times must be nonnegative")
        if type(saturated) is not bool:
            raise ValueError("saturated must be a JSON boolean")
        if hx711_ready is not None and (len(hx711_ready) != 4 or
                any(type(v) is not bool for v in hx711_ready)):
            raise ValueError("hx711_ready requires four JSON booleans")
        if cell_ids is not None and tuple(cell_ids) != CELL_IDS:
            raise ValueError("Unexpected cell order; expected [2, 4, 3, 1]")
        forces = _finite(((r - z) * g for r, z, g in
                          zip(raw, self.zero_counts, self.newtons_per_count)), 4, "force")
        # Do not clip a negative reaction: clipping fabricates force/moments.
        total = sum(forces)
        if not math.isfinite(total):
            raise ValueError("Total force overflow")
        reason = None
        if hx711_ready is not None and not all(hx711_ready):
            reason = "channel_not_ready"
        elif saturated or any(v >= 8388607 or v <= -8388608 for v in raw):
            reason = "adc_saturation"
        elif max(times) - min(times) > self.maximum_channel_skew_s:
            reason = "asynchronous_channels"
        elif total < self.minimum_force_n:
            reason = "below_contact_threshold"
        elif total > self.maximum_force_n:
            reason = "force_above_calibrated_range"
        x = y = None
        if reason is None:
            x = self.support_x_m * (forces[1] + forces[2]) / total
            y = self.support_y_m * (forces[2] + forces[3]) / total
            if not (0 <= x <= self.support_x_m and 0 <= y <= self.support_y_m):
                x = y = None
                reason = "reaction_centre_outside_supports"
        return {
            "time_s": sum(times) / 4,
            "channel_force_n": forces,
            "normal_force_n": total,
            "mass_equivalent_g": total / 9.80665 * 1000,
            "channel_skew_s": max(times) - min(times),
            "reaction_centre_x_m": x,
            "reaction_centre_y_m": y,
            "valid": reason is None,
            "invalid_reason": reason,
            "tip_position_measured": False,
        }


# User cell numbers on the plate: 1=near-right, 2=near-left, 3=far-right, 4=far-left.
CELL_IDS = (2, 4, 3, 1)


@dataclass(frozen=True)
class PlateGeometry:
    """Top-left board origin, right/down positive; dimensions in millimetres."""
    width_mm: float = 200.0
    height_mm: float = 300.0
    left_mm: float = 15.0
    right_mm: float = 185.0
    top_mm: float = 15.0
    bottom_mm: float = 285.0

    def __post_init__(self):
        _finite((self.width_mm, self.height_mm, self.left_mm, self.right_mm,
                 self.top_mm, self.bottom_mm), 6, "board geometry")
        if not (0 <= self.left_mm < self.right_mm <= self.width_mm and
                0 <= self.top_mm < self.bottom_mm <= self.height_mm):
            raise ValueError("Support rectangle must lie inside the board")

    @property
    def supports_mm(self):
        return ((self.left_mm, self.bottom_mm), (self.left_mm, self.top_mm),
                (self.right_mm, self.top_mm), (self.right_mm, self.bottom_mm))

    def locate(self, row):
        row = dict(row)
        row["board_x_mm"] = row["board_y_mm"] = None
        if row["valid"]:
            force = row["channel_force_n"]
            total = row["normal_force_n"]
            row["board_x_mm"] = sum(f * xy[0] for f, xy in zip(force, self.supports_mm)) / total
            row["board_y_mm"] = sum(f * xy[1] for f, xy in zip(force, self.supports_mm)) / total
        return row


def estimate_sample(calibration, sample, geometry=None):
    row = calibration.estimate(sample["raw_counts"], sample["channel_time_s"],
                               saturated=sample["saturated"],
                               hx711_ready=sample.get("hx711_ready"),
                               cell_ids=sample.get("cell_ids"))
    return geometry.locate(row) if geometry else row


def polarity_for_down(raw_counts, zero_counts) -> int:
    total = sum(r - z for r, z in zip(raw_counts, zero_counts))
    return -1 if total < 0 else 1


def equal_gain_centre(forces, *, min_total: float = 1.0) -> dict:
    """Unit-square centre. +X far, +Y right. Same bilinear map as estimate()."""
    values = _finite(forces, 4, "forces")
    total = sum(values)
    if total <= min_total:
        return {"valid": False, "total": total, "x": None, "y": None}
    x = (values[1] + values[2]) / total
    y = (values[2] + values[3]) / total
    inside = 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0
    return {"valid": inside, "total": total, "x": x, "y": y}


def plate_canvas_xy(x_far: float, y_right: float, left: float, top: float, width: float, height: float) -> tuple[float, float]:
    """Map plate coords to a y-down canvas. Far (+X) is up, right (+Y) is right."""
    return left + y_right * width, top + (1.0 - x_far) * height
