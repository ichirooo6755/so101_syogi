import adsk.core
import adsk.fusion
d=adsk.fusion.Design.cast(app.activeDocument.products.itemByProductType('DesignProductType'))
b=d.rootComponent.occurrences.itemByName('cartridge:1').bRepBodies.item(0)
faces=[f for f in b.faces if isinstance(f.geometry,adsk.core.Plane) and abs(f.geometry.normal.z)>.99 and
       abs(f.geometry.origin.z*10-30.5)<1e-5 and f.area*100>100]
assert len(faces)==1
print('active',ui.activeCommand,'added',ui.activeSelections.add(faces[0]))
