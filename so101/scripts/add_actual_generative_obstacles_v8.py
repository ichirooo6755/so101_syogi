"""Supplement existing 30 keepouts with actual adjacent parts and fasteners.

Edits ONLY the native Generative WorkingModel. No main assembly is edited.
The thin central wrist sweep closes the gap inside the existing conservative
outer sweep cylinders, using the V8 shallow-relief wrist candidate.
"""
import adsk.core
import adsk.fusion
import builtins
import json
import math
root='/Users/sugawaraichirou/Documents/ChatGPT/so101'; out=root+'/output/v8'
assert app.activeDocument.name.startswith('so101_V8_元取付部保持_ジェネレーティブ')
wm=adsk.fusion.WorkingModel.cast(app.activeProduct)
assert wm and ui.activeCommand=='SelectCommand'
assert not any(b.name.startswith('OBSTACLE_ACTUAL_') for b in wm.rootComponent.bRepBodies)
main=next(doc for doc in app.documents if doc.name=='so101書道')
md=adsk.fusion.Design.cast(main.products.itemByProductType('DesignProductType')); mr=md.rootComponent
wr=next(doc for doc in app.documents if doc.name=='Wrist_Roll_Clearance_V8_元取付対応')
wd=adsk.fusion.Design.cast(wr.products.itemByProductType('DesignProductType'))
t=adsk.fusion.TemporaryBRepManager.get(); seed=next(b for b in wm.rootComponent.bRepBodies if b.name.startswith('STARTING_'))
def cyl_z(z0,z1,r,x,y):
    return t.createCylinderOrCone(adsk.core.Point3D.create(x/10,y/10,z0/10),r/10,
        adsk.core.Point3D.create(x/10,y/10,z1/10),r/10)
def cyl_y(y0,y1,r):
    return t.createCylinderOrCone(adsk.core.Point3D.create(-.2,y0/10,3.4),r/10,
        adsk.core.Point3D.create(-.2,y1/10,3.4),r/10)
def overlap(a,b):
    if not a.boundingBox.intersects(b.boundingBox): return 0.
    x=t.copy(a); assert t.booleanOperation(x,b,adsk.fusion.BooleanTypes.IntersectionBooleanType)
    return x.volume*1000
shapes={}
for label,name in (('carrier','Brush_Load_Carrier_Compact_V5:1'),('cartridge','Brush_Cartridge_Symmetric_15mm_V5:1')):
    source=mr.occurrences.itemByName(name).bRepBodies.item(0)
    shape=t.copy(source)
    # Six small translations supply a 0.2 mm axial clearance shell rather
    # than merely preventing overlap at the unloaded nominal position.
    for axis in range(3):
        for sign in (-1,1):
            c=t.copy(source); m=adsk.core.Matrix3D.create()
            v=[0.,0.,0.]; v[axis]=sign*.02; m.translation=adsk.core.Vector3D.create(*v)
            assert t.transform(c,m)
            assert t.booleanOperation(shape,c,adsk.fusion.BooleanTypes.UnionBooleanType)
    shapes['OBSTACLE_ACTUAL_'+label+'_plus_0p2mm_axial_shell']=shape
sensor=next(o.bRepBodies.item(0) for o in mr.allOccurrences
    if o.fullPathName.startswith('SC616C_1kg_Fusion:1+') and o.bRepBodies.count)
shapes['OBSTACLE_ACTUAL_SC616C']=t.copy(sensor)
wrist=wd.rootComponent.bRepBodies.item(0)
shapes['OBSTACLE_ACTUAL_wrist_V8_all_user_edits']=t.copy(wrist)
# Exact inner sweep, complemented by the existing continuous R46.5 outer
# envelopes. Rotation of the fixed wrist in tool coordinates is the inverse
# of rotation of the tool in fixed wrist coordinates.
inner=t.copy(wrist)
assert t.booleanOperation(inner,cyl_y(-30,30,13.5),adsk.fusion.BooleanTypes.IntersectionBooleanType)
sweep=t.copy(inner)
for a in range(5,360,5):
    c=t.copy(inner); m=adsk.core.Matrix3D.create()
    m.setToRotation(math.radians(-a),adsk.core.Vector3D.create(0,1,0),adsk.core.Point3D.create(-.2,0,3.4))
    assert t.transform(c,m)
    assert t.booleanOperation(sweep,c,adsk.fusion.BooleanTypes.UnionBooleanType)
shapes['OBSTACLE_ACTUAL_inner_wrist_full_rotation_5deg_union']=sweep
for o in mr.allOccurrences:
    if o.isVisible and o.fullPathName.startswith('STS3215_c:1+') and '+Axes:' not in o.fullPathName:
        for index,b in enumerate(o.bRepBodies):
            if b.isSolid and b.volume>1e-6:
                shapes['OBSTACLE_ACTUAL_servo_'+str(len(shapes))+'_'+str(index)]=t.copy(b)
cy=md.userParameters.itemByName('sc_brush_axis_y').value*10
for i,y in enumerate((-2.43705379764,4.96294620236)):
    shapes[f'OBSTACLE_ACTUAL_free_M3_shank_{i}']=cyl_z(36.7,45.6,1.7,62,y)
    shapes[f'OBSTACLE_ACTUAL_free_M3_head_driver_{i}']=cyl_z(-90,36.7,3.1,62,y)
for i,y in enumerate((cy-20,cy+20)):
    shapes[f'OBSTACLE_ACTUAL_cartridge_M3_shank_{i}']=cyl_z(8.5,18.6,1.7,62,y)
    shapes[f'OBSTACLE_ACTUAL_cartridge_M3_head_driver_{i}']=cyl_z(-90,8.5,3.1,62,y)
    shapes[f'OBSTACLE_ACTUAL_cartridge_M3_nut_{i}']=cyl_z(15.8,18.6,3.4,62,y)
hits=[{'body':n,'overlap_mm3':v} for n,b in shapes.items() if (v:=overlap(seed,b))>.003]
assert not hits,hits
bf=wm.rootComponent.features.baseFeatures.add(); bf.name='V8_actual_neighbors_wrist_sweep_fastener_tool_keepouts'
assert bf.startEdit()
for n,b in shapes.items():
    body=wm.rootComponent.bRepBodies.add(b,bf); body.name=n
assert bf.finishEdit()
for b in wm.rootComponent.bRepBodies:
    if b.name.startswith('OBSTACLE_ACTUAL_'):
        b.isLightBulbOn=False
        b.attributes.add('so101_generative','role','obstacle')
report={'additional_obstacles':list(shapes),'additional_count':len(shapes),
    'total_expected_obstacle_count':30+len(shapes),'starting_shape_overlap':hits,
    'carrier_and_cartridge_clearance_shell_mm':.2,
    'fixed_and_free_M3_shank_head_driver_clearance_included':True,
    'cartridge_nut_pockets_protected':True,'actual_servo_bodies_included':True,
    'wrist':'V8 copy of latest user edits plus shallow annular reliefs',
    'inner_wrist_sweep_step_deg':5,'continuous_outer_sweep_radius_mm':46.5,
    'main_assembly_edited':False,'generation_authorized_credits':11,'native_generation_started':False}
with open(out+'/generative_obstacle_audit.json','w',encoding='utf-8') as f: json.dump(report,f,ensure_ascii=False,indent=2)
builtins._so101_v8_generative_model=wm
assert ui.commandDefinitions.itemById('FinishEditModelCommand').execute()
print('ADDED',len(shapes),'obstacles, seed intersections 0; finish model edit requested')
