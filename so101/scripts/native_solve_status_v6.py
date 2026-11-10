assert app.activeDocument.name=='so101_V6_短縮補強_筆圧検証'
print('active command',ui.activeCommand)
assert ui.activeCommand=='SelectCommand'
c=ui.commandDefinitions.itemById('SimSolveDetailsCmd'); print(c.id,c.name)
assert c.execute()
