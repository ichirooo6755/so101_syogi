"""Replacement parts with rotary clearance and a mirror-symmetric cartridge."""
import adsk.core
import adsk.fusion
import json
import math
import os

root='/Users/sugawaraichirou/Documents/ChatGPT/so101'
d=adsk.fusion.Design.cast(app.activeProduct); r=d.rootComponent; doc=app.activeDocument
assert doc.name=='so101書道'
assert not d.attributes.itemByName('so101_calligraphy','motion_v5')
with open(root+'/tmp/v5_before.json',encoding='utf-8') as f: before=json.load(f)
assert os.path.exists(root+'/reference/so101_before_motion_redesign_v5.f3d')
assert d.timeline.count-d.timeline.markerPosition==31
for name in ('部品１:1','Brush_Load_Carrier_Centered:1','Brush_Cartridge_Centered_15mm:1','Wrist_Roll_Follower_SO101 v1:3'):
    prev=next(o for o in before['occurrences'] if o['name']==name)
    live=r.occurrences.itemByName(name)
    assert abs(sum(b.volume for b in live.bRepBodies)*1000-sum(b['volume_mm3'] for b in prev['bodies']))<1e-5, name
if d.snapshots.hasPendingSnapshot:
    d.snapshots.add().name='V5_preserve_user_state_before_clearance_redesign'
vi=adsk.core.ValueInput.createByString
NEW=adsk.fusion.FeatureOperations.NewBodyFeatureOperation
JOIN=adsk.fusion.FeatureOperations.JoinFeatureOperation
CUT=adsk.fusion.FeatureOperations.CutFeatureOperation
t=adsk.fusion.TemporaryBRepManager.get()
cx=78.; cy=d.userParameters.itemByName('sc_brush_axis_y').value*10
def param(n,e,comment):
    assert not d.userParameters.itemByName(n),n
    return d.userParameters.add(n,vi(e),'mm',comment)
param('v5_brush_axis_x','78 mm','Tool center; aligned with SC616C center plane, not an offset load')
param('v5_brush_sleeve_length','24 mm','Shorter non-clamping hot glue cartridge; earlier versions retained')
param('v5_cartridge_flange_z','8.5 mm','Cartridge underside; shortened carrier rather than low hanging cage')
param('v5_brush_stop_z','v5_cartridge_flange_z + v5_brush_sleeve_length - 2 mm','Closed brush butt stop')
param('v5_rotary_axis_x','-2 mm','Matches actual imported servo output axis')
param('v5_rotary_axis_z','34 mm','Matches actual imported servo output axis')
def component(name):
    o=r.occurrences.addNewComponent(adsk.core.Matrix3D.create()); o.component.name=name
    return o,o.component
def sk(c,name,offset,kind='XY'):
    pl=c.xYConstructionPlane if kind=='XY' else (c.xZConstructionPlane if kind=='XZ' else c.yZConstructionPlane)
    # The live Fusion XZ construction plane has +Y normal (verified).
    pi=c.constructionPlanes.createInput(); pi.setByOffset(pl,vi(f'{offset:.10f} mm'))
    plane=c.constructionPlanes.add(pi); plane.name=name+'_plane'; plane.isLightBulbOn=False
    result=c.sketches.add(plane); result.name=name
    return result
def poly(s,pts):
    for a,b in zip(pts,pts[1:]+pts[:1]):
        line=s.sketchCurves.sketchLines.addByTwoPoints(s.modelToSketchSpace(adsk.core.Point3D.create(*(v/10 for v in a))),
                                                     s.modelToSketchSpace(adsk.core.Point3D.create(*(v/10 for v in b))))
        line.isFixed=True
def circle(s,xyz,expr):
    p=s.modelToSketchSpace(adsk.core.Point3D.create(*(v/10 for v in xyz)))
    curve=s.sketchCurves.sketchCircles.addByCenterRadius(p,d.unitsManager.evaluateExpression(expr,'mm')/2)
    curve.centerSketchPoint.isFixed=True
    dim=s.sketchDimensions.addDiameterDimension(curve,adsk.core.Point3D.create(p.x+.7,p.y+.3,0))
    dim.parameter.expression=expr
def extrude(c,s,depth,op,name,positive=True):
    profiles=adsk.core.ObjectCollection.create()
    for p in s.profiles: profiles.add(p)
    ei=c.features.extrudeFeatures.createInput(profiles,op)
    ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(vi(depth)),
        adsk.fusion.ExtentDirections.PositiveExtentDirection if positive else adsk.fusion.ExtentDirections.NegativeExtentDirection)
    if op!=NEW: ei.participantBodies=[c.bRepBodies.item(0)]
    feature=c.features.extrudeFeatures.add(ei); feature.name=name; s.isVisible=False
    assert int(feature.healthState)==0,(name,feature.errorOrWarningMessage)
    return feature
def box(c,name,x0,x1,y0,y1,z,depth,op=JOIN):
    s=sk(c,name,z); poly(s,[(x0,y0,z),(x1,y0,z),(x1,y1,z),(x0,y1,z)])
    return extrude(c,s,depth,op,name)
def cylY(c,name,x,z,y0,y1,diam,op=JOIN):
    s=sk(c,name,y0,'XZ'); circle(s,(x,y0,z),diam)
    return extrude(c,s,f'{y1-y0:.10f} mm',op,name,True)
def tempbox(x0,x1,y0,y1,z0,z1):
    return t.createBox(adsk.core.OrientedBoundingBox3D.create(adsk.core.Point3D.create((x0+x1)/20,(y0+y1)/20,(z0+z1)/20),
        adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
def basebody(c,body,name):
    bf=c.features.baseFeatures.add(); bf.name=name; assert bf.startEdit()
    assert c.bRepBodies.add(body,bf)
    assert bf.finishEdit()

# New one-piece yoke: outboard side rails and an overhead cross member.
yo,y=component('部品１_V5可動域改善')
cylY(y,'V5_negative_horn_mount',-2,34,-32.5,-17.05,'26 mm',NEW)
box(y,'V5_negative_outboard_rail',-2,72,-32.5,-28.5,23,'22 mm')
box(y,'V5_negative_front_upright',64,72,-32.5,-28.5,23,'32.5 mm')
box(y,'V5_overhead_tie',64,72,-32.5,31.5,49.5,'6 mm')
box(y,'V5_positive_front_upright',64,72,27.5,31.5,23,'32.5 mm')
box(y,'V5_positive_outboard_rail',-2,72,27.5,31.5,23,'22 mm')
cylY(y,'V5_positive_horn_mount',-2,34,20.2,31.5,'26 mm')
for side,y0,y1 in [('negative',-32.5,-17.05),('positive',20.2,31.5)]:
    cylY(y,'V5_'+side+'_center_key_access',-2,34,y0-.1,y1+.1,'6.5 mm',CUT)
    if side=='negative':
        cylY(y,'V5_negative_center_head_relief',-2,34,-18.9,-17.0,'8 mm',CUT)
        cylY(y,'V5_fixed_motor_boss_clearance',-2,34,-18.2,-17.0,'11 mm',CUT)
    else:
        cylY(y,'V5_positive_center_head_relief',-2,34,20.1,22.2,'8 mm',CUT)
    s=sk(y,'V5_'+side+'_4xM3_mount',y0-.1,'XZ')
    for a in range(4):
        circle(s,(-2+7*math.cos(a*math.pi/2),y0-.1,34+7*math.sin(a*math.pi/2)),'3.2 mm')
    extrude(y,s,f'{y1-y0+.2:.10f} mm',CUT,'V5_'+side+'_radial_pitch14_M3',True)
    start,end=(-32.6,-27.) if side=='negative' else (28.,31.6)
    s=sk(y,'V5_'+side+'_bolt_heads',start,'XZ')
    for a in range(4):
        circle(s,(-2+7*math.cos(a*math.pi/2),start,34+7*math.sin(a*math.pi/2)),'6.2 mm')
    extrude(y,s,f'{end-start:.10f} mm',CUT,'V5_'+side+'_M3_head_counterbores',True)

# Fixed end only: slide-in channel, integral roof, bottom entry machine screws.
box(y,'V5_fixed_cell_platform',70.8,85.2,23.46294620236,41.56294620236,29.5,'10 mm')
for x0,x1 in ((70.8,73.3),(82.7,85.2)):
    box(y,'V5_fixed_socket_wall_'+str(x0),x0,x1,23.46294620236,41.56294620236,39.5,'10 mm')
box(y,'V5_fixed_socket_roof',70.8,85.2,27.46294620236,41.56294620236,45.9,'3.6 mm')
box(y,'V5_fixed_socket_end_stop',73.3,82.7,38.86294620236,41.56294620236,39.5,'6.4 mm')
for diam,depth,label in [('sc_screw_clearance','10 mm','clearance'),('sc_head_dia','sc_head_depth','heads')]:
    s=sk(y,'V5_fixed_M3_'+label,29.5)
    for yy in (26.96294620236,34.36294620236): circle(s,(cx,yy,29.5),diam)
    extrude(y,s,depth,CUT,'V5_fixed_M3_'+label)
y.bRepBodies.item(0).name='V5_one_piece_yoke_M3_clearance_slide_socket'

# Copy the user's free-end seat only; all new brush-bearing structure is paired.
source=r.occurrences.itemByName('Brush_Load_Carrier_Centered:1').bRepBodies.item(0)
upper=t.copy(source)
assert t.booleanOperation(upper,tempbox(24,36,-8.53705379764,9.46294620236,18.5,30.5),adsk.fusion.BooleanTypes.IntersectionBooleanType)
m=adsk.core.Matrix3D.create(); m.translation=adsk.core.Vector3D.create(4.8,0,1.5); assert t.transform(upper,m)
co,c=component('Brush_Load_Carrier_Compact_V5')
basebody(c,upper,'V5_preserved_user_free_end_seat')
box(c,'V5_symmetric_upper_bridge',72,84,cy-14.5,cy+14.5,33.5,'3 mm')
for sign in (-1,1):
    yy=cy+sign*(14.5-1.6)
    box(c,'V5_paired_short_web_'+str(sign),72,84,yy-1.6,yy+1.6,18.5,'15 mm')
s=sk(c,'V5_receiver_ring',12.5); circle(s,(cx,cy,12.5),'brush_receiver_od')
extrude(c,s,'6 mm',JOIN,'V5_short_load_ring')
for sign in (-1,1): box(c,'V5_nut_ear_'+str(sign),72,84,cy+sign*20-6,cy+sign*20+6,12.5,'6 mm')
s=sk(c,'V5_slip_bore',12.5); circle(s,(cx,cy,12.5),'brush_receiver_id')
extrude(c,s,'6 mm',CUT,'V5_non_clamping_receiver')
for diam,depth,name in [('sc_screw_clearance','6 mm','clearance'),('sc_head_dia','sc_head_depth','head_recess')]:
    s=sk(c,'V5_free_M3_'+name,33.5)
    for yy in (-2.43705379764,4.96294620236): circle(s,(cx,yy,33.5),diam)
    extrude(c,s,depth,CUT,'V5_free_M3_'+name)
s=sk(c,'V5_cartridge_2xM3',12.5)
for sign in (-1,1): circle(s,(cx,cy+sign*20,12.5),'sc_screw_clearance')
extrude(c,s,'6 mm',CUT,'V5_cartridge_M3_clearance')
s=sk(c,'V5_captive_hex_nuts',18.5)
rr=d.userParameters.itemByName('brush_nut_af').value*10/math.sqrt(3)
for sign in (-1,1):
    yy=cy+sign*20
    poly(s,[(cx+rr*math.cos(a*math.pi/3),yy+rr*math.sin(a*math.pi/3),18.5) for a in range(6)])
extrude(c,s,'brush_nut_depth',CUT,'V5_M3_AF5p8_depth2p6_nuts',False)
c.bRepBodies.item(0).name='V5_compact_carrier_two_M3_nuts'

# Cartridge is mirrored about both vertical center planes, including glue ports.
ko,k=component('Brush_Cartridge_Symmetric_15mm_V5')
s=sk(k,'V5_cartridge_flange',8.5); circle(s,(cx,cy,8.5),'brush_flange_od')
extrude(k,s,'brush_flange_thickness',NEW,'V5_symmetric_flange')
for sign in (-1,1):
    y0,y1=(cy-26,cy-13) if sign<0 else (cy+13,cy+26)
    box(k,'V5_symmetric_ear_'+str(sign),72,84,y0,y1,8.5,'4 mm')
s=sk(k,'V5_sleeve_OD',8.5); circle(s,(cx,cy,8.5),'brush_cartridge_od')
extrude(k,s,'v5_brush_sleeve_length',JOIN,'V5_24mm_cartridge')
s=sk(k,'V5_blind_brush_bore',8.5); circle(s,(cx,cy,8.5),'brush_cartridge_id')
extrude(k,s,'v5_brush_sleeve_length - 2 mm',CUT,'V5_brush_bore_with_butt_stop')
for z in (8.5,28.5):
    s=sk(k,'V5_guide_fill_'+str(z),z); circle(s,(cx,cy,z),'brush_cartridge_od')
    extrude(k,s,'2 mm',JOIN,'V5_guide_land_'+str(z))
    s=sk(k,'V5_guide_bore_'+str(z),z); circle(s,(cx,cy,z),'brush_guide_dia')
    extrude(k,s,'2 mm',CUT,'V5_brush_guide_'+str(z))
s=sk(k,'V5_flange_M3_bolts',8.5)
for sign in (-1,1): circle(s,(cx,cy+sign*20,8.5),'sc_screw_clearance')
extrude(k,s,'4 mm',CUT,'V5_flange_M3_clearance')
s=sk(k,'V5_opposed_X_glue_ports',65,'YZ')
poly(s,[(65,cy-2,16.5),(65,cy+2,16.5),(65,cy+2,21.5),(65,cy-2,21.5)])
extrude(k,s,'26 mm',CUT,'V5_X_glue_ports')
s=sk(k,'V5_opposed_Y_glue_ports',cy-13,'XZ')
poly(s,[(cx-2,cy-13,16.5),(cx+2,cy-13,16.5),(cx+2,cy-13,21.5),(cx-2,cy-13,21.5)])
extrude(k,s,'26 mm',CUT,'V5_Y_glue_ports',True)
k.bRepBodies.item(0).name='V5_XY_mirror_symmetric_hot_glue_cartridge'

# Tiny concentric clearance cuts in a separate wrist variant. Originals remain.
wo,w=component('Wrist_Roll_Clearance_V5')
wrist=r.occurrences.itemByName('Wrist_Roll_Follower_SO101 v1:3')
basebody(w,t.copy(next(b for b in wrist.bRepBodies if b.volume>1e-6)),'V5_original_wrist_geometry')
wrist_initial=w.bRepBodies.item(0).volume*1000
for side,y0,y1 in [('negative',-33,-17.0),('positive',20.1,32)]:
    cylY(w,'V5_rotary_pad_clearance_'+side,-2,34,y0,y1,'27.5 mm',CUT)
w.bRepBodies.item(0).name='V5_wrist_with_concentric_pad_relief'

# Remove old constraints from the active variant, not their features or shapes.
suppressed=[]
for j in list(r.asBuiltJoints):
    if j.name in [q['name'] for q in before['as_built_joints']]:
        j.isSuppressed=True; suppressed.append(j.name)
cell=r.occurrences.itemByName('SC616C_1kg_Fusion:1')
sensor_before=list(cell.transform2.asArray())
matrix=cell.transform2
v=matrix.translation; v.x+=4.8; v.z+=1.5; matrix.translation=v; cell.transform2=matrix
if d.snapshots.hasPendingSnapshot: d.snapshots.add().name='V5_translate_sensor_no_rotation'
for a,b,name in ((yo,cell,'V5_sensor_fixed_end_to_yoke'),(cell,co,'V5_free_end_to_short_carrier'),(co,ko,'V5_cartridge_to_carrier')):
    ji=r.asBuiltJoints.createInput(a,b,None); ji.setAsRigidJointMotion()
    j=r.asBuiltJoints.add(ji); j.name=name; j.isLightBulbOn=False
for name in ('部品１:1','Brush_Load_Carrier_Centered:1','Brush_Cartridge_Centered_15mm:1','Wrist_Roll_Follower_SO101 v1:3'):
    r.occurrences.itemByName(name).isLightBulbOn=False
assert all(o.component.bRepBodies.count==1 and o.bRepBodies.item(0).isSolid for o in (yo,co,ko,wo))
d.attributes.add('so101_calligraphy','motion_v5','New yoke, short paired carrier, symmetric sleeve, centered translated cell, wrist relief')
report={'parts':{label:o.name for label,o in [('base',yo),('carrier',co),('cartridge',ko),('wrist',wo)]},
        'part_volumes_mm3':{o.name:o.bRepBodies.item(0).volume*1000 for o in (yo,co,ko,wo)},
        'wrist_removed_mm3':wrist_initial-w.bRepBodies.item(0).volume*1000,
        'brush_axis_mm':[cx,cy], 'sensor_translation_mm':[48,0,15], 'sensor_before_transform':sensor_before,
        'sensor_after_transform':list(cell.transform2.asArray()),'carrier_height_mm':33,'cartridge_length_mm':24,
        'brush_stop_z_mm':30.5,'cartridge_cap_top_z_mm':32.5,'suspended_upper_plate_z_mm':33.5,
        'suppressed_legacy_joints':suppressed,'timeline_future_count':d.timeline.count-d.timeline.markerPosition}
with open(root+'/output/v5/created.json','w',encoding='utf-8') as f: json.dump(report,f,ensure_ascii=False,indent=2)
app.activeViewport.refresh()
print(json.dumps(report,ensure_ascii=False,indent=2))
