import adsk.core
import adsk.fusion
import builtins
print('active', app.activeDocument.name, ui.activeCommand)
print('selections', [(s.entity.objectType, getattr(s.entity, 'name', '')) for s in ui.activeSelections])
assert ui.activeSelections.count >= 1
e = ui.activeSelections.item(0).entity
if e.objectType == 'adsk::fusion::Occurrence': wm = e.component.parentDesign
elif e.objectType == 'adsk::fusion::BRepFace': wm = e.body.parentComponent.parentDesign
elif e.objectType == 'adsk::fusion::BRepBody': wm = e.parentComponent.parentDesign
else: raise ValueError(e.objectType)
print('selected_design', wm.objectType)
assert wm.objectType == 'adsk::fusion::WorkingModel'
builtins._so101_v7_sim_design = wm
print('WM_READY', [(o.name, o.bRepBodies.count) for o in wm.rootComponent.occurrences])
