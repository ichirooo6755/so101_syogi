import adsk.core
import adsk.fusion
import json
d=adsk.fusion.Design.cast(app.activeProduct); r=d.rootComponent
entities=adsk.core.ObjectCollection.create()
for o in r.allOccurrences:
    print('OCC',o.fullPathName,o.isVisible,o.bRepBodies.count)
    if o.isVisible:
        for b in o.bRepBodies: entities.add(b)
inp=d.createInterferenceInput(entities); inp.areCoincidentFacesIncluded=False
results=d.analyzeInterference(inp)
for result in results:
    print('PAIR',result.entityOne.name,result.entityTwo.name,'volume mm3',result.interferenceBody.volume*1000,
          'bounds mm',[[x*10 for x in p.asArray()] for p in (result.interferenceBody.boundingBox.minPoint,result.interferenceBody.boundingBox.maxPoint)])
cam=app.activeViewport.camera; cam.viewOrientation=adsk.core.ViewOrientations.IsoTopRightViewOrientation; cam.isFitView=True
app.activeViewport.camera=cam; app.activeViewport.refresh()
print('timeline',d.timeline.markerPosition,d.timeline.count)
