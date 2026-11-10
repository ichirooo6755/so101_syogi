import builtins
assert app.activeDocument.name.startswith('so101_V8_元取付部保持_ジェネレーティブ')
wm=builtins._so101_v8_generative_model
ui.activeSelections.clear()
bodies=[b for b in wm.rootComponent.bRepBodies if b.name.startswith('STARTING_')]
assert len(bodies)==1
assert ui.activeSelections.add(bodies[0])
assert ui.commandDefinitions.itemById('SimGenerativeSeedTargetCommand').execute()
print('Starting shape preselected')
