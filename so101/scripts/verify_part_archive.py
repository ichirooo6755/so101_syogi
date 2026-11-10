import adsk.core
import adsk.fusion
import json
doc=app.activeDocument
assert doc.name=='Untitled'
d=adsk.fusion.Design.cast(app.activeProduct)
components=[d.rootComponent]+[o.component for o in d.rootComponent.allOccurrences]
bodies=[b for c in components for b in c.bRepBodies if b.isSolid and b.volume>1e-6]
assert len(bodies)==1
b=bodies[0]
expected=12562.820785034331
assert abs(b.volume*1000-expected)<0.001
holes=[]
for f in b.faces:
    g=f.geometry
    if isinstance(g,adsk.core.Cylinder) and abs(g.radius*10-1.7)<1e-5:
        holes.append(g.origin)
assert len(holes)==2
assert abs(holes[0].distanceTo(holes[1])*10-7.4)<1e-5
p=d.userParameters.itemByName('brush_dia')
if p is None:
    p=d.userParameters.add('brush_dia',adsk.core.ValueInput.createByString('15 mm'),'mm','Nominal brush diameter for the next-stage removable holder')
assert abs(p.value*10-15)<1e-5
path='/Users/sugawaraichirou/Documents/ChatGPT/so101/output/so101_sc616c_mount_editable.f3d'
assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(path))
report={'part_archive_reopened':True,'solid_count':len(bodies),
        'volume_mm3':b.volume*1000,'mount_hole_count':len(holes),
        'pitch_mm':holes[0].distanceTo(holes[1])*10,
        'brush_dia_mm':p.value*10,'editable_archive':path}
with open('/Users/sugawaraichirou/Documents/ChatGPT/so101/output/part_archive_verification.json','w') as f:
    json.dump(report,f,indent=2)
print(json.dumps(report,indent=2))
assert doc.close(False)
original=next(app.documents.item(i) for i in range(app.documents.count) if app.documents.item(i).name=='so101書道')
original.activate()
print('active original',app.activeDocument.name,'saved',not app.activeDocument.isModified)
