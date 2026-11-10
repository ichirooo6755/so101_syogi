import adsk.core
import adsk.fusion
import json
import os

root='/Users/sugawaraichirou/Documents/ChatGPT/so101'; out=root+'/output/v6'
assert ui.activeCommand=='SelectCommand'
main=next(doc for doc in app.documents if doc.name=='so101書道'); main.activate()
d=adsk.fusion.Design.cast(main.products.itemByProductType('DesignProductType'))
t=adsk.fusion.TemporaryBRepManager.get()
sources=[]
for o in d.rootComponent.allOccurrences:
    if not o.isVisible: continue
    bodies=[t.copy(b) for b in o.bRepBodies if b.isSolid and b.isVisible and b.volume>1e-6]
    if bodies: sources.append((o.fullPathName,bodies))
assert len(sources)>=5
doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
try:
    td=adsk.fusion.Design.cast(app.activeProduct); td.designType=adsk.fusion.DesignTypes.DirectDesignType
    for name,bodies in sources:
        o=td.rootComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create()); o.component.name=name.replace(':','_')
        for source in bodies: o.component.bRepBodies.add(source)
    archive=out+'/so101_V6_offline_geometry_assembly.f3d'
    assert td.exportManager.execute(td.exportManager.createFusionArchiveExportOptions(archive))
    assert td.exportManager.execute(td.exportManager.createSTEPExportOptions(out+'/so101_V6_visible_assembly.step'))
    expected=sum(b.volume*1000 for _,bb in sources for b in bb)
finally:
    doc.close(False); main.activate()
copy=app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(archive))
assert copy
try:
    cd=adsk.fusion.Design.cast(app.activeProduct)
    bodies=[b for o in cd.rootComponent.allOccurrences for b in o.bRepBodies]
    assert abs(sum(b.volume*1000 for b in bodies)-expected)<1e-3
    report={'independent_offline_archive_reopened':True,'external_references':False,
            'visible_component_count':len(sources),'solid_body_count':len(bodies),
            'volume_sum_mm3':expected,'full_parametric_history':False,
            'note':'World-position solid snapshot only. Main cloud design and separate editable part archives retain history.'}
finally:
    copy.close(False); main.activate()
with open(out+'/offline_assembly_verification.json','w',encoding='utf-8') as f: json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps(report,ensure_ascii=False,indent=2))
