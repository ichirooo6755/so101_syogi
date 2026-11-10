from pathlib import Path
import json
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
src=(ROOT/'scripts/check_stack_assembly_v7.py').read_text()
src=src.split('paths=[]',1)[0]
exec(compile(src,'key_probe_prefix','exec'),globals())
key_core=union([cbox(6,11.25,17.5,20.3,-3.8,-2.2),cbox(11.25,14.5,16.8,22.5,-3.8,-2.2)])
key_deflected=[('core',key_core,bbox(key_core))]
for i in range(16):
    a0=-.5+i*(13.5/16); a1=-.5+(i+1)*(13.5/16)+.025
    t=(13-(a0+a1)/2)/13.5; off=.55*t*t*(3-2*t)
    q=cbox(a0,a1,21.3-off,22.5-off,-3.8,-2.2); key_deflected.append((str(i),q,bbox(q)))
q=cbox(-.5,1,21.95,22.45,-3.8,-2.2);key_deflected.append(('barb',q,bbox(q)))
complete=printed[3:]+xiao+hdr+connectors+hx+perf
obstacles=printed[:2]+complete+existing
out=[]
for start in (15,20,25,30,40):
    initial=cached([(k,translate(b,scale(CA,start))) for k,b,bb in key_deflected])
    for label,axis in (('N-',scale(CN,-1)),('B+',CB),('B-',scale(CB,-1))):
        result=bundle_path(label,initial,axis,obstacles,(.1,.5,1,3,5,10,20,30,40))
        bad=[{'d':r['offset_mm'],'hits':r['hits'][:2]} for r in result if r['hits']]
        out.append({'start_A_mm':start,'axis':label,'bad':bad})
(CHECK/'key_approaches.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps(out,ensure_ascii=False,indent=2))
