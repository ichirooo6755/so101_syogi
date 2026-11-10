import adsk.core
import adsk.fusion
import json
from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
exec(compile((ROOT/'scripts/build_camera_addon_v1.py').read_text().split("progress('building_temporary_geometry')",1)[0],'mm','exec'),globals())
out=ROOT/'output/camera_mount_v7'; d0=json.loads((out/'design_check.json').read_text()); CB=tuple(d0['camera_basis']['B'])
ds=[]
for doc in app.documents:
    d=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    if d and d.rootComponent.occurrences.itemByName('01_A_slot_socket_V7:1'):ds.append(d)
root=ds[-1].rootComponent
def part(n):return T.copy(root.occurrences.itemByName(n+':1').bRepBodies.item(0))
gate=part('03_screw_locked_key_V7'); main=part('01_A_slot_socket_V7')
unit=[(n,part(n)) for n in ('04_XIAO_header_tray_V7','05_HX711_perf_stack_V7','06_stack_end_cap_V7')]
rows=[]
for dist in (.1,.25,.5,1,1.2,2,3,4,5,8,10,15):
    hits=[]
    for name,b in unit:
        q=T.copy(b); m=adsk.core.Matrix3D.create();m.translation=vec(scale(CB,-dist/10));T.transform(q,m)
        for target,label in ((gate,'gate'),(main,'main')):
            if (v:=hit(q,target,bbox(q),bbox(target)))>.01:hits.append([name,label,round(v,5)])
    rows.append({'withdraw_mm':dist,'hits':hits})
(out/'withdraw_probe.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
