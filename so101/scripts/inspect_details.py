import adsk.core
import adsk.fusion
import json
design=adsk.fusion.Design.cast(app.activeProduct)
root=design.rootComponent
def pt(p): return [round(c*10,5) for c in p.asArray()]
occurrences=[]
for o in root.allOccurrences:
    info={"name":o.fullPathName,"component":o.component.name,"visible":o.isVisible,
          "transform":list(o.transform2.asArray()),"bodies":[]}
    for b in o.bRepBodies:
        info['bodies'].append({"name":b.name,"bbox":[pt(b.boundingBox.minPoint),pt(b.boundingBox.maxPoint)],
           "faces":[{"id":f.tempId,"type":f.geometry.objectType,"centroid":pt(f.centroid),
           **({"axis":list(f.geometry.axis.asArray()),"origin":pt(f.geometry.origin),"radius":f.geometry.radius*10} if isinstance(f.geometry,adsk.core.Cylinder) else {})} for f in b.faces]})
    occurrences.append(info)
timeline=[]
for i in range(design.timeline.count):
    t=design.timeline.item(i)
    try:
        e=t.entity
        item={"i":i,"name":e.name,"type":e.objectType,"suppressed":t.isSuppressed,
              "health":int(e.healthState) if hasattr(e,'healthState') else None}
    except Exception as exc: item={"i":i,"error":str(exc)}
    timeline.append(item)
data={"occurrences":occurrences,"timeline":timeline}
with open('/Users/sugawaraichirou/Documents/ChatGPT/so101/tmp/fusion_details.json','w') as f: json.dump(data,f,ensure_ascii=False,indent=2)
print(json.dumps({"occurrences":[{"name":o['name'],"visible":o['visible'],"bodies":[{k:v for k,v in b.items() if k!='faces'} for b in o['bodies']]} for o in occurrences],"timeline":timeline},ensure_ascii=False,indent=2))
