import adsk.core
import adsk.fusion
import json
T=adsk.fusion.TemporaryBRepManager.get()
doc=next(d for d in app.documents if d.name=='so101_SelectionA_Simple_Camera_HX711_V4')
d=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
o=d.rootComponent.occurrences.itemByName('REFERENCE_XIAO_Sense_1pc:1'); b=o.bRepBodies.item(37)
def bbox(body):
    bb=body.boundingBox; return [[v*10 for v in p.asArray()] for p in (bb.minPoint,bb.maxPoint)]
q=T.copy(b); native=b.nativeObject or b; n=T.copy(native); T.transform(n,o.transform2)
print(json.dumps({'proxy_bbox':bbox(b),'copy_proxy_bbox':bbox(q),
    'native_bbox':bbox(native),'explicit_world_copy_bbox':bbox(n)},indent=2))
