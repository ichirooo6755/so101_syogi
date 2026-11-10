import adsk.core
import adsk.fusion
import builtins
wm=builtins._so101_v8_generative_model
b=next(b for b in wm.rootComponent.bRepBodies if b.name.startswith('PRESERVE_03'))
heads=sorted((f for f in b.faces if isinstance(f.geometry,adsk.core.Plane) and
    abs(f.geometry.normal.z)>.99 and abs(f.geometry.origin.z*10-32.7)<1e-5),key=lambda f:f.centroid.y)
assert len(heads)==2
F=-builtins._so101_v8_couple_force_N
normal=heads[1].evaluator.getNormalAtPoint(heads[1].centroid)[1]
ui.activeSelections.clear(); assert ui.activeSelections.add(heads[1])
assert ui.commandDefinitions.itemById('GenLoadsCommand').execute()
print('FAR_INPUT_N',-F/normal.z)
