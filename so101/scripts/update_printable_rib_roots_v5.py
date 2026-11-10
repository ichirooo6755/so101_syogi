"""Route both camera gussets outside the bolt access paths; update our V5 in place."""
import adsk.core
import adsk.fusion
import json
from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
target_doc=next(d for d in app.documents if d.name=='so101_SelectionA_Printable_Camera_HX711_V5')
target_design=adsk.fusion.Design.cast(target_doc.products.itemByProductType('DesignProductType'))
old_report=json.loads((ROOT/'output/print_camera_hx711_v5/export_report.json').read_text())
for row in old_report['exports']:
    o=target_design.rootComponent.occurrences.itemByName(row['part']+':1')
    assert abs(o.bRepBodies.item(0).volume*1000-row['volume_mm3'])<1e-6,'Do not overwrite unknown user geometry edits'
backup=ROOT/'output/camera_mount_v5/before_rib_tool_clearance_update.f3d'
assert not backup.exists()
assert target_design.exportManager.execute(target_design.exportManager.createFusionArchiveExportOptions(str(backup)))
exec(compile((ROOT/'scripts/build_printable_camera_v5.py').read_text(),'rebuild_checked_ribs_v5','exec'),globals())
temporary_doc=doc
target_doc.activate()
for name,body in parts.items():
    c=target_design.rootComponent.occurrences.itemByName(name+':1').component
    base=c.features.baseFeatures.item(0); base.startEdit()
    assert base.updateBody(base.sourceBodies[0],body)
    base.finishEdit()
for s in list(target_design.selectionSets):
    if s.name=='選択セット2_外側方向':s.deleteMe()
o=target_design.rootComponent.occurrences.itemByName('01_A1mini_ribbed_camera_bracket_V5:1')
faces=[f for f in o.component.bRepBodies.item(0).faces
    if f.geometry.surfaceType==adsk.core.SurfaceTypes.PlaneSurfaceType and abs(f.geometry.origin.y*10-49.75)<1e-6]
f=max(faces,key=lambda f:f.area)
target_design.selectionSets.add([f.createForAssemblyContext(o)],'選択セット2_外側方向')
for name,body in parts.items():
    b=target_design.rootComponent.occurrences.itemByName(name+':1').bRepBodies.item(0)
    assert abs(b.volume*1000-body.volume*1000)<1e-6
assert target_design.exportManager.execute(target_design.exportManager.createFusionArchiveExportOptions(str(archive)))
target_doc.save('Move camera gusset roots outside both M3 tool paths; no severed gusset root')
temporary_doc.close(False); target_doc.activate()
print(json.dumps({'updated_document':target_doc.name,'parts':list(parts),'source_V4_preserved':True},indent=2))
