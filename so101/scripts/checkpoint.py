import adsk.core
import adsk.fusion
import os
import json
design=adsk.fusion.Design.cast(app.activeProduct)
root=design.rootComponent
base='/Users/sugawaraichirou/Documents/ChatGPT/so101/reference'
os.makedirs(base,exist_ok=True)
manager=design.exportManager
for label,comp in [('so101_before_sc616c_mount',root),('yoke_before_sc616c_mount',root.occurrences.itemByName('部品１:1').component)]:
    try:
        options=manager.createFusionArchiveExportOptions(base+'/'+label+'.f3d',comp)
        print(label,manager.execute(options))
    except Exception as exc: print(label,'export:',str(exc))
print('brush_dependencies',json.dumps([{'name':p.name,'expression':p.expression} for p in design.allParameters if 'brush_dia' in p.expression],ensure_ascii=False))
print('marker',design.timeline.markerPosition)
