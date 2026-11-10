"""Stroke sources and conversion to 3-D writing waypoints."""

from so101_calligraphy.trajectory.education import (
    EducationKanji,
    JoyoTrajectoryDataset,
    load_education_kanji,
    load_education_trajectories,
    load_joyo_kanji,
    load_joyo_trajectories,
    lazy_joyo_trajectories,
)
from so101_calligraphy.trajectory.primitives import primitive_trajectory
from so101_calligraphy.trajectory.sequence import WaypointSequence, build_waypoint_sequence
from so101_calligraphy.trajectory.svg import load_svg_trajectory
from so101_calligraphy.trajectory.types import Stroke, Trajectory

__all__ = [
    "EducationKanji",
    "JoyoTrajectoryDataset",
    "Stroke",
    "Trajectory",
    "WaypointSequence",
    "build_waypoint_sequence",
    "load_education_kanji",
    "load_education_trajectories",
    "load_joyo_kanji",
    "load_joyo_trajectories",
    "lazy_joyo_trajectories",
    "load_svg_trajectory",
    "primitive_trajectory",
]
