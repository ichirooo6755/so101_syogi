import builtins
assert ui.activeCommand=='SimGenerativeObstacleBoundaryCommand'
wm=builtins._so101_v8_generative_model
ctx=builtins._so101_v8_generative_context
ui.activeSelections.clear()
bodies=[b for b in wm.rootComponent.bRepBodies if b.name.startswith('OBSTACLE_')]
assert len(bodies)==61
for b in bodies:
    b.isLightBulbOn=True
    assert ui.activeSelections.add(b.createForAssemblyContext(ctx))
print('ACTIVE_SELECTION_COUNT',ui.activeSelections.count)
