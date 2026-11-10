import adsk.core
import adsk.fusion
assert ui.activeCommand == 'SelectCommand'
doc = next(d for d in app.documents if d.name.startswith('so101_V7_閉断面補強_筆圧検証'))
doc.activate()
print('simulation_workspace', ui.workspaces.itemById('SimulationEnvironment').activate())
print('commands', [(c.id, c.name) for c in ui.commandDefinitions
    if any(k in c.id.lower() for k in ('study', 'generative', 'shapeoptim'))])
