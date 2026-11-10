from pathlib import Path
import json
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
src=(ROOT/'scripts/check_bolted_camera_v8.py').read_text().split('checks=[]',1)[0]
exec(compile(src,'v8_probe_helpers','exec'),globals())
complete=[tray,frame,cap]+xiao+hdr+connectors+hx+perf
axes=[('N+',CN),('N-',scale(CN,-1)),('A+',CA),('A-',scale(CA,-1)),('B+',CB),('B-',scale(CB,-1))]
out=[]
for label,bundle,obstacles in [('tray_off_arm',[tray],[main]),('complete_off_arm',complete,[main]),
                               ('complete_on_arm',complete,[main,back]+existing)]:
    for name,axis in axes:
        rows=bundle_path(label,bundle,axis,obstacles,(.1,.5,1,3,5,10,20,30,40))
        out.append({'route':label,'direction':name,'bad':[(r['offset_mm'],r['hits'][:1]) for r in rows if r['hits']]})
for k,b,bb in hardware:
    if k.startswith('M3x12_A_'):
        rows=bundle_path(k,[(k,b,bb)],EY,printed+existing+xiao+hdr+connectors+hx+perf,(.1,1,3,7,12,20,30))
        out.append({'route':k,'direction':'Y+','bad':[(r['offset_mm'],r['hits'][:1]) for r in rows if r['hits']]})
(CHECK/'route_probe.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps(out,ensure_ascii=False,indent=2))
