import adsk.core
import adsk.fusion
import json
from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
helper=(ROOT/'scripts/build_camera_addon_v1.py').read_text().split("progress('building_temporary_geometry')",1)[0]
exec(compile(helper,'mm_helpers','exec'),globals())
OUT=ROOT/'output/camera_mount_v6'
build=json.loads((OUT/'design_check.json').read_text())
CA=tuple(build['camera_basis']['A']); CB=tuple(build['camera_basis']['B']); CN=tuple(build['camera_basis']['N']); CO=tuple(build['parameters']['camera_pcb_origin_mm'])
docs=[]
for doc in app.documents:
    d=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    if d and d.rootComponent.occurrences.itemByName('01_flat_carrier_socket_V6:1'):docs.append((doc,d))
doc,d=docs[-1]; o=d.rootComponent.occurrences.itemByName('REFERENCE_XIAO_Sense_1pc:1')
def local(p):
    delta=[q*10-c for q,c in zip(p.asArray(),CO)]
    return [sum(v*a for v,a in zip(delta,axis)) for axis in (CA,CB,CN)]
rows=[]
for i in (10,18,37,71,101):
    b=T.copy(o.bRepBodies.item(i)); ps=[local(v.geometry) for v in b.vertices]
    rows.append({'index':i,'local_vertex_bounds':[[min(p[j] for p in ps) for j in range(3)],[max(p[j] for p in ps) for j in range(3)]],
        'vertices':ps if i==37 else [],
        'cylinders':[{'origin':local(f.geometry.origin),'axis':f.geometry.axis.asArray()} for f in b.faces
                     if f.geometry.surfaceType==adsk.core.SurfaceTypes.CylinderSurfaceType]})
tray=T.copy(d.rootComponent.occurrences.itemByName('04_slide_in_camera_tray_V6:1').bRepBodies.item(0))
gate=T.copy(d.rootComponent.occurrences.itemByName('03_common_screw_locked_gate_V6:1').bRepBodies.item(0))
withdraw=[]
for distance in (.2,.5,1,1.2,2,3,4,5,8,10,15):
    q=T.copy(tray); m=adsk.core.Matrix3D.create(); m.translation=vec(scale(CB,-distance/10)); T.transform(q,m)
    withdraw.append([distance,hit(q,gate)])
(OUT/'camera_retention_diagnostic.json').write_text(json.dumps({'bodies':rows,'withdraw_vs_gate':withdraw},indent=2))
print(json.dumps({'bodies':[{k:v for k,v in r.items() if k not in ('vertices','cylinders')} for r in rows],
    'withdraw':withdraw},indent=2))
