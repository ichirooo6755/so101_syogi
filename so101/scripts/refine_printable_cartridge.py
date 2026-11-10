"""Replace only the cartridge created in this task with a flat-bottom FDM part."""
import adsk.core
import adsk.fusion
import math
d=adsk.fusion.Design.cast(app.activeProduct)
r=d.rootComponent
assert d.attributes.itemByName('so101_calligraphy','holder_v2')
old=r.occurrences.itemByName('Brush_Cartridge_15mm:1')
assert old and old.component.bRepBodies.count==1
j=r.asBuiltJoints.itemByName('Cartridge_to_receiver')
if j: assert j.deleteMe()
assert old.deleteMe()
o=r.occurrences.addNewComponent(adsk.core.Matrix3D.create())
c=o.component; c.name='Brush_Cartridge_15mm'
y=d.userParameters.itemByName('sc_brush_axis_y').value*10
vi=adsk.core.ValueInput.createByString
NEW=adsk.fusion.FeatureOperations.NewBodyFeatureOperation
JOIN=adsk.fusion.FeatureOperations.JoinFeatureOperation
CUT=adsk.fusion.FeatureOperations.CutFeatureOperation
def plane(z):
    pi=c.constructionPlanes.createInput(); pi.setByOffset(c.xYConstructionPlane,vi(f'{z} mm'))
    p=c.constructionPlanes.add(pi); p.isLightBulbOn=False
    return p
def sk(z,name):
    s=c.sketches.add(plane(z)); s.name=name
    return s
def circle(s,x,cy,expr):
    center=adsk.core.Point3D.create(x/10,cy/10,0)
    circ=s.sketchCurves.sketchCircles.addByCenterRadius(center,d.unitsManager.evaluateExpression(expr,'mm')/2)
    circ.centerSketchPoint.isFixed=True
    dim=s.sketchDimensions.addDiameterDimension(circ,adsk.core.Point3D.create(center.x+1,center.y+0.4,0)); dim.parameter.expression=expr
def polygon(s,points):
    for a,b in zip(points,points[1:]+points[:1]):
        line=s.sketchCurves.sketchLines.addByTwoPoints(adsk.core.Point3D.create(a[0]/10,a[1]/10,0),adsk.core.Point3D.create(b[0]/10,b[1]/10,0)); line.isFixed=True
def extrude(s,length,op,name):
    profiles=adsk.core.ObjectCollection.create()
    for p in s.profiles: profiles.add(p)
    inp=c.features.extrudeFeatures.createInput(profiles,op)
    inp.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(vi(length)),adsk.fusion.ExtentDirections.PositiveExtentDirection)
    if op!=NEW: inp.participantBodies=[c.bRepBodies.item(0)]
    f=c.features.extrudeFeatures.add(inp); f.name=name; s.isVisible=False
    assert int(f.healthState)==0,(name,f.errorOrWarningMessage)
    return f
s=sk(8.5,'Flat_bottom_cartridge_flange'); circle(s,50,y,'brush_flange_od')
extrude(s,'brush_flange_thickness',NEW,'Flat_printing_flange')
for sign in (-1,1):
    s=sk(8.5,'Cartridge_retention_ear_'+str(sign))
    ymin,ymax=(y+13,y+26) if sign>0 else (y-26,y-13)
    polygon(s,[(44,ymin),(56,ymin),(56,ymax),(44,ymax)])
    extrude(s,'brush_flange_thickness',JOIN,'Cartridge_ear_'+str(sign))
s=sk(8.5,'Cartridge_common_22mm_interface'); circle(s,50,y,'brush_cartridge_od')
extrude(s,'brush_sleeve_length',JOIN,'Cartridge_vertical_sleeve')
s=sk(8.5,'Cartridge_glue_bore'); circle(s,50,y,'brush_cartridge_id')
extrude(s,'brush_sleeve_length',CUT,'Cartridge_parameterized_bore')
s=sk(8.5,'Cartridge_2xM3');
for sign in (-1,1): circle(s,50,y+sign*20,'sc_screw_clearance')
extrude(s,'brush_flange_thickness',CUT,'Cartridge_M3_clearance')
for z in (8.5,42.5):
    s=sk(z,'Brush_centering_land_fill'); circle(s,50,y,'brush_cartridge_od')
    extrude(s,'2 mm',JOIN,'Brush_centering_land')
    s=sk(z,'Brush_centering_land_bore'); circle(s,50,y,'brush_guide_dia')
    extrude(s,'2 mm',CUT,'Brush_non_clamping_centering_guide')
for z in (14.5,35):
    pi=c.constructionPlanes.createInput(); pi.setByOffset(c.yZConstructionPlane,vi('37 mm'))
    p=c.constructionPlanes.add(pi); p.isLightBulbOn=False
    s=c.sketches.add(p); s.name='Hot_glue_key_windows_'+str(z)
    points=[(37,y-2.5,z),(37,y+2.5,z),(37,y+2.5,z+5),(37,y-2.5,z+5)]
    for a,b in zip(points,points[1:]+points[:1]):
        line=s.sketchCurves.sketchLines.addByTwoPoints(s.modelToSketchSpace(adsk.core.Point3D.create(*(v/10 for v in a))),s.modelToSketchSpace(adsk.core.Point3D.create(*(v/10 for v in b)))); line.isFixed=True
    extrude(s,'26 mm',CUT,'Hot_glue_through_keys_'+str(z))
c.bRepBodies.item(0).name='Brush_Cartridge_15mm_FDM'
inp=r.asBuiltJoints.createInput(r.occurrences.itemByName('Brush_Load_Carrier:1'),o,None); inp.setAsRigidJointMotion()
j=r.asBuiltJoints.add(inp); j.name='Cartridge_to_receiver'; j.isLightBulbOn=False
print('Printable cartridge complete: flat flange bottom Z=8.5 mm, sleeve top Z=44.5 mm; four glue keys and two slip guides')
