import adsk.core
import adsk.fusion
import json
d=adsk.fusion.Design.cast(app.activeProduct)
r=d.rootComponent
c=r.occurrences.itemByName('部品１:1').component
print('active_component',d.activeComponent.name)
print('pending_snapshot',d.snapshots.hasPendingSnapshot)
print('timeline',d.timeline.markerPosition,d.timeline.count)
for obj in list(c.constructionPlanes)+list(c.sketches)+list(c.features.extrudeFeatures):
    if obj.name.startswith('SC616C'):
        try: print(obj.name,'timeline',obj.timelineObject.index,'health',int(obj.healthState))
        except Exception as e: print(obj.name,str(e))
for g in d.timeline.timelineGroups:
    print('group',g.name)
for j in r.asBuiltJoints:
    print('joint',j.name,'suppressed',j.isSuppressed,'occ',j.occurrenceOne.name,j.occurrenceTwo.name)
for o in r.occurrences:
    if o.name.startswith(('部品１','SC616')):
        print('position',o.name,list(o.transform2.asArray()))
print('snapshots',[(s.name,s.timelineObject.index) for s in d.snapshots])
