"""Assembly/removal and geometric positive-retention checks; no physical claims."""
import adsk.core
import adsk.fusion
import itertools
import json
import math
from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
helper=(ROOT/'scripts/build_camera_addon_v1.py').read_text().split("progress('building_temporary_geometry')",1)[0]
exec(compile(helper,'mm_geometry_helpers','exec'),globals())
CHECK=ROOT/'output/camera_mount_v6'
build=json.loads((CHECK/'design_check.json').read_text())
candidates=[]
for doc in app.documents:
    d=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    if d and d.rootComponent.occurrences.itemByName('01_flat_carrier_socket_V6:1'):candidates.append((doc,d))
document,design=candidates[-1]; root=design.rootComponent
names=list(build['geometry'])
parts={k:T.copy(root.occurrences.itemByName(k+':1').bRepBodies.item(0)) for k in names}
main,inner,gate,tray=[parts[k] for k in names]
def cached(items):return [(k,b,bbox(b)) for k,b in items]
printed=cached(parts.items())
existing=cached([(b.name,T.copy(b)) for b in root.occurrences.itemByName('REFERENCE_SO101_unchanged:1').bRepBodies])
fixed=existing[:17]; moving=existing[17:]
CA=tuple(build['camera_basis']['A']); CB=tuple(build['camera_basis']['B']); CN=tuple(build['camera_basis']['N'])
CO=tuple(build['parameters']['camera_pcb_origin_mm'])
modules={name:cached([(b.name,T.copy(b)) for b in root.occurrences.itemByName(name+':1').bRepBodies])
         for name in ('REFERENCE_XIAO_Sense_1pc','REFERENCE_HX711_1pc',
                      'REFERENCE_TXS0108E_5V_3V3_translator_1pc','REFERENCE_M3_hardware_do_not_print')}
xiao=modules['REFERENCE_XIAO_Sense_1pc']; hx=modules['REFERENCE_HX711_1pc']; tx=modules['REFERENCE_TXS0108E_5V_3V3_translator_1pc']
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
paths=[]
# Camera PCB is loaded before its tray is keyed to the main socket.
paths+=bundle_path('XIAO into loose tray',xiao,CA,[printed[3]],(.1,.25,.5,1,3,5,10,20,30,40))
paths+=bundle_path('Tray and populated XIAO into socket',[printed[3]]+xiao,scale(CB,-1),printed[:2]+existing,
                   (.1,.25,.5,1,3,5,10,20,30,40))
paths+=bundle_path('HX711 from right before gate',hx,EX,printed[:2]+[printed[3]]+existing+tx+xiao,
                   (.1,.25,.5,1,3,5,10,20,30,40))
paths+=bundle_path('TXS0108E from left before gate',tx,(-1,0,0),printed[:2]+[printed[3]]+existing+hx+xiao,
                   (.1,.25,.5,1,3,5,10,20,30,40))
paths+=bundle_path('Common gate outside approach',[printed[2]],EY,printed[:2]+[printed[3]]+existing+hx+tx+xiao,
                   (.1,.25,.5,1,3,5,10,20,30))
headpaths=[]
for k,b,bb in modules['REFERENCE_M3_hardware_do_not_print']:
    if k.startswith('M3x12'):
        headpaths+=bundle_path(k,[(k,b,bb)],EY,printed+existing+hx+tx+xiao,(.1,1,3,7,12,20,30))
issues=[r for r in paths+headpaths if r['hits']]

# Distinct boards/assumed soldered lead envelopes must not overlap each other.
module_hits=[]
for k,b,bb in hx:
    module_hits += [[k,*r] for r in collisions(b,tx+xiao)]

retention=[]
for label,body,axes in (('HX711 PCB',hx[0][1],(EX,EY,EZ)),
                        ('TXS0108E PCB',tx[0][1],(EX,EY,EZ)),
                        ('XIAO main PCB',xiao[37][1],(CA,CB,CN))):
    for axis_index,axis in enumerate(axes):
        for sign in (-1,1):
            hits=collisions(translate(body,scale(axis,sign*1.2)),printed)
            retention.append({'part':label,'axis_index':axis_index,'direction':scale(axis,sign),
                              'displacement_mm':1.2,'retaining_hits':hits})
tray_lock=[]
for sign in (-1,1):
    hits=collisions(translate(tray,scale(CB,sign*1.2)),[printed[0],printed[2]])
    tray_lock.append({'direction':scale(CB,sign),'offset_mm':1.2,'hits':hits})
support_contacts=[]
for a,b in itertools.product((-8.5,8.5),(-6.5,6.5)):
    pad=cbox(a-.6,a+.6,b-.6,b+.6,-1,0)
    overlap=hit(translate(xiao[37][1],scale(CN,-.05)),pad)
    support_contacts.append({'pad_a_b_mm':[a,b],'PCB_pushed_0p05mm_contact_mm3':overlap})

# Nominal .25 mm gaps close at the robot's outer/inner faces without collisions.
seated=[]
for k,b,bb in printed:seated.append((k,translate(b,(0,.25 if k.startswith('02_') else -.25,0))))
for values in modules.values():
    for k,b,bb in values:seated.append((k,translate(b,(0,.25 if k.startswith('M3_nut_A_') else -.25,0))))
seated_hits=[]
for k,b in seated:seated_hits += [[k,*r] for r in collisions(b,existing)]
for i,(k,b) in enumerate(seated[:4]):
    for q,qb in seated[i+1:]:
        if (v:=hit(b,qb))>.01:seated_hits.append([k,q,round(v,6)])

cartridge=[]
for offset in (1,5,10,25,50,100):
    cartridge.append({'offset_down_mm':offset,'hits':collisions(translate(moving[-2][1],(0,0,-offset)),printed)})
CO=tuple(build['parameters']['camera_pcb_origin_mm'])
# Representative straight USB-C plug envelope; not every bulky cable overmould.
plug=cbox(12.2,30,-5,5,.5,5.8)
usb_hits=collisions(plug,printed+existing+xiao)
report={'passed':len(headpaths)==14 and not (issues or module_hits or seated_hits or usb_hits) and
    all(r['retaining_hits'] for r in retention) and all(r['hits'] for r in tray_lock) and not any(r['hits'] for r in cartridge)
    and all(r['PCB_pushed_0p05mm_contact_mm3']>.02 for r in support_contacts),
    'PCB_and_gate_assembly_paths':paths,'complete_bolt_approach':headpaths,'path_issues':issues,
    'between_electronics_hits':module_hits,'PCB_positive_retention':retention,'camera_tongue_axial_retention':tray_lock,
    'four_camera_PCB_support_contacts':support_contacts,'GPIO_wire_paths_included':14,
    'gap_closing_per_jaw_mm':.25,'gap_closed_hits':seated_hits,'cartridge_removal':cartridge,
    'representative_USB_C_plug_local_mm':[[12.2,-5,.5],[30,5,5.8]],'USB_plug_hits':usb_hits,
    'actual_print_tolerance_retention_force_and_cable_flex_unverified':True}
(CHECK/'assembly_paths.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({'passed':report['passed'],'path_issues':issues,'between_electronics':module_hits,
    'retention_failures':[r for r in retention if not r['retaining_hits']],
    'tray_lock_failures':[r for r in tray_lock if not r['hits']],
    'gap_closed_hits':seated_hits,'USB_hits':usb_hits,'cartridge_removal':cartridge},ensure_ascii=False,indent=2))
assert report['passed'],'See assembly_paths.json; do not release yet'
