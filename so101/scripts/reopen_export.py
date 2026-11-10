import adsk.core
import adsk.fusion
original_doc=app.activeDocument
options=app.importManager.createFusionArchiveImportOptions('/Users/sugawaraichirou/Documents/ChatGPT/so101/output/so101_sc616c_mount_part.f3d')
doc=app.importManager.importToNewDocument(options)
assert doc is not None
print('reopened',doc.name,'original remains open',original_doc.name)
design=adsk.fusion.Design.cast(app.activeProduct)
print('timeline',design.timeline.markerPosition,design.timeline.count)
