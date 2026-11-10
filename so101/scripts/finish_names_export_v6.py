import adsk.core
import adsk.fusion
import json
from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
build=json.loads((ROOT/'output/camera_mount_v6/design_check.json').read_text())
owned=[]
for doc in app.documents:
    d=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    if d and d.rootComponent.occurrences.itemByName('01_flat_carrier_socket_V6:1'):owned.append((doc,d))
document,design=owned[-1]; root=design.rootComponent
labels={k:[k] for k in build['geometry']}
labels.update({'REFERENCE_SO101_unchanged':[f'existing_body_{i+1}' for i in range(26)],
    'REFERENCE_XIAO_Sense_1pc':[f'XIAO_reference_{i+1}' for i in range(103)]+[
        f'GPIO_wire_keepout_{a}_{sign}' for a in (-7.62,-5.08,-2.54,0,2.54,5.08,7.62) for sign in (-1,1)],
    'REFERENCE_HX711_1pc':['HX711_PCB','HX711_components_keepout','HX711_terminal_blocks','HX711_wires_keepout'],
    'REFERENCE_TXS0108E_5V_3V3_translator_1pc':['TXS0108E_PCB','TXS0108E_leads_left_keepout',
        'TXS0108E_leads_right_keepout','TXS0108E_IC_keepout'],
    'REFERENCE_M3_hardware_do_not_print':['M3x12_A_22','M3_nut_A_22','M3x12_A_34','M3_nut_A_34']})
for name,body_names in labels.items():
    o=root.occurrences.itemByName(name+':1'); assert o.bRepBodies.count==len(body_names),(name,o.bRepBodies.count)
    for b,label in zip(o.component.bRepBodies,body_names):
        b.name=label
        if 'keepout' in label:b.isLightBulbOn=False
name='so101_接着不要_カメラHX711_V6'
if not document.dataFile:
    source=next(d for d in app.documents if d.name=='so101書道')
    assert document.saveAs(name,source.dataFile.parentFolder,
        'Glueless rigid PCB capture, preserved USB side and original optical axis. Four flat prints, two M3x12 bolts/nuts. Physical fit untested.','')
elif document.isModified:document.save('V6 precise body labels and hidden lead keepouts')
exec(compile((ROOT/'scripts/check_glueless_assembly_v6.py').read_text(),'V6_rechecked_names_and_14_bolt_paths','exec'),globals())
exec(compile((ROOT/'scripts/export_glueless_camera_v6.py').read_text(),'V6_final_checked_exports','exec'),globals())
if document.isModified:document.save('V6 final print orientation, labels and module display')
