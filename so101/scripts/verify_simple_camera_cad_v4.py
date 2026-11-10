"""Reopen the two F3D and two STEP files natively."""
from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
script=(ROOT/'scripts/finish_camera_addon_v1.py').read_text().split('# All appearance edits below',1)[0]
script=script.replace('print_camera_hx711_v1','print_camera_hx711_v4')
script=script.replace('01_fixed_electronics_frame','01_simple_camera_HX711_bracket_V4')
exec(compile(script,'verify_simple_camera_cad_v4','exec'),globals())
print(json.dumps({'passed':True,'native_files_reopened':len(checks)},indent=2))
