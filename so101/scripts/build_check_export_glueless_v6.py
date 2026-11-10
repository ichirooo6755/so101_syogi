from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
for name in ('build_glueless_camera_v6.py','check_glueless_assembly_v6.py','export_glueless_camera_v6.py'):
    exec(compile((ROOT/'scripts'/name).read_text(),name,'exec'),globals())
