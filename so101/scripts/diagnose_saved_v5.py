import adsk.core
import adsk.fusion
import json
rows=[]
active=app.activeDocument
for doc in app.documents:
    de=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    if not de: continue
    row={'doc':doc.name,'modified':doc.isModified,'parts':[]}
    if de.designType==adsk.fusion.DesignTypes.ParametricDesignType:
        row.update(marker=de.timeline.markerPosition,count=de.timeline.count)
    for o in de.rootComponent.occurrences:
        if 'V5' not in o.name and 'Wrist_Roll_Follower_SO101 v1:3'!=o.name: continue
        row['parts'].append({'name':o.name,'visible':o.isVisible,'bodies':[{'name':b.name,'volume_mm3':b.volume*1000,
            'high_volume_mm3':b.getPhysicalProperties(adsk.fusion.CalculationAccuracy.HighCalculationAccuracy).volume*1000,
            'temp_volume_mm3':adsk.fusion.TemporaryBRepManager.get().copy(b).volume*1000,'solid':b.isSolid} for b in o.bRepBodies],
            'features':[(f.name,int(f.healthState)) for f in o.component.features]})
    rows.append(row)
print(json.dumps(rows,ensure_ascii=False,indent=2))
