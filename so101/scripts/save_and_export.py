import adsk.core
import adsk.fusion
import json
import os
d=adsk.fusion.Design.cast(app.activeProduct)
doc=app.activeDocument
out='/Users/sugawaraichirou/Documents/ChatGPT/so101/output'
os.makedirs(out,exist_ok=True)
comp=d.rootComponent.occurrences.itemByName('部品１:1').component
manager=d.exportManager
results={}
assert doc.isSaved, 'Original document needs an initial cloud folder before save'
results['fusion_saved']=doc.save('SC616C fixed-end mount; M3 holes at 7.4 mm pitch, floating flexure, 15 mm brush parameter')
results['fusion_archive']=manager.execute(manager.createFusionArchiveExportOptions(out+'/so101_calligraphy_sc616c_mount.f3d'))
results['mount_step']=manager.execute(manager.createSTEPExportOptions(out+'/so101_sc616c_mount.step',comp))
stl=manager.createSTLExportOptions(comp.bRepBodies.item(0),out+'/so101_sc616c_mount.stl')
stl.meshRefinement=adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
results['mount_stl']=manager.execute(stl)
results['is_modified']=doc.isModified
results['timeline_marker']=d.timeline.markerPosition
results['timeline_count']=d.timeline.count
print(json.dumps(results,indent=2))
with open(out+'/export_status.json','w') as f: json.dump(results,f,indent=2)
