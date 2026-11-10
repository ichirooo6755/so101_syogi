import adsk.core
import builtins
assert ui.activeCommand=='SimNewConstraintCmd'
wm=builtins._so101_v8_sim_design
occ=wm.rootComponent.occurrences.itemByName('base:1').createForAssemblyContext(builtins._so101_v8_sim_outer_context)
b=occ.bRepBodies.item(0)
faces=[f for f in b.faces if isinstance(f.geometry,adsk.core.Plane) and abs(f.geometry.normal.y)>.99 and
    any(abs(f.geometry.origin.y*10-y)<1e-5 for y in (-17.05,20.2)) and f.area*100>100]
assert len(faces)==2
ui.activeSelections.clear()
for f in faces: assert ui.activeSelections.add(f)
print('MOUNT_INPUT_2_FACES',occ.fullPathName)
