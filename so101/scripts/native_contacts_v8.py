assert app.activeDocument.name=='so101_V8_元取付部保持_筆圧検証'
assert ui.activeCommand=='SelectCommand'
ui.activeSelections.clear()
assert ui.commandDefinitions.itemById('SimFEACSAutoContactsCmd').execute()
print('Automatic contacts setup')
