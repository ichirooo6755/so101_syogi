import adsk.core
import adsk.fusion
import json
out='/Users/sugawaraichirou/Documents/ChatGPT/so101/output/v2'
with open(out+'/verification.json') as f: expected=json.load(f)
doc=app.activeDocument
d=adsk.fusion.Design.cast(app.activeProduct)
assert doc.name=='so101書道' and not doc.isModified
for name,volume in expected['part_volumes_mm3'].items():
    o=d.rootComponent.occurrences.itemByName(name)
    assert o and o.component.bRepBodies.count==1
    assert abs(o.bRepBodies.item(0).volume*1000-volume)<1e-4,(name,volume)
near=abs(d.userParameters.itemByName('brush_dia').value*10-15)<1e-6
assert near
cloud_version=doc.dataFile.versionNumber
archive=app.importManager.createFusionArchiveImportOptions(out+'/03_brush_cartridge_editable.f3d')
copy=app.importManager.importToNewDocument(archive)
try:
    cd=adsk.fusion.Design.cast(app.activeProduct)
    candidates=list(cd.rootComponent.bRepBodies)+[b for o in cd.rootComponent.allOccurrences for b in o.bRepBodies]
    solids=[b for b in candidates if b.isSolid and b.volume>1e-6]
    assert len(solids)==1
    assert abs(solids[0].volume*1000-expected['part_volumes_mm3']['Brush_Cartridge_15mm:1'])<1e-4
    assert abs(cd.userParameters.itemByName('brush_dia').value*10-15)<1e-5
    assert abs(cd.userParameters.itemByName('brush_cartridge_od').value*10-22)<1e-5
    print('Standalone editable cartridge opened and matches the final solid and brush parameters')
finally:
    assert copy.close(False)
    doc.activate()
with open(out+'/export_report.json') as f: export=json.load(f)
export.update(cloud_version=cloud_version,saved_assembly_reopened_and_verified=True,standalone_cartridge_reopened_and_verified=True)
with open(out+'/export_report.json','w') as f: json.dump(export,f,indent=2)
cam=app.activeViewport.camera; cam.viewOrientation=adsk.core.ViewOrientations.IsoTopRightViewOrientation; cam.isFitView=True
app.activeViewport.camera=cam; app.activeViewport.refresh()
print('Original assembly verified after reopen, cloud version',cloud_version,'modified',doc.isModified)
