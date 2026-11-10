import adsk.core
import adsk.fusion
import json
import os

root='/Users/sugawaraichirou/Documents/ChatGPT/so101'; out=root+'/output/v4'
with open(out+'/verification.json',encoding='utf-8') as f: checked=json.load(f)
assert checked['passed']
doc=app.activeDocument; d=adsk.fusion.Design.cast(app.activeProduct); r=d.rootComponent
parts=[('01_centered_load_carrier',r.occurrences.itemByName('Brush_Load_Carrier_Centered:1')),
       ('02_centered_brush_cartridge_15mm',r.occurrences.itemByName('Brush_Cartridge_Centered_15mm:1'))]
cell=r.occurrences.itemByName('SC616C_1kg_Fusion:1')
pose=list(cell.transform2.asArray())
# Verify that changing brush diameter still changes the inside, not the common
# 22 mm interchangeable exterior. All measurements are restored before saving.
p=d.userParameters.itemByName('brush_dia'); expression=p.expression
sweep=[]
try:
    for dia in (12,17):
        p.expression=f'{dia} mm'; d.computeAll()
        b=parts[1][1].bRepBodies.item(0)
        diameters=[f.geometry.radius*20 for f in b.faces if isinstance(f.geometry,adsk.core.Cylinder)]
        assert any(abs(v-dia-1)<1e-5 for v in diameters)
        assert sum(abs(v-dia-.4)<1e-5 for v in diameters)==2
        assert any(abs(v-22)<1e-5 for v in diameters)
        assert int(parts[1][1].component.features.extrudeFeatures.itemByName('V4_parameterized_blind_bore').healthState)==0
        sweep.append(dia)
finally:
    p.expression=expression; d.computeAll()
assert expression=='15 mm'
assert max(abs(a-b) for a,b in zip(cell.transform2.asArray(),pose))<1e-9
for label,o in parts: assert abs(o.bRepBodies.item(0).volume*1000-checked['part_volumes_mm3'][o.name])<1e-4
checked['brush_diameter_parameter_test_mm']=sweep
with open(out+'/verification.json','w',encoding='utf-8') as f: json.dump(checked,f,ensure_ascii=False,indent=2)
assert doc.save('V4 centered brush load path: 20 mm eccentricity removed, captive M3 nuts retained, base and sensor pose unchanged')
archives=[]
for label,o in parts:
    assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(out+'/'+label+'.step',o.component))
    path=out+'/'+label+'_editable.f3d'
    returned=d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(path,o.component))
    assert os.path.getsize(path)>1000
    archives.append({'part':label,'path':path,'reported':returned,'bytes':os.path.getsize(path)})
assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(out+'/so101_centered_v4_linked_backup.f3d'))
tmp=adsk.fusion.TemporaryBRepManager.get()
exports=[]
for label,o in parts:
    body=tmp.copy(o.bRepBodies.item(0)); bb=body.boundingBox
    m=adsk.core.Matrix3D.create(); m.translation=adsk.core.Vector3D.create(-bb.minPoint.x,-bb.minPoint.y,-bb.minPoint.z)
    assert tmp.transform(body,m)
    temp_doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    try:
        td=adsk.fusion.Design.cast(app.activeProduct); td.designType=adsk.fusion.DesignTypes.DirectDesignType
        solid=td.rootComponent.bRepBodies.add(body); solid.name=label
        stl=td.exportManager.createSTLExportOptions(solid,out+'/'+label+'.stl')
        stl.meshRefinement=adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        assert td.exportManager.execute(stl)
        bb=solid.boundingBox
        exports.append({'part':label,'size_mm':[(b-a)*10 for a,b in zip(bb.minPoint.asArray(),bb.maxPoint.asArray())],
                        'min_mm':[v*10 for v in bb.minPoint.asArray()],'volume_mm3':solid.volume*1000})
    finally:
        temp_doc.close(False); doc.activate()
# Freeze the exact world-space solids for a short mechanical comparison FEA.
analysis=out+'/analysis'; os.makedirs(analysis,exist_ok=True)
sensor=next(o.bRepBodies.item(0) for o in r.allOccurrences if o.fullPathName.startswith(cell.name+'+') and o.bRepBodies.count)
source={'base':r.occurrences.itemByName('部品１:1').bRepBodies.item(0),
        'carrier':parts[0][1].bRepBodies.item(0),'cartridge':parts[1][1].bRepBodies.item(0),'sensor':sensor}
copies={label:tmp.copy(b) for label,b in source.items()}
temp_doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
try:
    td=adsk.fusion.Design.cast(app.activeProduct); td.designType=adsk.fusion.DesignTypes.DirectDesignType
    for label,b in copies.items():
        o=td.rootComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create()); o.component.name=label
        o.component.bRepBodies.add(b).name=label
        assert td.exportManager.execute(td.exportManager.createSTEPExportOptions(analysis+'/'+label+'.step',o.component))
finally:
    temp_doc.close(False); doc.activate()
audit={'brush_axis_mm':checked['brush_axis_mm'],'brush_stop_z_mm':7.5,'assumed_brush_tip_z_mm':-75.,
       'bore_load_z_min_mm':-24.5,'bore_load_z_max_mm':5.5,
       'source_geometry_preserved':True,'source':'V4 centered replacement after parameter roundtrip',
       'load_path_note':'Axial load on the closed brush stop; lateral loads on the ideally bonded hot-glue bore',
       'sensor_model_note':'Existing approximate sensor; unknown actual gauge and bridge; no electrical accuracy prediction',
       'parts':{label:{'volume_mm3':b.volume*1000} for label,b in source.items()}}
with open(analysis+'/geometry_audit.json','w',encoding='utf-8') as f: json.dump(audit,f,indent=2)
report={'fusion_saved':not doc.isModified,'cloud_version':doc.dataFile.versionNumber,'parts':exports,'editable_archives':archives,
        'brush_diameter_parameter_test_mm':sweep,'new_vs_old_cartridge_frame_shift_mm':[-20,0,-35]}
with open(out+'/export_report.json','w',encoding='utf-8') as f: json.dump(report,f,indent=2)
cam=app.activeViewport.camera; cam.viewOrientation=adsk.core.ViewOrientations.IsoTopRightViewOrientation; cam.isFitView=True
app.activeViewport.camera=cam; app.activeViewport.refresh()
print(json.dumps(report,indent=2))
