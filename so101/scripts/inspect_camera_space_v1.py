"""Read-only source inventory and grid clearance for the additive camera mount."""
import adsk.core
import adsk.fusion
import json
from pathlib import Path

OUT = Path('/Users/sugawaraichirou/Documents/ChatGPT/so101/output/camera_mount_v1')
OUT.mkdir(parents=True, exist_ok=True)
main = next(x for x in app.documents if x.name.startswith('so101書道'))
main.activate()
d = adsk.fusion.Design.cast(main.products.itemByProductType('DesignProductType'))
r = d.rootComponent
t = adsk.fusion.TemporaryBRepManager.get()

def bbox(b):
    bb = b.boundingBox
    return [[getattr(p, c)*10 for c in ('x','y','z')] for p in (bb.minPoint, bb.maxPoint)]

report = {'document': main.name, 'modified': main.isModified,
          'timeline': [d.timeline.markerPosition,d.timeline.count],
          'occurrences': [], 'visible_bodies': []}
for o in r.allOccurrences:
    report['occurrences'].append({'path':o.fullPathName, 'visible':o.isVisible,
        'transform':list(o.transform2.asArray()),
        'bodies':[{'name':b.name,'volume_mm3':b.volume*1000,'bbox_mm':bbox(b)}
                  for b in o.bRepBodies if b.isSolid]})
    if o.isVisible:
        for b in o.bRepBodies:
            if b.isSolid and b.volume > 1e-6:
                report['visible_bodies'].append({'path':o.fullPathName+'/'+b.name,
                    'volume_mm3':b.volume*1000,'bbox_mm':bbox(b)})
try:
    report['version'] = main.dataFile.versionNumber
except Exception:
    pass
(OUT/'source_inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
camera = app.activeViewport.camera
camera.viewOrientation = adsk.core.ViewOrientations.IsoTopRightViewOrientation
camera.isFitView = True
app.activeViewport.camera = camera
app.activeViewport.refresh()
app.activeViewport.saveAsImageFile(str(OUT/'source_assembly.png'),1600,1200)
print(json.dumps({k:v for k,v in report.items() if k!='occurrences'},ensure_ascii=False,indent=2))
