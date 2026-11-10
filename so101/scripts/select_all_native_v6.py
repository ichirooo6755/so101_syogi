assert app.activeDocument.name=='so101_V6_短縮補強_筆圧検証'
assert ui.commandDefinitions.itemById('SimSelectAllOccurrencesCommand').execute()
print('Select all simulation occurrences requested')
