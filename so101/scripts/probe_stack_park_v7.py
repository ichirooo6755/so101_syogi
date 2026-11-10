import adsk.core
import adsk.fusion
import json
from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
exec(compile((ROOT/'scripts/build_camera_addon_v1.py').read_text().split("progress('building_temporary_geometry')",1)[0],'mm','exec'),globals())
OUT=ROOT/'output/camera_mount_v7'; build=json.loads((OUT/'design_check.json').read_text())
CB=tuple(build['camera_basis']['B'])
owned=[]
for doc in app.documents:
    d=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    if d and d.rootComponent.occurrences.itemByName('01_A_slot_socket_V7:1'):owned.append((doc,d))
d=owned[-1][1]; root=d.rootComponent
def bodies(n):return [(b.name,T.copy(b),bbox(b)) for b in root.occurrences.itemByName(n+':1').bRepBodies]
gate=bodies('03_screw_locked_key_V7')[0][1]
unit=[]
for n in ('04_XIAO_header_tray_V7','05_HX711_perf_stack_V7','06_stack_end_cap_V7',
    'REFERENCE_XIAO_Sense_1pc','REFERENCE_XIAO_two_pin_headers',
    'REFERENCE_SparkFun_SEN13879_HX711_1pc','REFERENCE_perfboard_same_size_1pc'):unit+=bodies(n)
def shifted(b,delta):
    q=T.copy(b); m=adsk.core.Matrix3D.create(); m.translation=vec(scale(delta,.1)); T.transform(q,m); return q
rows=[]
for i in range(1,25):
    p=i*.5; g=shifted(gate,(0,p,0)); gb=bbox(g); close=[]; entry=[]
    for name,b,bb in unit:
        v=hit(g,b,gb,bb)
        if v>.01:close.append([name,round(v,4)])
        for dist in (.1,.25,.5,1,2,3,5,8,10,15,20):
            delta=scale(CB,-dist)
            shifted_bb=[[bb[j][k]+delta[k] for k in range(3)] for j in (0,1)]
            if not boxes_overlap(gb,shifted_bb):continue
            v=hit(g,shifted(b,delta),gb,shifted_bb)
            if v>.01:entry.append([name,dist,round(v,4)]);break
    rows.append({'park_y_mm':p,'gate_vs_final_unit':close,'insertion_hits':entry})
(OUT/'park_probe.json').write_text(json.dumps(rows,indent=2))
print(json.dumps([{'park_y_mm':r['park_y_mm'],'unit_hits':len(r['gate_vs_final_unit']),
    'insertion_hits':len(r['insertion_hits'])} for r in rows],indent=2))
