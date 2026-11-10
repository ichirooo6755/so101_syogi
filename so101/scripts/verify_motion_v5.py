import adsk.core
import adsk.fusion
import json
import math
import os

root='/Users/sugawaraichirou/Documents/ChatGPT/so101'; out=root+'/output/v5'
with open(out+'/created.json',encoding='utf-8') as f: created=json.load(f)
with open(root+'/tmp/v5_before.json',encoding='utf-8') as f: before=json.load(f)
d=adsk.fusion.Design.cast(app.activeProduct); r=d.rootComponent; t=adsk.fusion.TemporaryBRepManager.get()
parts={k:r.occurrences.itemByName(n) for k,n in created['parts'].items()}
cell=r.occurrences.itemByName('SC616C_1kg_Fusion:1')
sensor=next(o.bRepBodies.item(0) for o in r.allOccurrences if o.fullPathName.startswith(cell.name+'+') and o.bRepBodies.count)
bodies={k:o.bRepBodies.item(0) for k,o in parts.items()}; bodies['sensor']=sensor
assert d.timeline.count-d.timeline.markerPosition==31
old_preserved=[]
for name in ('部品１:1','Brush_Load_Carrier_Centered:1','Brush_Cartridge_Centered_15mm:1','Wrist_Roll_Follower_SO101 v1:3'):
    old=next(o for o in before['occurrences'] if o['name']==name); o=r.occurrences.itemByName(name)
    assert not o.isVisible
    assert max(abs(a-b) for a,b in zip(o.transform2.asArray(),old['transform']))<1e-9
    assert abs(sum(b.volume*1000 for b in o.bRepBodies)-sum(b['volume_mm3'] for b in old['bodies']))<1e-4
    old_preserved.append(name)
now=cell.transform2.asArray(); prev=created['sensor_before_transform']
assert max(abs(now[i]-prev[i]) for i in (0,1,2,4,5,6,8,9,10))<1e-10
def overlap(a,b):
    if not a.boundingBox.intersects(b.boundingBox): return 0.
    c=t.copy(a)
    assert t.booleanOperation(c,b,adsk.fusion.BooleanTypes.IntersectionBooleanType)
    return c.volume*1000
def transformed(b,m):
    c=t.copy(b); assert t.transform(c,m); return c
def moved(b,dx=0,dy=0,dz=0):
    m=adsk.core.Matrix3D.create(); m.translation=adsk.core.Vector3D.create(dx/10,dy/10,dz/10)
    return transformed(b,m)
def box(x0,x1,y0,y1,z0,z1):
    return t.createBox(adsk.core.OrientedBoundingBox3D.create(adsk.core.Point3D.create((x0+x1)/20,(y0+y1)/20,(z0+z1)/20),
        adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
def cylinder(x,y,z0,z1,diam):
    return t.createCylinderOrCone(adsk.core.Point3D.create(x/10,y/10,z0/10),diam/20,
                                adsk.core.Point3D.create(x/10,y/10,z1/10),diam/20)
entities=adsk.core.ObjectCollection.create()
for b in bodies.values(): entities.add(b)
ii=d.createInterferenceInput(entities); ii.areCoincidentFacesIncluded=False
ir=d.analyzeInterference(ii)
interference=[{'one':v.entityOne.name,'two':v.entityTwo.name,'volume_mm3':v.interferenceBody.volume*1000} for v in ir]
assert not interference,interference

symmetry=[]
for label,axis,center in [('cartridge',0,78),('cartridge',1,created['brush_axis_mm'][1]),('carrier',0,78)]:
    m=adsk.core.Matrix3D.create(); m.setCell(axis,axis,-1); m.setCell(axis,3,center/5)
    reflected=transformed(bodies[label],m)
    common=overlap(bodies[label],reflected)
    difference=(bodies[label].volume+reflected.volume)*1000-2*common
    assert abs(difference)<1e-4,(label,axis,difference)
    symmetry.append({'part':label,'mirror_axis':('X','Y','Z')[axis],'symmetric_difference_mm3':difference})

fixed=[]
for o in r.allOccurrences:
    if not o.isVisible: continue
    if o.fullPathName.startswith('Wrist_Roll_Clearance_V5:1') or (o.fullPathName.startswith('STS3215_c:1+') and '+Axes:' not in o.fullPathName):
        for b in o.bRepBodies:
            if b.isSolid and b.volume>1e-6: fixed.append((o.fullPathName+'/'+b.name,t.copy(b)))
cx,cy=created['brush_axis_mm']
brush=cylinder(cx,cy,-52,30.5,15)
moving=[(k,t.copy(bodies[k])) for k in ('base','carrier','cartridge','sensor')]+[('assumed_brush',brush)]
rows=[]
for angle in range(-180,181,2):
    m=adsk.core.Matrix3D.create(); m.setToRotation(math.radians(angle),adsk.core.Vector3D.create(0,1,0),adsk.core.Point3D.create(-.2,0,3.4))
    hits=[]
    for label,b in moving:
        moved_body=transformed(b,m)
        for name,fb in fixed:
            v=overlap(moved_body,fb)
            if v>.01: hits.append({'moving':label,'fixed':name,'volume_mm3':v})
    rows.append({'angle_deg':angle,'hits':hits})
assert not any(row['hits'] for row in rows),[row for row in rows if row['hits']]

keepout=box(72.65,83.35,9.56,23.36,38.5,47)
gauge={label:overlap(bodies[label],keepout) for label in ('base','carrier','cartridge')}
assert max(gauge.values())<1e-4,gauge
removal=[]
for distance in (1,10,24,50,100):
    b=moved(bodies['cartridge'],dz=-distance)
    hits=[overlap(b,bb) for key,bb in bodies.items() if key!='cartridge']+[overlap(b,fb) for _,fb in fixed]
    assert max(hits)<1e-4,(distance,hits)
    removal.append({'down_mm':distance,'max_overlap_mm3':max(hits)})
insertion=[]
for distance in (1,5,15,45,70):
    b=moved(sensor,dy=-distance)
    hits=[overlap(b,bodies['base'])]+[overlap(b,fb) for _,fb in fixed]
    assert max(hits)<1e-4,(distance,hits)
    insertion.append({'from_front_mm':distance,'max_overlap_mm3':max(hits)})
features=[]
for label,o in parts.items():
    assert o.component.bRepBodies.count==1 and o.bRepBodies.item(0).isSolid
    for feature in o.component.features:
        assert int(feature.healthState)==0,(o.name,feature.name,feature.errorOrWarningMessage)
        features.append(feature.name)
parameter_test=[]
dia=d.userParameters.itemByName('brush_dia'); original=dia.expression
try:
    for value in (12,17):
        dia.expression=f'{value} mm'; d.computeAll()
        b=parts['cartridge'].bRepBodies.item(0)
        diameters=[f.geometry.radius*20 for f in b.faces if isinstance(f.geometry,adsk.core.Cylinder) and abs(f.geometry.axis.z)>.99]
        assert any(abs(v-value-1)<1e-5 for v in diameters)
        assert sum(abs(v-value-.4)<1e-5 for v in diameters)==2
        assert any(abs(v-22)<1e-5 for v in diameters)
        parameter_test.append(value)
finally:
    dia.expression=original; d.computeAll()
report={'passed':True,'native_static_interference_count':ir.count,
        'native_kernel_sweep':{'checked_range_deg':[-180,180],'step_deg':2,'poses':len(rows),'all_clear':True,
                             'rotation_axis_world':[0,1,0],'axis_origin_mm':[-2,0,34],
                             'includes_assumed_brush_mm':{'diameter':15,'length':82.5,'tip_z':-52,'butt_z':30.5},
                             'excluded':'Upstream arm absent; wire routing, servo limits, print error and dynamic deflection not simulated',
                             'collision_threshold_mm3':.01},
        'symmetry':symmetry,'sensor_orientation_unchanged':True,
        'nominal_axial_torsional_eccentricity_mm':0,'brush_axis_mm':[cx,cy],
        'cartridge_removed_without_clamp':removal,'sensor_slides_into_fixed_socket_before_carrier_attached':insertion,
        'sensing_keepout_intersections_mm3':gauge,'preserved_hidden':old_preserved,
        'healthy_features':len(features),'brush_diameter_parameter_test_mm':parameter_test,
        'part_volumes_mm3':created['part_volumes_mm3'],'wrist_removed_mm3':created['wrist_removed_mm3'],
        'full_robot_motion_validated':False,'print_test_performed':False,'sensor_electrical_accuracy_validated':False}
with open(out+'/verification.json','w',encoding='utf-8') as f: json.dump(report,f,ensure_ascii=False,indent=2)
with open(out+'/motion_after.json','w',encoding='utf-8') as f: json.dump(rows,f,ensure_ascii=False,indent=2)
print(json.dumps(report,ensure_ascii=False,indent=2))
