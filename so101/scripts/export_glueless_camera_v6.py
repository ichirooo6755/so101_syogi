"""Export the latest checked V6 candidate in explicit flat print orientations."""
import adsk.core
import adsk.fusion
import datetime
import hashlib
import json
import shutil
from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
helper=(ROOT/'scripts/build_camera_addon_v1.py').read_text().split("progress('building_temporary_geometry')",1)[0]
exec(compile(helper,'mm_geometry_helpers','exec'),globals())
CHECK=ROOT/'output/camera_mount_v6'; OUT=CHECK/'print_candidate'
build=json.loads((CHECK/'design_check.json').read_text())
assert json.loads((CHECK/'assembly_paths.json').read_text())['passed']
documents=[]
for doc in app.documents:
    d=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    if d and d.rootComponent.occurrences.itemByName('01_flat_carrier_socket_V6:1'):documents.append((doc,d))
document,design=documents[-1]; document.activate(); root=design.rootComponent
for sub in ('source_cad','checks','preview'):(OUT/sub).mkdir(parents=True,exist_ok=True)
lib=app.materialLibraries.itemByName('Fusion 外観ライブラリ'); source=lib.appearances.itemByName('ABS(白)')
def color(name,rgb):
    a=design.appearances.itemByName(name) or design.appearances.addByCopy(source,name)
    adsk.core.ColorProperty.cast(a.appearanceProperties.itemById('opaque_albedo')).value=adsk.core.Color.create(*rgb,255)
    return a
blue=color('V6_Print_carrier_blue',(55,145,230)); orange=color('V6_Print_common_gate_orange',(245,155,45))
cyan=color('V6_Print_camera_tray_cyan',(45,180,195)); gray=color('V6_Existing_gray',(165,170,175))
green=color('V6_HX711_one_green',(40,145,75)); purple=color('V6_Voltage_translator_purple',(165,85,195))
dark=color('V6_XIAO_Sense_dark',(55,65,70))
for o in root.occurrences:
    n=o.component.name
    a=blue if n.startswith(('01_','02_')) else orange if n.startswith('03_') else cyan if n.startswith('04_') else green if 'HX711_1pc' in n else purple if 'TXS0108E' in n else dark if 'XIAO' in n else gray
    for b in o.bRepBodies:b.appearance=a
try:app.activeViewport.visualStyle=adsk.core.VisualStyles.ShadedWithVisibleEdgesOnlyVisualStyle
except Exception:pass
if '選択セット2_外側方向' not in [s.name for s in design.selectionSets]:
    o=root.occurrences.itemByName('01_flat_carrier_socket_V6:1')
    fs=[f for f in o.component.bRepBodies.item(0).faces
        if f.geometry.surfaceType==adsk.core.SurfaceTypes.PlaneSurfaceType and abs(f.geometry.origin.y*10-47)<1e-6]
    f=max(fs,key=lambda f:f.area)
    design.selectionSets.add([f.createForAssemblyContext(o)],'選択セット2_外側方向')
def preview(name,eye,target=(22,36,35)):
    cam=app.activeViewport.camera; cam.eye=point(eye); cam.target=point(target); cam.upVector=vec(EZ); cam.isFitView=True
    app.activeViewport.camera=cam; app.activeViewport.refresh()
    assert app.activeViewport.saveAsImageFile(str(OUT/'preview'/(name+'.png')),1600,1200)
preview('01_assembled_front',(180,240,140))
preview('02_camera_USB_side',(-130,180,70))
for o in root.occurrences:
    if o.component.name.startswith('REFERENCE_'):o.isLightBulbOn=False
preview('03_four_printed_parts',(180,240,140))
for o in root.occurrences:
    if o.component.name.startswith('REFERENCE_'):o.isLightBulbOn=True
archive=OUT/'source_cad/SO101_Glueless_Camera_HX711_V6_assembly_DO_NOT_PRINT.f3d'
assert design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(archive)))
CA=tuple(build['camera_basis']['A']); CB=tuple(build['camera_basis']['B']); CN=tuple(build['camera_basis']['N'])
exports=[]
for name in build['geometry']:
    o=root.occurrences.itemByName(name+':1'); body=o.bRepBodies.item(0)
    assert design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(OUT/'source_cad'/(name+'_editable.f3d')),o.component))
    b=T.copy(body); rot=adsk.core.Matrix3D.create()
    rows=(CA,scale(CB,-1),CN) if name.startswith('04_') else (EX,(0,0,-1),EY)
    for i,row in enumerate(rows):
        for j,v in enumerate(row):rot.setCell(i,j,v)
    assert abs(rot.determinant-1)<1e-8
    T.transform(b,rot)
    shift=adsk.core.Matrix3D.create(); shift.translation=vec(scale(b.boundingBox.minPoint.asArray(),-1)); T.transform(b,shift)
    pd_doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    try:
        pd=adsk.fusion.Design.cast(pd_doc.products.itemByProductType('DesignProductType'))
        pd.designType=adsk.fusion.DesignTypes.DirectDesignType
        pb=pd.rootComponent.bRepBodies.add(b); pb.name=name
        stl=OUT/(name+'.stl'); opt=pd.exportManager.createSTLExportOptions(pb,str(stl))
        opt.unitType=adsk.fusion.DistanceUnits.MillimeterDistanceUnits; opt.isBinaryFormat=True
        opt.sendToPrintUtility=False; opt.meshRefinement=adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        assert pd.exportManager.execute(opt)
        assert pd.exportManager.execute(pd.exportManager.createSTEPExportOptions(str(OUT/'source_cad'/(name+'.step')),pd.rootComponent))
        cam=app.activeViewport.camera; cam.viewOrientation=adsk.core.ViewOrientations.IsoTopRightViewOrientation; cam.isFitView=True
        app.activeViewport.camera=cam; app.activeViewport.refresh()
        app.activeViewport.saveAsImageFile(str(OUT/'preview'/(name+'.png')),1000,800)
        bb=bbox(pb)
        exports.append({'part':name,'stem':name,'quantity':1,'volume_mm3':pb.volume*1000,
            'size_mm':[bb[1][i]-bb[0][i] for i in range(3)],'solid_lumps':pb.lumps.count,
            'orientation':'camera tray broad back face down' if name.startswith('04_') else 'flat broad back face down',
            'rotation_matrix':list(rot.asArray()),'stl_units':'mm','stl_sha256':hashlib.sha256(stl.read_bytes()).hexdigest()})
    finally:pd_doc.close(False); document.activate()
for f in ('design_check.json','candidate_geometry.json','static_check.json','fastener_check.json',
          'rotation_check.json','assembly_paths.json','camera_sightline.json'):
    shutil.copy2(CHECK/f,OUT/'checks'/f)
report={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exports':exports,
    'assembly_archive':str(archive),'existing_assembly_preserved':True,'hardware':build['hardware'],
    'printed_parts':4,'hot_glue_required':False,'PCB_or_camera_extra_fasteners':0,
    'physical_print_fit_strength_and_electrical_test_performed':False}
(OUT/'export_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
preview('01_assembled_front',(180,240,140))
print(json.dumps({'folder':str(OUT),'exports':exports},ensure_ascii=False,indent=2))
