"""Export checked V8 in explicit A1 mini print orientations."""
from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
script=(ROOT/'scripts/export_glueless_camera_v6.py').read_text()
script=script.replace('camera_mount_v6','camera_mount_v8').replace('V6','V8')
script=script.replace('01_flat_carrier_socket_V8','01_bolted_mount_V8')
script=script.replace("n.startswith(('01_','02_'))","n.startswith(('01_','02_','04_'))")
script=script.replace("n.startswith('03_')","n.startswith('05_')")
script=script.replace("n.startswith('04_')","n.startswith('03_')")
script=script.replace("'TXS0108E' in n","'perfboard_same_size' in n")
script=script.replace('abs(f.geometry.origin.y*10-47)<1e-6','abs(f.geometry.origin.y*10-35.75)<1e-6')
old="rows=(CA,scale(CB,-1),CN) if name.startswith('04_') else (EX,(0,0,-1),EY)"
new="rows=(CB,CN,scale(CA,-1)) if name.startswith('05_') else (scale(CB,-1),CN,CA) if name.startswith(('03_','04_')) else (EX,(0,0,-1),EY)"
assert old in script;script=script.replace(old,new)
script=script.replace("'camera tray broad back face down' if name.startswith('04_') else 'flat broad back face down'", "'camera or stack end face down' if name.startswith(('03_','04_','05_')) else 'flat broad back face down'")
old_visibility="for o in root.occurrences:\n    if o.component.name.startswith('REFERENCE_'):o.isLightBulbOn=False\npreview('03_four_printed_parts',(180,240,140))\nfor o in root.occurrences:\n    if o.component.name.startswith('REFERENCE_'):o.isLightBulbOn=True"
new_visibility="reference_visibility={o.name:o.isLightBulbOn for o in root.occurrences if o.component.name.startswith('REFERENCE_')}\nfor o in root.occurrences:\n    if o.component.name.startswith('REFERENCE_'):o.isLightBulbOn=False\npreview('03_five_printed_parts',(180,240,140))\nfor o in root.occurrences:\n    if o.name in reference_visibility:o.isLightBulbOn=reference_visibility[o.name]"
assert old_visibility in script;script=script.replace(old_visibility,new_visibility)
script=script.replace("'printed_parts':4","'printed_parts':5")
script=script.replace("'PCB_or_camera_extra_fasteners':0","'PCB_or_camera_extra_fasteners':4")
script=script.replace('SO101_Glueless_Camera_HX711_V8_assembly_DO_NOT_PRINT.f3d','SO101_XIAO_SEN13879_bolted_V8_assembly_DO_NOT_PRINT.f3d')
exec(compile(script,'V8_native_export','exec'),globals())
