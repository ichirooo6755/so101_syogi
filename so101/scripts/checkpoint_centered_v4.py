import adsk.core
import adsk.fusion
import json
import os

d=adsk.fusion.Design.cast(app.activeProduct); r=d.rootComponent
assert app.activeDocument.name=='so101書道'
root='/Users/sugawaraichirou/Documents/ChatGPT/so101'
path=root+'/tmp/v4_before.json'
assert not os.path.exists(path),'The v4 baseline already exists; do not overwrite it.'
data={'document':app.activeDocument.name,'modified':app.activeDocument.isModified,
      'timeline_marker':d.timeline.markerPosition,'timeline_count':d.timeline.count,
      'parameters':{p.name:p.expression for p in d.userParameters},'occurrences':[]}
for o in r.allOccurrences:
    data['occurrences'].append({'name':o.fullPathName,'visible':o.isVisible,'light':o.isLightBulbOn,
        'transform':list(o.transform2.asArray()),'bodies':[{'name':b.name,'volume_mm3':b.volume*1000,
        'bbox_mm':[[v*10 for v in p.asArray()] for p in (b.boundingBox.minPoint,b.boundingBox.maxPoint)]} for b in o.bRepBodies]})
archive=root+'/reference/so101_before_centered_load_path_v4.f3d'
assert not os.path.exists(archive)
assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(archive))
with open(path,'w',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,indent=2)
print(json.dumps({key:value for key,value in data.items() if key!='parameters'},ensure_ascii=False,indent=2))
