import adsk.core
import adsk.fusion
import builtins
wm=builtins._so101_v8_generative_model
b=next(b for b in wm.rootComponent.bRepBodies if b.name.startswith('PRESERVE_03'))
plane=[f for f in b.faces if isinstance(f.geometry,adsk.core.Plane)]
seat=max((f for f in plane if abs(f.geometry.normal.z)>.99 and abs(f.geometry.origin.z*10-39.5)<1e-5),key=lambda f:f.area)
cy=2.762946202
moment=6*(cy-seat.centroid.y*10)
builtins._so101_v8_required_Mx_Nmm=moment
face=max((f for f in plane if abs(f.geometry.normal.x)>.99 and abs(f.geometry.origin.x*10-69.2)<1e-5),key=lambda f:f.area)
print('Force face centroid mm',[v*10 for v in seat.centroid.asArray()])
print('REQUIRED_GLOBAL_Mx_Nmm',moment,'normal on selected side face',list(face.geometry.normal.asArray()))
ui.activeSelections.clear(); assert ui.activeSelections.add(face)
assert ui.commandDefinitions.itemById('SimMomentLoadCommand').execute()
print('workspace',[(w.id,w.name) for w in ui.workspaces if w.isActive])
