"""Finish the source-body update after discovering the BaseFeature edit API."""
import adsk.core
import adsk.fusion
import json
from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
target_doc=next(d for d in app.documents if d.name=='so101_SelectionA_Printable_Camera_HX711_V5')
target_design=adsk.fusion.Design.cast(target_doc.products.itemByProductType('DesignProductType'))
candidates=[]
for doc in app.documents:
    d=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    if doc!=target_doc and d and d.rootComponent.occurrences.itemByName('01_A1mini_ribbed_camera_bracket_V5:1'):
        candidates.append((doc,d))
assert len(candidates)==1
temporary_doc,temp=candidates[0]; T=adsk.fusion.TemporaryBRepManager.get()
names=['01_A1mini_ribbed_camera_bracket_V5','02_joined_slot_backing_V5']
new={name:T.copy(temp.rootComponent.occurrences.itemByName(name+':1').bRepBodies.item(0)) for name in names}
target_doc.activate()
for name in names:
    o=target_design.rootComponent.occurrences.itemByName(name+':1'); base=o.component.features.baseFeatures.item(0)
    base.finishEdit(); target_design.timeline.moveToEnd()
    q=T.copy(new[name]); inv=o.transform2.copy(); inv.invert(); T.transform(q,inv)
    assert base.startEdit()
    assert len(base.sourceBodies)==1
    assert base.updateBody(base.sourceBodies[0],q)
    assert base.finishEdit()
    target_design.timeline.moveToEnd()
    assert abs(o.bRepBodies.item(0).volume*1000-new[name].volume*1000)<1e-6
for s in list(target_design.selectionSets):
    if s.name=='選択セット2_外側方向':s.deleteMe()
o=target_design.rootComponent.occurrences.itemByName(names[0]+':1')
faces=[f for f in o.bRepBodies.item(0).faces
    if f.geometry.surfaceType==adsk.core.SurfaceTypes.PlaneSurfaceType and abs(f.geometry.origin.y*10-49.75)<1e-6]
f=max(faces,key=lambda f:f.area)
target_design.selectionSets.add([f],'選択セット2_外側方向')
archive=ROOT/'output/camera_mount_v5/SO101_SelectionA_Printable_Camera_HX711_V5_assembly.f3d'
assert target_design.exportManager.execute(target_design.exportManager.createFusionArchiveExportOptions(str(archive)))
target_doc.save('Move both camera gusset roots clear of M3 tool passages')
temporary_doc.close(False); target_doc.activate()
print(json.dumps({'updated_document':target_doc.name,'parts':names,'camera_gussets_clear_of_tool_holes':True},indent=2))
