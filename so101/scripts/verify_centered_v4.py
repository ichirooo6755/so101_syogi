import adsk.core
import adsk.fusion
import json
import math
import os

root='/Users/sugawaraichirou/Documents/ChatGPT/so101'
out=root+'/output/v4'; os.makedirs(out,exist_ok=True)
d=adsk.fusion.Design.cast(app.activeProduct); r=d.rootComponent
with open(root+'/tmp/v4_before.json',encoding='utf-8') as f: before=json.load(f)
with open(root+'/tmp/v4_created.json',encoding='utf-8') as f: created=json.load(f)
fz=created['cartridge_flange_z_mm']; rz=fz+4; rt=rz+6; nz=rt-2.6
names=['部品１:1','Brush_Load_Carrier_Centered:1','Brush_Cartridge_Centered_15mm:1']
occs=[r.occurrences.itemByName(name) for name in names]
bodies=[o.bRepBodies.item(0) for o in occs]
cell_o=r.occurrences.itemByName('SC616C_1kg_Fusion:1')
sensor_o=next(o for o in r.allOccurrences if o.fullPathName.startswith(cell_o.name+'+') and o.bRepBodies.count)
sensor=sensor_o.bRepBodies.item(0)
assert all(b.isSolid and o.component.bRepBodies.count==1 for o,b in zip(occs,bodies))
assert d.timeline.count-d.timeline.markerPosition==before['timeline_count']-before['timeline_marker']
assert max(abs(a-b) for a,b in zip(cell_o.transform2.asArray(),created['sensor_transform']))<1e-9
base_before=next(o for o in before['occurrences'] if o['name']=='部品１:1')
assert abs(bodies[0].volume*1000-base_before['bodies'][0]['volume_mm3'])<1e-5
preserved=[]
for name in ('部品１:1','Brush_Load_Carrier:1','Brush_Cartridge_15mm:1','Wrist_Roll_Follower_SO101 v1:3','STS3215_c:1'):
    old=next(o for o in before['occurrences'] if o['name']==name)
    live=r.occurrences.itemByName(name)
    assert max(abs(a-b) for a,b in zip(live.transform2.asArray(),old['transform']))<1e-9,name
    for b,previous in zip(live.bRepBodies,old['bodies']): assert abs(b.volume*1000-previous['volume_mm3'])<1e-5,name
    preserved.append(name)
assert not r.occurrences.itemByName('Brush_Load_Carrier:1').isVisible
assert not r.occurrences.itemByName('Brush_Cartridge_15mm:1').isVisible

def cylinders(b,diam,x=None):
    rows=[]
    for f in b.faces:
        g=f.geometry
        if isinstance(g,adsk.core.Cylinder) and abs(g.axis.z)>.99 and abs(g.radius*20-diam)<1e-5 and (x is None or abs(g.origin.x*10-x)<1e-5):
            rows.append({'x':g.origin.x*10,'y':g.origin.y*10,'z':[f.boundingBox.minPoint.z*10,f.boundingBox.maxPoint.z*10]})
    return sorted(rows,key=lambda h:h['y'])
def near(a,b): assert abs(a-b)<1e-5,(a,b)
cell_holes=cylinders(sensor,3)
free=cylinders(bodies[1],3.4,30)
free=[h for h in free if h['z'][0]>18]
heads=cylinders(bodies[1],6.2,30)
retention=[h for h in cylinders(bodies[1],3.4,30) if h['z'][0]<0]
flange=cylinders(bodies[2],3.4,30)
assert len(free)==len(heads)==len(retention)==len(flange)==2
for actual,expected in zip(free,cell_holes[:2]): near(actual['x'],expected['x']); near(actual['y'],expected['y'])
for h in heads: near(h['z'][0],18.5); near(h['z'][1],21.7)
for a,b in zip(retention,flange):
    near(a['x'],b['x']); near(a['y'],b['y']); near(a['z'][0],rz); near(a['z'][1],nz)
    near(b['z'][0],fz); near(b['z'][1],rz)
nut_faces=[f for f in bodies[1].faces if isinstance(f.geometry,adsk.core.Plane) and abs(f.geometry.normal.z)<1e-7
           and abs(f.boundingBox.minPoint.z*10-nz)<1e-5 and abs(f.boundingBox.maxPoint.z*10-rt)<1e-5]
assert len(nut_faces)==12,len(nut_faces)
assert occs[1].component.features.threadFeatures.count==0
cx,cy=created['brush_axis_mm']
assert cylinders(bodies[1],22.6,cx) and cylinders(bodies[2],16,cx) and len(cylinders(bodies[2],15.4,cx))==2
for h in cell_holes: near(cx,h['x'])

# Native interference of the replacement assembly. Baseline robot mating
# interferences are separately distinguished from any NEW collision.
entities=adsk.core.ObjectCollection.create()
for b in bodies+[sensor]: entities.add(b)
inp=d.createInterferenceInput(entities); inp.areCoincidentFacesIncluded=False
result=d.analyzeInterference(inp)
interferences=[{'one':v.entityOne.name,'two':v.entityTwo.name,'volume_mm3':v.interferenceBody.volume*1000,
                'bbox_mm':[[x*10 for x in p.asArray()] for p in (v.interferenceBody.boundingBox.minPoint,v.interferenceBody.boundingBox.maxPoint)]} for v in result]
assert result.count==0,interferences
tmp=adsk.fusion.TemporaryBRepManager.get()
def box(x0,x1,y0,y1,z0,z1):
    return tmp.createBox(adsk.core.OrientedBoundingBox3D.create(adsk.core.Point3D.create((x0+x1)/20,(y0+y1)/20,(z0+z1)/20),
        adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
def removed(b,tool):
    c=tmp.copy(b); v=c.volume
    assert tmp.booleanOperation(c,tool,adsk.fusion.BooleanTypes.DifferenceBooleanType)
    return (v-c.volume)*1000
def moved(b,dx=0,dy=0,dz=0):
    c=tmp.copy(b); m=adsk.core.Matrix3D.create(); m.translation=adsk.core.Vector3D.create(dx/10,dy/10,dz/10)
    assert tmp.transform(c,m)
    return c
def cylinder(x,y,z0,z1,diam):
    return tmp.createCylinderOrCone(adsk.core.Point3D.create(x/10,y/10,z0/10),diam/20,adsk.core.Point3D.create(x/10,y/10,z1/10),diam/20)
def clear(values,label): assert max(abs(v) for v in values)<1e-4,(label,values)
obstacles=[]
for o in r.allOccurrences:
    if not o.isVisible or o.fullPathName in names or o.fullPathName.startswith(cell_o.name+'+'): continue
    for b in o.bRepBodies:
        if b.isSolid and b.volume>1e-6: obstacles.append((o.fullPathName,b))
robot_checks=[]
for name,b in obstacles:
    values=[removed(m,b) for m in bodies[1:]]
    clear(values,('new part vs existing robot',name))
    robot_checks.append({'obstacle':name,'overlap_mm3':values})
keepout=box(24.65,35.35,9.56,23.36,23.5,32)
gauge=[removed(b,keepout) for b in bodies]
clear(gauge,'sensing keepout')
brush=cylinder(cx,cy,-120,created['brush_butt_stop_z_mm'],15)
brush_overlap=[removed(b,brush) for b in bodies+[sensor]]
clear(brush_overlap,'brush shaft')
stop=bodies[2].pointContainment(adsk.core.Point3D.create(cx/10,cy/10,(created['brush_butt_stop_z_mm']+1)/10))
assert stop==adsk.fusion.PointContainment.PointInsidePointContainment,stop

removal=[]
for distance in (1,10,33,50):
    moving=moved(bodies[2],dz=-distance)
    values=[removed(b,moving) for b in bodies[:2]+[sensor]]+[removed(b,moving) for name,b in obstacles]
    clear(values,('remove cartridge',distance))
    removal.append({'down_mm':distance,'maximum_overlap_mm3':max(abs(v) for v in values)})
head_access=[]
for group,seat,label in ((free,21.7,'free cell: remove cartridge first'),(flange,fz,'cartridge')):
    for h in group:
        tool=cylinder(h['x'],h['y'],-100,seat,5.6)
        tested=bodies[:2]+[sensor]+[b for name,b in obstacles]
        if label=='cartridge': tested.append(bodies[2])
        values=[removed(b,tool) for b in tested]
        clear(values,('head insertion',h))
        head_access.append({'interface':label,'center_mm':[h['x'],h['y']],'clear':True})

# Nuts approach horizontally BELOW the cell and fixed platform, then drop
# into the upward-facing hex recesses; straight insertion from above is not
# required or assumed.
def nut_prism(x,y,bottom):
    prism=box(x-10,x+10,y-2.8,y+2.8,bottom,bottom+2.5)
    for angle in (math.pi/3,2*math.pi/3):
        slab=box(x-10,x+10,y-2.8,y+2.8,bottom,bottom+2.5)
        m=adsk.core.Matrix3D.create(); m.setToRotation(angle,adsk.core.Vector3D.create(0,0,1),adsk.core.Point3D.create(x/10,y/10,0))
        assert tmp.transform(slab,m)
        assert tmp.booleanOperation(prism,slab,adsk.fusion.BooleanTypes.IntersectionBooleanType)
    return prism
nut_access=[]
for h in retention:
    approach=rt+2.5
    nut=nut_prism(h['x'],h['y'],approach)
    for dx in (15,8,0):
        tool=moved(nut,dx=dx)
        clear([removed(b,tool) for b in bodies+[sensor]]+[removed(b,tool) for name,b in obstacles],('nut side approach',h,dx))
    for bottom in (rt+1,rt-.5,nz):
        tool=moved(nut,dz=bottom-approach)
        clear([removed(b,tool) for b in bodies+[sensor]],('nut seat',h,bottom))
    nut_access.append({'center_mm':[h['x'],h['y']],'AF_test_mm':5.6,'thickness_test_mm':2.5,'side_approach_clear':True})

gaps={}
for label,b in (('carrier',bodies[1]),('cartridge',bodies[2])):
    gap=app.measureManager.measureMinimumDistance(bodies[0],b).value*10
    assert gap>0.5,(label,gap)
    gaps['base_to_'+label+'_mm']=gap
features=[]
for o in occs[1:]:
    for f in o.component.features:
        assert int(f.healthState)==0,(o.name,f.name,f.errorOrWarningMessage)
        features.append(f.name)

report={'passed':True,'native_new_assembly_interference_count':result.count,
        'robot_obstacles_checked':robot_checks,'preserved_existing_occurrences':preserved,
        'sensor_pose_unchanged':True,'base_geometry_unchanged':True,
        'brush_axis_mm':[cx,cy],'old_lateral_eccentricity_mm':20,'new_lateral_eccentricity_mm':0,
        'axial_5N_torsional_moment_before_Nmm':100,'axial_5N_torsional_moment_after_Nmm':0,
        'cartridge_frame_change_world_mm':created['reference_shift_mm'],
        'nut_pockets':{'count':2,'AF_mm':5.8,'depth_mm':2.6,'metal_M3_nuts':True},
        'sensor_bolts':'2x M3x8; phi3.4 clearance; same 5.2 mm nominal engagement',
        'cartridge_bolts':'2x M3x10 + 2x metal M3 hex nuts',
        'brush_stop_z_mm':created['brush_butt_stop_z_mm'],'brush_cap_top_z_mm':created['cartridge_top_z_mm'],'free_bolt_head_min_z_mm':18.5,
        'sensing_keepout_intersections_mm3':gauge,'brush_shaft_intersections_mm3':brush_overlap,
        'head_access':head_access,'nut_access':nut_access,'cartridge_removal':removal,
        'minimum_gaps':gaps,'checked_features':len(features),
        'part_volumes_mm3':{o.name:b.volume*1000 for o,b in zip(occs,bodies)},
        'print_test_performed':False,'electrical_accuracy_validated':False,'physical_strength_validated':False}
with open(out+'/verification.json','w',encoding='utf-8') as f: json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps(report,ensure_ascii=False,indent=2))
