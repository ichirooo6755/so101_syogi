"""Read-only wrist section maps to locate a non-invasive saddle attachment."""
import adsk.core
import adsk.fusion
import json
from pathlib import Path
BASE=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
main=next(x for x in app.documents if x.name.startswith('so101書道'))
d=adsk.fusion.Design.cast(main.products.itemByProductType('DesignProductType'))
r=d.rootComponent; t=adsk.fusion.TemporaryBRepManager.get()
w=t.copy(r.occurrences.itemByName('Wrist_Roll_Clearance_V8_元取付対応:1').bRepBodies.item(0))
servo=[t.copy(b) for o in r.allOccurrences if o.isVisible and o.fullPathName.startswith('STS3215_c:1+')
       for b in o.bRepBodies if b.isSolid]
sections=[]
for y in (-12,0,12,16,19,23):
    rows=[]
    for z in range(8,-9,-1):
        line=''
        for x in range(-29,17):
            p=adsk.core.Point3D.create(x/10,y/10,z/10)
            iw=int(w.pointContainment(p))!=2
            ins=any(b.boundingBox.contains(p) and int(b.pointContainment(p))!=2 for b in servo)
            line+= '!' if iw and ins else 'W' if iw else 'S' if ins else '.'
        rows.append([z,line])
    sections.append({'Y':y,'X_start':-29,'X_end':16,'rows':rows})
faces=[]
for f in w.faces:
    if f.geometry.surfaceType==adsk.core.SurfaceTypes.PlaneSurfaceType:
        bb=f.boundingBox
        faces.append({'area':f.area*100,'normal':list(f.geometry.normal.asArray()),
            'box':[[getattr(p,c)*10 for c in ('x','y','z')] for p in (bb.minPoint,bb.maxPoint)]})
(BASE/'output/camera_mount_v1/wrist_saddle_sections.json').write_text(json.dumps({'sections':sections,'faces':faces},indent=2))
for s in sections:
    print('Y',s['Y'],'X -29 to16')
    for z,line in s['rows']: print('%3d'%z,line)
print('PLANAR LARGE FACES',json.dumps([f for f in faces if f['area']>40],indent=2))
