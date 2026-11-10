assert app.activeDocument.name.startswith(('so101_V5_筆圧検証_理想接触','so101_V6_短縮補強_筆圧検証'))
print('document',app.activeDocument.name,'command',ui.activeCommand)
assert ui.commandDefinitions.itemById('SimResultTypeGroupCmd').execute()
