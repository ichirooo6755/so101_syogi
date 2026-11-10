import adsk.core
import adsk.fusion
import json
import os
d=adsk.fusion.Design.cast(app.activeProduct)
doc=app.activeDocument
r=d.rootComponent
def pt(p): return [v*10 for v in p.asArray()]
data={'document':doc.name,'modified':doc.isModified,'timeline_marker':d.timeline.markerPosition,
      'timeline_count':d.timeline.count,'parameters':[{ 'name':p.name,'expression':p.expression} for p in d.userParameters],
      'selection':[],'occurrences':[]}
for selection in ui.activeSelections:
    e=selection.entity
    data['selection'].append({'type':e.objectType,'parent':e.body.name if hasattr(e,'body') else getattr(e,'name','')})
for o in r.allOccurrences:
    if not o.isVisible: continue
    data['occurrences'].append({'name':o.fullPathName,'transform':list(o.transform2.asArray()),
        'bodies':[{'name':b.name,'volume':b.volume*1000,'bbox':[pt(b.boundingBox.minPoint),pt(b.boundingBox.maxPoint)]} for b in o.bRepBodies]})
path='/Users/sugawaraichirou/Documents/ChatGPT/so101/tmp/v3_before.json'
with open(path,'w') as f: json.dump(data,f,ensure_ascii=False,indent=2)
checkpoint='/Users/sugawaraichirou/Documents/ChatGPT/so101/reference/so101_before_slide_in_mount_and_threads.f3d'
if not os.path.exists(checkpoint):
    print('checkpoint',d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(checkpoint)))
print(json.dumps(data,ensure_ascii=False,indent=2))
