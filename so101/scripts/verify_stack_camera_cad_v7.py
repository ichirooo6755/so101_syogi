"""Reopen each exported native part without modifying existing Fusion documents."""
from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
script=(ROOT/'scripts/finish_camera_addon_v1.py').read_text().split('# All appearance edits below',1)[0]
script=script.replace('print_camera_hx711_v1','camera_mount_v7/print_candidate')
script=script.replace('01_fixed_electronics_frame','01_A_slot_socket_V7')
exec(compile(script,'verify_stack_camera_cad_v7','exec'),globals())
print(json.dumps({'passed':True,'native_files_reopened':len(checks)},indent=2))
