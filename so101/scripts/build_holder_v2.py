"""Reinforce the existing FDM base and add a bolted, hot-glued brush cartridge.
All engineering dimensions below are mm. Printed parts have no tapped threads.
"""
import adsk.core
import adsk.fusion
import json
import math

d=adsk.fusion.Design.cast(app.activeProduct)
r=d.rootComponent
assert app.activeDocument.name=='so101書道'
assert d.attributes.itemByName('so101_calligraphy','holder_v2') is None
yoke=r.occurrences.itemByName('部品１:1')
cell=r.occurrences.itemByName('SC616C_1kg_Fusion:1')
sensor_o=next(o for o in r.allOccurrences if o.fullPathName.startswith(cell.name+'+') and o.bRepBodies.count)
sensor=sensor_o.bRepBodies.item(0)
before_matrix=list(cell.transform2.asArray())
if d.snapshots.hasPendingSnapshot: d.snapshots.add()
vi=adsk.core.ValueInput.createByString
JOIN=adsk.fusion.FeatureOperations.JoinFeatureOperation
NEW=adsk.fusion.FeatureOperations.NewBodyFeatureOperation
CUT=adsk.fusion.FeatureOperations.CutFeatureOperation
def param(name,expression,description):
    p=d.userParameters.itemByName(name)
    if p: p.expression=expression
    else: p=d.userParameters.add(name,vi(expression),'mm',description)
    return p

# Use the current opposite outer arm faces, retaining the user's new edits.
arm_y=[]
for face in yoke.bRepBodies.item(0).faces:
    g=face.geometry
    if isinstance(g,adsk.core.Plane) and abs(g.normal.y)>.99 and face.boundingBox.maxPoint.z*10>40 and face.area*100>100:
        arm_y.append(g.origin.y*10)
brush_y=(min(arm_y)+max(arm_y))/2
free_holes=sorted([f.geometry.origin.y*10 for f in sensor.faces
    if isinstance(f.geometry,adsk.core.Cylinder) and abs(f.geometry.radius*10-1.5)<1e-5 and abs(f.geometry.axis.z)>.99])[:2]
free_y=sum(free_holes)/2
param('sc_mount_thickness','10 mm','Reinforced fixed base, including 6.8 mm material above head recess')
param('brush_dia','15 mm','Change this value to regenerate cartridge bore and guides; 8-17 mm with the standard interface')
param('brush_glue_allowance','1.0 mm','Diametral allowance for hot glue around brush')
param('brush_cartridge_od','22 mm','Fixed interchangeable interface; 3 mm wall at 15 mm brush, 2 mm wall at 17 mm brush')
param('brush_cartridge_id','brush_dia + brush_glue_allowance','Nominal brush bore')
param('brush_fit_clearance','0.6 mm','Diametral printed sliding clearance')
param('brush_receiver_id','brush_cartridge_od + brush_fit_clearance','Receiver bore for removable cartridge')
param('brush_receiver_od','brush_cartridge_od + 10 mm','Receiver outside diameter')
param('brush_flange_od','brush_cartridge_od + 8 mm','Cartridge load-bearing flange diameter')
param('brush_sleeve_length','36 mm','Length of replaceable glued brush sleeve')
param('brush_receiver_thickness','6 mm','Receiver load plate thickness')
param('brush_flange_thickness','4 mm','Cartridge flange thickness')
param('brush_nut_af','5.8 mm','M3 standard hex nut pocket across flats, including print clearance')
param('brush_nut_depth','2.6 mm','M3 nut pocket depth')
param('sc_brush_axis_x','50 mm','Brush passes beside the sensor, not through its solid aluminium body')
param('sc_brush_axis_y',f'{brush_y:.9f} mm','Mid-plane between current outer fork-arm faces')

def native(comp,world):
    p=adsk.core.Point3D.create(*(n/10 for n in world))
    if comp==yoke.component:
        inv=yoke.transform2.copy(); inv.invert(); p.transformBy(inv)
    return p

def plane(comp,name,kind,coord):
    source=comp.xYConstructionPlane if kind=='XY' else comp.yZConstructionPlane
    if comp==yoke.component:
        value=native(comp,(0,0,coord)).z*10 if kind=='XY' else native(comp,(coord,0,0)).x*10
    else: value=coord
    inp=comp.constructionPlanes.createInput()
    inp.setByOffset(source,vi(f'{value:.10f} mm'))
    pl=comp.constructionPlanes.add(inp); pl.name=name; pl.isLightBulbOn=False
    return pl

def sketch(comp,name,kind,coord):
    sk=comp.sketches.add(plane(comp,name+'_plane',kind,coord)); sk.name=name
    return sk

def polygon(sk,comp,points):
    for a,b in zip(points,points[1:]+points[:1]):
        line=sk.sketchCurves.sketchLines.addByTwoPoints(sk.modelToSketchSpace(native(comp,a)),sk.modelToSketchSpace(native(comp,b)))
        line.isFixed=True

def circle(sk,comp,x,y,z,diameter):
    p=sk.modelToSketchSpace(native(comp,(x,y,z)))
    value=d.unitsManager.evaluateExpression(diameter,'mm')
    c=sk.sketchCurves.sketchCircles.addByCenterRadius(p,value/2)
    c.centerSketchPoint.isFixed=True
    dim=sk.sketchDimensions.addDiameterDimension(c,adsk.core.Point3D.create(p.x+0.9,p.y+0.2,0))
    dim.parameter.expression=diameter
    return c

def extrude(comp,sk,length,op,name,positive=True):
    profiles=adsk.core.ObjectCollection.create()
    for p in sk.profiles: profiles.add(p)
    inp=comp.features.extrudeFeatures.createInput(profiles,op)
    extent=adsk.fusion.DistanceExtentDefinition.create(vi(length))
    direction=adsk.fusion.ExtentDirections.PositiveExtentDirection if positive else adsk.fusion.ExtentDirections.NegativeExtentDirection
    inp.setOneSideExtent(extent,direction)
    if op!=NEW: inp.participantBodies=[comp.bRepBodies.item(0)]
    f=comp.features.extrudeFeatures.add(inp); f.name=name; sk.isVisible=False
    assert int(f.healthState)==0, (name,f.errorOrWarningMessage)
    return f

def box(comp,name,x0,x1,y0,y1,z,height,op=JOIN):
    sk=sketch(comp,name,'XY',z)
    polygon(sk,comp,[(x0,y0,z),(x1,y0,z),(x1,y1,z),(x0,y1,z)])
    return extrude(comp,sk,f'{height} mm',op,name)

# A continuous underside rib brings load back into the original wall and
# remains beside the flexure, clear of both fixed-end screw access holes.
yc=yoke.component
rib_x=17.8773715053
sk=sketch(yc,'FDM_fixed_base_gusset','YZ',rib_x)
polygon(sk,yc,[(rib_x,18.46294620236,4.5),(rib_x,39.46294620236,14.5),(rib_x,18.46294620236,14.5)])
extrude(yc,sk,f'{24-rib_x:.10f} mm',JOIN,'FDM_fixed_base_continuous_gusset')
yc.bRepBodies.item(0).name='SO101_Yoke_SC616C_Reinforced'

# Separate moving-side carrier: it touches only the sensor's low-Y end.
carrier_o=r.occurrences.addNewComponent(adsk.core.Matrix3D.create())
carrier=carrier_o.component; carrier.name='Brush_Load_Carrier'
box(carrier,'Carrier_lower_bridge',24,50,free_y-11,free_y+11,18.5,3,NEW)
box(carrier,'Carrier_free_end_contact',24,50,free_y-9.5,free_y+8.2,21.5,3)
sk=sketch(carrier,'Receiver_load_plate','XY',12.5)
circle(sk,carrier,50,brush_y,12.5,'brush_receiver_od')
extrude(carrier,sk,'brush_receiver_thickness',JOIN,'Receiver_load_plate')
for sign in (-1,1):
    y=brush_y+sign*20
    box(carrier,'Receiver_M3_ear_'+str(sign),44,56,y-6,y+6,12.5,6)

for sign in (-1,1):
    y=free_y+sign*9-1.5
    # A YZ/XZ helper is unnecessary: model this triangular rib on an XZ
    # construction plane derived from a vertical rectangle sketch plane.
    inp=carrier.constructionPlanes.createInput()
    # Positive extrusion of this Fusion construction plane goes toward +Y.
    inp.setByOffset(carrier.xZConstructionPlane,vi(f'{-y:.10f} mm'))
    pl=carrier.constructionPlanes.add(inp); pl.name='Carrier_rib_plane'; pl.isLightBulbOn=False
    sk=carrier.sketches.add(pl); sk.name='Carrier_rib_'+str(sign)
    polygon(sk,carrier,[(26,y,18.5),(40,y,12.5),(40,y,18.5)])
    extrude(carrier,sk,'3 mm',JOIN,'Carrier_triangular_rib_'+str(sign),True)

# Bore is cut through both the load plate and the upper bridge so the
# removable cartridge can pass through without an unintended hard contact.
sk=sketch(carrier,'Receiver_cartridge_bore','XY',12.5)
circle(sk,carrier,50,brush_y,12.5,'brush_receiver_id')
extrude(carrier,sk,'12 mm',CUT,'Receiver_sliding_fit')
sk=sketch(carrier,'Free_end_2xM3','XY',18.5)
for y in free_holes: circle(sk,carrier,30,y,18.5,'sc_screw_clearance')
extrude(carrier,sk,'6 mm',CUT,'Free_end_M3_through')
sk=sketch(carrier,'Free_end_2xM3_heads','XY',18.5)
for y in free_holes: circle(sk,carrier,30,y,18.5,'sc_head_dia')
extrude(carrier,sk,'sc_head_depth',CUT,'Free_end_M3_socket_recess')

# Nut pockets open upward; screws enter from below through the cartridge.
sk=sketch(carrier,'Cartridge_retention_2xM3','XY',12.5)
for sign in (-1,1): circle(sk,carrier,50,brush_y+sign*20,12.5,'sc_screw_clearance')
extrude(carrier,sk,'6 mm',CUT,'Cartridge_retention_M3_through')
sk=sketch(carrier,'M3_captive_hex_nuts','XY',18.5)
hex_radius=5.8/math.sqrt(3)
for sign in (-1,1):
    y=brush_y+sign*20
    polygon(sk,carrier,[(50+hex_radius*math.cos(i*math.pi/3),y+hex_radius*math.sin(i*math.pi/3),18.5) for i in range(6)])
extrude(carrier,sk,'brush_nut_depth',CUT,'M3_captive_nut_pockets',False)
carrier.bRepBodies.item(0).name='Brush_Load_Carrier_FDM'

# Cartridge: a removable rigid sleeve. Hot glue keys through four side
# windows; no slit, collet, pinch screw, or printed female thread is used.
cartridge_o=r.occurrences.addNewComponent(adsk.core.Matrix3D.create())
cartridge=cartridge_o.component; cartridge.name='Brush_Cartridge_15mm'
sk=sketch(cartridge,'Brush_sleeve_OD','XY',-5.5)
circle(sk,cartridge,50,brush_y,-5.5,'brush_cartridge_od')
extrude(cartridge,sk,'brush_sleeve_length',NEW,'Brush_sleeve')
sk=sketch(cartridge,'Brush_cartridge_load_flange','XY',8.5)
circle(sk,cartridge,50,brush_y,8.5,'brush_flange_od')
extrude(cartridge,sk,'brush_flange_thickness',JOIN,'Brush_load_flange')
for sign in (-1,1):
    y=brush_y+sign*20
    box(cartridge,'Brush_flange_ear_'+str(sign),44,56,y-7,y+6,8.5,4)
sk=sketch(cartridge,'Brush_hot_glue_bore','XY',-5.5)
circle(sk,cartridge,50,brush_y,-5.5,'brush_cartridge_id')
extrude(cartridge,sk,'brush_sleeve_length',CUT,'Brush_parameterized_bore')
sk=sketch(cartridge,'Brush_flange_2xM3','XY',8.5)
for sign in (-1,1): circle(sk,cartridge,50,brush_y+sign*20,8.5,'sc_screw_clearance')
extrude(cartridge,sk,'brush_flange_thickness',CUT,'Brush_flange_M3_clearance')
for z0 in (0.5,21.0):
    sk=sketch(cartridge,'Hot_glue_key_windows_'+str(z0),'YZ',37)
    polygon(sk,cartridge,[(37,brush_y-2.5,z0),(37,brush_y+2.5,z0),(37,brush_y+2.5,z0+5),(37,brush_y-2.5,z0+5)])
    extrude(cartridge,sk,'26 mm',CUT,'Hot_glue_mechanical_key_'+str(z0))
cartridge.bRepBodies.item(0).name='Brush_Cartridge_15mm_FDM'

for a,b,name in ((cell,carrier_o,'Free_end_to_carrier'),(carrier_o,cartridge_o,'Cartridge_to_receiver')):
    inp=r.asBuiltJoints.createInput(a,b,None); inp.setAsRigidJointMotion()
    j=r.asBuiltJoints.add(inp); j.name=name; j.isLightBulbOn=False
assert max(abs(a-b) for a,b in zip(before_matrix,list(cell.transform2.asArray())))<1e-8
d.attributes.add('so101_calligraphy','holder_v2','reinforced base; bolted hot-glue cartridge; no brush clamp; PETG/PLA')
report={'brush_axis_mm':[50,brush_y],'current_arm_outer_faces_y_mm':[min(arm_y),max(arm_y)],
 'free_end_holes_y_mm':free_holes,'sensor_transform':before_matrix,
 'fixed_support_mm':10,'fixed_M3_screw':'M3x12, 5.2 mm nominal engagement',
 'moving_M3_screw':'M3x8, 5.2 mm nominal engagement',
 'cartridge_screws':'2x M3x10 + 2x standard M3 hex nuts',
 'cartridge_bore_mm':16,'cartridge_OD_mm':22,'receiver_ID_mm':22.6,
 'free_end_contact_limit_y_mm':free_y+8.2,
 'glue':'hot glue through four 5x5 mm key windows',
 'part_volumes_mm3':{c.name:c.bRepBodies.item(0).volume*1000 for c in (yc,carrier,cartridge)}}
with open('/Users/sugawaraichirou/Documents/ChatGPT/so101/tmp/holder_v2_created.json','w') as f: json.dump(report,f,ensure_ascii=False,indent=2)
camera=app.activeViewport.camera; camera.viewOrientation=adsk.core.ViewOrientations.IsoTopRightViewOrientation; camera.isFitView=True
app.activeViewport.camera=camera; app.activeViewport.refresh()
print(json.dumps(report,ensure_ascii=False,indent=2))
