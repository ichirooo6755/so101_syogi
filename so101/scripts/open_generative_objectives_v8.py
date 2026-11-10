assert app.activeDocument.name.startswith('so101_V8_元取付部保持_ジェネレーティブ')
ui.activeSelections.clear()
assert ui.commandDefinitions.itemById('SimGenerativeObjectivesCommand').execute()
print('GEN_COMMANDS',[(c.id,c.name) for c in ui.commandDefinitions if
    ('gen' in c.id.lower() or c.id.startswith('Sim')) and any(k in c.id.lower() for k in ('solve','precheck','generate','preview'))])
