import adsk.core
import adsk.fusion
import json

d=adsk.fusion.Design.cast(app.activeProduct)
r=d.rootComponent
assert app.activeDocument.name=='so101書道'
assert not d.attributes.itemByName('so101_calligraphy','slide_mount_v3')
yoke=r.occurrences.itemByName('部品１:1'); yc=yoke.component
carrier=r.occurrences.itemByName('Brush_Load_Carrier:1').component
cell=r.occurrences.itemByName('SC616C_1kg_Fusion:1')
before_transform=list(cell.transform2.asArray())
if d.snapshots.hasPendingSnapshot: d.snapshots.add()
vi=adsk.core.ValueInput.createByString
NEW=adsk.fusion.FeatureOperations.NewBodyFeatureOperation
JOIN=adsk.fusion.FeatureOperations.JoinFeatureOperation
CUT=adsk.fusion.FeatureOperations.CutFeatureOperation
fy=1.2629462023600713
fixed_y=fy+29.4
brush_y=d.userParameters.itemByName('sc_brush_axis_y').value*10
roof_start=fy+14.7
fixed_start=fy+22.2
rear_stop=fy+37.3
rear_end=rear_stop+3

def param(name,expression,comment):
    p=d.userParameters.itemByName(name)
    if p: p.expression=expression
    else: p=d.userParameters.add(name,vi(expression),'mm',comment)
    return p
param('sc_slide_width','10 mm','Nominal slide channel for SC616C width 9.0/9.3 mm')
param('sc_lid_flexure_gap','1.5 mm','Clearance above the central sensing section under the half-length cover')
param('sc_lid_top','35.4 mm','Top of removable fixed-end cover')
param('sc_lid_bolt_pitch','16 mm','Spacing between M3 cover screws')

def native(comp,xyz):
    p=adsk.core.Point3D.create(*(v/10 for v in xyz))
    if comp==yc:
        inv=yoke.transform2.copy(); inv.invert(); p.transformBy(inv)
    return p
def sketch(comp,name,z):
    offset=native(comp,(0,0,z)).z*10 if comp==yc else z
    inp=comp.constructionPlanes.createInput(); inp.setByOffset(comp.xYConstructionPlane,vi(f'{offset:.10f} mm'))
    pl=comp.constructionPlanes.add(inp); pl.name=name+'_plane'; pl.isLightBulbOn=False
    sk=comp.sketches.add(pl); sk.name=name
    return sk
def polygon(comp,sk,points):
    for a,b in zip(points,points[1:]+points[:1]):
        line=sk.sketchCurves.sketchLines.addByTwoPoints(sk.modelToSketchSpace(native(comp,a)),sk.modelToSketchSpace(native(comp,b))); line.isFixed=True
def circle(comp,sk,x,y,z,diameter):
    p=sk.modelToSketchSpace(native(comp,(x,y,z)))
    c=sk.sketchCurves.sketchCircles.addByCenterRadius(p,diameter/20); c.centerSketchPoint.isFixed=True
    dim=sk.sketchDimensions.addDiameterDimension(c,adsk.core.Point3D.create(p.x+0.7,p.y+0.3,0)); dim.parameter.expression=f'{diameter} mm'
def extrude(comp,sk,thickness,op,name,up=True):
    profiles=adsk.core.ObjectCollection.create()
    for p in sk.profiles: profiles.add(p)
    inp=comp.features.extrudeFeatures.createInput(profiles,op)
    # The existing yoke has its local Z axis pointing downward in assembly space.
    positive=not up if comp==yc else up
    direction=adsk.fusion.ExtentDirections.PositiveExtentDirection if positive else adsk.fusion.ExtentDirections.NegativeExtentDirection
    inp.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(vi(f'{thickness} mm')),direction)
    if op!=NEW: inp.participantBodies=[comp.bRepBodies.item(0)]
    f=comp.features.extrudeFeatures.add(inp); f.name=name; sk.isVisible=False
    assert int(f.healthState)==0,(name,f.errorOrWarningMessage)
    return f
def box(comp,name,x0,x1,y0,y1,z,thickness,op=JOIN):
    sk=sketch(comp,name,z)
    polygon(comp,sk,[(x0,y0,z),(x1,y0,z),(x1,y1,z),(x0,y1,z)])
    return extrude(comp,sk,thickness,op,name)

# Extend the existing fixed platform underneath the new outboard cover boss.
box(yc,'V3_fixed_platform_right_extension',35,42,fixed_start,rear_end,14.5,10)
box(yc,'V3_fixed_platform_rear_extension',23.5,42,fy+38.0,rear_end,14.5,10)
for x in (22,38):
    box(yc,'V3_lid_screw_boss_'+str(x),x-3,x+3,fixed_y-3,fixed_y+3,24.5,6)
for x0,x1 in ((23.5,25),(35,36.5)):
    box(yc,'V3_slide_entry_guide_'+str(x0),x0,x1,fy+23.2,fixed_y-3,24.5,6)
# Two separate rear stops leave a 7 mm wide cable opening between them.
for x0,x1 in ((25,26.5),(33.5,35)):
    box(yc,'V3_rear_stop_'+str(x0),x0,x1,rear_stop,rear_end,24.5,6)

# Convert only the cartridge retention interface to actual female threads.
# Sensor attachment holes remain clearance holes into the aluminium sensor.
for y in (brush_y-20,brush_y+20):
    box(carrier,'V3_replace_nut_pocket_'+str(y),46,54,y-4,y+4,12.5,6)

# The removable cover spans the fixed half. Its sensing-region underside is
# raised by 1.5 mm; the far fixed block alone gets a top contact surface.
lid_o=r.occurrences.addNewComponent(adsk.core.Matrix3D.create())
lid=lid_o.component; lid.name='SC616C_Slide_In_Top_Cover'
box(lid,'V3_half_length_cover_roof',18,42,roof_start,rear_end,32.0,3.4,NEW)
box(lid,'V3_fixed_end_top_seat',18,42,fixed_start,rear_end,30.5,1.5)
sk=sketch(lid,'V3_cover_M3_clearance',30.5)
for x in (22,38): circle(lid,sk,x,fixed_y,30.5,3.4)
extrude(lid,sk,4.9,CUT,'V3_cover_2xM3_clearance')
lid.bRepBodies.item(0).name='SC616C_Slide_In_Top_Cover_FDM'

# Pilot holes are cut from the accessible faces. The base blind holes are
# 8 mm deep; the cartridge's threaded holes pass through 6 mm of PETG/PLA.
for comp,points,z,depth,name in (
    (yc,[(22,fixed_y),(38,fixed_y)],30.5,8,'V3_cover_thread_pilots'),
    (carrier,[(50,brush_y-20),(50,brush_y+20)],18.5,6,'V3_cartridge_thread_pilots')):
    sk=sketch(comp,name,z)
    for x,y in points: circle(comp,sk,x,y,z,2.5)
    extrude(comp,sk,depth,CUT,name,False)

# Native modeled ISO M3x0.5 female threads, not display-only thread textures.
q=adsk.fusion.ThreadDataQuery.create(False)
thread_type=q.defaultMetricThreadType
thread_info=adsk.fusion.ThreadInfo.create(False,True,thread_type,'M3x0.5','6H',True)
threads=[]
for comp,name in ((yc,'V3_cover_M3x0p5_modeled'),(carrier,'V3_cartridge_M3x0p5_modeled')):
    faces=adsk.core.ObjectCollection.create()
    for f in comp.bRepBodies.item(0).faces:
        g=f.geometry
        if isinstance(g,adsk.core.Cylinder) and abs(g.radius*10-1.25)<1e-5:
            world=g.origin.copy()
            if comp==yc: world.transformBy(yoke.transform2)
            if comp==yc and abs(world.y*10-fixed_y)>1e-5: continue
            if comp==carrier and abs(world.x*10-50)>1e-5: continue
            faces.add(f)
    assert faces.count==2,(name,faces.count)
    inp=comp.features.threadFeatures.createInput(faces,thread_info)
    inp.isModeled=True; inp.isFullLength=True
    f=comp.features.threadFeatures.add(inp); f.name=name
    assert f.isModeled and int(f.healthState)==0
    threads.append({'name':name,'designation':f.threadInfo.threadDesignation,'class':f.threadInfo.threadClass,'is_modeled':f.isModeled})
joint_input=r.asBuiltJoints.createInput(yoke,lid_o,None); joint_input.setAsRigidJointMotion()
joint=r.asBuiltJoints.add(joint_input); joint.name='Slide_in_cover_to_fixed_base'; joint.isLightBulbOn=False
assert max(abs(a-b) for a,b in zip(before_transform,list(cell.transform2.asArray())))<1e-8
yc.bRepBodies.item(0).name='SO101_Yoke_SC616C_Slide_In_Base'
carrier.bRepBodies.item(0).name='Brush_Load_Carrier_M3_Threaded_FDM'
d.attributes.add('so101_calligraphy','slide_mount_v3','Half cover; M3 modeled female threads; central clearance 1.5 mm')
report={'fixed_boss_centers_mm':[[22,fixed_y],[38,fixed_y]],'slide_width_mm':10,
 'cell_width_max_mm':9.3,'cover_start_y_mm':roof_start,'fixed_top_contact_start_y_mm':fixed_start,
 'cover_end_y_mm':rear_end,'cover_top_z_mm':35.4,'central_underside_z_mm':32,'fixed_underside_z_mm':30.5,
 'central_top_gap_mm':1.5,'rear_stop_y_mm':rear_stop,'nominal_rear_end_clearance_mm':0.1,
 'cover_screws':'2x M3x10, nominal 5.1 mm engagement in printed base',
 'cartridge_screws':'2x M3x10, 6 mm engagement, metal nuts no longer used',
 'threads':threads,'sensor_transform':before_transform,
 'part_volumes_mm3':{o.name:o.bRepBodies.item(0).volume*1000 for o in (yoke,r.occurrences.itemByName('Brush_Load_Carrier:1'),r.occurrences.itemByName('Brush_Cartridge_15mm:1'),lid_o)}}
with open('/Users/sugawaraichirou/Documents/ChatGPT/so101/tmp/v3_created.json','w') as f: json.dump(report,f,ensure_ascii=False,indent=2)
app.activeViewport.refresh()
print(json.dumps(report,ensure_ascii=False,indent=2))
