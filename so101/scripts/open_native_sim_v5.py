import adsk.core
import adsk.fusion
print('active_command_before',ui.activeCommand)
assert ui.activeCommand in ('SelectCommand','', 'FusionSolidEnvironment','ConstrainedOrbitCommand','FusionPanCommand'), 'A model-editing command is in progress; leave it untouched'
doc=next(doc for doc in app.documents if doc.name=='so101_V5_筆圧検証_理想接触')
assert doc.activate()
sd=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
print('bodies',[(o.name,[(b.name,b.material.name,b.volume*1000) for b in o.bRepBodies]) for o in sd.rootComponent.occurrences])
assert ui.workspaces.itemById('SimulationEnvironment').activate()
print('workspace_activated',app.activeDocument.name)
