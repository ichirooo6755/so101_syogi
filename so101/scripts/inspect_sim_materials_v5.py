import adsk.core
import json
rows=[]
for lib in app.materialLibraries:
    matches=[]
    for material in lib.materials:
        if any(term in material.name.lower() for term in ('abs','aluminum','aluminium','アルミ','汎用プラスチック')):
            matches.append({'name':material.name,'id':material.id})
    rows.append({'library':lib.name,'id':lib.id,'matches':matches[:40]})
print(json.dumps(rows,ensure_ascii=False,indent=2))
