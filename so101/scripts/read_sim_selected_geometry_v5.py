import adsk.core
import adsk.fusion
import builtins
assert ui.activeSelections.count==1
e=ui.activeSelections.item(0).entity
print('selected',e.objectType)
face=adsk.fusion.BRepFace.cast(e); assert face
b=face.body; c=b.parentComponent; sd=c.parentDesign
print('body',b.name,'component',c.name,'design',sd.objectType,sd.productType)
print('face',face.geometry.objectType,'area',face.area*100,'centroid',face.centroid.asArray())
print('root',sd.rootComponent.name)
print('occurrences',[(o.fullPathName,[(bb.name,bb.volume*1000) for bb in o.bRepBodies]) for o in sd.rootComponent.allOccurrences])
builtins._so101_v5_sim_design=sd
builtins._so101_v5_sim_base=b
builtins._so101_v5_sim_mount_face=face
