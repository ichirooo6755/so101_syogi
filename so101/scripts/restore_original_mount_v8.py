"""Restore exact inner mounting BReps from the user's original part.

Only rigid registration places each original mount at the current servo axis.
Original diagonal holes, grip thickness, recesses and blind key pocket survive.
No source assembly geometry is edited by this script.
"""
import adsk.core
import adsk.fusion
import json
import math
import os

root='/Users/sugawaraichirou/Documents/ChatGPT/so101'; out=root+'/output/v8'
os.makedirs(out,exist_ok=True)
assert ui.activeCommand=='SelectCommand'
main=next(doc for doc in app.documents if doc.name.startswith('so101書道'))
md=adsk.fusion.Design.cast(main.products.itemByProductType('DesignProductType')); mr=md.rootComponent
original=mr.occurrences.itemByName('部品１:1').bRepBodies.item(0)
v7doc=next(doc for doc in app.documents if doc.name=='部品１_V7_閉断面台座補強')
v7d=adsk.fusion.Design.cast(v7doc.products.itemByProductType('DesignProductType'))
candidate=v7d.rootComponent.bRepBodies.item(0)
assert abs(candidate.volume*1000-39541.145691013226)<1e-4
t=adsk.fusion.TemporaryBRepManager.get()
def cylinder(x,z,y0,y1,r):
    return t.createCylinderOrCone(adsk.core.Point3D.create(x/10,y0/10,z/10),r/10,
        adsk.core.Point3D.create(x/10,y1/10,z/10),r/10)
def intersect(a,b):
    x=t.copy(a); assert t.booleanOperation(x,b,adsk.fusion.BooleanTypes.IntersectionBooleanType)
    return x
def overlap(a,b):
    if not a.boundingBox.intersects(b.boundingBox): return 0.
    return intersect(a,b).volume*1000
def difference(a,b):
    assert t.booleanOperation(a,b,adsk.fusion.BooleanTypes.DifferenceBooleanType)
def union(a,b):
    assert t.booleanOperation(a,b,adsk.fusion.BooleanTypes.UnionBooleanType)
def translate(b,x,y,z):
    m=adsk.core.Matrix3D.create(); m.translation=adsk.core.Vector3D.create(x/10,y/10,z/10)
    assert t.transform(b,m)
body=t.copy(candidate)
cx0=-1.62262849469649; cz0=33.89556811322882
dx=-2-cx0; dz=34-cz0
sources={}; details=[]
specs=[('negative',-21.73705379764,-14.73705379764,-16.23705379764,-17.05,-36.5,-22.55,-20.55),
       ('positive',18.66294620236,26.26294620236,20.16294620236,20.2,26.3,35.5,23.7)]
for side,y0,y1,old_face,new_face,back0,back1,head_seat in specs:
    piece=intersect(original,cylinder(cx0,cz0,y0,y1,13))
    assert piece.volume>0
    translate(piece,dx,new_face-old_face,dz)
    sources[side]=t.copy(piece)
    # Replace the whole old circular pad, rather than retaining its wrong holes.
    cut=cylinder(-2,34,-36.6,-15.4,13) if side=='negative' else cylinder(-2,34,18.5,35.6,13)
    difference(body,cut)
    back=cylinder(-2,34,back0,back1,13)
    # Keep original 5.4 mm outer head pockets; small-head M3 bolts are required.
    for a in range(4):
        angle=math.pi/4+a*math.pi/2
        x=-2+7*math.cos(angle); z=34+7*math.sin(angle)
        difference(back,cylinder(x,z,back0-.01,back1+.01,2.7))
    union(body,back); union(body,piece)
    details.append({'side':side,'rigid_translation_mm':[dx,new_face-old_face,dz],
        'source_inner_mount_face_y_mm':old_face,'registered_inner_face_y_mm':new_face,
        'registered_head_seat_y_mm':head_seat,'original_clamped_thickness_mm':3.5,
        'through_hole_mm':3.2,'head_pocket_mm':5.4,'diagonal_hole_pitch_circle_mm':14.0})
assert body.isSolid and body.lumps.count==1
preservation=[]
for side,piece in sources.items():
    bounds=piece.boundingBox
    mask=cylinder(-2,34,bounds.minPoint.y*10+1e-6,bounds.maxPoint.y*10-1e-6,13-1e-6)
    expected=intersect(piece,mask); actual=intersect(body,mask)
    error=(expected.volume+actual.volume)*1000-2*overlap(expected,actual)
    # Intersection integrals of near-coincident NURBS can differ by sub-0.001
    # mm3, including a small negative numerical residue. Do not call it exact 0.
    assert abs(error)<1e-3,(side,error)
    preservation.append({'side':side,'symmetric_difference_signed_residue_mm3':error,
        'boolean_volume_tolerance_mm3':.001})
# Check the real user-edited wrist and the fixed servo case, not a generic box.
fixed=[]
for o in mr.allOccurrences:
    if o.isVisible and (o.fullPathName.startswith('Wrist_Roll_Clearance_V5:1') or
        (o.fullPathName.startswith('STS3215_c:1+') and '+Axes:' not in o.fullPathName)):
        for b in o.bRepBodies:
            if b.isSolid and b.volume>1e-6: fixed.append((o.fullPathName+'/'+b.name,t.copy(b)))
hits=[{'fixed':n,'volume_mm3':v} for n,b in fixed if (v:=overlap(body,b))>.01]
report={'source':'Original 部品１:1; mounting detail copied as BRep, not recreated',
    'mounts':details,'preservation':preservation,'fixed_interferences':hits,
    'base_volume_mm3':body.volume*1000,'main_assembly_edited':False,
    'original_mount_reference_confirmation_pending':True}
with open(out+'/original_mount_restoration.json','w',encoding='utf-8') as f:
    json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps(report,ensure_ascii=False,indent=2))
# Always retain an independent visible candidate, even if its interface needs
# a user decision. Never silently cut copied original mounting details.
doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
d=adsk.fusion.Design.cast(app.activeProduct); r=d.rootComponent
bf=r.features.baseFeatures.add(); bf.name='V8_exact_original_inner_mounts_registered_to_servo_axis'
assert bf.startEdit(); result=r.bRepBodies.add(body,bf); assert bf.finishEdit()
result.name='V8_original_mounts_deep_web_supported_socket'
assert doc.saveAs('部品１_V8_元取付形状保持',main.dataFile.parentFolder,'',
    'Exact original inner mounting BReps; preserves diagonal M3 holes and pockets; V7 deep-web socket support; main remains unchanged')
report.update(document=doc.name,cloud_id=doc.dataFile.id)
with open(out+'/original_mount_restoration.json','w',encoding='utf-8') as f:
    json.dump(report,f,ensure_ascii=False,indent=2)
cam=app.activeViewport.camera; cam.viewOrientation=adsk.core.ViewOrientations.IsoTopRightViewOrientation
cam.isFitView=True; app.activeViewport.camera=cam; app.activeViewport.refresh()
print('V8 independent candidate',doc.name,'fixed intersections',len(hits))
