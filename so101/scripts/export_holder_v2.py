import adsk.core
import adsk.fusion
import math
import os
import json
source_doc=app.activeDocument
d=adsk.fusion.Design.cast(app.activeProduct)
r=d.rootComponent
out='/Users/sugawaraichirou/Documents/ChatGPT/so101/output/v2'
with open(out+'/verification.json') as f: verification=json.load(f)
assert verification['passed'] and d.userParameters.itemByName('brush_dia').expression=='15 mm'
parts=[('01_reinforced_base',r.occurrences.itemByName('部品１:1')),
       ('02_load_carrier',r.occurrences.itemByName('Brush_Load_Carrier:1')),
       ('03_brush_cartridge_15mm',r.occurrences.itemByName('Brush_Cartridge_15mm:1'))]
assert source_doc.save('FDM reinforced SC616C base, checked M3 hardware, removable hot-glued brush cartridge')
manager=d.exportManager
assert manager.execute(manager.createFusionArchiveExportOptions(out+'/so101_calligraphy_v2_linked.f3d'))
exports=[]
for label,o in parts:
    assert manager.execute(manager.createSTEPExportOptions(out+'/'+label+'.step',o.component))
cartridge_archive=out+'/03_brush_cartridge_editable.f3d'
reported=manager.execute(manager.createFusionArchiveExportOptions(cartridge_archive,parts[2][1].component))
print('cartridge component export reported',reported,'bytes',os.path.getsize(cartridge_archive))
tmp=adsk.fusion.TemporaryBRepManager.get()
for index,(label,o) in enumerate(parts):
    body=tmp.copy(o.bRepBodies.item(0))
    if index==0:
        rot=adsk.core.Matrix3D.create()
        rot.setToRotation(math.pi/2,adsk.core.Vector3D.create(1,0,0),adsk.core.Point3D.create(0,0,0))
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
                        'min_mm':[v*10 for v in bb.minPoint.asArray()],'volume_mm3':solid.volume*1000})
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
        'parts':exports,'cartridge_export_returned':reported,'cartridge_archive':cartridge_archive}
with open(out+'/export_report.json','w') as f: json.dump(report,f,indent=2)
print(json.dumps(report,indent=2))
