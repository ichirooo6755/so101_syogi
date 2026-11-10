import adsk.core
import adsk.fusion
import builtins
assert app.activeDocument.name.startswith('so101_V8_元取付部保持_ジェネレーティブ')
assert ui.activeSelections.count>=1
e=ui.activeSelections.item(0).entity
b=e.body if e.objectType=='adsk::fusion::BRepFace' else e
wm=b.parentComponent.parentDesign
assert wm.objectType=='adsk::fusion::WorkingModel',wm.objectType
builtins._so101_v8_generative_model=wm
bodies=list(wm.rootComponent.bRepBodies)+[b for o in wm.rootComponent.allOccurrences for b in o.bRepBodies]
print('working_bodies',[(b.name,b.volume*1000) for b in bodies])
ui.activeSelections.clear()
preserves=[b for b in bodies if b.name.startswith('PRESERVE_')]
assert len(preserves)==3
for b in preserves: assert ui.activeSelections.add(b)
print('preserve_command',ui.commandDefinitions.itemById('SimGenerativeKeepBoundaryCommand').execute())
print('load_commands',[(c.id,c.name) for c in ui.commandDefinitions if
    ('load' in c.id.lower() or 'gravity' in c.id.lower()) and
    any(k in c.id.lower() for k in ('sim','gen'))])
