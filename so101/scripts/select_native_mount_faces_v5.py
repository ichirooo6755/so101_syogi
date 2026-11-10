import adsk.core
import adsk.fusion
import builtins
assert app.activeDocument.name=='so101_V5_筆圧検証_理想接触'
d=builtins._so101_v5_sim_design
b=d.rootComponent.occurrences.itemByName('base:1').bRepBodies.item(0)
faces=[]
for f in b.faces:
    g=f.geometry
    if isinstance(g,adsk.core.Plane) and abs(g.normal.y)>.99 and any(abs(g.origin.y*10-y)<1e-5 for y in (-17.05,20.2)):
        faces.append(f)
assert len(faces)==2,len(faces)
ui.activeSelections.clear()
print('preselect',[(f.area*100,ui.activeSelections.add(f)) for f in faces])
print('selection_count',ui.activeSelections.count)
assert ui.commandDefinitions.itemById('SimNewConstraintCmd').execute()
