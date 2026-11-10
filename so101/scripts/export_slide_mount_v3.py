import adsk.core
import adsk.fusion
import math
import os
import json

source_doc=app.activeDocument
d=adsk.fusion.Design.cast(app.activeProduct)
r=d.rootComponent
out='/Users/sugawaraichirou/Documents/ChatGPT/so101/output/v3'
with open(out+'/verification.json') as f: verification=json.load(f)
assert verification['passed'] and d.userParameters.itemByName('brush_dia').expression=='15 mm'
parts=[('01_slide_in_base',r.occurrences.itemByName('部品１:1')),
       ('02_threaded_load_carrier',r.occurrences.itemByName('Brush_Load_Carrier:1')),
       ('03_brush_cartridge_15mm',r.occurrences.itemByName('Brush_Cartridge_15mm:1')),
       ('04_slide_in_top_cover',r.occurrences.itemByName('SC616C_Slide_In_Top_Cover:1'))]
for label,o in parts:
    assert abs(o.bRepBodies.item(0).volume*1000-verification['part_volumes_mm3'][o.name])<1e-4,('design changed since verification',label)
assert source_doc.save('Modeled M3 female threads, slide-in SC616C fixed-half top retention with sensing clearance')
manager=d.exportManager
assert manager.execute(manager.createFusionArchiveExportOptions(out+'/so101_calligraphy_v3_linked.f3d'))
archives=[]
for label,o in parts:
    assert manager.execute(manager.createSTEPExportOptions(out+'/'+label+'.step',o.component))
    path=out+'/'+label+'_editable.f3d'
    returned=manager.execute(manager.createFusionArchiveExportOptions(path,o.component))
    assert os.path.getsize(path)>1000
    archives.append({'part':label,'path':path,'reported':returned,'bytes':os.path.getsize(path)})
exports=[]
tmp=adsk.fusion.TemporaryBRepManager.get()
for index,(label,o) in enumerate(parts):
    body=tmp.copy(o.bRepBodies.item(0))
    angle={0:math.pi/2,3:math.pi}.get(index,0)
    if angle:
        rot=adsk.core.Matrix3D.create()
        rot.setToRotation(angle,adsk.core.Vector3D.create(1,0,0),adsk.core.Point3D.create(0,0,0))
        assert tmp.transform(body,rot)
    b=body.boundingBox
    translate=adsk.core.Matrix3D.create()
    translate.translation=adsk.core.Vector3D.create(-b.minPoint.x,-b.minPoint.y,-b.minPoint.z)
    assert tmp.transform(body,translate)
    print_doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    try:
        pd=adsk.fusion.Design.cast(app.activeProduct)
        pd.designType=adsk.fusion.DesignTypes.DirectDesignType
        solid=pd.rootComponent.bRepBodies.add(body); solid.name=label
        stl=pd.exportManager.createSTLExportOptions(solid,out+'/'+label+'.stl')
        stl.meshRefinement=adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        assert pd.exportManager.execute(stl)
        bb=solid.boundingBox
        exports.append({'part':label,'size_mm':[(hi-lo)*10 for lo,hi in zip(bb.minPoint.asArray(),bb.maxPoint.asArray())],
                        'min_mm':[v*10 for v in bb.minPoint.asArray()],'volume_mm3':solid.volume*1000,
                        'print_rotation_about_X_degrees':angle*180/math.pi})
    finally:
        assert print_doc.close(False)
        source_doc.activate()
source_doc.activate()
camera=app.activeViewport.camera
camera.viewOrientation=adsk.core.ViewOrientations.IsoTopRightViewOrientation
camera.isFitView=True
app.activeViewport.camera=camera
app.activeViewport.refresh()
report={'fusion_saved':not source_doc.isModified,'cloud_version':source_doc.dataFile.versionNumber,
        'parts':exports,'editable_archives':archives}
with open(out+'/export_report.json','w') as f: json.dump(report,f,indent=2)
print(json.dumps(report,indent=2))
