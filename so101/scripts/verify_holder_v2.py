import adsk.core
import adsk.fusion
import itertools
import math
import json
import os
d=adsk.fusion.Design.cast(app.activeProduct)
r=d.rootComponent
names=('部品１:1','Brush_Load_Carrier:1','Brush_Cartridge_15mm:1')
occs=[r.occurrences.itemByName(n) for n in names]
assert all(occs)
bodies=[o.bRepBodies.item(0) for o in occs]
sensor_o=next(o for o in r.allOccurrences if o.fullPathName.startswith('SC616C_1kg_Fusion:1+') and o.bRepBodies.count)
sensor=sensor_o.bRepBodies.item(0)
def cylinders(body,diameter,x=None):
    result=[]
    for f in body.faces:
        g=f.geometry
        if isinstance(g,adsk.core.Cylinder) and abs(g.axis.z)>.99 and abs(g.radius*20-diameter)<1e-5 and (x is None or abs(g.origin.x*10-x)<1e-5):
            result.append({'x':g.origin.x*10,'y':g.origin.y*10,'z':[f.boundingBox.minPoint.z*10,f.boundingBox.maxPoint.z*10],'diameter':g.radius*20})
    return sorted(result,key=lambda a:a['y'])
def near(a,b): assert abs(a-b)<1e-5,(a,b)
fixed=cylinders(bodies[0],3.4,30); free=cylinders(bodies[1],3.4,30)
fixed_heads=cylinders(bodies[0],6.2,30); free_heads=cylinders(bodies[1],6.2,30)
sensor_holes=cylinders(sensor,3)
assert len(fixed)==len(free)==len(fixed_heads)==len(free_heads)==2
for group,expected in ((fixed,sensor_holes[2:]),(free,sensor_holes[:2])):
    for a,b in zip(group,expected): near(a['x'],b['x']); near(a['y'],b['y'])
    near(group[1]['y']-group[0]['y'],7.4)
for h in fixed_heads: near(h['z'][0],14.5); near(h['z'][1],17.7)
for h in free_heads: near(h['z'][0],18.5); near(h['z'][1],21.7)
near(24.5-fixed_heads[0]['z'][1],6.8)
near(24.5-free_heads[0]['z'][1],2.8)
retention=cylinders(bodies[1],3.4,50); flange_holes=cylinders(bodies[2],3.4,50)
assert len(retention)==len(flange_holes)==2
for a,b in zip(retention,flange_holes):
    near(a['x'],b['x']); near(a['y'],b['y']); near(a['z'][0],12.5); near(b['z'][0],8.5); near(b['z'][1],12.5)
near(retention[1]['y']-retention[0]['y'],40)
cy=d.userParameters.itemByName('sc_brush_axis_y').value*10
with open('/Users/sugawaraichirou/Documents/ChatGPT/so101/tmp/holder_v2_created.json') as f: created=json.load(f)
near(cy,sum(created['current_arm_outer_faces_y_mm'])/2)
assert all(o.component.bRepBodies.count==1 and b.isSolid for o,b in zip(occs,bodies))

# Verify that only the cartridge's bore/lands change; the interchange diameter
# stays 22 mm so existing rigid receiver hardware need not be reprinted.
sweep=[]
p=d.userParameters.itemByName('brush_dia')
try:
    for dia in (12,17):
        p.expression=f'{dia} mm'
        d.computeAll()
        b=occs[2].bRepBodies.item(0)
        assert cylinders(b,dia+1) and len(cylinders(b,dia+0.4))==2
        assert cylinders(b,22)
        assert cylinders(occs[1].bRepBodies.item(0),22.6)
        sweep.append({'brush_diameter_mm':dia,'glue_bore_mm':dia+1,'guide_bore_mm':dia+0.4,'cartridge_od_mm':22})
finally:
    p.expression='15 mm'
    d.computeAll()
bodies=[o.bRepBodies.item(0) for o in occs]
assert cylinders(bodies[2],16) and len(cylinders(bodies[2],15.4))==2

entities=adsk.core.ObjectCollection.create()
for b in bodies+[sensor]: entities.add(b)
inp=d.createInterferenceInput(entities); inp.areCoincidentFacesIncluded=False
interference=d.analyzeInterference(inp)
assert interference is not None and interference.count==0, interference.count
tmp=adsk.fusion.TemporaryBRepManager.get()
def removed_volume(body,tool):
    candidate=tmp.copy(body); before=candidate.volume
    assert tmp.booleanOperation(candidate,tool,adsk.fusion.BooleanTypes.DifferenceBooleanType)
    return (before-candidate.volume)*1000
def cylinder(x,y,z0,z1,diam):
    return tmp.createCylinderOrCone(adsk.core.Point3D.create(x/10,y/10,z0/10),diam/20,adsk.core.Point3D.create(x/10,y/10,z1/10),diam/20)

# A 5.6 mm head can be inserted vertically from below every sensor fastener.
head_access=[]
for label,group,top in (('fixed',fixed,17.7),('free',free,21.7),('cartridge',flange_holes,8.5)):
    for h in group:
        tool=cylinder(h['x'],h['y'],-20,top,5.6)
        volumes=[removed_volume(b,tool) for b in bodies]
        assert max(abs(v) for v in volumes)<1e-4,(label,h,volumes)
        head_access.append({'interface':label,'x':h['x'],'y':h['y'],'head_insertion_clear':True})

# Axial brush clearance is checked through the complete assembly, not merely
# through the cartridge bore.
brush=cylinder(50,cy,-80,140,15)
brush_overlap=[removed_volume(b,brush) for b in bodies+[sensor]]
assert max(abs(v) for v in brush_overlap)<1e-4,brush_overlap
removal=[]
for distance in (1,10,33):
    cartridge=tmp.copy(bodies[2])
    m=adsk.core.Matrix3D.create(); m.translation=adsk.core.Vector3D.create(0,0,-distance/10)
    assert tmp.transform(cartridge,m)
    overlaps=[removed_volume(b,cartridge) for b in bodies[:2]+[sensor]]
    assert max(abs(v) for v in overlaps)<1e-4,(distance,overlaps)
    removal.append({'downward_travel_mm':distance,'interference_mm3':overlaps})

# No fixed printed part may bypass the sensor and contact the moving holder.
minimum_fixed_to_carrier=app.measureManager.measureMinimumDistance(bodies[0],bodies[1]).value*10
minimum_fixed_to_cartridge=app.measureManager.measureMinimumDistance(bodies[0],bodies[2]).value*10
assert min(minimum_fixed_to_carrier,minimum_fixed_to_cartridge)>0.5
current=list(r.occurrences.itemByName('SC616C_1kg_Fusion:1').transform2.asArray())
assert max(abs(a-b) for a,b in zip(current,created['sensor_transform']))<1e-8
features=[]
for o in occs:
    for f in o.component.features.extrudeFeatures:
        if o==occs[0] and not f.name.startswith(('FDM_','SC616C_')): continue
        assert int(f.healthState)==0,(o.name,f.name,int(f.healthState))
        features.append({'part':o.name,'name':f.name,'health':int(f.healthState)})
report={'passed':True,'native_interference_count':interference.count,
 'fixed_M3':{'clearance_mm':3.4,'head_recess_mm':[6.2,3.2],'plate_thickness_mm':10,'material_above_head_mm':6.8,'screws':'2x M3x12','engagement_mm':5.2},
 'free_M3':{'clearance_mm':3.4,'head_recess_mm':[6.2,3.2],'plate_thickness_mm':6,'screws':'2x M3x8','engagement_mm':5.2},
 'cartridge_M3':{'screws':'2x M3x10','nuts':'2x standard M3 hex nuts','nut_pocket_AF_mm':5.8,'nut_pocket_depth_mm':2.6},
 'brush_axis_mm':[50,cy],'guide_bore_mm':15.4,'glue_bore_mm':16,'cartridge_OD_mm':22,'receiver_ID_mm':22.6,
 'parameter_sweep':sweep,'head_access':head_access,'brush_clearance_interference_mm3':brush_overlap,
 'cartridge_removal':removal,'fixed_to_carrier_gap_mm':minimum_fixed_to_carrier,'fixed_to_cartridge_gap_mm':minimum_fixed_to_cartridge,
 'part_volumes_mm3':{o.name:b.volume*1000 for o,b in zip(occs,bodies)},'feature_count_checked':len(features),
 'load_test_performed':False,'print_test_performed':False}
out='/Users/sugawaraichirou/Documents/ChatGPT/so101/output/v2'; os.makedirs(out,exist_ok=True)
with open(out+'/verification.json','w') as f: json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps(report,ensure_ascii=False,indent=2))
