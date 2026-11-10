"""Place six flat parts on one A1 mini plate and slice using isolated profiles."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
script=(ROOT/'scripts/slice_glueless_camera_v6.py').read_text().replace('camera_mount_v6','camera_mount_v7')
script=script.replace('v6_final','v7_final').replace("choices=['v6']","choices=['v7']")
script=script.replace('[(8,8),(8,94),(104,8),(43,94)]','[(8,8),(70,8),(110,8),(8,65),(70,65),(110,65)]')
script=script.replace('len(list(build))==4','len(list(build))==6').replace('assert len(meshes)==4','assert len(meshes)==6')
exec(compile(script,'V7_A1mini_slice','exec'),globals())
