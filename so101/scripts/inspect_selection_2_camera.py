"""Read-only location of selection set 2, including inactive user documents."""
import adsk.core
import adsk.fusion
import json
from pathlib import Path
OUT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101/output/camera_mount_v3')
OUT.mkdir(parents=True,exist_ok=True)
def mm(p):return [v*10 for v in p.asArray()]
def describe(e):
    r={'type':e.objectType}
    try:
        bb=e.boundingBox; r['bounds_mm']=[mm(bb.minPoint),mm(bb.maxPoint)]
    except Exception: pass
    f=adsk.fusion.BRepFace.cast(e)
    if f:
        r.update({'area_mm2':f.area*100,'centroid_mm':mm(f.centroid),'body':f.body.name,
            'volume_mm3':f.body.volume*1000,'component':f.body.parentComponent.name,
            'occurrence':f.body.assemblyContext.fullPathName if f.body.assemblyContext else None})
        if f.geometry.surfaceType==adsk.core.SurfaceTypes.PlaneSurfaceType:
            r.update({'normal':list(f.geometry.normal.asArray()),'plane_origin_mm':mm(f.geometry.origin)})
    return r
report={'active_document':app.activeDocument.name,'documents':[],'active_selection':[]}
for doc in app.documents:
    d=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    if not d:continue
    sets=[{'name':s.name,'entities':[describe(e) for e in s.entities]} for s in d.selectionSets]
    report['documents'].append({'name':doc.name,'modified':doc.isModified,'selection_sets':sets})
for i in range(ui.activeSelections.count):report['active_selection'].append(describe(ui.activeSelections.item(i).entity))
cam=app.activeViewport.camera
report['camera']={'eye_mm':mm(cam.eye),'target_mm':mm(cam.target),'up':list(cam.upVector.asArray())}
app.activeViewport.saveAsImageFile(str(OUT/'selection_2_request_view.png'),1600,1200)
(OUT/'selection_2_inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
