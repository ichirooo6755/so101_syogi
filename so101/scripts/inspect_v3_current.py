import adsk.core
import adsk.fusion
import json
d=adsk.fusion.Design.cast(app.activeProduct); r=d.rootComponent
for name in ('部品１:1','Brush_Load_Carrier:1','Brush_Cartridge_15mm:1','SC616C_Slide_In_Top_Cover:1'):
    o=r.occurrences.itemByName(name)
    print('OCC',name,'TRANSFORM',o.transform2.asArray(),'VISIBLE',o.isVisible)
    for b in o.bRepBodies:
        print('BODY',b.name,'volume',b.volume*1000,'bbox',[[v*10 for v in p.asArray()] for p in (b.boundingBox.minPoint,b.boundingBox.maxPoint)])
    for f in o.component.features.extrudeFeatures:
        if f.name.startswith('V3_'):
            print('FEATURE',f.name,'health',int(f.healthState),'faces',f.faces.count)
    for p in o.component.constructionPlanes:
        if p.name.startswith('V3_'): print('PLANE',p.name,p.geometry.origin.asArray(),p.geometry.normal.asArray())
for joint in r.asBuiltJoints:
    print('JOINT',joint.name,joint.isSuppressed)
for i in range(max(0,d.timeline.markerPosition-12),d.timeline.markerPosition):
    t=d.timeline.item(i); print('TIMELINE',i,t.name,t.entity.objectType)
print('timeline',d.timeline.markerPosition,d.timeline.count)
