from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/print_camera_hx711_v5'
slicing=json.loads((OUT/'checks/A1mini_slicing_comparison.json').read_text())
roots=json.loads((OUT/'checks/gusset_root_connectivity.json').read_text())
assert slicing['passed'] and slicing['support_extrusion_reduction_fraction']>.7
assert roots['passed'] and len(roots['gussets'])==2
assert all(r['connected_solids_after_tool_relief']==1 and r['root_connection_unchanged'] for r in roots['gussets'])
assert (OUT/'A1mini_0.4_PLA_V5.3mf').exists()
script=(ROOT/'scripts/package_simple_camera_v4.py').read_text()
script=script.replace('v4','v5').replace('V4','V5').replace('V5_simple_print_files.zip','V5_A1mini_PLA_print_files.zip')
exec(compile(script,'package_printable_camera_v5','exec'),globals())
