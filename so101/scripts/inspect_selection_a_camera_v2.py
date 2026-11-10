"""Read-only selection-set A and current view inventory for the revised bracket."""
import adsk.core
import adsk.fusion
import json
from pathlib import Path

out=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101/output/camera_mount_v2')
out.mkdir(parents=True,exist_ok=True)
doc=app.activeDocument
d=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
assert d,'Active document is not a Fusion design'
def coords(p): return [v*10 for v in p.asArray()]
def describe(e):
    row={'type':e.objectType}
    for attr in ('name','entityToken'):
        try: row[attr]=getattr(e,attr)
        except Exception: pass
    try:
        row['bounds_mm']=[coords(e.boundingBox.minPoint),coords(e.boundingBox.maxPoint)]
    except Exception: pass
    face=adsk.fusion.BRepFace.cast(e)
    body=adsk.fusion.BRepBody.cast(e)
    if face:
        body=face.body
        row['area_mm2']=face.area*100
        row['centroid_mm']=coords(face.centroid)
        row['surface_type']=int(face.geometry.surfaceType)
        if face.geometry.surfaceType==adsk.core.SurfaceTypes.PlaneSurfaceType:
            row['normal']=list(face.geometry.normal.asArray())
            row['plane_origin_mm']=coords(face.geometry.origin)
        row['vertices_mm']=[coords(v.geometry) for v in face.vertices]
    if body:
        row['body_name']=body.name
        row['body_volume_mm3']=body.volume*1000
        try: row['occurrence']=body.assemblyContext.fullPathName if body.assemblyContext else None
        except Exception: pass
        try: row['component']=body.parentComponent.name
        except Exception: pass
    return row
report={'document':doc.name,'modified':doc.isModified,'timeline':[d.timeline.markerPosition,d.timeline.count],
        'selection_api':{},'sets':[],'active_selection':[]}
for ownername,owner in (('design',d),('root',d.rootComponent),('document',doc)):
    report['selection_api'][ownername]=[s for s in dir(owner) if 'selection' in s.lower()]
    if hasattr(owner,'selectionSets'):
        sets=owner.selectionSets
        for s in sets:
            row={'owner':ownername,'name':s.name,'api':[a for a in dir(s) if not a.startswith('_')]}
            if hasattr(s,'entities'):
                entities=s.entities
                row['entities']=[describe(entity) for entity in entities]
            report['sets'].append(row)
for i in range(ui.activeSelections.count): report['active_selection'].append(describe(ui.activeSelections.item(i).entity))
cam=app.activeViewport.camera
direction=cam.target.vectorTo(cam.eye); direction.normalize()
left=cam.upVector.crossProduct(direction); left.normalize(); left.scaleBy(-1)
report['camera']={'eye_mm':coords(cam.eye),'target_mm':coords(cam.target),
    'up':list(cam.upVector.asArray()),'screen_left_unit':list(left.asArray()),'view_extents_cm':cam.viewExtents}
report['root_occurrences']=[{'name':o.name,'visible':o.isVisible,'transform':list(o.transform2.asArray()),
    'bodies':[{'name':b.name,'volume_mm3':b.volume*1000} for b in o.bRepBodies if b.isSolid]} for o in d.rootComponent.occurrences]
(out/'selection_a_inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
app.activeViewport.saveAsImageFile(str(out/'selection_a_current_view.png'),1600,1200)
print(json.dumps(report,ensure_ascii=False,indent=2))
