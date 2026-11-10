import adsk.core
import adsk.fusion
import json
import math

d=adsk.fusion.Design.cast(app.activeProduct); r=d.rootComponent
t=adsk.fusion.TemporaryBRepManager.get()
fixed=[(o.fullPathName,t.copy(b)) for o in r.allOccurrences if o.isVisible and
       (o.fullPathName.startswith('Wrist_Roll_Follower_SO101 v1:3') or o.fullPathName in
        ['STS3215_c:1+'+s+':1' for s in ('Top','Middle','Bottom')]) for b in o.bRepBodies if b.volume>1e-6]
def cyl(y0,y1,diam):
    return t.createCylinderOrCone(adsk.core.Point3D.create(-.2,y0/10,3.4),diam/20,
                                 adsk.core.Point3D.create(-.2,y1/10,3.4),diam/20)
def overlap(a,b):
    if not a.boundingBox.intersects(b.boundingBox): return 0
    a=t.copy(a); assert t.booleanOperation(a,b,adsk.fusion.BooleanTypes.IntersectionBooleanType)
    return a.volume*1000
pads=[]
for side,y0,y1,clear0,clear1 in [('negative',-31.5,-17.05,-18.2,-17.05),('positive',20.2,30.5,20.2,20.3)]:
    pad=cyl(y0,y1,24)
    assert t.booleanOperation(pad,cyl(y0-.1,y1+.1,7.8),adsk.fusion.BooleanTypes.DifferenceBooleanType)
    assert t.booleanOperation(pad,cyl(clear0,clear1,11),adsk.fusion.BooleanTypes.DifferenceBooleanType)
    pads.append((side,pad))
hits=[{'side':n,'fixed':fn,'mm3':overlap(p,b)} for n,p in pads for fn,b in fixed]
horns=[]
for o in r.allOccurrences:
    if not o.isVisible or '+Axes:' not in o.fullPathName: continue
    for b in o.bRepBodies:
        rows=[]
        for f in b.faces:
            g=f.geometry
            if isinstance(g,adsk.core.Cylinder) and abs(g.axis.y)>.99:
                row={'x':g.origin.x*10,'z':g.origin.z*10,'dia':g.radius*20,
                     'y_range':[f.boundingBox.minPoint.y*10,f.boundingBox.maxPoint.y*10]}
                if not any(all(abs(row[k]-q[k])<1e-5 for k in ('x','z','dia')) for q in rows): rows.append(row)
        horns.append({'name':o.fullPathName,'cylinders':rows})
report={'pads_fixed_interference':hits,'horns':horns}
with open('/Users/sugawaraichirou/Documents/ChatGPT/so101/output/v5/yoke_clearance_inspection.json','w',encoding='utf-8') as f: json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps(report,ensure_ascii=False,indent=2))
