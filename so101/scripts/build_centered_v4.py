"""Centered brush load path; preserve the user's base, cell pose and old parts."""
import adsk.core
import adsk.fusion
import json
import math

root='/Users/sugawaraichirou/Documents/ChatGPT/so101'
doc=app.activeDocument; d=adsk.fusion.Design.cast(app.activeProduct); r=d.rootComponent
assert doc.name=='so101書道'
assert not d.attributes.itemByName('so101_calligraphy','centered_v4')
assert not r.occurrences.itemByName('Brush_Load_Carrier_Centered:1')
old_carrier=r.occurrences.itemByName('Brush_Load_Carrier:1')
old_cartridge=r.occurrences.itemByName('Brush_Cartridge_15mm:1')
cell=r.occurrences.itemByName('SC616C_1kg_Fusion:1')
base=r.occurrences.itemByName('部品１:1')
cell_transform=list(cell.transform2.asArray())
base_volume=base.bRepBodies.item(0).volume
if d.snapshots.hasPendingSnapshot:
    snapshot=d.snapshots.add(); snapshot.name='V4_preserve_current_user_placement'
vi=adsk.core.ValueInput.createByString
NEW=adsk.fusion.FeatureOperations.NewBodyFeatureOperation
JOIN=adsk.fusion.FeatureOperations.JoinFeatureOperation
CUT=adsk.fusion.FeatureOperations.CutFeatureOperation
cx=30.; cy=d.userParameters.itemByName('sc_brush_axis_y').value*10
flange_z=-26.5; receiver_z=-22.5; receiver_top=-16.5; sleeve_top=9.5
def param(name,expr,comment):
    existing=d.userParameters.itemByName(name)
    if existing:
        existing.expression=expr
        return existing
    return d.userParameters.add(name,vi(expr),'mm',comment)
param('centered_brush_axis_x','30 mm','V4 brush axis on the SC616C longitudinal center plane; previous 50 mm')
param('centered_brush_axis_y','sc_brush_axis_y','Retains the existing midpoint between the fork arms')
param('centered_receiver_z','-22.5 mm','V4 receiver underside; down 35 mm from the old receiver')
param('centered_cartridge_flange_z','centered_receiver_z - brush_flange_thickness','V4 sleeve flange underside')
param('centered_brush_stop_z','7.5 mm','Brush butt stop; prevents the brush from touching the load cell')
param('centered_brush_cap_thickness','2 mm','Closed upper cap transfers axial brush force to moving carrier only')

def sketch(c,name,z,kind='XY',x=None):
    source=c.xYConstructionPlane if kind=='XY' else c.yZConstructionPlane
    value=z if kind=='XY' else x
    pi=c.constructionPlanes.createInput(); pi.setByOffset(source,vi(f'{value:.10f} mm'))
    pl=c.constructionPlanes.add(pi); pl.name=name+'_plane'; pl.isLightBulbOn=False
    sk=c.sketches.add(pl); sk.name=name
    return sk
def polygon(sk,points):
    for a,b in zip(points,points[1:]+points[:1]):
        aa=sk.modelToSketchSpace(adsk.core.Point3D.create(*(v/10 for v in a)))
        bb=sk.modelToSketchSpace(adsk.core.Point3D.create(*(v/10 for v in b)))
        line=sk.sketchCurves.sketchLines.addByTwoPoints(aa,bb); line.isFixed=True
def circle(sk,x,y,z,expr):
    p=sk.modelToSketchSpace(adsk.core.Point3D.create(x/10,y/10,z/10))
    curve=sk.sketchCurves.sketchCircles.addByCenterRadius(p,d.unitsManager.evaluateExpression(expr,'mm')/2)
    curve.centerSketchPoint.isFixed=True
    dim=sk.sketchDimensions.addDiameterDimension(curve,adsk.core.Point3D.create(p.x+.7,p.y+.3,0)); dim.parameter.expression=expr
def extrude(c,sk,depth,op,name,up=True):
    profiles=adsk.core.ObjectCollection.create()
    for p in sk.profiles: profiles.add(p)
    ei=c.features.extrudeFeatures.createInput(profiles,op)
    direction=adsk.fusion.ExtentDirections.PositiveExtentDirection if up else adsk.fusion.ExtentDirections.NegativeExtentDirection
    ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(vi(depth)),direction)
    if op!=NEW: ei.participantBodies=[c.bRepBodies.item(0)]
    f=c.features.extrudeFeatures.add(ei); f.name=name; sk.isVisible=False
    assert int(f.healthState)==0,(name,f.errorOrWarningMessage)
    return f
def box(c,name,x0,x1,y0,y1,z,depth,op=JOIN):
    sk=sketch(c,name,z)
    polygon(sk,[(x0,y0,z),(x1,y0,z),(x1,y1,z),(x0,y1,z)])
    return extrude(c,sk,depth,op,name)

# Keep the exact current user-edited upper sensor seat and its insertion guides.
# Lower nut interface and old offset receiver are intentionally not copied.
tmp=adsk.fusion.TemporaryBRepManager.get()
upper=tmp.copy(old_carrier.bRepBodies.item(0))
clip=tmp.createBox(adsk.core.OrientedBoundingBox3D.create(adsk.core.Point3D.create(3.0,.046294620236,2.45),
    adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),1.2,1.8,1.2))
assert tmp.booleanOperation(upper,clip,adsk.fusion.BooleanTypes.IntersectionBooleanType)
assert upper.volume>.5,upper.volume
carrier_o=r.occurrences.addNewComponent(adsk.core.Matrix3D.create()); c=carrier_o.component
c.name='Brush_Load_Carrier_Centered'
bf=c.features.baseFeatures.add(); bf.name='V4_preserved_user_free_end_seat'
assert bf.startEdit()
body=c.bRepBodies.add(upper,bf)
assert body and bf.finishEdit()
# A symmetric lower yoke supports a ring on the cell's X=30 mm load plane.
box(c,'V4_symmetric_upper_bridge',24,36,cy-14.5,cy+14.5,18.5,'3 mm')
for sign in (-1,1):
    y0,y1=(cy-14.5,cy-12) if sign<0 else (cy+12,cy+14.5)
    box(c,'V4_centered_vertical_web_'+str(sign),24,36,y0,y1,receiver_top,'35 mm')
sk=sketch(c,'V4_centered_receiver_ring',receiver_z); circle(sk,cx,cy,receiver_z,'brush_receiver_od')
extrude(c,sk,'brush_receiver_thickness',JOIN,'V4_centered_load_ring')
for sign in (-1,1):
    y=cy+sign*20
    box(c,'V4_retention_ear_'+str(sign),24,36,y-6,y+6,receiver_z,'brush_receiver_thickness')
sk=sketch(c,'V4_receiver_slip_bore',receiver_z); circle(sk,cx,cy,receiver_z,'brush_receiver_id')
extrude(c,sk,'6 mm',CUT,'V4_receiver_slip_bore')
# Re-open all sensor bolt access after joining the new symmetric bridge.
free_y=(-2.4370537976399254,4.962946202360068)
for diam,depth,name in (('sc_screw_clearance','6 mm','through'),('sc_head_dia','sc_head_depth','head_recess')):
    sk=sketch(c,'V4_free_M3_'+name,18.5)
    for y in free_y: circle(sk,30,y,18.5,diam)
    extrude(c,sk,depth,CUT,'V4_free_M3_'+name)
sk=sketch(c,'V4_cartridge_2xM3_clearance',receiver_z)
for sign in (-1,1): circle(sk,cx,cy+sign*20,receiver_z,'sc_screw_clearance')
extrude(c,sk,'brush_receiver_thickness',CUT,'V4_cartridge_M3_through')
sk=sketch(c,'V4_2xM3_hex_nut_pockets',receiver_top)
radius=d.userParameters.itemByName('brush_nut_af').value*10/math.sqrt(3)
for sign in (-1,1):
    y=cy+sign*20
    polygon(sk,[(cx+radius*math.cos(i*math.pi/3),y+radius*math.sin(i*math.pi/3),receiver_top) for i in range(6)])
extrude(c,sk,'brush_nut_depth',CUT,'V4_M3_nut_pockets_AF5p8_depth2p6',False)
c.bRepBodies.item(0).name='Centered_Carrier_M3_Captive_Nuts_FDM'

# Rebuild the diameter-adjustable sleeve at the centered, lowered position.
# Its upper cap prevents the brush from creating a parallel load path.
cartridge_o=r.occurrences.addNewComponent(adsk.core.Matrix3D.create()); k=cartridge_o.component
k.name='Brush_Cartridge_Centered_15mm'
sk=sketch(k,'V4_cartridge_load_flange',flange_z); circle(sk,cx,cy,flange_z,'brush_flange_od')
extrude(k,sk,'brush_flange_thickness',NEW,'V4_flat_cartridge_flange')
for sign in (-1,1):
    y0,y1=(cy-26,cy-13) if sign<0 else (cy+13,cy+26)
    box(k,'V4_cartridge_flange_ear_'+str(sign),24,36,y0,y1,flange_z,'brush_flange_thickness')
sk=sketch(k,'V4_cartridge_OD',flange_z); circle(sk,cx,cy,flange_z,'brush_cartridge_od')
extrude(k,sk,'brush_sleeve_length',JOIN,'V4_cartridge_vertical_sleeve')
sk=sketch(k,'V4_brush_blind_bore',flange_z); circle(sk,cx,cy,flange_z,'brush_cartridge_id')
extrude(k,sk,'brush_sleeve_length - centered_brush_cap_thickness',CUT,'V4_parameterized_blind_bore')
for z in (flange_z,5.5):
    sk=sketch(k,'V4_centering_land_fill_'+str(z),z); circle(sk,cx,cy,z,'brush_cartridge_od')
    extrude(k,sk,'2 mm',JOIN,'V4_centering_land_'+str(z))
    sk=sketch(k,'V4_centering_land_bore_'+str(z),z); circle(sk,cx,cy,z,'brush_guide_dia')
    extrude(k,sk,'2 mm',CUT,'V4_non_clamping_brush_guide_'+str(z))
sk=sketch(k,'V4_cartridge_2xM3',flange_z)
for sign in (-1,1): circle(sk,cx,cy+sign*20,flange_z,'sc_screw_clearance')
extrude(k,sk,'brush_flange_thickness',CUT,'V4_cartridge_M3_clearance')
for z in (-20.5,0.):
    sk=sketch(k,'V4_hot_glue_keys_'+str(z),z,kind='YZ',x=17.)
    polygon(sk,[(17,cy-2.5,z),(17,cy+2.5,z),(17,cy+2.5,z+5),(17,cy-2.5,z+5)])
    extrude(k,sk,'26 mm',CUT,'V4_hot_glue_key_windows_'+str(z))
k.bRepBodies.item(0).name='Centered_15mm_Hot_Glue_Cartridge_With_Stop'
for a,b,name in ((cell,carrier_o,'V4_sensor_to_centered_carrier'),(carrier_o,cartridge_o,'V4_centered_cartridge_to_carrier')):
    ji=r.asBuiltJoints.createInput(a,b,None); ji.setAsRigidJointMotion()
    j=r.asBuiltJoints.add(ji); j.name=name; j.isLightBulbOn=False
assert max(abs(a-b) for a,b in zip(cell.transform2.asArray(),cell_transform))<1e-9
assert abs(base.bRepBodies.item(0).volume-base_volume)<1e-8
# Originals remain available and unmodified, but must not be printed/installed
# with the replacements. No existing part or feature is deleted.
old_carrier.isLightBulbOn=False; old_cartridge.isLightBulbOn=False
d.attributes.add('so101_calligraphy','centered_v4','Carrier X30; flange Z-26.5; centered nut cartridge; original base/cell preserved')
report={'carrier_occurrence':carrier_o.name,'cartridge_occurrence':cartridge_o.name,
    'brush_axis_mm':[cx,cy],'previous_brush_axis_mm':[50,cy],
    'previous_cartridge_flange_z_mm':8.5,'cartridge_flange_z_mm':flange_z,
    'cartridge_top_z_mm':sleeve_top,'brush_butt_stop_z_mm':7.5,
    'reference_shift_mm':[-20,0,-35],
    'nominal_torsional_eccentricity_mm':0.,'sensor_transform':cell_transform,
    'base_volume_mm3':base_volume*1000,'originals_preserved_hidden':[old_carrier.name,old_cartridge.name],
    'part_volumes_mm3':{o.name:o.bRepBodies.item(0).volume*1000 for o in (carrier_o,cartridge_o)}}
with open(root+'/tmp/v4_created.json','w',encoding='utf-8') as f: json.dump(report,f,ensure_ascii=False,indent=2)
app.activeViewport.refresh()
print(json.dumps(report,ensure_ascii=False,indent=2))
