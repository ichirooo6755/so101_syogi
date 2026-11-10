assert app.activeDocument.name=='so101_V6_短縮補強_筆圧検証'
assert ui.activeCommand=='SelectCommand'
ui.activeSelections.clear()
assert ui.commandDefinitions.itemById('SimFEACSAutoContactsCmd').execute()
print('Automatic contact setup requested')
