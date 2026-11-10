"""Check each gusset stays one connected solid after bolt-tool relief cuts."""
from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
script=(ROOT/'scripts/build_printable_camera_v5.py').read_text().split('tail=v4.split',1)[0]
exec(compile(script,'temporary_gusset_geometry_only','exec'),globals())
rows=[]
for index,body in enumerate(pieces[-2:]):
    q=T.copy(body)
    for x in (22,34):subtract(q,[cylinder((x,40,35),(x,90,35),6.2)])
    assert q.lumps.count==1,(index,q.lumps.count)
    root=box(10,46,35.75,40,20.5,45.5)
    root_before=hit(body,root); root_after=hit(q,root)
    assert root_after>10 and abs(root_after-root_before)<1e-5
    sections=[]
    for y in (40.01,41.01,42.01,43.01,44.01,45.01):
        slab=box(-100,100,y,y+.1,-100,100)
        a=hit(body,slab)/.1; b=hit(q,slab)/.1
        if a>.01:sections.append({'Y_mm':y,'original_area_mm2':a,'after_relief_area_mm2':b})
    rows.append({'rib':index+1,'connected_solids_after_tool_relief':1,
        'root_connection_volume_mm3':root_after,'root_connection_unchanged':True,'sections':sections})
out=ROOT/'output/print_camera_hx711_v5/checks/gusset_root_connectivity.json'
out.write_text(json.dumps({'passed':True,'gussets':rows,'not_a_structural_stress_or_strength_test':True},indent=2))
print(json.dumps({'passed':True,'gussets':rows},indent=2))
