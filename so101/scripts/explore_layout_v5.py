import adsk.core
import adsk.fusion
import json
import math
import os

d = adsk.fusion.Design.cast(app.activeProduct); r = d.rootComponent
t = adsk.fusion.TemporaryBRepManager.get()
root = '/Users/sugawaraichirou/Documents/ChatGPT/so101'
fixed = [(o.fullPathName, t.copy(b)) for o in r.allOccurrences if o.isVisible and
         (o.fullPathName.startswith('Wrist_Roll_Follower_SO101 v1:3') or
          o.fullPathName in ['STS3215_c:1+' + s + ':1' for s in ('Top', 'Middle', 'Bottom')])
         for b in o.bRepBodies if b.volume > 1e-6]
moving = [(n, t.copy(r.occurrences.itemByName(n).bRepBodies.item(0))) for n in
          ('Brush_Load_Carrier_Centered:1', 'Brush_Cartridge_Centered_15mm:1')]
sensor = next(o for o in r.allOccurrences if o.fullPathName.startswith('SC616C_1kg_Fusion:1+') and o.bRepBodies.count)
moving.append(('cell', t.copy(sensor.bRepBodies.item(0))))
moving.append(('brush_82p5mm', t.createCylinderOrCone(adsk.core.Point3D.create(3, .276294620236, -7.5), .75,
                                                     adsk.core.Point3D.create(3, .276294620236, .75), .75)))
def tr(b, dx, dz, a=0):
    b = t.copy(b)
    m = adsk.core.Matrix3D.create(); m.translation = adsk.core.Vector3D.create(dx/10, 0, dz/10)
    assert t.transform(b, m)
    m = adsk.core.Matrix3D.create(); m.setToRotation(math.radians(a), adsk.core.Vector3D.create(0,1,0), adsk.core.Point3D.create(-.2,0,3.4))
    assert t.transform(b, m)
    return b
def hit(b, c):
    if not b.boundingBox.intersects(c.boundingBox): return 0
    b = t.copy(b)
    assert t.booleanOperation(b, c, adsk.fusion.BooleanTypes.IntersectionBooleanType)
    return b.volume * 1000
report = []
for dx,dz in [(45,35),(50,35),(55,35),(50,0)]:
    dx0=dx-.377371505303448; dz0=dz+.1044318867712
    rows=[]
    for a in range(-160,161,10):
        hits=[]
        for name,b in moving:
            for fn,fb in fixed:
                v=hit(tr(b,dx0,dz0,a),fb)
                if v>.01: hits.append([name,fn,round(v,3)])
        rows.append({'angle':a,'hits':hits})
    limits={}
    for include_brush,label in ((False,'hardware'),(True,'with_assumed_brush')):
        limits[label]=[]
        for sign in (-1,1):
            first=next((abs(row['angle']) for row in (rows if sign>0 else reversed(rows)) if row['angle']*sign>0 and
                        any(include_brush or h[0]!='brush_82p5mm' for h in row['hits'])),None)
            limits[label].append(None if first is None else sign*first)
    report.append({'dx_mm':dx,'dz_mm':dz,'first_collision_coarse_deg':limits,'sweep':rows})
with open(root+'/output/v5/layout_exploration_extended.json','w',encoding='utf-8') as f: json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps([{k:v for k,v in row.items() if k!='sweep'} for row in report],ensure_ascii=False,indent=2))
