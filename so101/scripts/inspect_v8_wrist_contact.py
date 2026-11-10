import adsk.core
import adsk.fusion
import math
import json
root='/Users/sugawaraichirou/Documents/ChatGPT/so101'
main=next(d for d in app.documents if d.name=='so101書道')
md=adsk.fusion.Design.cast(main.products.itemByProductType('DesignProductType'))
source=next(d for d in app.documents if d.name=='部品１_V8_元取付形状保持')
sd=adsk.fusion.Design.cast(source.products.itemByProductType('DesignProductType'))
t=adsk.fusion.TemporaryBRepManager.get()
wb=max(md.rootComponent.occurrences.itemByName('Wrist_Roll_Clearance_V5:1').bRepBodies,key=lambda b:b.volume)
base=sd.rootComponent.bRepBodies.item(0)
for angle in (0,45,90,95,180):
    m=adsk.core.Matrix3D.create(); m.setToRotation(math.radians(angle),adsk.core.Vector3D.create(0,1,0),adsk.core.Point3D.create(-.2,0,3.4))
    hit=t.copy(base); t.transform(hit,m)
    assert t.booleanOperation(hit,wb,adsk.fusion.BooleanTypes.IntersectionBooleanType)
    if hit.volume>1e-8:
        bb=hit.boundingBox
        print('HIT',angle,hit.volume*1000,'bbox',[[p.x*10,p.y*10,p.z*10] for p in (bb.minPoint,bb.maxPoint)])
        print('vertices',[[round(c,5) for c in (v.geometry.x*10,v.geometry.y*10,v.geometry.z*10)] for v in hit.vertices])
print('GEN_EDIT',[(c.id,c.name) for c in ui.commandDefinitions if 'Gen' in c.id and any(k in c.id.lower() for k in ('edit','finish','model'))])
print('WRIST_FEATURES',[(f.name,f.objectType) for f in md.rootComponent.occurrences.itemByName('Wrist_Roll_Clearance_V5:1').component.features])
