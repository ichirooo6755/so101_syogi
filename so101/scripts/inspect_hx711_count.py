"""Read-only electronics inventory of the live Fusion document."""
import adsk.core
import adsk.fusion
import json
from pathlib import Path

out=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101/output/camera_mount_v1')
rows=[]
for doc in app.documents:
    d=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    if not d: continue
    item={'name':doc.name,'active':doc==app.activeDocument,'modified':doc.isModified,
          'root_occurrences':[],'electronics':[]}
    for o in d.rootComponent.occurrences:
        item['root_occurrences'].append({'name':o.name,'visible':o.isVisible})
    for o in d.rootComponent.allOccurrences:
        if any(s in o.fullPathName.lower() for s in ('hx711','txs','level','112370')):
            bodies=[]
            for b in o.bRepBodies:
                bb=b.boundingBox
                bodies.append({'name':b.name,'visible':b.isVisible,'light_on':b.isLightBulbOn,
                    'size_mm':[(hi-lo)*10 for hi,lo in zip(bb.maxPoint.asArray(),bb.minPoint.asArray())],
                    'bounds_mm':[[v*10 for v in p.asArray()] for p in (bb.minPoint,bb.maxPoint)]})
            item['electronics'].append({'path':o.fullPathName,'visible':o.isVisible,'bodies':bodies})
    rows.append(item)
(out/'hx711_live_inventory.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
app.activeViewport.saveAsImageFile(str(out/'hx711_live_view.png'),1600,1200)
print(json.dumps(rows,ensure_ascii=False,indent=2))
