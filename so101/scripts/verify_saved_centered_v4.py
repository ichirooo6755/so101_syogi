import adsk.core
import adsk.fusion
import json

root='/Users/sugawaraichirou/Documents/ChatGPT/so101'; out=root+'/output/v4'
with open(out+'/verification.json',encoding='utf-8') as f: expected=json.load(f)
with open(out+'/export_report.json',encoding='utf-8') as f: exported=json.load(f)
doc=app.activeDocument; d=adsk.fusion.Design.cast(app.activeProduct); r=d.rootComponent
assert doc.name=='so101書道' and not doc.isModified
for name,volume in expected['part_volumes_mm3'].items():
    o=r.occurrences.itemByName(name)
    assert o and o.isVisible and o.component.bRepBodies.count==1
    assert abs(o.bRepBodies.item(0).volume*1000-volume)<1e-4,name
assert not r.occurrences.itemByName('Brush_Load_Carrier:1').isVisible
assert not r.occurrences.itemByName('Brush_Cartridge_15mm:1').isVisible
assert abs(d.userParameters.itemByName('brush_dia').value*10-15)<1e-6
assert abs(d.userParameters.itemByName('centered_brush_axis_x').value*10-30)<1e-6
for record in exported['editable_archives']:
    options=app.importManager.createFusionArchiveImportOptions(record['path'])
    copy=app.importManager.importToNewDocument(options)
    try:
        cd=adsk.fusion.Design.cast(app.activeProduct)
        solids=list(cd.rootComponent.bRepBodies)+[b for o in cd.rootComponent.allOccurrences for b in o.bRepBodies]
        solids=[b for b in solids if b.isSolid and b.volume>1e-6]
        assert len(solids)==1,(record['part'],len(solids))
        volume=next(p['volume_mm3'] for p in exported['parts'] if p['part']==record['part'])
        assert abs(solids[0].volume*1000-volume)<1e-4
        if 'cartridge' in record['part']:
            assert abs(cd.userParameters.itemByName('brush_dia').value*10-15)<1e-6
        record['standalone_reopened_and_verified']=True
    finally:
        assert copy.close(False); doc.activate()
exported['cloud_version']=doc.dataFile.versionNumber
exported['saved_assembly_reopened_and_verified']=True
exported['fusion_saved']=not doc.isModified
with open(out+'/export_report.json','w',encoding='utf-8') as f: json.dump(exported,f,indent=2)
cam=app.activeViewport.camera; cam.viewOrientation=adsk.core.ViewOrientations.IsoTopRightViewOrientation; cam.isFitView=True
app.activeViewport.camera=cam; app.activeViewport.refresh()
assert app.activeViewport.saveAsImageFile(out+'/assembly.png',1600,1200)
print('Saved centered assembly and both standalone editable parts verified, cloud version',exported['cloud_version'],'modified',doc.isModified)
