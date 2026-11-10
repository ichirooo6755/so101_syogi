import adsk.fusion
import json
doc = next(doc for doc in app.documents if doc.name.startswith('so101書道'))
d = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
r = d.rootComponent
print(json.dumps({'document': doc.name, 'modified': doc.isModified,
    'timeline': [d.timeline.markerPosition, d.timeline.count],
    'occurrences': [{'name': o.name, 'visible': o.isVisible,
        'volumes_mm3': [b.volume*1000 for b in o.bRepBodies],
        'transform': list(o.transform2.asArray())}
        for o in r.occurrences if any(s in o.name for s in ('V5','V6','SC616'))]},
    ensure_ascii=False, indent=2))
