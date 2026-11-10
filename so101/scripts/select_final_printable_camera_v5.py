"""Retain checked replacement assembly; discard only our unchanged failed edit copy."""
import adsk.core
import adsk.fusion
import json
from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
old=next(doc for doc in app.documents if doc.name=='so101_SelectionA_Printable_Camera_HX711_V5')
assert (ROOT/'output/camera_mount_v5/before_rib_tool_clearance_update.f3d').exists()
candidates=[]
for doc in app.documents:
    d=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    if doc!=old and d and d.rootComponent.occurrences.itemByName('01_A1mini_ribbed_camera_bracket_V5:1'):
        candidates.append((doc,d))
assert len(candidates)==1
new_doc,d=candidates[0]
expected=json.loads((ROOT/'output/camera_mount_v5/candidate_geometry.json').read_text())['parts']
for name,row in expected.items():
    b=d.rootComponent.occurrences.itemByName(name+':1').bRepBodies.item(0)
    assert abs(b.volume*1000-row['volume_mm3'])<1e-6
# The old saved cloud design and its explicit local backup are retained.
assert old.close(False)
new_doc.activate()
main=next(doc for doc in app.documents if doc.name=='so101書道')
assert new_doc.saveAs('so101_A1mini_PLA_造形用_V5',main.dataFile.parentFolder,
    'A1 mini PLA: rib roots clear of bolt tool paths, two M3x10, two nuts. Physical test pending.','')
print(json.dumps({'document':new_doc.name,'checked_replacement_active':True,'old_cloud_and_local_backup_retained':True},ensure_ascii=False,indent=2))
