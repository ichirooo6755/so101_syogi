import adsk.core
import adsk.fusion
import builtins
assert app.activeDocument.name=='so101_V6_短縮補強_筆圧検証'
wm=builtins._so101_v6_sim_design
b=wm.rootComponent.occurrences.itemByName('cartridge:1').bRepBodies.item(0)
faces=[f for f in b.faces if isinstance(f.geometry,adsk.core.Plane) and abs(f.geometry.normal.z)>.99 and
       abs(f.geometry.origin.z*10-30.5)<1e-5 and f.area*100>100]
assert len(faces)==1
ui.activeSelections.clear(); assert ui.activeSelections.add(faces[0])
assert ui.commandDefinitions.itemById('SimLoadsCommand').execute()
print('Butt stop selected',faces[0].area*100)
