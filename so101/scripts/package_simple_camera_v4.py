"""Audit and package the two-print / two-bolt simple mount only."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/print_camera_hx711_v4'
native=json.loads((OUT/'checks/release_native_check.json').read_text())
simple=json.loads((OUT/'checks/simplification_check.json').read_text())
paths=json.loads((OUT/'checks/assembly_paths.json').read_text())
assert native['passed'] and native['assembly_archive_reopened']
assert len(native['fastener_engagement'])==2
assert simple['passed'] and simple['printed_parts']==2 and simple['nuts']=={'M3_hex':2}
assert simple['bolts']=={'M3x10':2} and simple['separate_PCB_keepers']==0
assert len(paths['clamp_complete_bolt_insertion_before_PCB'])==14
assert not any(r['printed_part_hits'] for r in paths['clamp_complete_bolt_insertion_before_PCB'])
assert len(paths['populated_PCB_approach'])==18 and not any(r['hits'] for r in paths['populated_PCB_approach'])
script=(ROOT/'scripts/package_camera_addon_v1.py').read_text()
script=script.replace('print_camera_hx711_v1','print_camera_hx711_v4')
script=script.replace('so101_camera_hx711_V1_print_files.zip','so101_camera_hx711_V4_simple_print_files.zip')
script=script.replace("len(mesh)==6","len(mesh)==2").replace("len(cad['files'])==12","len(cad['files'])==4")
script=script.replace("'printable_part_types':6,'printed_piece_count':6","'printable_part_types':2,'printed_piece_count':2")
script=script.replace("'M3x8_socket_cap':5,'M3x10_socket_cap':1,'M3_hex_nut':6","'M3x10_socket_cap':2,'M3_hex_nut':2")
script=script.replace("'native_cad_reopened':12","'native_cad_reopened':4")
old="assert paths['passed'] and not any(r['hits'] for r in paths['paths']+paths['cartridge_removal'])"
assert script.count(old)==1
script=script.replace(old,"assert paths['passed'] and not any(r['moving_part_hits'] or r['fixed_hits'] for r in paths['paths']) and not any(r['hits'] for r in paths['cartridge_removal'])")
exec(compile(script,'package_simple_camera_v4','exec'),globals())
