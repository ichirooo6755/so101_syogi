import adsk.core
import adsk.fusion
import json

d=adsk.fusion.Design.cast(app.activeProduct)
r=d.rootComponent
report={}
for name in ('部品１:1','Brush_Load_Carrier:1'):
    o=r.occurrences.itemByName(name)
    assert o and o.bRepBodies.count==1,name
    rows=[]
    for f in o.bRepBodies.item(0).faces:
        g=f.geometry
        if isinstance(g,adsk.core.Cylinder) and abs(g.axis.z)>.99 and abs(g.origin.x*10-30)<1e-5:
            rows.append({'diameter_mm':g.radius*20,'center_y_mm':g.origin.y*10,
                         'z_mm':[f.boundingBox.minPoint.z*10,f.boundingBox.maxPoint.z*10]})
    report[name]={'sensor_mount_holes':rows,'threads':[{'name':f.name,'suppressed':f.isSuppressed} for f in o.component.features.threadFeatures]}
sensor=next(o.bRepBodies.item(0) for o in r.allOccurrences if o.fullPathName.startswith('SC616C_1kg_Fusion:1+') and o.bRepBodies.count)
report['load_cell_nominal_M3_holes']=[{'diameter_mm':f.geometry.radius*20,'center_y_mm':f.geometry.origin.y*10}
    for f in sensor.faces if isinstance(f.geometry,adsk.core.Cylinder) and abs(f.geometry.radius*20-3)<1e-5 and abs(f.geometry.axis.z)>.99]
report['document_modified']=app.activeDocument.isModified
print(json.dumps(report,ensure_ascii=False,indent=2))
