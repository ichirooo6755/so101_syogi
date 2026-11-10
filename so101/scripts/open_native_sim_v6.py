import adsk.core
import adsk.fusion
assert ui.activeCommand in ('SelectCommand','','FusionSolidEnvironment')
doc=next(doc for doc in app.documents if doc.name=='so101_V6_短縮補強_筆圧検証')
assert doc.activate()
assert ui.workspaces.itemById('SimulationEnvironment').activate()
print('Activated',doc.name)
