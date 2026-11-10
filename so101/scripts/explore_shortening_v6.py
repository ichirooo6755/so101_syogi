import adsk.core
import adsk.fusion
import json
import math
import os

root='/Users/sugawaraichirou/Documents/ChatGPT/so101'; out=root+'/output/v6'; os.makedirs(out,exist_ok=True)
doc=next(doc for doc in app.documents if doc.name=='so101書道')
d=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType')); r=d.rootComponent
t=adsk.fusion.TemporaryBRepManager.get()
fixed=[(o.fullPathName,t.copy(b)) for o in r.allOccurrences if o.isVisible and
       (o.fullPathName.startswith('Wrist_Roll_Clearance_V5:1') or (o.fullPathName.startswith('STS3215_c:1+') and '+Axes:' not in o.fullPathName))
       for b in o.bRepBodies if b.volume>1e-6]
moving=[(name,t.copy(r.occurrences.itemByName(name).bRepBodies.item(0))) for name in
        ('Brush_Load_Carrier_Compact_V5:1','Brush_Cartridge_Symmetric_15mm_V5:1')]
moving.append(('sensor',t.copy(next(o.bRepBodies.item(0) for o in r.allOccurrences if o.fullPathName.startswith('SC616C_1kg_Fusion:1+') and o.bRepBodies.count))))
moving.append(('assumed_15x82p5_brush',t.createCylinderOrCone(adsk.core.Point3D.create(7.8,.276294620236,-5.2),.75,
                                                          adsk.core.Point3D.create(7.8,.276294620236,3.05),.75)))
def move(b,dx,a):
    b=t.copy(b); m=adsk.core.Matrix3D.create(); m.translation=adsk.core.Vector3D.create(dx/10,0,0); assert t.transform(b,m)
    m=adsk.core.Matrix3D.create(); m.setToRotation(math.radians(a),adsk.core.Vector3D.create(0,1,0),adsk.core.Point3D.create(-.2,0,3.4))
    assert t.transform(b,m); return b
def overlap(a,b):
    if not a.boundingBox.intersects(b.boundingBox): return 0
    a=t.copy(a); assert t.booleanOperation(a,b,adsk.fusion.BooleanTypes.IntersectionBooleanType)
    return a.volume*1000
report=[]
for shift in (-10,-14,-16,-18,-20,-24):
    rows=[]
    for a in range(-180,181,5):
        hits=[]
        for name,b in moving:
            cb=move(b,shift,a)
            for fn,fb in fixed:
                v=overlap(cb,fb)
                if v>.01: hits.append([name,fn,round(v,5)])
        if hits: rows.append({'angle':a,'hits':hits})
    report.append({'shift_x_mm':shift,'brush_axis_x_mm':78+shift,'all_poses_clear':not rows,
                   'collision_angles_deg':[x['angle'] for x in rows],'collisions':rows})
with open(out+'/shortening_candidates.json','w',encoding='utf-8') as f: json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps([{k:v for k,v in row.items() if k!='collisions'} for row in report],ensure_ascii=False,indent=2))
