"""Slice five V8 parts as one A1 mini plate with local isolated settings."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
script=(ROOT/'scripts/slice_glueless_camera_v6.py').read_text().replace('camera_mount_v6','camera_mount_v8')
script=script.replace('v6_final','v8_final').replace("choices=['v6']","choices=['v8']")
script=script.replace('[(8,8),(8,94),(104,8),(43,94)]','[(8,8),(70,8),(8,70),(65,70),(120,70)]')
script=script.replace('len(list(build))==4','len(list(build))==5').replace('assert len(meshes)==4','assert len(meshes)==5')
exec(compile(script,'V8_A1mini_slice','exec'),globals())
