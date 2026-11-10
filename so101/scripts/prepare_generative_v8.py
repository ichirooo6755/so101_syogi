"""Generative study geometry: preserved original mounts and fixed socket only.

The load cell and brush carrier are obstacles, not designable plastic. Complete
wrist sweep and assembly/driver corridors are explicit geometric obstacles.
"""
import adsk.core
import adsk.fusion
import json
import math
import os

root='/Users/sugawaraichirou/Documents/ChatGPT/so101'; out=root+'/output/v8'
assert ui.activeCommand=='SelectCommand'
main=next(doc for doc in app.documents if doc.name.startswith('so101書道'))
md=adsk.fusion.Design.cast(main.products.itemByProductType('DesignProductType')); mr=md.rootComponent
source=next(doc for doc in app.documents if doc.name=='部品１_V8_元取付形状保持')
sd=adsk.fusion.Design.cast(source.products.itemByProductType('DesignProductType'))
t=adsk.fusion.TemporaryBRepManager.get(); seed=t.copy(sd.rootComponent.bRepBodies.item(0))
def cyl_y(y0,y1,r,x=-2,z=34):
    return t.createCylinderOrCone(adsk.core.Point3D.create(x/10,y0/10,z/10),r/10,
        adsk.core.Point3D.create(x/10,y1/10,z/10),r/10)
def cyl_z(z0,z1,r,x,y):
    return t.createCylinderOrCone(adsk.core.Point3D.create(x/10,y/10,z0/10),r/10,
        adsk.core.Point3D.create(x/10,y/10,z1/10),r/10)
def box(x0,x1,y0,y1,z0,z1):
    return t.createBox(adsk.core.OrientedBoundingBox3D.create(
        adsk.core.Point3D.create((x0+x1)/20,(y0+y1)/20,(z0+z1)/20),
        adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),
        (x1-x0)/10,(y1-y0)/10,(z1-z0)/10))
def clip(a,b):
    c=t.copy(a); assert t.booleanOperation(c,b,adsk.fusion.BooleanTypes.IntersectionBooleanType)
    return c
def subtract(a,b):
    c=t.copy(a); assert t.booleanOperation(c,b,adsk.fusion.BooleanTypes.DifferenceBooleanType)
    return c
def overlap(a,b):
    if not a.boundingBox.intersects(b.boundingBox): return 0.
    return clip(a,b).volume*1000
cy=md.userParameters.itemByName('sc_brush_axis_y').value*10
preserves={
    'PRESERVE_01_original_negative_servo_interface':clip(seed,cyl_y(-23.55,-15.55,13)),
    'PRESERVE_02_original_positive_servo_interface':clip(seed,cyl_y(18.7,27.3,13)),
    'PRESERVE_03_M3_slide_in_fixed_socket':clip(seed,box(54.8,69.2,23.46294620236,41.56294620236,29.5,49.5))}
assert all(b.isSolid and b.volume>0 for b in preserves.values())
obstacles={
    'OBSTACLE_wrist_full_rotation_core':cyl_y(-15.05,18.2,46.5),
    'OBSTACLE_negative_wrist_sweep_annulus':subtract(cyl_y(-28.5,-15.05,46.5),cyl_y(-28.51,-15.04,13.5)),
    'OBSTACLE_positive_wrist_sweep_annulus':subtract(cyl_y(18.2,27.5,46.5),cyl_y(18.19,27.51,13.5)),
    'OBSTACLE_cartridge_neck_pullout':cyl_z(-90,33,11.5,62,cy),
    'OBSTACLE_cartridge_flange_ears_pullout':box(46.5,77.5,cy-26.5,cy+26.5,-90,13),
    'OBSTACLE_carrier_upper_bridge':box(55.6,68.4,cy-14.9,cy+14.9,33.1,39.49),
    'OBSTACLE_load_cell_sliding_corridor':box(57.3,66.7,-70,38.86294620236,39.5,45.9),
    'OBSTACLE_cell_strain_gauge_clearance':box(56.65,67.35,9.56,23.36,38.5,47)}
for i,y in enumerate((26.96294620236,34.36294620236)):
    obstacles[f'OBSTACLE_fixed_M3_head_driver_{i}']=cyl_z(-90,32.7,3.1,62,y)
    obstacles[f'OBSTACLE_fixed_M3_shank_{i}']=cyl_z(32.7,39.5,1.7,62,y)
for side,y0,y1,seat in (('negative',-60,-15.55,-20.55),('positive',18.7,60,23.7)):
    for i in range(4):
        a=math.pi/4+i*math.pi/2; x=-2+7*math.cos(a); z=34+7*math.sin(a)
        head0,head1=(y0,seat) if side=='negative' else (seat,y1)
        shank0,shank1=(seat,-17.05) if side=='negative' else (20.2,seat)
        obstacles[f'OBSTACLE_{side}_original_head_driver_{i}']=cyl_y(head0,head1,2.7,x,z)
        obstacles[f'OBSTACLE_{side}_original_shank_{i}']=cyl_y(shank0,shank1,1.6,x,z)
# Exact copied inner pockets are also empty space, including the original
# non-circular/partial drive key recess. No newly generated plastic may fill it.
for side,y0,y1,key in (('negative',-23.55,-15.55,'PRESERVE_01_original_negative_servo_interface'),
                        ('positive',18.7,27.3,'PRESERVE_02_original_positive_servo_interface')):
    obstacles['OBSTACLE_'+side+'_exact_original_mount_voids']=subtract(cyl_y(y0,y1,13),preserves[key])
hits=[]
for name,b in obstacles.items():
    v=overlap(seed,b)
    if v>.003: hits.append([name,v])
assert not hits,hits
doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
d=adsk.fusion.Design.cast(app.activeProduct); d.designType=adsk.fusion.DesignTypes.DirectDesignType
r=d.rootComponent
lib=app.materialLibraries.itemById('C1EEA57C-3F56-45FC-B8CB-A9EC46A9994C')
plastic=d.materials.addByCopy(lib.materials.itemById('PrismMaterial-022'),'PRINT_ASSUMED_E1500MPa_ISOTROPIC_NOT_TESTED')
for p in plastic.materialProperties:
    if p.objectType!='adsk::core::FloatProperty': continue
    if p.id.startswith('structural_Young_modulus'): p.value=1500000
    elif p.id.startswith('structural_Poisson_ratio'): p.value=.35
    elif p.id.startswith('structural_Shear_modulus'): p.value=1500000/2.7
    elif p.id in ('structural_Density','thermal_Density'): p.value=1240
    elif p.id=='structural_Minimum_yield_stress': p.value=20000
    elif p.id=='structural_Minimum_tensile_strength': p.value=25000
for role,shapes in (('preserve',preserves),('obstacle',obstacles),('starting',{'STARTING_V8_supported_yoke':seed})):
    for name,b in shapes.items():
        body=r.bRepBodies.add(b); body.name=name; body.material=plastic
        body.attributes.add('so101_generative','role',role)
        if role=='obstacle': body.isLightBulbOn=False
assert doc.saveAs('so101_V8_元取付部保持_ジェネレーティブ',main.dataFile.parentFolder,'',
    'Original servo mounts preserved; 360-degree wrist sweep, cell flexure, cartridge removal and screw-driver spaces excluded. Base plastic only.')
report={'document':doc.name,'cloud_id':doc.dataFile.id,
    'preserve_bodies':list(preserves),'obstacle_bodies':list(obstacles),
    'starting_volume_mm3':seed.volume*1000,'obstacle_starting_interferences':hits,
    'printed_material_E_MPa':1500,'sensor_in_designable_material':False,
    'nominal_brush_axis_mm':[62,cy],'brush_tip_z_mm':-52,
    'required_base_equivalent_load':{'force_N':[0,0,6],
        'application_point_mm':[62,cy,30.5],
        'fixed_socket_reference_mm':[62,30.66294620236,39.5],
        'moment_at_socket_Nmm':[-167.4,0,0]},
    'additional_load_cases_required':'Brush-side +/-0.5 N at Z=-52 and +/-10 Nmm twist',
    'suggested_objective':'Maximize stiffness; mass target 0.045 kg; safety factor 2; displacement limit 0.1 mm',
    'preserved_mount_details':'Original copied diagonal holes and inner pockets, no redesign',
    'native_generation_started':False,'credits_spent':0}
with open(out+'/generative_preparation.json','w',encoding='utf-8') as f: json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps(report,ensure_ascii=False,indent=2))
assert ui.workspaces.itemById('GenerativeEnvironment').activate()
print('Generative workspace activated')
