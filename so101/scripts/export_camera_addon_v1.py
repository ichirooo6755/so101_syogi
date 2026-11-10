"""Assembly-path checks and exact-body printable exports of the camera addon."""
import adsk.core
import adsk.fusion
import datetime
import hashlib
import json
import math
import shutil
from pathlib import Path

ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
CHECK=ROOT/'output/camera_mount_v1'
OUT=ROOT/'output/print_camera_hx711_v1'
assert not OUT.exists(),'Do not overwrite an earlier release or user files'
main=next(x for x in app.documents if x.name.startswith('so101書道'))
md=adsk.fusion.Design.cast(main.products.itemByProductType('DesignProductType'))
candidates=[]
for doc in app.documents:
    d=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    if d and d.rootComponent.occurrences.itemByName('01_fixed_electronics_frame:1'):
        candidates.append((doc,d))
document,design=candidates[-1]
document.activate(); root=design.rootComponent
T=adsk.fusion.TemporaryBRepManager.get()
I=adsk.fusion.BooleanTypes.IntersectionBooleanType
def bbox(b):
    return [[getattr(p,c)*10 for c in ('x','y','z')] for p in (b.boundingBox.minPoint,b.boundingBox.maxPoint)]
def box_hits(a,b):return all(a[0][i]<=b[1][i] and b[0][i]<=a[1][i] for i in range(3))
def hit(a,b,ab,bb):
    if not box_hits(ab,bb): return 0.
    q=T.copy(a); assert T.booleanOperation(q,b,I)
    return q.volume*1000
def translated(b,delta):
    q=T.copy(b); m=adsk.core.Matrix3D.create(); m.translation=adsk.core.Vector3D.create(*(x/10 for x in delta)); T.transform(q,m)
    return q
names=list(json.loads((CHECK/'design_check.json').read_text())['geometry'])
parts={k:root.occurrences.itemByName(k+':1').bRepBodies.item(0) for k in names}
fixed=[]
for o in md.rootComponent.allOccurrences:
    if not o.isVisible: continue
    if o.fullPathName.startswith('STS3215_c:1+') or o.fullPathName=='Wrist_Roll_Clearance_V8_元取付対応:1':
        for b in o.bRepBodies:
            if b.isSolid and b.volume>1e-6:
                q=T.copy(b); fixed.append((o.fullPathName+'/'+b.name,q,bbox(q)))
paths=[]
for key,distances,axis in (
    ('02_wrist_lower_shoe',(.1,.25,.5,1,3,10,30),(0,0,-1)),
    ('01_fixed_electronics_frame',(.1,1,5,20,60),(1,0,0))):
    for dist in distances:
        b=translated(parts[key],tuple(dist*x for x in axis)); bb=bbox(b)
        hits=[(k,v) for k,q,qb in fixed if (v:=hit(b,q,bb,qb))>.01]
        paths.append({'part':key,'offset_mm':dist,'direction':axis,'hits':hits})
assert not any(x['hits'] for x in paths),paths
# A whole brush is outside a 56.5 mm minimum radius about the gripper axis;
# the additional hardware/reference camera and print parts stay inside that.
part_cached=[(k,T.copy(b),bbox(b)) for k,b in parts.items()]
cartridge=md.rootComponent.occurrences.itemByName('Brush_Cartridge_Symmetric_15mm_V5:1').bRepBodies.item(0)
removal=[]
for dist in (1,5,10,25,50,100):
    b=translated(cartridge,(0,0,-dist)); bb=bbox(b)
    hits=[(k,v) for k,q,qb in part_cached if (v:=hit(b,q,bb,qb))>.01]
    removal.append({'down_mm':dist,'hits':hits})
assert not any(x['hits'] for x in removal),removal
(CHECK/'assembly_paths.json').write_text(json.dumps({'passed':True,'paths':paths,'cartridge_removal':removal},ensure_ascii=False,indent=2))

# Distinguish printed parts from reference hardware in the native preview.
color_log=[]
try:
    lib=next(lib for lib in app.materialLibraries if 'Appearance' in lib.name)
    source=next((a for a in lib.appearances if 'Matte' in a.name and 'Plastic' in a.name),lib.appearances.item(0))
    def color(name,rgb):
        a=design.appearances.addByCopy(source,name)
        for p in a.appearanceProperties:
            cp=adsk.core.ColorProperty.cast(p)
            if cp:
                cp.value=adsk.core.Color.create(*rgb,255); color_log.append([name,p.id]); break
        return a
    blue=color('NEW_printed_blue',(65,145,230))
    orange=color('NEW_keepers_orange',(240,155,60))
    gray=color('EXISTING_reference_gray',(155,160,165))
    green=color('PCB_reference_green',(35,135,85))
    for o in root.occurrences:
        a=blue if o.component.name[:2] in ('01','02') else orange if o.component.name[:2] in ('03','04','05','06') else green if 'envelopes' in o.component.name else gray
        if 'XIAO' not in o.component.name:
            for b in o.bRepBodies: b.appearance=a
except Exception as exc:
    color_log.append(['optional_appearance_error',str(exc)])

OUT.mkdir(); (OUT/'source_cad').mkdir(); (OUT/'preview').mkdir(); (OUT/'checks').mkdir()
for f in ('design_check.json','static_check.json','rotation_check.json','fastener_check.json','assembly_paths.json','candidate_geometry.json'):
    shutil.copy2(CHECK/f,OUT/'checks'/f)
archive=OUT/'source_cad/SO101_Camera_HX711_Addon_V1_assembly_DO_NOT_PRINT.f3d'
assert design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(archive)))

for label,eye in (('assembly_front',(120,-125,-65)),('assembly_rear',(-90,120,95))):
    cam=app.activeViewport.camera
    cam.eye=adsk.core.Point3D.create(*(x/10 for x in eye)); cam.target=adsk.core.Point3D.create(2.5,0,2.5)
    cam.upVector=adsk.core.Vector3D.create(0,0,1); cam.isFitView=True
    app.activeViewport.camera=cam; app.activeViewport.refresh()
    app.activeViewport.saveAsImageFile(str(OUT/'preview'/f'{label}.png'),1600,1200)

exports=[]
for name,source_body in parts.items():
    native=OUT/'source_cad'/f'{name}_editable.f3d'
    assert design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(native),root.occurrences.itemByName(name+':1').component))
    b=T.copy(source_body)
    rotation=adsk.core.Matrix3D.create(); description='assembly orientation; frame needs removable support'
    if name=='03_camera_end_keeper':
        an=math.radians(25); rows=((0,-1,0),(math.cos(an),0,math.sin(an)),(-math.sin(an),0,math.cos(an)))
        for i,row in enumerate(rows):
            for j,v in enumerate(row): rotation.setCell(i,j,v)
        description='camera keeper outer flat face on bed; locating pins upwards'
    elif name.startswith(('04_','05_')):
        rows=((0,1,0),(0,0,-1),(-1,0,0))
        for i,row in enumerate(rows):
            for j,v in enumerate(row): rotation.setCell(i,j,v)
        description='HX711 keeper broad outer face on bed'
    elif name.startswith('06_'):
        rows=((0,1,0),(0,0,1),(1,0,0))
        for i,row in enumerate(rows):
            for j,v in enumerate(row): rotation.setCell(i,j,v)
        description='level shifter keeper broad nut-entry face on bed; pins upwards'
    assert abs(rotation.determinant-1)<1e-9
    T.transform(b,rotation)
    minimum=b.boundingBox.minPoint
    shift=adsk.core.Matrix3D.create(); shift.translation=adsk.core.Vector3D.create(*(-v for v in minimum.asArray())); T.transform(b,shift)
    print_doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    try:
        pd=adsk.fusion.Design.cast(print_doc.products.itemByProductType('DesignProductType')); pd.designType=adsk.fusion.DesignTypes.DirectDesignType
        pb=pd.rootComponent.bRepBodies.add(b); pb.name=name
        stl=OUT/f'{name}.stl'
        opts=pd.exportManager.createSTLExportOptions(pb,str(stl)); opts.unitType=adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        opts.isBinaryFormat=True; opts.sendToPrintUtility=False; opts.meshRefinement=adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        assert pd.exportManager.execute(opts)
        assert pd.exportManager.execute(pd.exportManager.createSTEPExportOptions(str(OUT/'source_cad'/f'{name}.step'),pd.rootComponent))
        cam=app.activeViewport.camera; cam.viewOrientation=adsk.core.ViewOrientations.IsoTopRightViewOrientation; cam.isFitView=True
        app.activeViewport.camera=cam; app.activeViewport.refresh()
        app.activeViewport.saveAsImageFile(str(OUT/'preview'/f'{name}.png'),1000,800)
        bb=bbox(pb)
        exports.append({'part':name,'stem':name,'quantity':1,'volume_mm3':pb.volume*1000,
            'size_mm':[bb[1][i]-bb[0][i] for i in range(3)],'solid_lumps':pb.lumps.count,
            'orientation':description,'rotation_matrix':list(rotation.asArray()),
            'stl_units':'mm','stl_sha256':hashlib.sha256(stl.read_bytes()).hexdigest()})
    finally:
        print_doc.close(False); document.activate()

# Compare the unmodified original against the captured source inventory.
inventory=json.loads((CHECK/'source_inventory.json').read_text())
now={o.fullPathName:o for o in md.rootComponent.allOccurrences}
assert len(now)==len(inventory['occurrences'])
for row in inventory['occurrences']:
    o=now[row['path']]
    assert o.isVisible==row['visible']
    assert list(o.transform2.asArray())==row['transform'],row['path']
    actual=[b for b in o.bRepBodies if b.isSolid]
    assert len(actual)==len(row['bodies'])
    for a,b in zip(actual,row['bodies']): assert a.name==b['name'] and abs(a.volume*1000-b['volume_mm3'])<1e-6,row['path']
assert not main.isModified and main.dataFile.versionNumber==26 and md.timeline.count==520
report={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exports':exports,
    'assembly_archive':str(archive),'source_geometry_poses_materials_preserved':True,
    'source_version':26,'source_timeline':[520,520],'appearance_log':color_log,
    'physical_print_fit_or_electrical_test_performed':False}
(OUT/'export_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
document.activate()
cam=app.activeViewport.camera; cam.eye=adsk.core.Point3D.create(12,-12.5,-6.5); cam.target=adsk.core.Point3D.create(2.5,0,2.5)
cam.upVector=adsk.core.Vector3D.create(0,0,1); cam.isFitView=True; app.activeViewport.camera=cam; app.activeViewport.refresh()
print(json.dumps(report,ensure_ascii=False,indent=2))
