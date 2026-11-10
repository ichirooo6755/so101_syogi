import adsk.core
import adsk.fusion
import builtins
assert app.activeDocument.name=='so101_V5_筆圧検証_理想接触'
d=builtins._so101_v5_sim_design
b=d.rootComponent.occurrences.itemByName('cartridge:1').bRepBodies.item(0)
faces=[f for f in b.faces if isinstance(f.geometry,adsk.core.Plane) and abs(f.geometry.normal.z)>.99 and
       abs(f.geometry.origin.z*10-30.5)<1e-5 and f.area*100>100]
assert len(faces)==1,[(f.area*100,list(f.centroid.asArray())) for f in faces]
ui.activeSelections.clear(); print('brush_stop_face_selected',ui.activeSelections.add(faces[0]),faces[0].area*100)
assert ui.commandDefinitions.itemById('SimLoadsCommand').execute()
