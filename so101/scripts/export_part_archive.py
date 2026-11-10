import adsk.core
import adsk.fusion
import os
d=adsk.fusion.Design.cast(app.activeProduct)
comp=d.rootComponent.occurrences.itemByName('部品１:1').component
path='/Users/sugawaraichirou/Documents/ChatGPT/so101/output/so101_sc616c_mount_part.f3d'
result=d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(path,comp))
print('part archive result',result,'bytes',os.path.getsize(path) if os.path.exists(path) else None)
