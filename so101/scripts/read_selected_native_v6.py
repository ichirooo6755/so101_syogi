import adsk.core
import adsk.fusion
import builtins
assert app.activeDocument.name=='so101_V6_短縮補強_筆圧検証'
assert ui.activeSelections.count>=1,ui.activeSelections.count
entity=ui.activeSelections.item(0).entity
print(entity.objectType)
face=adsk.fusion.BRepFace.cast(entity); body=adsk.fusion.BRepBody.cast(entity)
assert face or body
wm=(face.body if face else body).parentComponent.parentDesign
assert wm.objectType=='adsk::fusion::WorkingModel',wm.objectType
builtins._so101_v6_sim_design=wm
print('Working model',[(o.name,o.bRepBodies.item(0).volume*1000) for o in wm.rootComponent.occurrences])
