assert app.activeDocument.name=='so101_V6_短縮補強_筆圧検証'
assert ui.activeCommand=='SelectCommand'
print([(c.id,c.name) for c in ui.commandDefinitions if c.id in ('SimSolveCmd','SimFEACSCloudSolveCmd','SimFEACSMeshSolveCmd')])
assert ui.commandDefinitions.itemById('SimSolveCmd').execute()
print('Solve options requested, no paid operation authorized')
