"""Check the restored mount in the current assembly, snapshot final four parts.

Main geometry/placements/wrist remain untouched. Native analysis copy carries
the user's current steel material; local solver also evaluates PDF aluminum.
"""
import adsk
import adsk.core
import adsk.fusion
import json
import os
import runpy

root='/Users/sugawaraichirou/Documents/ChatGPT/so101'; out=root+'/output/v8'
assert ui.activeCommand=='SelectCommand'
active=app.activeDocument
if active.name.startswith('so101_V8_元取付部保持_ジェネレーティブ'):
    assert active.save('V8 original mounting details preserved. Polymer E1500MPa assumption; 6N plus equivalent socket bending; additive 3mm; 11-credit generation not submitted.')
result=runpy.run_path(root+'/scripts/verify_v7_clearance.py',init_globals={
    'app':app,'ui':ui,'candidate_name':'部品１_V8_元取付形状保持','report_version':'v8',
    'wrist_candidate_doc':'Wrist_Roll_Clearance_V8_元取付対応'})
adsk.doEvents()
main=result['main']; md=result['d']; r=md.rootComponent; t=result['t']; cy=result['cy']
sources=result['bodies']
path=out+'/four_part'; os.makedirs(path,exist_ok=True)
doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
d=adsk.fusion.Design.cast(app.activeProduct); d.designType=adsk.fusion.DesignTypes.DirectDesignType
lib=app.materialLibraries.itemById('C1EEA57C-3F56-45FC-B8CB-A9EC46A9994C')
plastic=d.materials.addByCopy(lib.materials.itemById('PrismMaterial-022'),'PRINT_ASSUMED_E1500MPa_ISOTROPIC_NOT_TESTED')
for p in plastic.materialProperties:
    if p.objectType!='adsk::core::FloatProperty': continue
    if p.id.startswith('structural_Young_modulus'): p.value=1500000
    elif p.id.startswith('structural_Poisson_ratio'): p.value=.35
    elif p.id.startswith('structural_Shear_modulus'): p.value=1500000/2.7
    elif p.id in ('structural_Density','thermal_Density'): p.value=1240
    elif p.id=='structural_Minimum_yield_stress': p.value=20000
    elif p.id=='structural_Minimum_tensile_strength': p.value=25000
sensor_original=next(o.bRepBodies.item(0) for o in r.allOccurrences
    if o.fullPathName.startswith('SC616C_1kg_Fusion:1+') and o.bRepBodies.count)
steel=d.materials.addByCopy(sensor_original.material,'USER_SELECTED_'+sensor_original.material.name)
print('USER_SENSOR_MATERIAL',sensor_original.material.name)
for k,b in sources.items():
    o=d.rootComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create()); o.component.name=k
    body=o.component.bRepBodies.add(t.copy(b)); body.name=k
    body.material=steel if k=='sensor' else plastic
    assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(path+'/'+k+'.step',o.component))
audit={'brush_axis_mm':[62,cy],'brush_stop_z_mm':30.5,'assumed_brush_tip_z_mm':-52,
    'bore_load_z_min_mm':10.5,'bore_load_z_max_mm':28.5,'base_included':True,
    'base_clamp_faces_y_mm':[-17.05,20.2],
    'source':'Final V8 actual BRep: original diagonal servo interfaces restored; M3 shank holes verified open',
    'sensor_native_material':sensor_original.material.name,
    'sensor_PDF_material':'Aluminum alloy; compare separately, do not silently overwrite user selection',
    'parts':{k:{'volume_mm3':b.volume*1000} for k,b in sources.items()}}
with open(path+'/geometry_audit.json','w',encoding='utf-8') as f: json.dump(audit,f,ensure_ascii=False,indent=2)
assert doc.saveAs('so101_V8_元取付部保持_筆圧検証',main.dataFile.parentFolder,'',
    'Final V8 four-part native analysis copy; user steel loadcell material. Main wrist and assembly unchanged.')
with open(out+'/original_mount_restoration.json',encoding='utf-8') as f: report=json.load(f)
report['original_mount_reference_confirmation_pending']=False
report['user_confirmed_reference']='First original 部品１ inner diagonal four-hole and mating design, confirmed 2026-10-22'
with open(out+'/original_mount_restoration.json','w',encoding='utf-8') as f: json.dump(report,f,ensure_ascii=False,indent=2)
print('SNAPSHOT_SAVED',doc.name,{k:round(b.volume*1000,4) for k,b in sources.items()})
print('MAIN_UNEDITED',md.timeline.markerPosition,md.timeline.count)
