from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
exec(compile((ROOT/'scripts/build_glueless_camera_v6.py').read_text(),'build_V6','exec'),globals())
exec(compile((ROOT/'scripts/check_glueless_assembly_v6.py').read_text(),'assembly_check_V6','exec'),globals())
