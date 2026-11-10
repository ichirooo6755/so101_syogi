doc=next(d for d in app.documents if d.name.startswith('so101_V8_元取付部保持_ジェネレーティブ'))
doc.activate()
assert ui.activeCommand=='SelectCommand'
assert ui.commandDefinitions.itemById('EditModelCommand').execute()
print('Requested native generative model edit; preserve/load settings retained')
