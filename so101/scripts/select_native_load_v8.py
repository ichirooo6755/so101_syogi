import adsk.core
import adsk.fusion
import builtins
assert app.activeDocument.name=='so101_V8_元取付部保持_筆圧検証'
wm=builtins._so101_v8_sim_design
occ=wm.rootComponent.occurrences.itemByName('cartridge:1')
if builtins._so101_v8_sim_outer_context: occ=occ.createForAssemblyContext(builtins._so101_v8_sim_outer_context)
b=occ.bRepBodies.item(0)
faces=[f for f in b.faces if isinstance(f.geometry,adsk.core.Plane) and abs(f.geometry.normal.z)>.99 and
    abs(f.geometry.origin.z*10-30.5)<1e-5 and f.area*100>100]
assert len(faces)==1
ui.activeSelections.clear(); assert ui.activeSelections.add(faces[0])
assert ui.commandDefinitions.itemById('SimLoadsCommand').execute()
print('Butt stop selected',faces[0].area*100,'normal',faces[0].geometry.normal.asArray())
