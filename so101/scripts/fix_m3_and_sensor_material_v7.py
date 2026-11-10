"""Restore through shanks after gusset union; copy the user's sensor material."""
import adsk.core
import adsk.fusion
import json

root='/Users/sugawaraichirou/Documents/ChatGPT/so101'; out=root+'/output/v7'
assert ui.activeCommand=='SelectCommand'
doc=next(x for x in app.documents if x.name=='部品１_V7_閉断面台座補強')
doc.activate(); ui.workspaces.itemById('FusionSolidEnvironment').activate()
d=adsk.fusion.Design.cast(app.activeProduct); r=d.rootComponent
assert abs(r.bRepBodies.item(0).volume*1000-39664.62284866992)<1e-4
ns={}
with open(root+'/scripts/fusion_shapes.py',encoding='utf-8') as f: exec(compile(f.read(),'<shapes>','exec'),ns)
h=ns['Shapes'](d)
s=h.sketch(r,'V7_fixed_M3_shank_through_restored',32.7)
for y in (26.96294620236,34.36294620236): h.circle(s,(62,y,32.7),'3.4 mm')
h.extrude(r,s,'6.9 mm',h.CUT,'V7_M3_clear_shanks_above_head_seat')
body=r.bRepBodies.item(0)
assert all(int(f.healthState)==0 for f in r.features)
t=adsk.fusion.TemporaryBRepManager.get()
def cylinder(y,z0,z1,diameter):
    return t.createCylinderOrCone(adsk.core.Point3D.create(6.2,y/10,z0/10),diameter/20,
        adsk.core.Point3D.create(6.2,y/10,z1/10),diameter/20)
def interference(a,b):
    x=t.copy(a); assert t.booleanOperation(x,b,adsk.fusion.BooleanTypes.IntersectionBooleanType)
    return x.volume*1000
checks=[]
for y in (26.96294620236,34.36294620236):
    shaft=interference(cylinder(y,32.7,44.7,3.0),body)
    head_seated=interference(cylinder(y,29.7,32.7,5.5),body)
    head_raised=interference(cylinder(y,29.8,32.8,5.5),body)
    assert shaft<1e-5 and head_seated<1e-5 and head_raised>1.,(shaft,head_seated,head_raised)
    annuli=[f.area*100 for f in body.faces if isinstance(f.geometry,adsk.core.Plane)
        and abs(f.geometry.normal.z)>.99 and abs(f.geometry.origin.z*10-32.7)<1e-6
        and abs(f.centroid.x*10-62)<1e-5 and abs(f.centroid.y*10-y)<1e-5]
    assert len(annuli)==1 and abs(annuli[0]-21.1115026321234)<1e-5,annuli
    checks.append({'y_mm':y,'shank_hole_mm':3.4,'head_bore_mm':6.2,'head_seat_z_mm':32.7,
        'seat_annulus_mm2':annuli[0],'M3_3mm_shaft_interference_mm3':shaft,
        'M3_5p5mm_head_seated_interference_mm3':head_seated,
        'head_cannot_pass_seat_interference_at_0p1mm_mm3':head_raised,
        'fixed_screw_M3x12_nominal_engagement_mm':5.2})
copy=t.copy(body)
assert doc.save('Restore phi3.4 through shanks after gusset union; verify head stops on phi6.2/3.4 annular shoulder')
reference=next(x for x in app.documents if x.name.startswith('SC616C_1kg_Fusion.f3d'))
rd=adsk.fusion.Design.cast(reference.products.itemByProductType('DesignProductType'))
refbody=next(b for o in rd.rootComponent.allOccurrences for b in o.bRepBodies if b.volume>1e-6)
user_material=refbody.material
assert user_material.name=='鋼',user_material.name
simdoc=next(x for x in app.documents if x.name.startswith('so101_V7_閉断面補強_筆圧検証'))
simdoc.activate(); ui.workspaces.itemById('FusionSolidEnvironment').activate()
sd=adsk.fusion.Design.cast(app.activeProduct)
base=sd.rootComponent.occurrences.itemByName('base:1').component
old=base.bRepBodies.item(0); plastic=old.material
assert old.deleteMe()
b=base.bRepBodies.add(copy); b.name='base'; b.material=plastic
steel=sd.materials.addByCopy(user_material,'SC616C_USER_SELECTED_STEEL')
sensor=sd.rootComponent.occurrences.itemByName('sensor:1').component.bRepBodies.item(0)
sensor.material=steel
assert sd.exportManager.execute(sd.exportManager.createSTEPExportOptions(out+'/analysis/base.step',base))
assert simdoc.save('Copy user-selected steel from SC616C source; restore fixed M3 shank holes')
with open(out+'/fastener_check.json','w',encoding='utf-8') as f:
    json.dump({'passed':True,'holes':checks,'sensor_material':steel.name,
        'sensor_E_MPa':steel.materialProperties.itemById('structural_Young_modulus').value/1000,
        'material_source':reference.name,'actual_sensor_alloy_verified':False},f,ensure_ascii=False,indent=2)
with open(out+'/created.json',encoding='utf-8') as f: made=json.load(f)
made.update(base_volume_mm3=body.volume*1000,fastener_check_passed=True,
    sensor_material=steel.name,steel_comparison_pending=True)
with open(out+'/created.json','w',encoding='utf-8') as f: json.dump(made,f,ensure_ascii=False,indent=2)
print(json.dumps({'M3_checks':checks,'sensor_material':steel.name,'volume_mm3':body.volume*1000},ensure_ascii=False,indent=2))
