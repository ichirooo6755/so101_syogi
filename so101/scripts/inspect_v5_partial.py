import adsk.core
import adsk.fusion
import json
d=adsk.fusion.Design.cast(app.activeProduct); r=d.rootComponent
o=r.occurrences.itemByName('部品１_V5可動域改善:1'); c=o.component
print('XZ',c.xZConstructionPlane.geometry.origin.asArray(),c.xZConstructionPlane.geometry.normal.asArray())
print('bodies',[(b.name,b.volume*1000,[p.asArray() for p in (b.boundingBox.minPoint,b.boundingBox.maxPoint)]) for b in c.bRepBodies])
print('sketches',[(s.name,list(s.transform.asArray()),list(s.referencePlane.geometry.origin.asArray()),list(s.referencePlane.geometry.normal.asArray())) for s in c.sketches if 'negative' in s.name])
print('features',[(f.name,int(f.healthState),f.errorOrWarningMessage) for f in c.features])
