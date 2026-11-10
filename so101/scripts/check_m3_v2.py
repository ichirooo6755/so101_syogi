import adsk.core
import adsk.fusion
import json
d=adsk.fusion.Design.cast(app.activeProduct)
d.userParameters.itemByName('brush_cartridge_od').expression='22 mm'
result={}
for name in ('部品１:1','Brush_Load_Carrier:1','Brush_Cartridge_15mm:1'):
    o=d.rootComponent.occurrences.itemByName(name)
    rows=[]
    for f in o.bRepBodies.item(0).faces:
        g=f.geometry
        if isinstance(g,adsk.core.Cylinder):
            rows.append({'diameter':g.radius*20,'origin':[v*10 for v in g.origin.asArray()],
            'axis':list(g.axis.asArray()),'z':[f.boundingBox.minPoint.z*10,f.boundingBox.maxPoint.z*10]})
    result[name]=rows
print(json.dumps(result,ensure_ascii=False,indent=2))
