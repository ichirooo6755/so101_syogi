import adsk.core
import adsk.fusion
import json
report=[]
for doc in app.documents:
    d=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    if not d: continue
    report.append({'name':doc.name,'modified':doc.isModified,'bodies':d.rootComponent.bRepBodies.count,
                   'timeline':([d.timeline.markerPosition,d.timeline.count] if d.designType==adsk.fusion.DesignTypes.ParametricDesignType else None),
                   'features':[{'name':f.name,'state':int(f.healthState),'message':f.errorOrWarningMessage} for f in d.rootComponent.features],
                   'volumes':[b.volume*1000 for b in d.rootComponent.bRepBodies]})
print(json.dumps(report,ensure_ascii=False,indent=2))
