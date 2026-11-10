"""Export DfAM geometry and keep the verified two-bolt / two-part assembly paths."""
from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
script=(ROOT/'scripts/export_simple_camera_v4.py').read_text()
script=script.replace('v4','v5').replace('V4','V5')
script=script.replace('01_simple_camera_HX711_bracket','01_A1mini_ribbed_camera_bracket')
script=script.replace('02_A_slot_backing','02_joined_slot_backing').replace('SelectionA_Simple','SelectionA_Printable')
script=script.replace('removable open support under PCB tray and angled camera ledge required',
    '45 degree ribs and low overhangs; verify limited organic support in supplied A1 mini 3MF')
save_helper="""def save_or_update(name,folder,description,version):
    if document.dataFile and document.name in (name,'so101_A1mini_PLA_造形用_V5'):
        if document.isModified: document.save(description)
        return True
    return document.saveAs(name,folder,description,version)
cloud={}"""
needle="exec(compile(script,'export_simple_camera_v5','exec'),globals())"
assert script.count(needle)==1
injection="script=script.replace('assert document.saveAs(', 'assert save_or_update(')\n"
injection+="script=script.replace('cloud={}',"+repr(save_helper)+")\n"
script=script.replace(needle,injection+needle)
exec(compile(script,'export_printable_camera_v5','exec'),globals())
shutil.copy2(CHECK/'DfAM_check.json',OUT/'checks/DfAM_check.json')
