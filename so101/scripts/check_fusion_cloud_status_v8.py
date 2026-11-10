print('OFFLINE',app.isOffLine)
print('ACTIVE',app.activeDocument.name,'modified',app.activeDocument.isModified)
for doc in app.documents:
    if 'V8' in doc.name:
        f=doc.dataFile
        print('V8_FILE',doc.name,f.id if f else None,'complete',f.isComplete if f else None)
