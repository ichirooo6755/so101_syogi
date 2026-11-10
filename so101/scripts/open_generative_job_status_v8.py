assert ui.activeCommand=='SelectCommand'
doc=next(d for d in app.documents if d.name.startswith('so101_V8_元取付部保持_ジェネレーティブ'))
assert doc.activate()
assert ui.workspaces.itemById('GenerativeEnvironment').activate()
assert ui.commandDefinitions.itemById('GenGenerateDetailsCmd').execute()
print('Opened native Generative job status, current doc',doc.name)
