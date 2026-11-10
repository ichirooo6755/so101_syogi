assert app.activeDocument.name=='so101_V8_元取付部保持_筆圧検証'
assert ui.activeCommand=='SelectCommand'
if app.activeDocument.isModified:
    assert app.activeDocument.save('V8 actual original servo mounting planes clamped; 6N upward brush stop load; steel cell per user; E1500MPa printed plastic; ideal bonded contacts.')
assert ui.commandDefinitions.itemById('SimSolveCmd').execute()
print('Native solve dialog opened, check price before submission')
