"""Audit and package only the current short Selection 2-side print set."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/print_camera_hx711_v3'
native=json.loads((OUT/'checks/release_native_check.json').read_text())
compact=json.loads((OUT/'checks/compaction_check.json').read_text())
paths=json.loads((OUT/'checks/assembly_paths.json').read_text())
assert native['passed'] and native['assembly_archive_reopened']
assert compact['passed'] and compact['previous_V2_preserved']
assert compact['frame_x_width_compact_mm']<47
assert len(paths['clamp_complete_bolt_insertion_before_PCB'])==14
assert not any(r['printed_part_hits'] for r in paths['clamp_complete_bolt_insertion_before_PCB'])
script=(ROOT/'scripts/package_camera_addon_v1.py').read_text()
script=script.replace('print_camera_hx711_v1','print_camera_hx711_v3')
script=script.replace('so101_camera_hx711_V1_print_files.zip','so101_camera_hx711_V3_compact_print_files.zip')
script=script.replace("'M3x8_socket_cap':5,'M3x10_socket_cap':1", "'M3x8_socket_cap':3,'M3x10_socket_cap':3")
old="assert paths['passed'] and not any(r['hits'] for r in paths['paths']+paths['cartridge_removal'])"
assert script.count(old)==1
script=script.replace(old,"assert paths['passed'] and not any(r['moving_part_hits'] or r['fixed_hits'] for r in paths['paths']) and not any(r['hits'] for r in paths['cartridge_removal'])")
exec(compile(script,'package_compact_camera_v3','exec'),globals())
