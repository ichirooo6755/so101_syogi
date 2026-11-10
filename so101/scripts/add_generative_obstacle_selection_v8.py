import builtins
assert ui.activeCommand=='SimGenerativeObstacleBoundaryCommand'
wm=builtins._so101_v8_generative_model
added=[]
for b in wm.rootComponent.bRepBodies:
    if b.name.startswith('OBSTACLE_ACTUAL_'):
        b.isLightBulbOn=True
        added.append((b.name,ui.activeSelections.add(b)))
assert len(added)==31 and all(v for _,v in added)
print('ADDED_TO_ACTIVE_OBSTACLE_INPUT',len(added),'active selections',ui.activeSelections.count)
