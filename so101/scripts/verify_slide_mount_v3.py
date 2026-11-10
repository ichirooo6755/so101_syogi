import adsk.core
import adsk.fusion
import json
import os

d=adsk.fusion.Design.cast(app.activeProduct)
r=d.rootComponent
root='/Users/sugawaraichirou/Documents/ChatGPT/so101'
with open(root+'/tmp/v3_created.json') as f: created=json.load(f)
with open(root+'/tmp/v3_before.json') as f: before=json.load(f)
names=('部品１:1','Brush_Load_Carrier:1','Brush_Cartridge_15mm:1','SC616C_Slide_In_Top_Cover:1')
occs=[r.occurrences.itemByName(n) for n in names]
assert all(occs)
bodies=[o.bRepBodies.item(0) for o in occs]
sensor_o=next(o for o in r.allOccurrences if o.fullPathName.startswith('SC616C_1kg_Fusion:1+') and o.bRepBodies.count)
sensor=sensor_o.bRepBodies.item(0)
assert all(o.component.bRepBodies.count==1 and b.isSolid for o,b in zip(occs,bodies))
assert d.timeline.count-d.timeline.markerPosition==before['timeline_count']-before['timeline_marker']
current=list(r.occurrences.itemByName('SC616C_1kg_Fusion:1').transform2.asArray())
assert max(abs(a-b) for a,b in zip(current,created['sensor_transform']))<1e-8
assert abs(d.userParameters.itemByName('brush_dia').value*10-15)<1e-7
cy=d.userParameters.itemByName('sc_brush_axis_y').value*10

def near(a,b): assert abs(a-b)<1e-5,(a,b)
def cylinders(body,diameter,x=None):
    result=[]
    for f in body.faces:
        g=f.geometry
        if isinstance(g,adsk.core.Cylinder) and abs(g.axis.z)>.99 and abs(g.radius*20-diameter)<1e-5 and (x is None or abs(g.origin.x*10-x)<1e-5):
            result.append({'x':g.origin.x*10,'y':g.origin.y*10,'z':[f.boundingBox.minPoint.z*10,f.boundingBox.maxPoint.z*10]})
    return sorted(result,key=lambda a:a['y'])

# Aluminium threads remain the fastening destination for all four sensor bolts.
fixed=cylinders(bodies[0],3.4,30); free=cylinders(bodies[1],3.4,30)
fixed_heads=cylinders(bodies[0],6.2,30); free_heads=cylinders(bodies[1],6.2,30)
sensor_holes=cylinders(sensor,3)
assert len(fixed)==len(free)==len(fixed_heads)==len(free_heads)==2
for group,expected in ((fixed,sensor_holes[2:]),(free,sensor_holes[:2])):
    for a,b in zip(group,expected): near(a['x'],b['x']); near(a['y'],b['y'])
    near(group[1]['y']-group[0]['y'],7.4)
for h in fixed_heads: near(h['z'][0],14.5); near(h['z'][1],17.7)
for h in free_heads: near(h['z'][0],18.5); near(h['z'][1],21.7)
flange_holes=cylinders(bodies[2],3.4,50)
lid_holes=[h for h in cylinders(bodies[3],3.4) if abs(h['y']-created['fixed_boss_centers_mm'][0][1])<1e-6]
assert len(flange_holes)==len(lid_holes)==2
assert cylinders(bodies[2],16) and len(cylinders(bodies[2],15.4))==2
assert cylinders(bodies[1],22.6) and cylinders(bodies[2],22)

threads=[]
for o in (occs[0],occs[1]):
    fs=[f for f in o.component.features.threadFeatures if f.name.startswith('V3_')]
    assert len(fs)==1
    f=fs[0]
    assert f.isModeled and f.isRightHanded and int(f.healthState)==0
    assert f.threadInfo.threadDesignation=='M3x0.5' and f.threadInfo.threadClass=='6H'
    # A cosmetic thread has no generated helical surface faces.
    surface_types={}
    for face in f.faces:
        typ=face.geometry.objectType
        surface_types[typ]=surface_types.get(typ,0)+1
    assert any('Nurbs' in name for name in surface_types),surface_types
    threads.append({'part':o.name,'feature':f.name,'modeled':f.isModeled,
                    'designation':f.threadInfo.threadDesignation,'class':f.threadInfo.threadClass,
                    'right_handed':f.isRightHanded,'hole_count':2,'generated_surface_types':surface_types})

entities=adsk.core.ObjectCollection.create()
for b in bodies+[sensor]: entities.add(b)
inp=d.createInterferenceInput(entities); inp.areCoincidentFacesIncluded=False
interference=d.analyzeInterference(inp)
if interference and interference.count:
    for result in interference:
        print('INTERFERENCE',result.entityOne.name,result.entityTwo.name,result.interferenceBody.volume*1000,
              [[v*10 for v in p.asArray()] for p in (result.interferenceBody.boundingBox.minPoint,result.interferenceBody.boundingBox.maxPoint)])
assert interference is not None and interference.count==0,interference.count
tmp=adsk.fusion.TemporaryBRepManager.get()
def removed_volume(body,tool):
    candidate=tmp.copy(body); volume=candidate.volume
    assert tmp.booleanOperation(candidate,tool,adsk.fusion.BooleanTypes.DifferenceBooleanType)
    return (volume-candidate.volume)*1000
def cylinder(x,y,z0,z1,diam):
    return tmp.createCylinderOrCone(adsk.core.Point3D.create(x/10,y/10,z0/10),diam/20,adsk.core.Point3D.create(x/10,y/10,z1/10),diam/20)
def moved(body,dx=0,dy=0,dz=0):
    result=tmp.copy(body); m=adsk.core.Matrix3D.create()
    m.translation=adsk.core.Vector3D.create(dx/10,dy/10,dz/10)
    assert tmp.transform(result,m)
    return result
def box(x0,x1,y0,y1,z0,z1):
    bb=adsk.core.OrientedBoundingBox3D.create(adsk.core.Point3D.create((x0+x1)/20,(y0+y1)/20,(z0+z1)/20),
        adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10)
    return tmp.createBox(bb)
def clear(values,label): assert max(abs(v) for v in values)<1e-4,(label,values)

# Enlarged keepout includes the gauge section, below/above the cell, and both sides.
keepout=box(24.65,35.35,9.56,23.36,23.5,32)
gauge_clearance=[removed_volume(b,keepout) for b in bodies]
clear(gauge_clearance,'central sensing keepout')

# Loosen both cover screws one M3 coarse-pitch turn and lift the cover 0.5 mm.
# Slide the sensor/holder assembly in from the free-end side, without rotation.
raised_lid=moved(bodies[3],dz=.5)
slide=[]
for distance in (0,1,5,10,20,30,45,60):
    volumes=[]
    for mobile in [sensor,bodies[1],bodies[2]]:
        candidate=moved(mobile,dy=-distance)
        volumes.extend(removed_volume(fixed_part,candidate) for fixed_part in (bodies[0],raised_lid))
    clear(volumes,('slide',distance))
    slide.append({'travel_towards_entry_mm':distance,'interference_mm3':volumes})

# Worst nominal width from the PDF is 9.3 mm, vs the modeled sensor's 9.0 mm.
wide_sensor=box(25.35,34.65,-6.53705379764,38.46294620236,24.5,30.5)
wide_slide=[]
for distance in (0,1,5,10,20,30,45,60):
    candidate=moved(wide_sensor,dy=-distance)
    volumes=[removed_volume(b,candidate) for b in (bodies[0],raised_lid)]
    clear(volumes,('9.3mm width slide',distance))
    wide_slide.append({'travel_towards_entry_mm':distance,'interference_mm3':volumes})

head_access=[]
for label,group,z0,z1 in (('fixed',fixed,-20,17.7),('free',free,-20,21.7),
                         ('cartridge',flange_holes,-20,8.5),('cover',lid_holes,35.4,60)):
    for h in group:
        tool=cylinder(h['x'],h['y'],z0,z1,5.6)
        values=[removed_volume(b,tool) for b in bodies]
        clear(values,('screw head',label,h))
        head_access.append({'interface':label,'x':h['x'],'y':h['y'],'head_insertion_clear':True})
brush=cylinder(50,cy,-80,140,15)
brush_overlap=[removed_volume(b,brush) for b in bodies+[sensor]]
clear(brush_overlap,'brush')
removal=[]
for distance in (1,10,33):
    cartridge=moved(bodies[2],dz=-distance)
    values=[removed_volume(b,cartridge) for b in (bodies[0],bodies[1],bodies[3],sensor)]
    clear(values,('cartridge removal',distance))
    removal.append({'downward_travel_mm':distance,'interference_mm3':values})

gaps={}
for label,fixed_part in (('base',bodies[0]),('cover',bodies[3])):
    for mobile_label,mobile in (('carrier',bodies[1]),('cartridge',bodies[2])):
        gap=app.measureManager.measureMinimumDistance(fixed_part,mobile).value*10
        assert gap>0.5,(label,mobile_label,gap)
        gaps[label+'_to_'+mobile_label+'_mm']=gap
features=[]
for o in occs:
    for f in o.component.features.extrudeFeatures:
        if o==occs[0] and not f.name.startswith(('FDM_','SC616C_','V3_')): continue
        assert int(f.healthState)==0,(o.name,f.name,f.errorOrWarningMessage)
        features.append({'part':o.name,'name':f.name,'health':int(f.healthState)})
report={'passed':True,'native_interference_count':interference.count,'threads':threads,
        'modeled_female_thread_holes':4,'cell_orientation_unchanged':True,
        'central_sensing_keepout_interference_mm3':gauge_clearance,'central_top_gap_mm':1.5,
        'slide_with_lid_lift_mm':.5,'slide_checks':slide,'slide_9p3_width_checks':wide_slide,
        'head_access':head_access,'brush_clearance_interference_mm3':brush_overlap,
        'cartridge_removal':removal,'load_path_gaps':gaps,
        'part_volumes_mm3':{o.name:b.volume*1000 for o,b in zip(occs,bodies)},
        'feature_count_checked':len(features),'preserved_future_timeline_features':d.timeline.count-d.timeline.markerPosition,
        'print_test_performed':False,'load_test_performed':False,'calibration_performed':False}
out=root+'/output/v3'; os.makedirs(out,exist_ok=True)
with open(out+'/verification.json','w') as f: json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps(report,ensure_ascii=False,indent=2))
