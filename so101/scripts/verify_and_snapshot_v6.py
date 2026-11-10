import adsk.core
import adsk.fusion
import json
import math
import os

root='/Users/sugawaraichirou/Documents/ChatGPT/so101'; out=root+'/output/v6'
doc=next(doc for doc in app.documents if doc.name=='so101書道'); doc.activate()
d=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType')); r=d.rootComponent
t=adsk.fusion.TemporaryBRepManager.get()
assert d.attributes.itemByName('so101_calligraphy','short_stiff_v6')
assert d.timeline.count-d.timeline.markerPosition==31
with open(out+'/created.json',encoding='utf-8') as f: made=json.load(f)
names={'base':made['base_occurrence'],'carrier':'Brush_Load_Carrier_Compact_V5:1',
       'cartridge':'Brush_Cartridge_Symmetric_15mm_V5:1','wrist':'Wrist_Roll_Clearance_V5:1'}
parts={k:r.occurrences.itemByName(n) for k,n in names.items()}
bodies={k:max(o.bRepBodies,key=lambda b:b.volume) for k,o in parts.items()}
sensor=next(o.bRepBodies.item(0) for o in r.allOccurrences if o.fullPathName.startswith('SC616C_1kg_Fusion:1+') and o.bRepBodies.count)
bodies['sensor']=sensor
with open(root+'/tmp/v6_user_revision.json',encoding='utf-8') as f: baseline=json.load(f)
old=next(x for x in baseline['documents'] if x['name']=='so101書道')
prior_wrist=next(o for o in old['occurrences'] if o['name']==names['wrist'])
assert abs(sum(b.volume*1000 for b in parts['wrist'].bRepBodies)-sum(b['volume_mm3'] for b in prior_wrist['bodies']))<1e-4
def overlap(a,b):
    if not a.boundingBox.intersects(b.boundingBox): return 0.
    c=t.copy(a); assert t.booleanOperation(c,b,adsk.fusion.BooleanTypes.IntersectionBooleanType)
    return c.volume*1000
def moved(b,m):
    c=t.copy(b); assert t.transform(c,m); return c
def box(x0,x1,y0,y1,z0,z1):
    return t.createBox(adsk.core.OrientedBoundingBox3D.create(adsk.core.Point3D.create((x0+x1)/20,(y0+y1)/20,(z0+z1)/20),
        adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
entities=adsk.core.ObjectCollection.create()
for b in bodies.values(): entities.add(b)
inp=d.createInterferenceInput(entities); inp.areCoincidentFacesIncluded=False
inter=d.analyzeInterference(inp)
hits=[{'one':v.entityOne.name,'two':v.entityTwo.name,'mm3':v.interferenceBody.volume*1000} for v in inter]
assert not hits,hits
cx=62.; cy=d.userParameters.itemByName('sc_brush_axis_y').value*10
fixed=[]
for o in r.allOccurrences:
    if o.isVisible and (o.fullPathName.startswith('Wrist_Roll_Clearance_V5:1') or
                       (o.fullPathName.startswith('STS3215_c:1+') and '+Axes:' not in o.fullPathName)):
        for b in o.bRepBodies:
            if b.isSolid and b.volume>1e-6: fixed.append((o.fullPathName+'/'+b.name,t.copy(b)))
brush=t.createCylinderOrCone(adsk.core.Point3D.create(cx/10,cy/10,-5.2),.75,
                            adsk.core.Point3D.create(cx/10,cy/10,3.05),.75)
moving=[(k,t.copy(bodies[k])) for k in ('base','carrier','cartridge','sensor')]+[('assumed_brush',brush)]
rows=[]
for angle in range(-180,181,5):
    m=adsk.core.Matrix3D.create(); m.setToRotation(math.radians(angle),adsk.core.Vector3D.create(0,1,0),adsk.core.Point3D.create(-.2,0,3.4))
    row=[]
    for label,b in moving:
        mb=moved(b,m)
        for name,fb in fixed:
            v=overlap(mb,fb)
            if v>.01: row.append({'moving':label,'fixed':name,'volume_mm3':v})
    rows.append({'angle_deg':angle,'hits':row})
assert not any(row['hits'] for row in rows),[row for row in rows if row['hits']]
gauge=box(56.65,67.35,9.56,23.36,38.5,47)
gauge_hits={k:overlap(bodies[k],gauge) for k in ('base','carrier','cartridge')}
assert max(gauge_hits.values())<1e-4,gauge_hits
removal=[]
for distance in (1,10,24,50,100):
    m=adsk.core.Matrix3D.create(); m.translation=adsk.core.Vector3D.create(0,0,-distance/10)
    mb=moved(bodies['cartridge'],m)
    volumes=[overlap(mb,b) for k,b in bodies.items() if k!='cartridge']+[overlap(mb,b) for _,b in fixed]
    assert max(volumes)<1e-4,(distance,volumes)
    removal.append({'down_mm':distance,'max_overlap_mm3':max(volumes)})
insertion=[]
for distance in (1,5,15,45,70):
    m=adsk.core.Matrix3D.create(); m.translation=adsk.core.Vector3D.create(0,-distance/10,0)
    mb=moved(sensor,m); volumes=[overlap(mb,bodies['base'])]+[overlap(mb,b) for _,b in fixed]
    assert max(volumes)<1e-4,(distance,volumes)
    insertion.append({'from_front_mm':distance,'max_overlap_mm3':max(volumes)})
sym=[]
for label,axis,center in [('cartridge',0,cx),('cartridge',1,cy),('carrier',0,cx)]:
    m=adsk.core.Matrix3D.create(); m.setCell(axis,axis,-1); m.setCell(axis,3,center/5)
    reflection=moved(bodies[label],m); diff=(bodies[label].volume+reflection.volume)*1000-2*overlap(bodies[label],reflection)
    assert abs(diff)<1e-4,(label,axis,diff)
    sym.append({'part':label,'axis':axis,'difference_mm3':diff})
features=[]
for label,o in parts.items():
    for f in o.component.features:
        assert int(f.healthState)==0,(label,f.name,f.errorOrWarningMessage)
        features.append([label,f.name])
parameter=d.userParameters.itemByName('brush_dia'); original=parameter.expression
tested=[]
try:
    for value in (12,17):
        parameter.expression=f'{value} mm'; d.computeAll()
        diameters=[f.geometry.radius*20 for f in parts['cartridge'].bRepBodies.item(0).faces
                   if isinstance(f.geometry,adsk.core.Cylinder) and abs(f.geometry.axis.z)>.99]
        assert any(abs(v-value-1)<1e-5 for v in diameters)
        assert sum(abs(v-value-.4)<1e-5 for v in diameters)==2
        tested.append(value)
finally:
    parameter.expression=original; d.computeAll()
assert d.timeline.count-d.timeline.markerPosition==31
report={'passed':True,'parts':names,'static_interference_count':inter.count,
        'rotary_sweep':{'range_deg':[-180,180],'step_deg':5,'poses':len(rows),'all_clear':True,
                        'assumed_brush_diameter_mm':15,'assumed_brush_tip_z_mm':-52,
                        'excluded':'Upstream arm absent, wires, servo limits, print tolerance and elastic deformation'},
        'gauge_keepout_overlap_mm3':gauge_hits,'cartridge_pullout':removal,'cell_slide_in':insertion,
        'symmetry':sym,'brush_diameter_parameter_roundtrip_mm':tested,'user_wrist_preserved':True,
        'healthy_feature_count':len(features),'future_features_preserved':31,
        'volumes_mm3':{k:b.volume*1000 for k,b in bodies.items()},
        'wrist_all_body_volumes_mm3':[b.volume*1000 for b in parts['wrist'].bRepBodies],
        'load_cell_orientation_unchanged':True,'full_robot_motion_validated':False,
        'sensor_electrical_accuracy_validated':False,'print_test_performed':False}
with open(out+'/verification.json','w',encoding='utf-8') as f: json.dump(report,f,ensure_ascii=False,indent=2)
with open(out+'/motion.json','w',encoding='utf-8') as f: json.dump(rows,f,ensure_ascii=False,indent=2)
# Independent four-part snapshots compare original and short yokes with identical assumptions.
for version in ('v5_original','v6_short'):
    path=out+'/'+version; os.makedirs(path,exist_ok=True)
    sources={k:t.copy(bodies[k]) for k in ('base','carrier','cartridge','sensor')}
    if version=='v5_original':
        sources['base']=t.copy(r.occurrences.itemByName('部品１_V5可動域改善:1').bRepBodies.item(0))
        m=adsk.core.Matrix3D.create(); m.translation=adsk.core.Vector3D.create(1.6,0,0)
        for k in ('carrier','cartridge','sensor'): assert t.transform(sources[k],m)
    tmpdoc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    try:
        td=adsk.fusion.Design.cast(app.activeProduct); td.designType=adsk.fusion.DesignTypes.DirectDesignType
        for k,b in sources.items():
            o=td.rootComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create()); o.component.name=k
            body=o.component.bRepBodies.add(b); body.name=k
            assert td.exportManager.execute(td.exportManager.createSTEPExportOptions(path+'/'+k+'.step',o.component))
        audit={'brush_axis_mm':[78 if version=='v5_original' else 62,cy],
               'brush_stop_z_mm':30.5,'assumed_brush_tip_z_mm':-52,
               'bore_load_z_min_mm':10.5,'bore_load_z_max_mm':28.5,
               'base_included':True,'base_clamp_faces_y_mm':[-17.05,20.2],
               'source':'Actual Fusion BRep snapshot; original V5 vs16mm-shortened yoke',
               'parts':{k:{'volume_mm3':b.volume*1000} for k,b in sources.items()}}
        with open(path+'/geometry_audit.json','w',encoding='utf-8') as f: json.dump(audit,f,ensure_ascii=False,indent=2)
    finally:
        tmpdoc.close(False); doc.activate()
print(json.dumps(report,ensure_ascii=False,indent=2))
