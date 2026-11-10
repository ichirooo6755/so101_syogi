from pathlib import Path
import json
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
src=(ROOT/'scripts/check_bolted_camera_v8.py').read_text().split('checks=[]',1)[0]
exec(compile(src,'preload_probe','exec'),globals())
q=translate(tray[1],scale(CN,-.25));assert T.booleanOperation(q,main[1],I)
coords=[]
for v in q.vertices:
    p=tuple(x*10 for x in v.geometry.asArray());delta=tuple(p[i]-CO[i] for i in range(3))
    coords.append([sum(delta[i]*axis[i] for i in range(3)) for axis in (CA,CB,CN)])
print(json.dumps({'volume_mm3':q.volume*1000,'bounds_local':[[min(p[i] for p in coords) for i in range(3)],[max(p[i] for p in coords) for i in range(3)]]},indent=2))
