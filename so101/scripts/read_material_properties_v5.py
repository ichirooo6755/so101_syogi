import adsk.core
import json
lib=app.materialLibraries.itemById('C1EEA57C-3F56-45FC-B8CB-A9EC46A9994C')
result=[]
for mid in ('PrismMaterial-022','PrismMaterial-002'):
    m=lib.materials.itemById(mid)
    props=[]
    for p in m.materialProperties:
        if p.objectType=='adsk::core::FloatProperty':
            props.append({'id':p.id,'name':p.name,'value':p.value,'units':p.units,'readonly':p.isReadOnly})
    result.append({'name':m.name,'id':mid,'properties':props})
print(json.dumps(result,ensure_ascii=False,indent=2))
