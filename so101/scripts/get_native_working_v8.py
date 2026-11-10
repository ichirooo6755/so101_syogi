import builtins
import adsk
assert app.activeDocument.name=='so101_V8_元取付部保持_筆圧検証'
ui.activeSelections.clear()
assert ui.commandDefinitions.itemById('SimSelectAllOccurrencesCommand').execute()
adsk.doEvents()
for s in ui.activeSelections:
    e=s.entity
    if e.objectType=='adsk::fusion::Occurrence': wm=e.component.parentDesign
    elif hasattr(e,'body'): wm=e.body.parentComponent.parentDesign
    else: continue
    if wm.objectType=='adsk::fusion::WorkingModel':
        builtins._so101_v8_sim_design=wm
        print('WM_READY',[(o.name,o.bRepBodies.count) for o in wm.rootComponent.occurrences])
        break
else: print('Native selection requires another event cycle')
