import json
print('active_doc',app.activeDocument.name,'active_cmd',ui.activeCommand)
print('documents',[(doc.name,doc.isModified,doc.dataFile.id if doc.dataFile else None) for doc in app.documents])
print('workspaces',[(w.id,w.name) for w in ui.workspaces if w.isActive])
