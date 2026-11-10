"""Reopen all separate F3D and STEP parts without touching existing docs."""
from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
script=(ROOT/'scripts/verify_stack_camera_cad_v7.py').read_text()
script=script.replace('camera_mount_v7','camera_mount_v8').replace('01_A_slot_socket_V7','01_bolted_mount_V8')
exec(compile(script,'verify_bolted_camera_cad_v8','exec'),globals())
