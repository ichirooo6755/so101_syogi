"""Assembly paths, full annuli and fastener access for the V8 candidate."""
from pathlib import Path
import json
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
src=(ROOT/'scripts/check_stack_assembly_v7.py').read_text()
src=src.replace('camera_mount_v7','camera_mount_v8').replace('01_A_slot_socket_V7:1','01_bolted_mount_V8:1')
src=src.split('paths=[]',1)[0]
exec(compile(src,'assembly_probe_helpers','exec'),globals())
main,back,tray,frame,cap=printed
obstacles=printed+existing
checks=[]
def run(label,bundle,axis,objects,distances=(.1,.5,1,3,5,10,20,30,40)):
    checks.extend(bundle_path(label,bundle,axis,objects,distances))
# Assemble the cassette off the arm, then slide the complete unit into place.
run('empty frame onto loose tray',[frame],scale(CA,-1),[tray])
run('XIAO with headers and connectors',xiao+hdr+connectors,CA,[tray,frame])
run('HX711 into frame',hx,CA,[tray,frame]+xiao+hdr+connectors)
run('perfboard into frame',perf,CA,[tray,frame]+xiao+hdr+connectors+hx)
run('rigid end plate onto frame',[cap],CA,[tray,frame]+xiao+hdr+connectors+hx+perf)
complete=[tray,frame,cap]+xiao+hdr+connectors+hx+perf
run('complete cassette slides onto mounted base',complete,scale(CB,-1),[main,back]+existing)
for name,b,bb in hardware:
    if name.startswith('M3x12_A_'):
        run(name,[(name,b,bb)],EY,[main,back]+existing,(.1,1,3,7,12,20,30))
    elif name.startswith('M3x12_tray_'):
        run(name,[(name,b,bb)],CN,printed+existing+xiao+hdr+connectors+hx+perf,(.1,1,3,6,12,20))
    elif name.startswith('M3_nut_tray_'):
        run(name,[(name,b,bb)],scale(CN,-1),[main,back,tray]+existing,(.1,1,3,6,12,20))
    elif name.startswith('M3x12_cap_'):
        run(name,[(name,b,bb)],CA,[tray,frame,cap]+xiao+hdr+connectors+hx+perf,(.1,1,3,6,12,20))
    elif name.startswith('M3_nut_cap_'):
        sign=-1 if '-16.4' in name else 1
        run(name,[(name,b,bb)],scale(CB,sign),[tray,frame],(.1,.5,1,3,6,12))

# At the loaded face, a complete annulus around each mounting bore must be
# present, not merely a watertight mesh or a shaft with some head contact.
annuli=[]
def annulus(label,p0,p1,target):
    ring=cylinder(p0,p1,6.0);subtract(ring,[cylinder(p0,p1,3.4)])
    overlap=hit(ring,target[1]);vol=ring.volume*1000
    annuli.append({'label':label,'expected_mm3':vol,'present_mm3':overlap,'fraction':overlap/vol})
for x in (22,34):
    annulus(f'arm_mount_{x}',(x,36,35),(x,41.8,35),main)
    annulus(f'arm_backing_{x}',(x,33.1,35),(x,34.7,35),back)
for a in (-6,6):
    annulus(f'tray_{a}',cp(a,18,-4.9),cp(a,18,-.9),tray)
    annulus(f'mount_tongue_{a}',cp(a,18,-8.9),cp(a,18,-5.3),main)
for b in (-16.4,16.4):
    annulus(f'frame_lug_{b}',cp(9,b,-24),cp(15,b,-24),frame)
    annulus(f'end_plate_{b}',cp(15.6,b,-24),cp(17.4,b,-24),cap)

contacts=[]
for a in (-8.5,8.5):
    for b in (-4.4,4.4):
        pad=cbox(a-.6,a+.6,b-.6,b+.6,-1,0)
        contacts.append(hit(translate(xiao[37][1],scale(CN,-.05)),pad))
modules=[]
for bundle,other in ((hx,perf+xiao+hdr+connectors),(perf,xiao+hdr+connectors),(hdr,hx+perf)):
    for k,b,bb in bundle:modules += [[k,*r] for r in collisions(b,other)]
plug=cbox(12.2,30,-5,5,.5,5.8)
usb=collisions(plug,printed+existing+xiao+hdr+connectors+hx+perf)
tool_hits=[]
for x in (22,34):
    q=cylinder((x,45.05,35),(x,65,35),3.5)
    tool_hits += [[f'arm_{x}',*v] for v in collisions(q,[main,back]+existing)]
for a in (-6,6):
    q=cylinder(cp(a,18,2.25),cp(a,18,25),3.5)
    tool_hits += [[f'tray_{a}',*v] for v in collisions(q,printed+existing+xiao+hdr+connectors+hx+perf)]
for b in (-16.4,16.4):
    q=cylinder(cp(20.55,b,-24),cp(42,b,-24),3.5)
    tool_hits += [[f'cap_{b}',*v] for v in collisions(q,[tray,frame,cap]+xiao+hdr+connectors+hx+perf)]
wire_hits=[]
for h in (-17.3,-26.2):
    for a in (-8,-4,0):
        q=cylinder(cp(a,-10,h),cp(a,-18,h),1.4)
        wire_hits += [[a,h,*v] for v in collisions(q,printed)]
cartridge=[]
for d in (1,5,10,25,50,100):
    cartridge += [[d,*v] for v in collisions(translate(existing[-2][1],(0,0,-d)),printed)]
preload_hits=[]
for k,b,bb in complete:
    preload_hits += [[k,*v] for v in collisions(translate(b,scale(CN,-.20)),[main,back]+existing)]
failures={'path_issues':[r for r in checks if r['hits']],'annuli_incomplete':[r for r in annuli if r['fraction']<.999],
    'module_issues':modules,'usb_hits':usb,'driver_hits':tool_hits,'wire_hits':wire_hits,
    'cartridge_hits':cartridge,'tray_gap_closure_hits':preload_hits,'xiao_support_missing':any(v<.02 for v in contacts)}
result={'passed':not any(failures.values()),'failures':failures,'paths':checks,
    'bolt_bearing_annuli':annuli,'xiao_support_contacts_mm3':contacts,
    'hardware':'6 x M3x12 and 6 x M3 nuts; physical assembly untested'}
(CHECK/'assembly_paths.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps({'passed':result['passed'],'failures':failures,'annuli':annuli},ensure_ascii=False,indent=2))
assert result['passed'],'Investigate assembly_paths.json'
