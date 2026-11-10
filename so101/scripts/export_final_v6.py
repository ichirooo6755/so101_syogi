import adsk.core
import adsk.fusion
import json
import os

root='/Users/sugawaraichirou/Documents/ChatGPT/so101'; out=root+'/output/v6'
with open(out+'/verification.json',encoding='utf-8') as f: checked=json.load(f)
assert checked['passed']
assert ui.activeCommand=='SelectCommand'
main=next(doc for doc in app.documents if doc.name=='so101書道'); main.activate()
d=adsk.fusion.Design.cast(main.products.itemByProductType('DesignProductType')); r=d.rootComponent
assert d.timeline.count-d.timeline.markerPosition==31
t=adsk.fusion.TemporaryBRepManager.get()
stems={'base':'01_yoke_short_stiff_V6','carrier':'02_compact_load_carrier_V6',
       'cartridge':'03_symmetric_brush_cartridge_15mm_V6','wrist':'04_user_wrist_roll_clearance_V5'}
exports=[]
for label,name in checked['parts'].items():
    o=r.occurrences.itemByName(name); stem=stems[label]
    if label!='base':
        path=out+'/'+stem+'_editable.f3d'
        returned=d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(path,o.component))
        assert os.path.getsize(path)>1000,(label,'native editable archive')
    b=t.copy(max(o.bRepBodies,key=lambda body:body.volume)); bb=b.boundingBox
    m=adsk.core.Matrix3D.create(); m.translation=adsk.core.Vector3D.create(-bb.minPoint.x,-bb.minPoint.y,-bb.minPoint.z)
    assert t.transform(b,m)
    tmp=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    try:
        td=adsk.fusion.Design.cast(app.activeProduct); td.designType=adsk.fusion.DesignTypes.DirectDesignType
        po=td.rootComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create()); po.component.name=stem
        body=po.component.bRepBodies.add(b); body.name=stem
        step=out+'/'+stem+'.step'
        assert td.exportManager.execute(td.exportManager.createSTEPExportOptions(step,po.component))
        assert os.path.getsize(step)>1000
        options=td.exportManager.createSTLExportOptions(body,out+'/'+stem+'.stl')
        options.meshRefinement=adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        assert td.exportManager.execute(options)
        exports.append({'part':label,'stem':stem,'volume_mm3':body.volume*1000,
                        'size_mm':[(b-a)*10 for a,b in zip(body.boundingBox.minPoint.asArray(),body.boundingBox.maxPoint.asArray())],
                        'printed_body_count':1,'original_CAD_body_count':o.bRepBodies.count,
                        'omitted_fragment_mm3':sum(x.volume*1000 for x in o.bRepBodies)-body.volume*1000})
    finally:
        tmp.close(False); main.activate()
assert not main.isModified
path=out+'/so101_V6_assembly_backup.f3d'
returned=d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(path))
assert os.path.getsize(path)>100000
cam=app.activeViewport.camera; cam.viewOrientation=adsk.core.ViewOrientations.IsoTopRightViewOrientation; cam.isFitView=True
app.activeViewport.camera=cam; app.activeViewport.refresh()
assert app.activeViewport.saveAsImageFile(out+'/assembly.png',1600,1200)
report={'main_cloud_version':main.dataFile.versionNumber,'main_saved':not main.isModified,
        'exports':exports,'future_features':31,'assembly_archive_reported':returned,
        'user_wrist_CAD_all_bodies_preserved':True,'print_orientation_not_yet_tested':True}
with open(out+'/export_report.json','w',encoding='utf-8') as f: json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps(report,ensure_ascii=False,indent=2))
