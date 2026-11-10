import adsk.core
import adsk.fusion
import builtins
assert app.activeDocument.name.startswith('so101_V8_元取付部保持_ジェネレーティブ')
wm=builtins._so101_v8_generative_model
ui.activeSelections.clear()
b=next(b for b in wm.rootComponent.bRepBodies if b.name.startswith('PRESERVE_03'))
faces=[f for f in b.faces if isinstance(f.geometry,adsk.core.Plane)
    and abs(f.geometry.normal.z)>.99 and abs(f.geometry.origin.z*10-39.5)<1e-5]
face=max(faces,key=lambda f:f.area)
assert face.area*100>50
assert ui.activeSelections.add(face)
assert ui.commandDefinitions.itemById('GenLoadsCommand').execute()
print('Fixed load-cell seating face',face.area*100,'mm2; apply Fz=6N plus Mx=-167.4Nmm, not centered-force-only')
