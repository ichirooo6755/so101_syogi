import adsk.core
import adsk.fusion
import builtins
assert app.activeDocument.name=='so101_V8_元取付部保持_筆圧検証'
wm=builtins._so101_v8_sim_design
occ=wm.rootComponent.occurrences.itemByName('base:1')
if builtins._so101_v8_sim_outer_context: occ=occ.createForAssemblyContext(builtins._so101_v8_sim_outer_context)
b=occ.bRepBodies.item(0)
faces=[f for f in b.faces if isinstance(f.geometry,adsk.core.Plane) and abs(f.geometry.normal.y)>.99 and
    any(abs(f.geometry.origin.y*10-y)<1e-5 for y in (-17.05,20.2)) and f.area*100>100]
assert len(faces)==2,len(faces)
ui.activeSelections.clear()
for f in faces: assert ui.activeSelections.add(f)
assert ui.commandDefinitions.itemById('SimNewConstraintCmd').execute()
print('Mount mating planes',[(f.area*100,f.geometry.origin.y*10) for f in faces])
