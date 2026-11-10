import builtins
import json
assert app.activeDocument.name.startswith('so101_V8_元取付部保持_ジェネレーティブ')
wm=builtins._so101_v8_generative_model
with open('/Users/sugawaraichirou/Documents/ChatGPT/so101/output/v8/generative_obstacle_audit.json',encoding='utf-8') as f: audit=json.load(f)
assert wm.rootComponent.bRepBodies.count==65
added=list(wm.rootComponent.bRepBodies)[34:]
assert len(added)==len(audit['additional_obstacles'])==31
for b,name in zip(added,audit['additional_obstacles']):
    b.name=name
    b.isLightBulbOn=False
    b.attributes.add('so101_generative','role','obstacle')
ui.activeSelections.clear()
bodies=[b for b in wm.rootComponent.bRepBodies if b.name.startswith('OBSTACLE_')]
assert len(bodies)==61
for b in bodies: assert ui.activeSelections.add(b)
assert ui.commandDefinitions.itemById('SimGenerativeObstacleBoundaryCommand').execute()
print('Obstacle bodies preselected',len(bodies))
