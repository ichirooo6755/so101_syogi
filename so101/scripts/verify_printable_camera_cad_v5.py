from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
script=(ROOT/'scripts/verify_simple_camera_cad_v4.py').read_text()
script=script.replace('v4','v5').replace('V4','V5').replace('01_simple_camera_HX711_bracket','01_A1mini_ribbed_camera_bracket')
exec(compile(script,'verify_printable_camera_cad_v5','exec'),globals())
