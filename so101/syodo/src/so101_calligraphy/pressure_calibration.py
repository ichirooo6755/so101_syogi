"""Versioned monotonic pressure-to-Z lookup table and calibration representation."""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
import json
import math
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Sequence

CALIBRATION_SCHEMA_VERSION = 2
DEFAULT_CAD_FINGERPRINT = "pivot30-offset7.764571-tip38"
DEFAULT_BRUSH_FINGERPRINT = "tip-only-v1"

SUPPORTED_LAYOUT_CLASSES = ("85mm", "110mm")
SUPPORTED_PHASES = ("entry", "send", "corner", "finish")
SUPPORTED_ANGLES_DEG = (0, 4, 8, 12, 20, 30, 45)


def monotone_non_decreasing(
    values: Sequence[float],
    weights: Sequence[float] | None = None,
) -> tuple[float, ...]:
    """Pool Adjacent Violators Algorithm (PAVA) for isotonic regression."""
    y = [float(v) for v in values]
    n = len(y)
    w = [float(w_val) for w_val in weights] if weights is not None else [1.0] * n
    if len(w) != n:
        raise ValueError("values and weights must have the same length")
    if any(w_val <= 0.0 or not math.isfinite(w_val) for w_val in w):
        raise ValueError("weights must be positive and finite")
    if any(not math.isfinite(v) for v in y):
        raise ValueError("values must be finite")
    if not y:
        return ()

    # Stack of blocks: each block is [sum_w*y, sum_w, [indices]]
    blocks: list[list[Any]] = []
    for i in range(n):
        blocks.append([w[i] * y[i], w[i], [i]])
        while len(blocks) >= 2:
            mean_prev = blocks[-2][0] / blocks[-2][1]
            mean_curr = blocks[-1][0] / blocks[-1][1]
            if mean_prev <= mean_curr:
                break
            # Merge blocks[-1] into blocks[-2]
            prev = blocks.pop()
            blocks[-1][0] += prev[0]
            blocks[-1][1] += prev[1]
            blocks[-1][2].extend(prev[2])

    result = [0.0] * n
    for wy_sum, w_sum, indices in blocks:
        mean_val = wy_sum / w_sum
        for idx in indices:
            result[idx] = mean_val
    return tuple(result)


@dataclass(frozen=True)
class PressureCurve:
    pressure: tuple[float, ...]
    offset_m: tuple[float, ...]
    sample_weight: tuple[float, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "pressure", tuple(float(p) for p in self.pressure))
        object.__setattr__(self, "offset_m", tuple(float(o) for o in self.offset_m))
        object.__setattr__(self, "sample_weight", tuple(float(w) for w in self.sample_weight))

    def validate(self, maximum_offset_m: float = 0.005) -> None:
        n = len(self.pressure)
        if n < 2:
            raise ValueError("curve must have at least 2 knots")
        if len(self.offset_m) != n or len(self.sample_weight) != n:
            raise ValueError("pressure, offset_m, sample_weight must have the same length")
        for p in self.pressure:
            if not math.isfinite(p):
                raise ValueError("pressure knots must be finite")
        for o in self.offset_m:
            if not math.isfinite(o):
                raise ValueError("offset knots must be finite")
            if abs(o) > maximum_offset_m + 1e-9:
                raise ValueError(f"offset knot {o} exceeds maximum_offset_m {maximum_offset_m}")
        for w in self.sample_weight:
            if not math.isfinite(w) or w <= 0.0:
                raise ValueError("sample weights must be positive and finite")
        for i in range(n - 1):
            if self.pressure[i + 1] <= self.pressure[i]:
                raise ValueError("pressure knots must be strictly increasing")
            if self.offset_m[i + 1] > self.offset_m[i] + 1e-9:
                raise ValueError("offset_m must be monotone non-increasing")

    def lookup(self, target_pressure: float) -> tuple[float, bool]:
        """Piecewise linear interpolation on monotone table. Returns (offset_m, clipped)."""
        if not math.isfinite(target_pressure):
            raise ValueError("target_pressure must be finite")
        if target_pressure <= self.pressure[0]:
            return self.offset_m[0], target_pressure < self.pressure[0]
        if target_pressure >= self.pressure[-1]:
            return self.offset_m[-1], target_pressure > self.pressure[-1]

        right = bisect_right(self.pressure, target_pressure)
        left = right - 1
        fraction = (
            (target_pressure - self.pressure[left])
            / (self.pressure[right] - self.pressure[left])
        )
        offset = self.offset_m[left] + fraction * (
            self.offset_m[right] - self.offset_m[left]
        )
        return offset, False

    def to_dict(self) -> dict[str, list[float]]:
        return {
            "pressure": list(self.pressure),
            "offset_m": list(self.offset_m),
            "sample_weight": list(self.sample_weight),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Sequence[float]]) -> PressureCurve:
        for field in ("pressure", "offset_m", "sample_weight"):
            if field not in data:
                raise ValueError(f"{field} is required")
        return cls(
            pressure=tuple(float(x) for x in data["pressure"]),
            offset_m=tuple(float(x) for x in data["offset_m"]),
            sample_weight=tuple(float(x) for x in data["sample_weight"]),
        )


@dataclass(frozen=True)
class PressureLookup:
    offset_m: float
    clipped: bool
    fallback: bool

    def to_dict(self) -> dict[str, float | bool]:
        return {
            "offset_m": self.offset_m,
            "clipped": self.clipped,
            "fallback": self.fallback,
        }


# Compatibility for the already-integrated environment on this branch.
PressureLookupResult = PressureLookup


def _format_angle_deg(angle_deg: float) -> str | None:
    try:
        value = float(angle_deg)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(value):
        return None
    if value == 0.0:
        value = 0.0
    if value.is_integer():
        return str(int(value))
    return format(value, ".15g")


@dataclass(frozen=True)
class PressureCalibration:
    schema_version: int
    cad_fingerprint: str
    brush_fingerprint: str
    maximum_offset_m: float
    curves: Mapping[str, PressureCurve]
    provenance: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "curves", MappingProxyType(dict(self.curves)))
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))
        self.validate()

    def validate(self) -> None:
        if self.schema_version != CALIBRATION_SCHEMA_VERSION:
            raise ValueError(f"Unsupported schema_version: {self.schema_version}")
        if not self.cad_fingerprint or not isinstance(self.cad_fingerprint, str):
            raise ValueError("cad_fingerprint must be a non-empty string")
        if not self.brush_fingerprint or not isinstance(self.brush_fingerprint, str):
            raise ValueError("brush_fingerprint must be a non-empty string")
        if self.maximum_offset_m <= 0.0 or not math.isfinite(self.maximum_offset_m):
            raise ValueError("maximum_offset_m must be positive and finite")
        try:
            json.dumps(dict(self.provenance), allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise ValueError("provenance must contain only finite JSON values") from exc
        for key, curve in self.curves.items():
            if not isinstance(key, str):
                raise ValueError("curve keys must be strings")
            parts = key.split("/")
            if len(parts) != 3:
                raise ValueError(f"Invalid curve key format: {key}")
            layout_class, angle_str, phase = parts
            if layout_class not in SUPPORTED_LAYOUT_CLASSES:
                raise ValueError(f"Unsupported layout class in curve key: {key}")
            try:
                angle_int = int(angle_str)
            except ValueError:
                raise ValueError(f"Invalid angle in curve key: {key}")
            if angle_str != str(angle_int):
                raise ValueError(f"Invalid angle in curve key: {key}")
            if angle_int not in SUPPORTED_ANGLES_DEG:
                raise ValueError(f"Unsupported angle in curve key: {key}")
            if phase not in SUPPORTED_PHASES:
                raise ValueError(f"Unsupported phase in curve key: {key}")
            curve.validate(self.maximum_offset_m)

    def lookup(
        self,
        layout_class: str,
        angle_deg: float,
        phase: str,
        target_pressure: float,
    ) -> PressureLookup:
        angle = _format_angle_deg(angle_deg)
        key = None if angle is None else f"{layout_class}/{angle}/{phase}"
        curve = None if key is None else self.curves.get(key)
        if curve is None:
            return PressureLookup(
                offset_m=0.0,
                clipped=False,
                fallback=True,
            )
        offset, clipped = curve.lookup(target_pressure)
        return PressureLookup(
            offset_m=offset,
            clipped=clipped,
            fallback=False,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "cad_fingerprint": self.cad_fingerprint,
            "brush_fingerprint": self.brush_fingerprint,
            "maximum_offset_m": self.maximum_offset_m,
            "curves": {k: c.to_dict() for k, c in self.curves.items()},
            "provenance": dict(self.provenance),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PressureCalibration:
        required = (
            "schema_version",
            "cad_fingerprint",
            "brush_fingerprint",
            "maximum_offset_m",
            "curves",
            "provenance",
        )
        for field in required:
            if field not in data:
                raise ValueError(f"{field} is required")
        curves_raw = data["curves"]
        if not isinstance(curves_raw, Mapping):
            raise ValueError("curves must be a JSON object")
        provenance = data["provenance"]
        if not isinstance(provenance, Mapping):
            raise ValueError("provenance must be a JSON object")
        curves = {k: PressureCurve.from_dict(v) for k, v in curves_raw.items()}
        return cls(
            schema_version=int(data["schema_version"]),
            cad_fingerprint=str(data["cad_fingerprint"]),
            brush_fingerprint=str(data["brush_fingerprint"]),
            maximum_offset_m=float(data["maximum_offset_m"]),
            curves=curves,
            provenance=dict(provenance),
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2, allow_nan=False)

    @classmethod
    def load(cls, path: Path) -> PressureCalibration:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)
