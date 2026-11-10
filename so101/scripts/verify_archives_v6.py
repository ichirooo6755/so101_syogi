import adsk.core
import adsk.fusion
import json

root='/Users/sugawaraichirou/Documents/ChatGPT/so101'; out=root+'/output/v6'
with open(out+'/export_report.json',encoding='utf-8') as f: exported=json.load(f)
with open(out+'/verification.json',encoding='utf-8') as f: checked=json.load(f)
main=next(doc for doc in app.documents if doc.name=='so101書道'); main.activate()
assert not main.isModified
rows=[]
for part in exported['exports']:
    path=out+'/'+part['stem']+'_editable.f3d'
    doc=app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(path))
    assert doc
    try:
        d=adsk.fusion.Design.cast(app.activeProduct)
        bodies=list(d.rootComponent.bRepBodies)+[b for o in d.rootComponent.allOccurrences for b in o.bRepBodies]
        solids=[b for b in bodies if b.isSolid and b.volume>1e-6]
        assert len(solids)==1,(part['part'],len(solids))
        assert abs(solids[0].volume*1000-part['volume_mm3'])<1e-4
        if part['part']=='cartridge':
            assert abs(d.userParameters.itemByName('brush_dia').value*10-15)<1e-6
        rows.append({'part':part['part'],'reopened':True,'main_solid_volume_mm3':solids[0].volume*1000,
                     'total_body_count':len(bodies),'editable_timeline_count':d.timeline.count})
    finally:
        doc.close(False); main.activate()
linked_archive_error=None
try:
    doc=app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(out+'/so101_V6_assembly_backup.f3d'))
except RuntimeError as e:
    assert 'external references' in str(e)
    linked_archive_error=str(e)
    doc=None
if doc:
    d=adsk.fusion.Design.cast(app.activeProduct); r=d.rootComponent
    assert d.timeline.count-d.timeline.markerPosition==31
    for label,name in checked['parts'].items():
        o=r.occurrences.itemByName(name); assert o and o.isVisible
        assert abs(max(b.volume*1000 for b in o.bRepBodies)-checked['volumes_mm3'][label])<1e-4
    assert not r.occurrences.itemByName('部品１_V5可動域改善:1').isVisible
    assert abs(d.userParameters.itemByName('brush_dia').value*10-15)<1e-6
    assembly={'local_archive_reopened':True,'future_features':31,'part_names_and_volumes_match':True}
    doc.close(False); main.activate()
else:
    file=main.dataFile
    assert not main.isModified
    main.close(False)
    main=app.documents.open(file)
    assert main and main.name=='so101書道'
    d=adsk.fusion.Design.cast(main.products.itemByProductType('DesignProductType')); r=d.rootComponent
    assert d.timeline.count-d.timeline.markerPosition==31
    for label,name in checked['parts'].items():
        o=r.occurrences.itemByName(name); assert o and o.isVisible
        assert abs(max(b.volume*1000 for b in o.bRepBodies)-checked['volumes_mm3'][label])<1e-4
    assembly={'local_archive_reopened':False,'local_archive_contains_external_references':True,
              'local_archive_limitation':linked_archive_error,'cloud_design_reopened':True,
              'future_features':31,'part_names_and_volumes_match':True}
report={'standalone':rows,'assembly':assembly,'original_still_saved':not main.isModified}
with open(out+'/archive_verification.json','w',encoding='utf-8') as f: json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps(report,ensure_ascii=False,indent=2))
