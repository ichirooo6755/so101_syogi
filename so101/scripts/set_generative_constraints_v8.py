import adsk.core
import adsk.fusion
import builtins
assert app.activeDocument.name.startswith('so101_V8_元取付部保持_ジェネレーティブ')
workspace=ui.workspaces.itemById('GenerativeEnvironment')
if not workspace.isActive: workspace.activate()
assert workspace.isActive
wm=builtins._so101_v8_generative_model
ui.activeSelections.clear()
mounts=[b for b in wm.rootComponent.bRepBodies if b.name.startswith(('PRESERVE_01','PRESERVE_02'))]
faces=[f for b in mounts for f in b.faces if isinstance(f.geometry,adsk.core.Plane)
    and abs(f.geometry.normal.y)>.99 and any(abs(f.geometry.origin.y*10-y)<1e-5 for y in (-17.05,20.2))]
assert len(faces)==2,[(f.area*100,f.geometry.origin.y*10) for f in faces]
for b in wm.rootComponent.bRepBodies:
    if b.name.startswith('OBSTACLE_'): b.isLightBulbOn=False
    if b.name.startswith('STARTING_'): b.isLightBulbOn=False
print('constraints',[(c.id,c.name) for c in ui.commandDefinitions if 'constraint' in c.id.lower() and ('sim' in c.id.lower() or 'gen' in c.id.lower())])
for f in faces: assert ui.activeSelections.add(f)
command=ui.commandDefinitions.itemById('GenNewConstraintCmd')
assert command.execute()
print('constraint surfaces',[(f.area*100,f.geometry.origin.y*10) for f in faces],command.id)
