import builtins
assert app.activeDocument.name.startswith('so101_V8_元取付部保持_ジェネレーティブ')
assert ui.activeCommand=='SelectCommand'
ui.activeSelections.clear()
assert ui.commandDefinitions.itemById('SimGenerativeObstacleBoundaryCommand').execute()
print('Opened obstacle definition without preselection')
for line in app.executeTextCommand('TextCommands.List /hidden').splitlines():
    if 'commit' in line.lower() and len(line)<300: print(line)
