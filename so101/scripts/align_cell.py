import adsk.core
import adsk.fusion
import json
d=adsk.fusion.Design.cast(app.activeProduct)
r=d.rootComponent
yoke=r.occurrences.itemByName('部品１:1')
cell=r.occurrences.itemByName('SC616C_1kg_Fusion:1')
print('parent_design',yoke.component.parentDesign==d,yoke.component.parentDesign.designType)
joint=r.asBuiltJoints.itemByName('SC616C_fixed_end_to_yoke')
if joint:
    print('delete_our_joint',joint.deleteMe())
with open('/Users/sugawaraichirou/Documents/ChatGPT/so101/tmp/fusion_inspection.json') as f:
    baseline=json.load(f)
data=next(o['transform'] for o in baseline['occurrences'] if o['name']=='SC616C_1kg_Fusion:1')
data[3]+=0.55
data[7]+=(1.2629462023600935-1.8)/10
matrix=adsk.core.Matrix3D.create()
matrix.setWithArray(data)
cell.transform2=matrix
print('after_set',list(cell.transform2.asArray()),'pending',d.snapshots.hasPendingSnapshot)
app.activeViewport.refresh()
print('after_refresh',list(cell.transform2.asArray()),'pending',d.snapshots.hasPendingSnapshot)
if d.snapshots.hasPendingSnapshot:
    snap=d.snapshots.add()
    snap.name='SC616C_mount_alignment'
    print('snapshot',snap.name)
print('final',list(cell.transform2.asArray()))
print('new_features',[(f.name,f.isParametric) for f in yoke.component.features.extrudeFeatures if f.name.startswith('SC616C')])
