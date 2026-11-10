"""Temporary-body fit trials. No changes to any source CAD geometry."""
import adsk.core
import adsk.fusion
import json
import math
from pathlib import Path

BASE=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
main=next(x for x in app.documents if x.name.startswith('so101書道'))
d=adsk.fusion.Design.cast(main.products.itemByProductType('DesignProductType'))
r=d.rootComponent
t=adsk.fusion.TemporaryBRepManager.get()
def pt(x,y,z): return adsk.core.Point3D.create(x/10,y/10,z/10)
def box(x0,x1,y0,y1,z0,z1):
    return t.createBox(adsk.core.OrientedBoundingBox3D.create(pt((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),
        adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
def cyl(x,z,y0,y1,dia): return t.createCylinderOrCone(pt(x,y0,z),dia/20,pt(x,y1,z),dia/20)
def hit(a,b):
    if not a.boundingBox.intersects(b.boundingBox): return 0.
    q=t.copy(a)
    assert t.booleanOperation(q,b,adsk.fusion.BooleanTypes.IntersectionBooleanType)
    return q.volume*1000
fixed=[]; moving=[]
for o in r.allOccurrences:
    if not o.isVisible: continue
    if o.fullPathName.startswith('STS3215_c:1+') and '+Axes:' not in o.fullPathName:
        fixed += [(o.fullPathName+'/'+b.name,t.copy(b)) for b in o.bRepBodies if b.isSolid and b.volume>1e-6]
    elif o.fullPathName=='Wrist_Roll_Clearance_V8_元取付対応:1':
        fixed += [('wrist',t.copy(b)) for b in o.bRepBodies if b.isSolid]
    elif o.fullPathName in ('部品１_V8_元取付形状保持:1','Brush_Load_Carrier_Compact_V5:1','Brush_Cartridge_Symmetric_15mm_V5:1') or o.fullPathName.startswith('SC616C_1kg_Fusion:1+'):
        moving += [(o.fullPathName,t.copy(b)) for b in o.bRepBodies if b.isSolid]

Y=21.2411812186212
trial={
    'anchor_3mm':box(-6.8,2.8,Y,Y+3,3.7,19.8),
    'anchor_5.5mm':box(-6.8,2.8,Y,Y+5.5,3.7,19.8),
    'M3x8_upper_head':cyl(-2,15.8017381605,Y+5.5,Y+8.5,5.5),
    'M3x8_lower_head':cyl(-2,7.7017381605,Y+5.5,Y+8.5,5.5),
    'side_route':box(1,17,Y,Y+3,6,19),
    'inward_route':box(14,18,8,Y+3,16,21),
    'hx_full_envelope':box(14.5,28,-15.4,15.4,34.5,58),
    'hx_back_tray':box(12,14.5,-17.7,17.7,32.5,60.5),
    'txs_rear_envelope':box(5,12,-14.3,14.3,45.5,59),
}
# Conservative open camera envelope: 21 mm along Y, 17.8 mm tilted width,
# 15 mm front height; connector and board version need their own later check.
def camera_box(cx,cz,ang):
    an=math.radians(ang)
    n=adsk.core.Vector3D.create(math.sin(an),0,-math.cos(an))
    u=adsk.core.Vector3D.create(0,-1,0)
    # x=u,y=n,z=u cross n. Offset center of bounding envelope 7 mm outwards.
    c=pt(cx+7*math.sin(an),0,cz-7*math.cos(an))
    return t.createBox(adsk.core.OrientedBoundingBox3D.create(c,u,n,2.5,1.6,1.86))
for cx,cz in ((23,23),(23,26),(25,26),(22,25)):
    for angle in (20,25,30):
        trial[f'camera_{cx}_{cz}_{angle}']=camera_box(cx,cz,angle)
report={'static':{},'sweep_hits':{},'pocket_samples':[]}
for name,b in trial.items():
    report['static'][name]=[[k,round(v,6)] for k,q in fixed if (v:=hit(b,q))>.001]
    report['sweep_hits'][name]=[]
for angle in range(-180,181,5):
    m=adsk.core.Matrix3D.create()
    m.setToRotation(math.radians(angle),adsk.core.Vector3D.create(0,1,0),pt(-2,0,34))
    for k,b in moving:
        mb=t.copy(b); t.transform(mb,m)
        for name,q in trial.items():
            v=hit(mb,q)
            if v>.01:
                report['sweep_hits'][name].append([angle,k,round(v,4)])
w=next(b for k,b in fixed if k=='wrist')
for y in (17,17.5,17.94,18,18.5,20,21,21.3,22,24):
    row={'y':y,'r':[]}
    for rad in (0,1.5,1.8,2.5,2.8,3.2,3.5,4):
        row['r'].append([rad,int(w.pointContainment(pt(-2+rad,y,15.8017381605)))])
    report['pocket_samples'].append(row)
(BASE/'output/camera_mount_v1/layout_probe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
for name in trial:
    print(name,'static',report['static'][name],'sweep',len(report['sweep_hits'][name]),report['sweep_hits'][name][:4])
print('pocket',report['pocket_samples'])
print('Source untouched:',not main.isModified,'timeline',d.timeline.count)
