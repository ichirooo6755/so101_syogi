"""Read-only virtual fastener clearance/shoulder checks on final V8 BReps."""
import adsk.core
import adsk.fusion
import json
import math
root='/Users/sugawaraichirou/Documents/ChatGPT/so101'; out=root+'/output/v8'
doc=next(d for d in app.documents if d.name=='部品１_V8_元取付形状保持')
d=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
body=d.rootComponent.bRepBodies.item(0)
t=adsk.fusion.TemporaryBRepManager.get()
def cyl_z(x,y,z0,z1,dia):
    return t.createCylinderOrCone(adsk.core.Point3D.create(x/10,y/10,z0/10),dia/20,
        adsk.core.Point3D.create(x/10,y/10,z1/10),dia/20)
def cyl_y(x,z,y0,y1,dia):
    return t.createCylinderOrCone(adsk.core.Point3D.create(x/10,y0/10,z/10),dia/20,
        adsk.core.Point3D.create(x/10,y1/10,z/10),dia/20)
def hit(a,b=body):
    x=t.copy(a); assert t.booleanOperation(x,b,adsk.fusion.BooleanTypes.IntersectionBooleanType)
    return x.volume*1000
fixed=[]
for y in (26.96294620236,34.36294620236):
    shaft=hit(cyl_z(62,y,32.7,44.7,3))
    head=hit(cyl_z(62,y,29.7,32.7,5.5))
    stop=hit(cyl_z(62,y,29.8,32.8,5.5))
    assert shaft<1e-5 and head<1e-5 and stop>1
    fixed.append({'y_mm':y,'shank_diameter_mm':3.4,'head_access_diameter_mm':6.2,
        'shaft_overlap_mm3':shaft,'seated_head_overlap_mm3':head,'head_pushed_0p1mm_overlap_mm3':stop,
        'M3x12_nominal_engagement_mm':5.2})
servo=[]
for side,seat,direction in (('negative',-20.55,1),('positive',23.7,-1)):
    for i in range(4):
        a=math.pi/4+i*math.pi/2; x=-2+7*math.cos(a); z=34+7*math.sin(a)
        h0,h1=sorted((seat-direction*3,seat))
        s0,s1=sorted((seat,seat+direction*6))
        shaft=hit(cyl_y(x,z,s0,s1,3))
        smallhead=hit(cyl_y(x,z,h0,h1,4.5))
        ordinary=hit(cyl_y(x,z,h0,h1,5.5))
        assert shaft<1e-4 and smallhead<1e-4 and ordinary>.5,(side,i,shaft,smallhead,ordinary)
        servo.append({'side':side,'index':i,'shaft_overlap_mm3':shaft,'small_head_overlap_mm3':smallhead,
            'normal_5p5mm_head_overlap_mm3':ordinary,'head_pocket_diameter_mm':5.4,
            'required_small_head_diameter_mm':4.5,'M3x6_nominal_engagement_mm':2.5})
report={'passed':True,'source_document':doc.name,'base_volume_mm3':body.volume*1000,
    'fixed_loadcell_holes':fixed,'servo_8_small_head_bolts':servo,
    'physical_print_and_actual_thread_depth_not_tested':True}
with open(out+'/fastener_check.json','w',encoding='utf-8') as f: json.dump(report,f,ensure_ascii=False,indent=2)
print('V8 FASTENERS PASS: 2 fixed-end M3 shafts pass, heads stop; 8 servo small heads fit, standard heads do not.')
