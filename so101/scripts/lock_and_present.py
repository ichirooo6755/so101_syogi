import adsk.core
import adsk.fusion
d=adsk.fusion.Design.cast(app.activeProduct)
r=d.rootComponent
yoke=r.occurrences.itemByName('部品１:1')
cell=r.occurrences.itemByName('SC616C_1kg_Fusion:1')
if d.snapshots.hasPendingSnapshot: d.snapshots.add()
if r.asBuiltJoints.itemByName('SC616C_fixed_end_to_yoke') is None:
    inp=r.asBuiltJoints.createInput(yoke,cell,None)
    inp.setAsRigidJointMotion()
    joint=r.asBuiltJoints.add(inp)
    joint.name='SC616C_fixed_end_to_yoke'
    joint.isLightBulbOn=False
camera=app.activeViewport.camera
camera.viewOrientation=adsk.core.ViewOrientations.IsoTopRightViewOrientation
camera.isFitView=True
app.activeViewport.camera=camera
app.activeViewport.refresh()
print('Sensor fixed to yoke; presentation view ready')
