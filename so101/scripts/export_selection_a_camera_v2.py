"""Verify practical assembly, color, save and export the separate Selection A V2."""
import adsk.core
import adsk.fusion
import datetime
import hashlib
import json
import math
import shutil
from pathlib import Path

ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
CHECK=ROOT/'output/camera_mount_v2'
OUT=ROOT/'output/print_camera_hx711_v2'
assert not OUT.exists(),'Do not overwrite an earlier release'
helpers=(ROOT/'scripts/build_camera_addon_v1.py').read_text().split("progress('building_temporary_geometry')",1)[0]
exec(compile(helpers,'mm_geometry_helpers','exec'),globals())
OUT=ROOT/'output/print_camera_hx711_v2'
CHECK=ROOT/'output/camera_mount_v2'
build=json.loads((CHECK/'design_check.json').read_text())
candidates=[]
for doc in app.documents:
    d=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    if d and d.rootComponent.occurrences.itemByName('01_A_left_arm_frame_V2:1'):
        candidates.append((doc,d))
assert len(candidates)==1
document,design=candidates[0]; document.activate(); root=design.rootComponent
parts={k:root.occurrences.itemByName(k+':1').bRepBodies.item(0) for k in build['geometry']}
cached=[(k,T.copy(b),bbox(b)) for k,b in parts.items()]
ref=root.occurrences.itemByName('REFERENCE_SO101_unchanged:1')
existing=[(b.name,T.copy(b),bbox(b)) for b in ref.bRepBodies]
fixed=existing[:17]; moving=existing[17:]
def translate(b,delta):
    q=T.copy(b); m=adsk.core.Matrix3D.create(); m.translation=vec(tuple(x/10 for x in delta)); T.transform(q,m)
    return q
def rotate(b,angle):
    q=T.copy(b); m=adsk.core.Matrix3D.create(); m.setToRotation(math.radians(angle),vec(EY),point((-2,0,34)))
    T.transform(q,m); return q
def collisions(b,obstacles):
    bb=bbox(b)
    return [[k,round(v,6)] for k,q,qb in obstacles if (v:=hit(b,q,bb,qb))>.01]

# Closing the nominal print-fit gaps translates both jaws by 0.25 mm.
seated=[]
for k,b,_ in cached:
    seated.append((k,translate(b,(0,.25 if k.startswith('02_') else -.25,0))))
for name in ('REFERENCE_XIAO_Sense_1pc','REFERENCE_HX711_1pc',
             'REFERENCE_TXS0108E_level_shifter_1pc','REFERENCE_M3_hardware_do_not_print'):
    for b in root.occurrences.itemByName(name+':1').bRepBodies:
        seated.append((b.name,translate(b,(0,.25 if b.name.startswith('M3_nut_A_') else -.25,0))))
seated_issues=[]
for k,b in seated:
    seated_issues += [[k,*x] for x in collisions(b,existing)]
for i,(k,b) in enumerate(seated[:6]):
    for q,qb in seated[i+1:]:
        v=hit(b,qb)
        if v>.01: seated_issues.append([k,q,round(v,6)])
assert not seated_issues,seated_issues

paths=[]
for name,axis in (('01_A_left_arm_frame_V2',EY),('02_A_slot_inner_jaw_V2',(0,-1,0))):
    for dist in (.1,.25,.5,1,3,10,30):
        q=translate(parts[name],scale(axis,dist))
        paths.append({'part':name,'offset_mm':dist,'direction':axis,
                      'moving_part_hits':collisions(q,moving),'fixed_hits':collisions(q,fixed)})
assert not any(p['moving_part_hits'] for p in paths),paths
access=[]
for angle in (0,45,90,135,180,225,270,315):
    hits=[]
    for dist in (.1,.25,.5,1,3,10,30):
        q=rotate(translate(parts['02_A_slot_inner_jaw_V2'],(0,-dist,0)),angle)
        hits += [[dist,*x] for x in collisions(q,fixed)]
    access.append({'angle_deg':angle,'inner_jaw_fixed_hits':hits})
clear_poses=[p['angle_deg'] for p in access if not p['inner_jaw_fixed_hits']]
removal=[]
for dist in (1,5,10,25,50,100):
    b=translate(moving[-2][1],(0,0,-dist))
    removal.append({'down_mm':dist,'hits':collisions(b,cached)})
assert not any(r['hits'] for r in removal),removal
path_report={'passed':True,'nominal_clamped_gap_closure_mm_per_jaw':.25,
    'clamped_static_issues':seated_issues,'paths':paths,'inner_jaw_access_poses':access,
    'in_place_inner_jaw_clear_sample_angles_deg':clear_poses,
    'remove_part_1_from_servo_if_no_clear_access':not bool(clear_poses),'cartridge_removal':removal}
(CHECK/'assembly_paths.json').write_text(json.dumps(path_report,ensure_ascii=False,indent=2))

# Distinct module names AND appearances prevent the former two-HX711 ambiguity.
lib=app.materialLibraries.itemByName('Fusion 外観ライブラリ')
source=lib.appearances.itemByName('ABS(白)')
def color(name,rgb):
    a=design.appearances.addByCopy(source,name)
    adsk.core.ColorProperty.cast(a.appearanceProperties.itemById('opaque_albedo')).value=adsk.core.Color.create(*rgb,255)
    return a
blue=color('V2_NEW_frame_blue',(55,145,230)); orange=color('V2_NEW_keepers_orange',(245,155,45))
gray=color('V2_EXISTING_gray',(165,170,175)); green=color('V2_HX711_green',(40,145,75))
purple=color('V2_TXS0108E_purple',(165,85,195)); dark=color('V2_XIAO_dark',(55,65,70))
for o in root.occurrences:
    n=o.component.name
    a=blue if n.startswith(('01_','02_')) else orange if n.startswith(('03_','04_','05_','06_')) else green if 'HX711_1pc' in n else purple if 'TXS0108E' in n else dark if 'XIAO' in n else gray
    for b in o.bRepBodies: b.appearance=a
try: app.activeViewport.visualStyle=adsk.core.VisualStyles.ShadedWithVisibleEdgesOnlyVisualStyle
except Exception: pass
OUT.mkdir(); (OUT/'source_cad').mkdir(); (OUT/'checks').mkdir(); (OUT/'preview').mkdir()
for f in ('design_check.json','candidate_geometry.json','static_check.json','fastener_check.json',
          'rotation_check.json','assembly_paths.json','camera_sightline.json','selection_A_request_view.json'):
    shutil.copy2(CHECK/f,OUT/'checks'/f)

def preview(name,eye,up=(0,0,1)):
    cam=app.activeViewport.camera; cam.eye=point(eye); cam.target=point((-5,15,28)); cam.upVector=vec(up); cam.isFitView=True
    app.activeViewport.camera=cam; app.activeViewport.refresh()
    app.activeViewport.saveAsImageFile(str(OUT/'preview'/(name+'.png')),1600,1200)
request=json.loads((CHECK/'selection_A_request_view.json').read_text())
preview('01_requested_left_view',request['eye_mm'],request['up'])
preview('02_clamp_and_left_beam',(-120,140,105))
for o in root.occurrences:
    if o.component.name.startswith('REFERENCE_'): o.isLightBulbOn=False
preview('03_printed_parts_only',(-120,140,105))
for o in root.occurrences:
    if o.component.name.startswith('REFERENCE_'): o.isLightBulbOn=True

cloud={}
try:
    original=next(d for d in app.documents if d.name.startswith('so101書道'))
    assert document.saveAs('so101_SelectionA_Left_Camera_HX711_V2',original.dataFile.parentFolder,
        'Selected A slot sandwich, left extension; original servo, wrist and load-cell interfaces unchanged. Prototype.','')
    cloud={'saveAs_returned':True,'document':document.name,'id':document.dataFile.id,'version':document.dataFile.versionNumber,
           'cloud_upload_completion_verified':False}
except Exception as exc: cloud={'local_archives_available':True,'cloud_save_note':str(exc)}
archive=OUT/'source_cad/SO101_SelectionA_Left_Camera_HX711_V2_assembly_DO_NOT_PRINT.f3d'
assert design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(archive)))

CA=tuple(build['camera_basis']['A']); CB=tuple(build['camera_basis']['B']); CN=tuple(build['camera_basis']['N'])
exports=[]
for name,source_body in parts.items():
    native=OUT/'source_cad'/(name+'_editable.f3d')
    c=root.occurrences.itemByName(name+':1').component
    assert design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(native),c))
    b=T.copy(source_body); rotation=adsk.core.Matrix3D.create()
    description='assembly orientation; brim and removable support required beneath the arm and camera cradle'
    rows=None
    if name.startswith('02_'):
        rows=(EX,(0,0,-1),EY); description='inner jaw broad back face on bed; slot keys and nut tunnels upwards'
    elif name.startswith('03_'):
        rows=(CA,CB,scale(CN,-1)); description='camera keeper broad outer face on bed; locating pins upwards'
    elif name.startswith(('04_','05_')):
        rows=(EX,EZ,(0,-1,0)); description='HX711 keeper broad outer face on bed'
    elif name.startswith('06_'):
        rows=(EX,(0,0,-1),EY); description='TXS0108E keeper nut-entry face on bed; pins upwards'
    if rows:
        for i,row in enumerate(rows):
            for j,v in enumerate(row): rotation.setCell(i,j,v)
    assert abs(rotation.determinant-1)<1e-9
    T.transform(b,rotation)
    shift=adsk.core.Matrix3D.create(); shift.translation=vec(tuple(-v for v in b.boundingBox.minPoint.asArray())); T.transform(b,shift)
    print_doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    try:
        pd=adsk.fusion.Design.cast(print_doc.products.itemByProductType('DesignProductType'))
        pd.designType=adsk.fusion.DesignTypes.DirectDesignType
        pb=pd.rootComponent.bRepBodies.add(b); pb.name=name
        stl=OUT/(name+'.stl')
        opt=pd.exportManager.createSTLExportOptions(pb,str(stl)); opt.unitType=adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        opt.isBinaryFormat=True; opt.sendToPrintUtility=False; opt.meshRefinement=adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        assert pd.exportManager.execute(opt)
        assert pd.exportManager.execute(pd.exportManager.createSTEPExportOptions(str(OUT/'source_cad'/(name+'.step')),pd.rootComponent))
        cam=app.activeViewport.camera; cam.viewOrientation=adsk.core.ViewOrientations.IsoTopRightViewOrientation; cam.isFitView=True
        app.activeViewport.camera=cam; app.activeViewport.refresh()
        app.activeViewport.saveAsImageFile(str(OUT/'preview'/(name+'.png')),1000,800)
        bb=bbox(pb)
        exports.append({'part':name,'stem':name,'quantity':1,'volume_mm3':pb.volume*1000,
            'size_mm':[bb[1][i]-bb[0][i] for i in range(3)],'solid_lumps':pb.lumps.count,
            'orientation':description,'rotation_matrix':list(rotation.asArray()),'stl_units':'mm',
            'stl_sha256':hashlib.sha256(stl.read_bytes()).hexdigest()})
    finally:
        print_doc.close(False); document.activate()
report={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exports':exports,'assembly_archive':str(archive),
    'source_geometry_poses_materials_preserved':True,'source_fingerprint_verified_by_build':True,'cloud_copy':cloud,
    'attachment_moves_with_part_1':True,'hardware':build['hardware'],
    'physical_print_fit_strength_or_electrical_test_performed':False}
(OUT/'export_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
preview('01_requested_left_view',request['eye_mm'],request['up'])
print(json.dumps({'exports':exports,'cloud':cloud,'assembly_access_clear_angles_deg':clear_poses,'folder':str(OUT)},ensure_ascii=False,indent=2))
