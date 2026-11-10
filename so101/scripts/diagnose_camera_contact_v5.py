from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
script=(ROOT/'scripts/build_printable_camera_v5.py').read_text().split('tail=v4.split',1)[0]
exec(compile(script,'temporary_v5_geometry_only','exec'),globals())
q=T.copy(source_camera.bRepBodies.item(37)); qb=bbox(q)
conflicts=[]
for i,b in enumerate(pieces):
    bb=bbox(b); volume=hit(b,q,bb,qb)
    if volume>.001:conflicts.append({'piece_index':i,'volume_mm3':volume,'bounds_mm':bb})
result={'reference_bbox_mm':qb,'reference_transform':list(source_camera.transform2.asArray()),'conflicts':conflicts}
(OUT/'camera_contact_diagnostic.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
