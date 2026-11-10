"""Add the fixed-end mount at the user's current rollback position.

All coordinates are millimetres in the assembly reference frame. The load
cell rotation is preserved. Its low-Y end is reserved for the future brush.
"""
import adsk.core
import adsk.fusion
import json
import math

design=adsk.fusion.Design.cast(app.activeProduct)
root=design.rootComponent
assert app.activeDocument.name=='so101書道'
assert design.attributes.itemByName('so101_calligraphy','mount_created') is None, 'Mount already exists'
assert design.timeline.markerPosition==66, 'Reinspect the current timeline before editing'
yoke=root.occurrences.itemByName('部品１:1')
cell=root.occurrences.itemByName('SC616C_1kg_Fusion:1')
comp=yoke.component
body=comp.bRepBodies.item(0)
before_volume=body.volume*1000
before_rotation=list(cell.transform2.asArray())
start=design.timeline.markerPosition
if design.snapshots.hasPendingSnapshot:
    design.snapshots.add()
vi=adsk.core.ValueInput.createByString
params=design.userParameters

def parameter(name,expression,comment):
    p=params.itemByName(name)
    if p: p.expression=expression
    else: p=params.add(name,vi(expression),'mm',comment)
    return p

parameter('brush_dia','15 mm','Nominal replaceable brush diameter; brush holder is a later stage')
parameter('sc_hole_pitch','7.4 mm','SC616C PDF: two M3 holes per end, 7.4 +/- 0.1 mm')
parameter('sc_screw_clearance','3.4 mm','Printed base M3 clearance; sensor itself has M3 threaded holes')
parameter('sc_mount_thickness','6 mm','Fixed-end support thickness')
parameter('sc_head_dia','6.2 mm','Underside socket-head recess diameter')
parameter('sc_head_depth','3.2 mm','Underside socket-head recess depth; M3x8 gives 5.2 mm engagement')
parameter('sc_brush_axis_x','30 mm','Future brush axis, clear of the existing yoke wall')
center_y=(yoke.boundingBox.minPoint.y+yoke.boundingBox.maxPoint.y)*5
parameter('sc_brush_axis_y',f'{center_y:.9f} mm','Mid-plane between the existing yoke arms')

# Translate only: free-end M3-pair midpoint goes onto the yoke mid-plane.
matrix=adsk.core.Matrix3D.create()
matrix.setWithArray(before_rotation)
delta=adsk.core.Vector3D.create((30-24.5)/10,(center_y-1.8)/10,0)
t=matrix.translation
matrix.translation=adsk.core.Vector3D.create(t.x+delta.x,t.y+delta.y,t.z+delta.z)
cell.transform2=matrix
if design.snapshots.hasPendingSnapshot:
    design.snapshots.add()

inverse=yoke.transform2.copy()
inverse.invert()
def local_point(x,y,z):
    p=adsk.core.Point3D.create(x/10,y/10,z/10)
    p.transformBy(inverse)
    return p

top_z=24.5
top_local_z=local_point(0,0,top_z).z*10

def offset_plane(name,expression):
    inp=comp.constructionPlanes.createInput()
    inp.setByOffset(comp.xYConstructionPlane,vi(expression))
    p=comp.constructionPlanes.add(inp)
    p.name=name
    p.isLightBulbOn=False
    return p

top=offset_plane('SC616C_fixed_end_contact',f'{top_local_z:.10f} mm')
base=offset_plane('SC616C_screw_entry',f'{top_local_z:.10f} mm + sc_mount_thickness')

def sketch_point(sk,x,y,z): return sk.modelToSketchSpace(local_point(x,y,z))

def extrude(sk,expression,operation,name,positive=True):
    profiles=adsk.core.ObjectCollection.create()
    for p in sk.profiles: profiles.add(p)
    assert profiles.count>0
    inp=comp.features.extrudeFeatures.createInput(profiles,operation)
    extent=adsk.fusion.DistanceExtentDefinition.create(vi(expression))
    direction=adsk.fusion.ExtentDirections.PositiveExtentDirection if positive else adsk.fusion.ExtentDirections.NegativeExtentDirection
    inp.setOneSideExtent(extent,direction)
    inp.participantBodies=[body]
    f=comp.features.extrudeFeatures.add(inp)
    f.name=name
    sk.isVisible=False
    assert int(f.healthState)==0, f.errorOrWarningMessage
    return f

# An L-shaped footprint joins the existing wall, but reaches under only the
# high-Y fixed end. The web stays 1.5 mm beside the sensor's relieved section.
fixed_inner=center_y+25.7
fixed_outer=fixed_inner+7.4
pad_start=center_y+22.2
pad_end=center_y+38.2
web_start=center_y+17.2
x_join=yoke.boundingBox.maxPoint.x*10-2.0
footprint=[(x_join,web_start),(24,web_start),(24,pad_start),
           (36,pad_start),(36,pad_end),(x_join,pad_end)]
sk=comp.sketches.add(top)
sk.name='SC616C_fixed_end_support_outline'
for a,b in zip(footprint,footprint[1:]+footprint[:1]):
    line=sk.sketchCurves.sketchLines.addByTwoPoints(sketch_point(sk,*a,top_z),sketch_point(sk,*b,top_z))
    line.isFixed=True
extrude(sk,'sc_mount_thickness',adsk.fusion.FeatureOperations.JoinFeatureOperation,'SC616C_integral_fixed_end_support')

def screw_sketch(plane,name,z,diameter):
    sk=comp.sketches.add(plane)
    sk.name=name
    circles=[]
    for y in (fixed_inner,fixed_outer):
        c=sk.sketchCurves.sketchCircles.addByCenterRadius(sketch_point(sk,30,y,z),params.itemByName(diameter).value/2)
        c.centerSketchPoint.isFixed=True
        label=adsk.core.Point3D.create(c.centerSketchPoint.geometry.x+0.6,c.centerSketchPoint.geometry.y+0.2,0)
        dim=sk.sketchDimensions.addDiameterDimension(c,label)
        dim.parameter.expression=diameter
        circles.append(c)
    # The measured spacing is also exposed as a reference sketch dimension.
    dim=sk.sketchDimensions.addDistanceDimension(circles[0].centerSketchPoint,circles[1].centerSketchPoint,
        adsk.fusion.DimensionOrientations.AlignedDimensionOrientation,
        adsk.core.Point3D.create(circles[0].centerSketchPoint.geometry.x+0.9,circles[0].centerSketchPoint.geometry.y-0.3,0),False)
    return sk

sk=screw_sketch(top,'SC616C_2x_M3_clearance_7p4_pitch',top_z,'sc_screw_clearance')
extrude(sk,'sc_mount_thickness',adsk.fusion.FeatureOperations.CutFeatureOperation,'SC616C_2x_M3_through')
sk=screw_sketch(base,'SC616C_underside_head_recesses',top_z-6,'sc_head_dia')
extrude(sk,'sc_head_depth',adsk.fusion.FeatureOperations.CutFeatureOperation,'SC616C_2x_socket_head_recess',False)
body.name='SO101_Yoke_SC616C_Mount'

joint_input=root.asBuiltJoints.createInput(yoke,cell,None)
joint_input.setAsRigidJointMotion()
joint=root.asBuiltJoints.add(joint_input)
joint.name='SC616C_fixed_end_to_yoke'
joint.isLightBulbOn=False
end=design.timeline.markerPosition
group=design.timeline.timelineGroups.add(start,end-1)
group.name='SC616C_fixed_end_mount'
design.attributes.add('so101_calligraphy','mount_created','2026-10-21; fixed high-Y end; original rotation preserved')

after_rotation=list(cell.transform2.asArray())
rotation_indices=(0,1,2,4,5,6,8,9,10)
assert max(abs(after_rotation[i]-before_rotation[i]) for i in rotation_indices)<1e-10
assert comp.bRepBodies.count==1 and body.isSolid
report={
    'fixed_holes_world_mm':[[30,fixed_inner,top_z],[30,fixed_outer,top_z]],
    'future_brush_axis_mm':[30,center_y],
    'cell_translation_mm':[delta.x*10,delta.y*10,0],
    'rotation_unchanged':True,'mount_thickness_mm':6,
    'M3_clearance_mm':3.4,'head_recess_diameter_mm':6.2,'head_recess_depth_mm':3.2,
    'recommended_screw':'2x M3x8 socket head, 5.2 mm nominal engagement',
    'support_contact_y_mm':[pad_start,center_y+37.2],
    'central_web_side_clearance_mm':1.5,
    'future_15mm_brush_to_yoke_wall_mm':30-7.5-yoke.boundingBox.maxPoint.x*10,
    'body_volume_before_mm3':before_volume,'body_volume_after_mm3':body.volume*1000,
    'timeline_marker':design.timeline.markerPosition,'timeline_count':design.timeline.count,
}
# Account for the extended support in the final body bounding box: the old
# yoke wall used for brush clearance is retained as the pre-edit x=19.877 mm.
report['future_15mm_brush_to_original_yoke_wall_mm']=30-7.5-(x_join+2)
report.pop('future_15mm_brush_to_yoke_wall_mm')
with open('/Users/sugawaraichirou/Documents/ChatGPT/so101/tmp/sc616c_mount_created.json','w') as out:
    json.dump(report,out,ensure_ascii=False,indent=2)
app.activeViewport.refresh()
print(json.dumps(report,ensure_ascii=False,indent=2))
