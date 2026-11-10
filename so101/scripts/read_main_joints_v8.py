import adsk.fusion
doc=next(d for d in app.documents if d.name=='so101書道')
d=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType')); r=d.rootComponent
print('MAIN_TIMELINE',d.timeline.markerPosition,d.timeline.count)
for j in r.asBuiltJoints:
    print('AS_BUILT',j.name,'suppressed',j.isSuppressed,j.occurrenceOne.name,j.occurrenceTwo.name)
for j in r.joints:
    print('JOINT',j.name,'suppressed',j.isSuppressed)
for o in r.occurrences:
    if any(k in o.name for k in ('部品１','Wrist','STS','Brush','SC616')):
        print('OCC',o.name,'visible',o.isVisible,'grounded',o.isGrounded,'transform',list(o.transform2.asArray()),'materials',[(b.name,b.material.name) for b in o.bRepBodies])
