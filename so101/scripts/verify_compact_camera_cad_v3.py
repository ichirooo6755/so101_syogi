"""Reopen all six F3D and six STEP files natively without changing the user models."""
from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
script=(ROOT/'scripts/finish_camera_addon_v1.py').read_text().split('# All appearance edits below',1)[0]
script=script.replace('print_camera_hx711_v1','print_camera_hx711_v3')
script=script.replace('01_fixed_electronics_frame','01_A_compact_outward_frame_V3')
exec(compile(script,'verify_compact_camera_cad_v3','exec'),globals())
print(json.dumps({'passed':True,'native_files_reopened':len(checks)},indent=2))
