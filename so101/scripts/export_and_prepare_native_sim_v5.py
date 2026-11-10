import adsk.core
import adsk.fusion
import json
import os

root='/Users/sugawaraichirou/Documents/ChatGPT/so101'; out=root+'/output/v5'; analysis=out+'/analysis'
os.makedirs(analysis,exist_ok=True)
with open(out+'/verification.json',encoding='utf-8') as f: checked=json.load(f)
with open(out+'/created.json',encoding='utf-8') as f: made=json.load(f)
assert checked['passed']
doc=app.activeDocument; d=adsk.fusion.Design.cast(app.activeProduct); r=d.rootComponent
assert doc.name=='so101書道'
parts={k:r.occurrences.itemByName(n) for k,n in made['parts'].items()}
assert d.timeline.count-d.timeline.markerPosition==31
assert doc.save('V5: outboard rotary-clearance yoke, short paired carrier, symmetric removable sleeve, centered translated SC616C')
folder=doc.dataFile.parentFolder
t=adsk.fusion.TemporaryBRepManager.get()
stems={'base':'01_yoke_rotary_clearance_V5','carrier':'02_compact_load_carrier_V5',
       'cartridge':'03_symmetric_brush_cartridge_15mm_V5','wrist':'04_wrist_roll_clearance_V5'}
exports=[]
for label,o in parts.items():
    stem=stems[label]
    assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(out+'/'+stem+'.step',o.component))
    path=out+'/'+stem+'_editable.f3d'
    returned=d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(path,o.component))
    assert os.path.getsize(path)>1000
    body=t.copy(o.bRepBodies.item(0)); bb=body.boundingBox
    m=adsk.core.Matrix3D.create(); m.translation=adsk.core.Vector3D.create(-bb.minPoint.x,-bb.minPoint.y,-bb.minPoint.z)
    assert t.transform(body,m)
    temp_doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    try:
        td=adsk.fusion.Design.cast(app.activeProduct); td.designType=adsk.fusion.DesignTypes.DirectDesignType
        b=td.rootComponent.bRepBodies.add(body); b.name=stem
        stl=td.exportManager.createSTLExportOptions(b,out+'/'+stem+'.stl')
        stl.meshRefinement=adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        assert td.exportManager.execute(stl)
        exports.append({'part':label,'stem':stem,'min_mm':[v*10 for v in b.boundingBox.minPoint.asArray()],
                        'size_mm':[(b-a)*10 for a,b in zip(b.boundingBox.minPoint.asArray(),b.boundingBox.maxPoint.asArray())],
                        'volume_mm3':b.volume*1000,'archive_reported':returned})
    finally:
        temp_doc.close(False); doc.activate()
assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(out+'/so101_V5_linked_assembly_backup.f3d'))
cam=app.activeViewport.camera; cam.viewOrientation=adsk.core.ViewOrientations.IsoTopRightViewOrientation; cam.isFitView=True
app.activeViewport.camera=cam; app.activeViewport.refresh()
assert app.activeViewport.saveAsImageFile(out+'/assembly.png',1600,1200)

sensor=next(o.bRepBodies.item(0) for o in r.allOccurrences if o.fullPathName.startswith('SC616C_1kg_Fusion:1+') and o.bRepBodies.count)
sources={k:t.copy(parts[k].bRepBodies.item(0)) for k in ('base','carrier','cartridge')}
sources['sensor']=t.copy(sensor)
simdoc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
sd=adsk.fusion.Design.cast(app.activeProduct); sd.designType=adsk.fusion.DesignTypes.DirectDesignType
lib=app.materialLibraries.itemById('C1EEA57C-3F56-45FC-B8CB-A9EC46A9994C')
plastic=sd.materials.addByCopy(lib.materials.itemById('PrismMaterial-022'),'PRINT_ASSUMED_E1500MPa_ISOTROPIC_NOT_TESTED')
al=sd.materials.addByCopy(lib.materials.itemById('PrismMaterial-002'),'SC616C_APPROX_Al_E69000MPa_ALLOY_UNKNOWN')
def assign_values(material,young_kpa,nu,density,yield_kpa,tensile_kpa):
    for p in material.materialProperties:
        if p.objectType!='adsk::core::FloatProperty': continue
        if p.id.startswith('structural_Young_modulus'): p.value=young_kpa
        elif p.id.startswith('structural_Poisson_ratio'): p.value=nu
        elif p.id.startswith('structural_Shear_modulus'): p.value=young_kpa/(2*(1+nu))
        elif p.id in ('structural_Density','thermal_Density'): p.value=density
        elif p.id=='structural_Minimum_yield_stress': p.value=yield_kpa
        elif p.id=='structural_Minimum_tensile_strength': p.value=tensile_kpa
assign_values(plastic,1500000,.35,1240,20000,25000)
assign_values(al,69000000,.33,2700,55000,90000)
materials=[]
for material in (plastic,al):
    materials.append({'name':material.name,'properties':{p.id:{'value':p.value,'units':p.units} for p in material.materialProperties
                    if p.objectType=='adsk::core::FloatProperty' and p.id in
                    ('structural_Young_modulus','structural_Poisson_ratio','structural_Density','structural_Minimum_yield_stress')}})
for label,b in sources.items():
    o=sd.rootComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create()); o.component.name=label
    body=o.component.bRepBodies.add(b); body.name=label
    body.material=al if label=='sensor' else plastic
    assert sd.exportManager.execute(sd.exportManager.createSTEPExportOptions(analysis+'/'+label+'.step',o.component))
assert simdoc.saveAs('so101_V5_筆圧検証_理想接触',folder,'','Native Fusion static stress; approximate isotropic print properties; not electrical bridge or print strength certification')
audit={'brush_axis_mm':made['brush_axis_mm'],'brush_stop_z_mm':30.5,'assumed_brush_tip_z_mm':-52,
       'bore_load_z_min_mm':10.5,'bore_load_z_max_mm':28.5,'source_geometry_preserved':True,
       'source':'V5 verified final geometry; native Fusion analysis copy',
       'sensor_model_note':'Approximate aluminium solid with no gauges, bridge, resin, cable, slip or bolt preload',
       'parts':{k:{'volume_mm3':b.volume*1000} for k,b in sources.items()},'materials':materials}
with open(analysis+'/geometry_audit.json','w',encoding='utf-8') as f: json.dump(audit,f,ensure_ascii=False,indent=2)
report={'fusion_saved':not doc.isModified,'main_cloud_version':doc.dataFile.versionNumber,'exports':exports,
        'native_simulation_document':simdoc.name,'materials':materials,'native_simulation_solved':False}
with open(out+'/export_report.json','w',encoding='utf-8') as f: json.dump(report,f,ensure_ascii=False,indent=2)
cam=app.activeViewport.camera; cam.viewOrientation=adsk.core.ViewOrientations.IsoTopRightViewOrientation; cam.isFitView=True
app.activeViewport.camera=cam; app.activeViewport.refresh()
print(json.dumps(report,ensure_ascii=False,indent=2))
