import adsk.core
import adsk.fusion
import builtins
assert app.activeDocument.name.startswith('so101_V7_閉断面補強_筆圧検証')
ui.activeSelections.clear()
command = ui.commandDefinitions.itemById('SimSelectAllOccurrencesCommand')
print('select_all', command.execute())
adsk.doEvents()
print('selections', [(s.entity.objectType, getattr(s.entity, 'name', '')) for s in ui.activeSelections])
for s in ui.activeSelections:
    e = s.entity
    if e.objectType == 'adsk::fusion::Occurrence': wm = e.component.parentDesign
    elif e.objectType == 'adsk::fusion::BRepFace': wm = e.body.parentComponent.parentDesign
    elif e.objectType == 'adsk::fusion::BRepBody': wm = e.parentComponent.parentDesign
    else: continue
    print('selected_design', wm.objectType)
    if wm.objectType == 'adsk::fusion::WorkingModel':
        builtins._so101_v7_sim_design = wm
        print('WM_READY', [(o.name, o.bRepBodies.count) for o in wm.rootComponent.occurrences])
        break
