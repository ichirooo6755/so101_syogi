from dataclasses import replace
import json

import pytest

from so101_calligraphy.force_plate import ForcePlateCalibration
from scripts.analyze_force_plate import main


def calibration():
    return ForcePlateCalibration(.3, .2, (100.,) * 4, (.01,) * 4, .05, 10., .005)


def test_known_point_load_after_tare():
    # Bilinear support reactions for 2 N applied at X=.225, Y=.05.
    row = calibration().estimate([137.5, 212.5, 137.5, 112.5], [1.] * 4)
    assert row["normal_force_n"] == pytest.approx(2.)
    assert row["reaction_centre_x_m"] == pytest.approx(.225)
    assert row["reaction_centre_y_m"] == pytest.approx(.05)
    assert row["valid"]


def test_user_cell_numbers_map_to_plate_corners():
    from so101_calligraphy.force_plate import CELL_IDS, equal_gain_centre

    assert CELL_IDS == (2, 4, 3, 1)
    far_left = equal_gain_centre((0, 100, 0, 0), min_total=1)
    assert far_left["x"] == pytest.approx(1)
    assert far_left["y"] == pytest.approx(0)
    near_right = equal_gain_centre((0, 0, 0, 100), min_total=1)
    assert near_right["x"] == pytest.approx(0)
    assert near_right["y"] == pytest.approx(1)


def test_plate_canvas_puts_far_left_at_top_left():
    from so101_calligraphy.force_plate import plate_canvas_xy

    x, y = plate_canvas_xy(1, 0, 10, 20, 100, 200)
    assert x == pytest.approx(10)
    assert y == pytest.approx(20)
    x, y = plate_canvas_xy(0, 1, 10, 20, 100, 200)
    assert x == pytest.approx(110)
    assert y == pytest.approx(220)


@pytest.mark.parametrize("raw,times,saturation,reason", [
    ([100.] * 4, [1.] * 4, False, "below_contact_threshold"),
    ([150.] * 4, [1., 1., 1., 1.02], False, "asynchronous_channels"),
    ([150.] * 4, [1.] * 4, True, "adc_saturation"),
    ([400.] * 4, [1.] * 4, False, "force_above_calibrated_range"),
    ([0., 100., 200., 100.], [1.] * 4, False, "below_contact_threshold"),
])
def test_invalid_sample_never_invents_tip_position(raw, times, saturation, reason):
    row = calibration().estimate(raw, times, saturated=saturation)
    assert not row["valid"]
    assert row["invalid_reason"] == reason
    assert row["reaction_centre_x_m"] is None
    assert row["tip_position_measured"] is False


def test_negative_reactions_are_not_clipped():
    row = calibration().estimate([90., 210., 100., 100.], [1.] * 4)
    assert row["normal_force_n"] == pytest.approx(1.)
    assert row["invalid_reason"] == "reaction_centre_outside_supports"


def test_signed_channel_gain_and_nonfinite_rejection():
    c = replace(calibration(), newtons_per_count=(-.01,) * 4)
    assert c.estimate([50.] * 4, [1.] * 4)["normal_force_n"] == pytest.approx(2.)
    with pytest.raises(ValueError):
        c.estimate([float("nan")] * 4, [1.] * 4)


def test_converter_writes_diagnostic_bundle_and_rejects_duplicate_clock(tmp_path):
    from dataclasses import asdict
    config = tmp_path / "calibration.json"
    config.write_text(json.dumps({"schema": 1, "calibration": asdict(calibration())}))
    raw = tmp_path / "raw.jsonl"
    sample = json.dumps({"raw_counts": [150.] * 4, "channel_time_s": [1.] * 4, "saturated": False})
    raw.write_text(sample + "\n")
    out = tmp_path / "result"
    assert main([str(raw), "--calibration", str(config), "--out", str(out)]) == 0
    summary = json.loads((out / "summary.json").read_text())
    assert summary["valid_samples"] == 1
    assert summary["training_eligible"] is False
    raw.write_text(sample + "\n" + sample + "\n")
    with pytest.raises(ValueError, match="timestamp"):
        main([str(raw), "--calibration", str(config), "--out", str(tmp_path / "invalid")])
    assert not (tmp_path / "invalid").exists()
