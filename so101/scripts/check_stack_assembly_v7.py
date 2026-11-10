"""Test board, header and removable-cap assembly in the V7 Fusion document."""
import adsk.core
import adsk.fusion
import itertools
import json
import math
from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
helper=(ROOT/'scripts/build_camera_addon_v1.py').read_text().split("progress('building_temporary_geometry')",1)[0]
exec(compile(helper,'mm_geometry_helpers','exec'),globals())
CHECK=ROOT/'output/camera_mount_v7'; build=json.loads((CHECK/'design_check.json').read_text())
owned=[]
for doc in app.documents:
    d=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    if d and d.rootComponent.occurrences.itemByName('01_A_slot_socket_V7:1'):owned.append((doc,d))
document,design=owned[-1]; root=design.rootComponent
names=list(build['geometry']); parts={k:T.copy(root.occurrences.itemByName(k+':1').bRepBodies.item(0)) for k in names}
def cached(items):return [(k,b,bbox(b)) for k,b in items]
printed=cached(parts.items())
existing=cached([(b.name,T.copy(b)) for b in root.occurrences.itemByName('REFERENCE_SO101_unchanged:1').bRepBodies])
modules={name:cached([(b.name,T.copy(b)) for b in root.occurrences.itemByName(name+':1').bRepBodies]) for name in (
    'REFERENCE_XIAO_Sense_1pc','REFERENCE_XIAO_two_pin_headers','REFERENCE_SparkFun_SEN13879_HX711_1pc',
    'REFERENCE_perfboard_same_size_1pc','REFERENCE_M3_hardware_do_not_print','REFERENCE_header_connector_clearance')}
xiao=modules['REFERENCE_XIAO_Sense_1pc']; hdr=modules['REFERENCE_XIAO_two_pin_headers']
hx=modules['REFERENCE_SparkFun_SEN13879_HX711_1pc']; perf=modules['REFERENCE_perfboard_same_size_1pc']
hardware=modules['REFERENCE_M3_hardware_do_not_print']
connectors=modules['REFERENCE_header_connector_clearance']
CA=tuple(build['camera_basis']['A']); CB=tuple(build['camera_basis']['B']); CN=tuple(build['camera_basis']['N'])
CO=tuple(build['parameters']['camera_pcb_origin_mm'])
def translate(b,delta):
    q=T.copy(b); m=adsk.core.Matrix3D.create(); m.translation=vec(scale(delta,.1)); T.transform(q,m); return q
def collisions(b,obstacles):
    bb=bbox(b); return [[k,round(v,6)] for k,q,qb in obstacles if (v:=hit(b,q,bb,qb))>.01]
def bundle_path(label,bundle,axis,obstacles,distances):
    out=[]
    for distance in distances:
        hits=[]
        for k,b,bb in bundle:hits += [[k,*r] for r in collisions(translate(b,scale(axis,distance)),obstacles)]
        out.append({'label':label,'offset_mm':distance,'direction':axis,'hits':hits})
    return out
distances=(.1,.25,.5,1,3,5,10,20,30,40)
paths=[]
# Assemble the cassette off the arm, then insert it into the mounted socket.
paths+=bundle_path('01 empty frame onto loose tray',[printed[4]],scale(CA,-1),[printed[3]],distances)
paths+=bundle_path('02 XIAO with both headers and connectors into loose tray',xiao+hdr+connectors,CA,[printed[3],printed[4]],distances)
paths+=bundle_path('03 HX711 into loose cassette',hx,CA,[printed[3],printed[4]]+xiao+hdr+connectors,distances)
paths+=bundle_path('04 universal PCB into loose cassette',perf,CA,[printed[3],printed[4]]+xiao+hdr+connectors+hx,distances)
complete=[printed[3],printed[4],printed[5]]+xiao+hdr+connectors+hx+perf
paths+=bundle_path('05 assembled cassette into socket; side key absent',complete,scale(CB,-1),printed[:2]+existing,distances)
headpaths=[]
for k,b,bb in hardware:
    if k.startswith('M3x12'):
        headpaths+=bundle_path(k,[(k,b,bb)],EY,printed[:2]+existing,(.1,1,3,7,12,20,30))
assert len(headpaths)==14
modules_hits=[]
for bundle,other in ((hx,perf+xiao+hdr+connectors),(perf,xiao+hdr+connectors),(hdr,hx+perf)):
    for k,b,bb in bundle:modules_hits += [[k,*r] for r in collisions(b,other)]

retention=[]
for label,body,axes in (('HX711 PCB',hx[0][1],(CA,CB,CN)),
                        ('Universal PCB',perf[0][1],(CA,CB,CN)),
                        ('XIAO PCB',xiao[37][1],(CA,CB,CN))):
    for index,axis in enumerate(axes):
        for sign in (-1,1):
            r=collisions(translate(body,scale(axis,sign*1.2)),printed)
            retention.append({'part':label,'axis':index,'direction':scale(axis,sign),'displacement_mm':1.2,'hits':r})
tray_lock=[]
for sign in (-1,1):
    tray_lock.append({'direction':scale(CB,sign),'hits':collisions(translate(printed[3][1],scale(CB,sign*1.2)),[printed[0],printed[2]])})
frame_lock=[]
for sign in (-1,1):
    hits=[]
    for k,b,bb in (printed[4],printed[5]):hits += [[k,*v] for v in collisions(translate(b,scale(CA,sign*1.2)),[printed[3]])]
    frame_lock.append({'direction':scale(CA,sign),'hits':hits})
cap_lock=[]
for sign in (-1,1):
    cap_lock.append({'direction':scale(CA,sign),'hits':collisions(translate(printed[5][1],scale(CA,sign*1.2)),[printed[4]])})
side_key_lock=collisions(translate(printed[2][1],scale(CA,1.2)),[printed[0],printed[3]])

# Approximate both cantilevers pushed outward 0.8 mm during assembly. This is
# a kinematic interference check, not a PLA stress/retention-force test.
cap_core=union([cbox(15.49,17.49,-13.5,13.5,-33.3,-6.4),
    cbox(10.55,17.49,-2.6,2.6,-6.1,-4.3),cbox(15.49,17.49,-2.6,2.6,-7.5,-4.3)]+[
    cbox(15.3,17.49,b0,b1,-26,-22.5) for b0,b1 in ((13.5,14.95),(-14.95,-13.5))])
deflected=[('cap_core',cap_core,bbox(cap_core))]
for sign in (-1,1):
    strips=[]
    for i in range(16):
        a0=2.95+i*(12.54/16); a1=2.95+(i+1)*(12.54/16)+.025
        t=(15.49-(a0+a1)/2)/12.54; off=.8*t*t*(3-2*t)
        lo,hi=(13.75+off,14.95+off) if sign>0 else (-14.95-off,-13.75-off)
        strips.append(cbox(a0,a1,lo,hi,-26,-22.5))
    lo,hi=(13.8,14.55) if sign>0 else (-14.55,-13.8)
    strips.append(cbox(2.95,5.05,lo,hi,-26,-22.5))
    for i,b in enumerate(strips):deflected.append((f'arm_{sign}_{i}',b,bbox(b)))
cap_path=bundle_path('Removable cap before mounting, arms deflected 0.8mm',deflected,CA,
                     [printed[3],printed[4]]+hx+perf+xiao+hdr+connectors,(.1,.25,.5,1,3,5,10,20,30,40))

# Side key enters from +A, with its single spring flexed inward 0.55 mm.
key_core=union([cbox(6,11.25,17.5,20.3,-3.8,-2.2),cbox(11.25,14.5,16.8,22.5,-3.8,-2.2)])
key_deflected=[('side_key_core',key_core,bbox(key_core))]
for i in range(16):
    a0=-.5+i*(13.5/16); a1=-.5+(i+1)*(13.5/16)+.025
    t=(13-(a0+a1)/2)/13.5; off=.55*t*t*(3-2*t)
    q=cbox(a0,a1,21.3-off,22.5-off,-3.8,-2.2)
    key_deflected.append((f'key_spring_{i}',q,bbox(q)))
q=cbox(-.5,1,21.95,22.45,-3.8,-2.2);key_deflected.append(('key_barb_deflected',q,bbox(q)))
key_path=bundle_path('06 side key inserted with spring flexed',key_deflected,CA,
    printed[:2]+complete+existing,(.1,.25,.5,1,3,5,10))
key_start=cached([(k,translate(b,scale(CA,10))) for k,b,bb in key_deflected])
key_path+=bundle_path('06 side key approach from outside at 10mm offset',key_start,scale(CN,-1),
    printed[:2]+complete+existing,(.1,.5,1,3,5,10,20,30))

contacts=[]
for a,b in itertools.product((-8.5,8.5),(-4.4,4.4)):
    pad=cbox(a-.6,a+.6,b-.6,b+.6,-1,0)
    contacts.append({'a_b_mm':[a,b],'contact_mm3':hit(translate(xiao[37][1],scale(CN,-.05)),pad)})
plug=cbox(12.2,30,-5,5,.5,5.8)
usb_hits=collisions(plug,printed+existing+xiao+hdr+connectors+hx+perf)
release_tool=cylinder(cp(.25,22.75,-3),cp(.25,34,-3),1.5)
release_hits=collisions(release_tool,printed[:2]+printed[3:]+existing+xiao+hdr+connectors+hx+perf)
wire_paths=[]
for h in (-17.3,-26.2):
    for a in (-8,-4,0):
        q=cylinder(cp(a,-10,h),cp(a,-18,h),1.4)
        wire_paths.append({'a_mm':a,'h_mm':h,'printed_hits':collisions(q,printed)})
closed=[]
for k,b,bb in printed:closed.append((k,translate(b,(0,.25 if k.startswith('02_') else -.25,0))))
for values in modules.values():
    for k,b,bb in values:closed.append((k,translate(b,(0,.25 if k.startswith('M3_nut_A_') else -.25,0))))
closed_hits=[]
for k,b in closed:closed_hits += [[k,*v] for v in collisions(b,existing)]
for i,(k,b) in enumerate(closed[:6]):
    for q,qb in closed[i+1:]:
        if (v:=hit(b,qb))>.01:closed_hits.append([k,q,round(v,6)])
cartridge=[]
for d in (1,5,10,25,50,100):
    cartridge.append({'down_mm':d,'hits':collisions(translate(existing[-2][1],(0,0,-d)),printed)})
issues=[r for r in paths+headpaths+cap_path+key_path if r['hits']]
failures={'path_issues':issues,'module_issues':modules_hits,'PCB_retention_failures':[r for r in retention if not r['hits']],
    'tray_key_failures':[r for r in tray_lock if not r['hits']],'frame_tongue_failures':[r for r in frame_lock if not r['hits']],
    'cap_hook_failures':[r for r in cap_lock if not r['hits']],'side_key_not_locked':not bool(side_key_lock),
    'USB_hits':usb_hits,'release_tool_hits':release_hits,'wire_window_hits':[r for r in wire_paths if r['printed_hits']],'closed_hits':closed_hits,
    'support_failures':[r for r in contacts if r['contact_mm3']<.02],'cartridge_hits':[r for r in cartridge if r['hits']]}
passed=not any(failures.values())
report={'passed':passed,'failures':failures,'assembly_paths':paths,'bolt_paths':headpaths,
    'cap_deflected_kinematic_paths':cap_path,'nominal_cantilever_deflection_mm':.8,
    'approx_beam_strain_fraction':3*1.2*.8/(2*12.54**2),'snap_strength_creep_and_cycles_not_tested':True,
    'PCB_retention':retention,'tray_key':tray_lock,'frame_tongue':frame_lock,'cap_hook':cap_lock,
    'side_key_lock':side_key_lock,'side_key_approach':key_path,'release_tool_hits':release_hits,'wire_window_paths':wire_paths,
    'camera_PCB_support_contacts':contacts,'USB_plug_envelope_local_mm':[[12.2,-5,.5],[30,5,5.8]],
    'closed_gap_per_jaw_mm':.25,'cartridge_removal':cartridge,'cable_routing_and_actual_assembly_not_verified':True}
(CHECK/'assembly_paths.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({'passed':passed,'failures':failures,'support_contacts':contacts},ensure_ascii=False,indent=2))
assert passed,'Review assembly_paths.json before printing'
