import adsk.core
import adsk.fusion
import builtins
assert app.activeDocument.name=='so101_V6_短縮補強_筆圧検証'
wm=builtins._so101_v6_sim_design
b=wm.rootComponent.occurrences.itemByName('base:1').bRepBodies.item(0)
faces=[f for f in b.faces if isinstance(f.geometry,adsk.core.Plane) and abs(f.geometry.normal.y)>.99 and
       any(abs(f.geometry.origin.y*10-y)<1e-5 for y in (-17.05,20.2))]
assert len(faces)==2,len(faces)
ui.activeSelections.clear()
print('Mount faces selected',[(f.area*100,ui.activeSelections.add(f)) for f in faces])
assert ui.commandDefinitions.itemById('SimNewConstraintCmd').execute()
