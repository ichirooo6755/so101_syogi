assert app.activeDocument.name.startswith('so101_V8_元取付部保持_ジェネレーティブ')
assert ui.activeCommand=='SelectCommand'
assert ui.commandDefinitions.itemById('GenFEACSPreSolveCheckCmd').execute()
print('Opened native Generative precheck')
