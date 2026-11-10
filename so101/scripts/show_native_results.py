print('Showing results for',app.activeDocument.name)
assert app.activeDocument.name in ('so101_V5_筆圧検証_理想接触','so101_V6_短縮補強_筆圧検証')
assert ui.activeCommand=='SelectCommand'
assert ui.commandDefinitions.itemById('SimSwitchToPostProcessingCommand').execute()
