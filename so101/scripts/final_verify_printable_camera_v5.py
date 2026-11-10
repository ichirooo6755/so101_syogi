from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
script=(ROOT/'scripts/final_verify_simple_camera_v4.py').read_text()
script=script.replace('v4','v5').replace('V4','V5')
script=script.replace('01_simple_camera_HX711_bracket','01_A1mini_ribbed_camera_bracket').replace('SelectionA_Simple','SelectionA_Printable')
script=script.replace('SelectionA_Printable_Camera_HX711_V5','A1mini_PLA_造形用_V5')
script=script.replace("'source_V3_preserved':True","'source_V4_preserved':True")
exec(compile(script,'final_verify_printable_camera_v5','exec'),globals())
