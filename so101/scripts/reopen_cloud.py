import adsk.core
import adsk.fusion
doc=app.activeDocument
assert doc.isSaved and not doc.isModified
file=doc.dataFile
print('saved_cloud_file',file.name,'version',file.versionNumber,'complete',file.isComplete)
assert file.isComplete
assert doc.close(False)
reopened=app.documents.open(file,True)
assert reopened is not None
print('reopened',reopened.name)
