import adsk.core
import adsk.fusion
import json
d=adsk.fusion.Design.cast(app.activeProduct)
r=d.rootComponent
def pt(p): return [round(v*10,6) for v in p.asArray()]
data={'document':app.activeDocument.name,'modified':app.activeDocument.isModified,
      'timeline_marker':d.timeline.markerPosition,'timeline_count':d.timeline.count,
      'occurrences':[], 'parameters':[{ 'name':p.name,'expression':p.expression} for p in d.userParameters]}
for o in r.allOccurrences:
    if not o.isVisible: continue
    row={'name':o.fullPathName,'transform':list(o.transform2.asArray()),'bodies':[]}
    for b in o.bRepBodies:
        row['bodies'].append({'name':b.name,'volume':b.volume*1000,'bbox':[pt(b.boundingBox.minPoint),pt(b.boundingBox.maxPoint)],
         'faces':[{'id':f.tempId,'bbox':[pt(f.boundingBox.minPoint),pt(f.boundingBox.maxPoint)],'area':f.area*100,'type':f.geometry.objectType,
           **({'axis':list(f.geometry.axis.asArray()),'origin':pt(f.geometry.origin),'radius':f.geometry.radius*10} if isinstance(f.geometry,adsk.core.Cylinder) else {})} for f in b.faces]})
    data['occurrences'].append(row)
with open('/Users/sugawaraichirou/Documents/ChatGPT/so101/tmp/v2_before.json','w') as f: json.dump(data,f,ensure_ascii=False,indent=2)
print(json.dumps({k:v for k,v in data.items() if k!='occurrences'},ensure_ascii=False,indent=2))
print([(o['name'],[(b['name'],b['bbox']) for b in o['bodies']]) for o in data['occurrences']])
out='/Users/sugawaraichirou/Documents/ChatGPT/so101/reference/so101_before_reinforcement_and_holder.f3d'
print('checkpoint',d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(out)))
