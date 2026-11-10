assert app.activeDocument.name.startswith('so101_V8_元取付部保持_ジェネレーティブ')
ui.activeSelections.clear()
assert ui.commandDefinitions.itemById('SimGenerativeManufacturingCommand').execute()
print('Opened native Generative manufacturing settings')
