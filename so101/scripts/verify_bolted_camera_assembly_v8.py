"""Reopen the V8 full assembly and audit the unchanged V5 source."""
from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
script=(ROOT/'scripts/verify_stack_assembly_archive_v7.py').read_text()
script=script.replace('camera_mount_v7','camera_mount_v8').replace('01_A_slot_socket_V7','01_bolted_mount_V8')
script=script.replace('occurrences.count==13','occurrences.count==12').replace("'assembly_root_occurrences':13","'assembly_root_occurrences':12")
exec(compile(script,'verify_bolted_camera_assembly_v8','exec'),globals())
