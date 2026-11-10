import adsk.core
import adsk.fusion
import json
from pathlib import Path
OUT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101/output/camera_mount_v6')
OUT.mkdir(parents=True,exist_ok=True)
T=adsk.fusion.TemporaryBRepManager.get()
def bb(body):
    b=body.boundingBox
    return [[v*10 for v in p.asArray()] for p in (b.minPoint,b.maxPoint)]
rows=[]
for doc in app.documents:
    if doc.name not in ('so101_SelectionA_Simple_Camera_HX711_V4','so101_A1mini_PLA_造形用_V5'):continue
    d=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    o=d.rootComponent.occurrences.itemByName('REFERENCE_XIAO_Sense_1pc:1')
    row={'document':doc.name,'modified':doc.isModified,'active':doc==app.activeDocument,
         'transform':list(o.transform2.asArray()),'bodies':[]}
    for i,b in enumerate(o.bRepBodies):
        q=T.copy(b)
        row['bodies'].append({'index':i,'name':b.name,'volume_mm3':q.volume*1000,'bbox_mm':bb(q),
            'cylinders':[{'origin_mm':[v*10 for v in f.geometry.origin.asArray()],
                 'axis':list(f.geometry.axis.asArray()),'radius_mm':f.geometry.radius*10}
                for f in q.faces if f.geometry.surfaceType==adsk.core.SurfaceTypes.CylinderSurfaceType]})
    path=OUT/(('current_V4' if 'V4' in doc.name else 'current_V5')+'_before_changes.f3d')
    if not path.exists():assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(path)))
    rows.append(row)
result={'active_document':app.activeDocument.name,'command':ui.activeCommand,'documents':rows}
(OUT/'current_camera_inspection.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps({'active':result['active_document'],'command':result['command'],
    'documents':[dict((k,v) for k,v in r.items() if k!='bodies') for r in rows]},ensure_ascii=False,indent=2))
