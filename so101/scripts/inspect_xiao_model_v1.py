"""Import the manufacturer reference into its own document, never the source assembly."""
import adsk.core
import adsk.fusion
import json
from pathlib import Path

BASE=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
path=BASE/'reference/camera_electronics/xiao_official/Seeed Studio XIAO-ESP32-S3-Sense.step'
doc=app.importManager.importToNewDocument(app.importManager.createSTEPImportOptions(str(path)))
d=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
def bbox(b):
    return [[getattr(p,c)*10 for c in ('x','y','z')]
            for p in (b.boundingBox.minPoint,b.boundingBox.maxPoint)]
rows=[]
for o in d.rootComponent.allOccurrences:
    for b in o.bRepBodies:
        if b.isSolid:
            rows.append({'path':o.fullPathName+'/'+b.name,'volume_mm3':b.volume*1000,'bbox_mm':bbox(b)})
for b in d.rootComponent.bRepBodies:
    rows.append({'path':'root/'+b.name,'volume_mm3':b.volume*1000,'bbox_mm':bbox(b)})
(BASE/'output/camera_mount_v1/xiao_reference_inventory.json').write_text(json.dumps(rows,indent=2))
print('Reference document:',doc.name)
print(json.dumps(rows,indent=2))
