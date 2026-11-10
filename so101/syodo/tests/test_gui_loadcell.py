import csv
import json
from pathlib import Path
import time

import pytest

from scripts.gui_loadcell import LoadCell, binding, decode_sample
from scripts.export_gui_learning import export


def config():
    return {"camera_url":"http://sensor", "brush_length_mm":240., "tuft_mm":42.,
            "reach_mm":180., "loadcell_enabled":True, "force_limit_n":2.}


def packet(**changes):
    return {"schema":1,"sensor":"hx711-single","boot_id":"test-boot","sequence":1,
            "raw_counts":100000,"device_time_us":1000000,"server_time_us":1010000,
            "ready":True,"saturated":False,**changes}


@pytest.mark.parametrize("changes", [{"ready":False},{"saturated":True},{"raw_counts":8388607},
    {"raw_counts":True},{"sensor":"four-cell"},{"sequence":True},
    {"server_time_us":2000000},{"device_time_us":True},{"server_time_us":float("nan")}])
def test_bad_or_stale_measurement_is_never_a_force(changes):
    with pytest.raises(ValueError): decode_sample(packet(**changes),10,10.02)


def test_device_age_is_subtracted_and_rtt_uncertainty_retained():
    row=decode_sample(packet(),10,10.02)
    assert row["host_sample_monotonic_s"] == pytest.approx(10)
    assert row["clock_uncertainty_s"] == pytest.approx(.01)


def fill(sensor, raw, sequence, boot="test-boot"):
    sensor.samples.clear()
    for i in range(20):
        row=decode_sample(packet(raw_counts=raw+i%2,sequence=sequence+i,boot_id=boot),time.monotonic()-.002,time.monotonic())
        sensor.samples.append(row)
    sensor.latest=sensor.samples[-1]


def calibrated(tmp_path):
    settings=config()
    sensor=LoadCell(tmp_path/"cal.json", lambda:settings)
    fill(sensor,100000,1);sensor.calibrate("tare")
    fill(sensor,110000,40);sensor.calibrate("gain",100)
    assert sensor.status()["axis_force_n"] is None
    fill(sensor,105000,80);sensor.calibrate("verify",50)
    return sensor,settings


def test_single_cell_requires_independent_validation_and_binding(tmp_path):
    sensor,settings=calibrated(tmp_path)
    assert sensor.status()["valid"]
    assert sensor.status()["axis_force_n"] == pytest.approx(.4903325,abs=.0001)
    assert not sensor.status()["normal_force_measured"]
    settings["reach_mm"]=190
    assert not sensor.status()["valid"]
    assert sensor.status()["axis_force_n"] is None


def test_reboot_invalidates_tare_and_cannot_record_fake_zero(tmp_path):
    sensor,_=calibrated(tmp_path)
    fill(sensor,105000,1,"new-boot")
    assert not sensor.status()["valid"]
    with pytest.raises(ValueError): sensor.begin_record(tmp_path/"run")


def test_same_weight_is_not_an_independent_check(tmp_path):
    settings=config(); sensor=LoadCell(tmp_path/"cal.json",lambda:settings)
    fill(sensor,100000,1); sensor.calibrate("tare")
    fill(sensor,110000,40); sensor.calibrate("gain",100)
    fill(sensor,110000,80)
    with pytest.raises(ValueError,match="別の重り"): sensor.calibrate("verify",100)


def test_learning_export_keeps_real_rate_and_separates_axis_force(tmp_path):
    sensor,settings=calibrated(tmp_path)
    session=tmp_path/"run";session.mkdir()
    header={"event":"session","force_session":"s1","calibration":sensor.calibration}
    force=[header]
    robot=[]
    names=("shoulder_pan","shoulder_lift","elbow_flex","wrist_flex","wrist_roll","gripper")
    for i in range(25):
        force.append({**packet(raw_counts=105000,sequence=200+i),"binding":binding(settings),
            "host_sample_monotonic_s":100+i*.1,"clock_uncertainty_s":.003})
        for sub in range(3):
            row={"phase":"write","host_monotonic_s":100+i*.1+sub*.02,"pen_down":"True","target_pressure":.72}
            row.update({f"position_deg:{j}":1. for j in names})
            row.update({f"command_deg:{j}":1.2 for j in names})
            robot.append(row)
    (session/"loadcell.jsonl").write_text("\n".join(json.dumps(r) for r in force))
    with (session/"write.csv").open("w") as f:
        writer=csv.DictWriter(f,fieldnames=list(robot[0]));writer.writeheader();writer.writerows(robot)
    (session/"review.json").write_text(json.dumps({"result":"good","physical_result_reviewed":True}))
    report=export(session,tmp_path/"dataset")
    assert report["observations"] == 25
    assert report["policy_trained"] is False
    assert report["tip_force_measured"] is False
    assert report["evaluation_split"] == "hold_out_complete_sessions"
