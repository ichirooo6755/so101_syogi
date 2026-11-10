import adsk.core
import adsk.fusion
import json
from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
prior=json.loads((ROOT/'output/print_camera_hx711_v4/checks/design_check.json').read_text())
CO=prior['parameters']['camera_pcb_origin_mm']; axes=prior['camera_basis']
doc=next(d for d in app.documents if d.name=='so101_SelectionA_Simple_Camera_HX711_V4')
d=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
o=d.rootComponent.occurrences.itemByName('REFERENCE_XIAO_Sense_1pc:1')
b=o.bRepBodies.item(37)
pts=[v.geometry.asArray() for v in b.vertices]
local={k:[sum((p[i]*10-CO[i])*a[i] for i in range(3)) for p in pts] for k,a in axes.items()}
result={'index':38,'name':b.name,'volume_mm3':b.volume*1000,
    'camera_local_bounds_mm':{k:[min(v),max(v)] for k,v in local.items()}}
(ROOT/'output/camera_mount_v5/camera_body38.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
