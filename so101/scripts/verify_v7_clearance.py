"""Read-only CAD checks on the candidate and the actual user-edited wrist."""
import adsk.core
import adsk.fusion
import json
import math

root = '/Users/sugawaraichirou/Documents/ChatGPT/so101'
main = next(doc for doc in app.documents if doc.name.startswith('so101書道'))
d = adsk.fusion.Design.cast(main.products.itemByProductType('DesignProductType'))
r = d.rootComponent
candidate_name = globals().get('candidate_name', '部品１_V7_閉断面台座補強')
report_version = globals().get('report_version', 'v7')
candidate = next(doc for doc in app.documents if doc.name == candidate_name)
cd = adsk.fusion.Design.cast(candidate.products.itemByProductType('DesignProductType'))
t = adsk.fusion.TemporaryBRepManager.get()
source = cd.rootComponent.bRepBodies.item(0)
bodies = {'base': t.copy(source)}
for label, name in (('carrier', 'Brush_Load_Carrier_Compact_V5:1'),
                    ('cartridge', 'Brush_Cartridge_Symmetric_15mm_V5:1')):
    bodies[label] = t.copy(r.occurrences.itemByName(name).bRepBodies.item(0))
bodies['sensor'] = t.copy(next(o.bRepBodies.item(0) for o in r.allOccurrences
    if o.fullPathName.startswith('SC616C_1kg_Fusion:1+') and o.bRepBodies.count))
def overlap(a, b):
    if not a.boundingBox.intersects(b.boundingBox): return 0.
    x = t.copy(a)
    assert t.booleanOperation(x, b, adsk.fusion.BooleanTypes.IntersectionBooleanType)
    return x.volume*1000
def moved(b, m):
    x = t.copy(b)
    assert t.transform(x, m)
    return x
def box(x0, x1, y0, y1, z0, z1):
    return t.createBox(adsk.core.OrientedBoundingBox3D.create(
        adsk.core.Point3D.create((x0+x1)/20, (y0+y1)/20, (z0+z1)/20),
        adsk.core.Vector3D.create(1,0,0), adsk.core.Vector3D.create(0,1,0),
        (x1-x0)/10, (y1-y0)/10, (z1-z0)/10))
fixed=[]
wrist_candidate_doc=globals().get('wrist_candidate_doc')
for o in r.allOccurrences:
    if o.isVisible and (o.fullPathName.startswith('Wrist_Roll_Clearance_V5:1') or
        (o.fullPathName.startswith('STS3215_c:1+') and '+Axes:' not in o.fullPathName)):
        selected_bodies=o.bRepBodies
        if wrist_candidate_doc and o.fullPathName=='Wrist_Roll_Clearance_V5:1':
            wd=adsk.fusion.Design.cast(next(doc for doc in app.documents if doc.name==wrist_candidate_doc).products.itemByProductType('DesignProductType'))
            selected_bodies=wd.rootComponent.bRepBodies
        for b in selected_bodies:
            if b.isSolid and b.volume>1e-6: fixed.append((o.fullPathName+'/'+b.name, t.copy(b)))
assert len(fixed) >= 10
cx=62.; cy=d.userParameters.itemByName('sc_brush_axis_y').value*10
brush=t.createCylinderOrCone(adsk.core.Point3D.create(cx/10,cy/10,-5.2), .75,
    adsk.core.Point3D.create(cx/10,cy/10,3.05), .75)
static=[]
keys=list(bodies)
for i,k in enumerate(keys):
    for q in keys[i+1:]:
        v=overlap(bodies[k],bodies[q])
        if v>.001: static.append([k,q,v])
assert not static, static
moving=list(bodies.items())+[('assumed_brush',brush)]
rotary=[]
for angle in range(-180,181,5):
    m=adsk.core.Matrix3D.create()
    m.setToRotation(math.radians(angle),adsk.core.Vector3D.create(0,1,0),adsk.core.Point3D.create(-.2,0,3.4))
    hits=[]
    for k,b in moving:
        mb=moved(b,m)
        for name,fb in fixed:
            v=overlap(mb,fb)
            if v>.01: hits.append([k,name,v])
    rotary.append({'angle_deg':angle,'hits':hits})
assert not any(row['hits'] for row in rotary), [row for row in rotary if row['hits']]
gauge=box(56.65,67.35,9.56,23.36,38.5,47)
keepout={k:overlap(bodies[k],gauge) for k in ('base','carrier','cartridge')}
assert max(keepout.values())<1e-4
pullout=[]
for distance in (1,10,24,50,100):
    m=adsk.core.Matrix3D.create(); m.translation=adsk.core.Vector3D.create(0,0,-distance/10)
    mb=moved(bodies['cartridge'],m)
    v=max([overlap(mb,b) for k,b in bodies.items() if k!='cartridge']+
          [overlap(mb,b) for _,b in fixed])
    assert v<1e-4, (distance,v)
    pullout.append([distance,v])
insertion=[]
for distance in (1,5,15,45,70):
    m=adsk.core.Matrix3D.create(); m.translation=adsk.core.Vector3D.create(0,-distance/10,0)
    mb=moved(bodies['sensor'],m)
    v=max([overlap(mb,bodies['base'])]+[overlap(mb,b) for _,b in fixed])
    assert v<1e-4,(distance,v)
    insertion.append([distance,v])
report={'passed':True,'static_interferences':static,'rotary_poses':rotary,
    'wrist_candidate_document':wrist_candidate_doc,
    'fixed_body_count':len(fixed),'gauge_keepout_mm3':keepout,
    'cartridge_pullout_down_mm_overlap_mm3':pullout,'cell_slide_in_mm_overlap_mm3':insertion,
    'base_volume_mm3':source.volume*1000,'main_timeline':[d.timeline.markerPosition,d.timeline.count],
    'wrist_volumes_mm3':[b.volume*1000 for b in r.occurrences.itemByName('Wrist_Roll_Clearance_V5:1').bRepBodies],
    'limitations':'5 degree sampled sweep, no upstream arm/wires/servo travel limits/FDM tolerances or elastic deflection',
    'main_geometry_edited':False}
with open(root+'/output/'+report_version+'/clearance.json','w',encoding='utf-8') as f:
    json.dump(report,f,ensure_ascii=False,indent=2)
print(report_version+' clearance PASSED:',len(rotary),'poses; fixed bodies',len(fixed))
print('Gauge, cartridge removal and sensor insertion clear. Main assembly not modified.')
