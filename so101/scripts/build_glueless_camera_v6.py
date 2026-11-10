"""Flat-print, rigid PCB capture. Two M3x12 bolts/nuts secure four prints.

Existing source documents are read-only. Camera optical pose is the original
chosen pose; board roll preserves the nearest possible present USB direction.
Dimensions mm. Run inside the existing Fusion RPC add-in.
"""
import adsk.core
import adsk.fusion
import itertools
import json
import math
from pathlib import Path

ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
helper=(ROOT/'scripts/build_camera_addon_v1.py').read_text().split("progress('building_temporary_geometry')",1)[0]
exec(compile(helper,'mm_brep_helpers','exec'),globals())
OUT=ROOT/'output/camera_mount_v6'; OUT.mkdir(parents=True,exist_ok=True)
source_doc=next(d for d in app.documents if d.name=='so101_A1mini_PLA_造形用_V5')
source_design=adsk.fusion.Design.cast(source_doc.products.itemByProductType('DesignProductType'))
source_ref=source_design.rootComponent.occurrences.itemByName('REFERENCE_SO101_unchanged:1')
source_camera=source_design.rootComponent.occurrences.itemByName('REFERENCE_XIAO_Sense_1pc:1')
assert source_ref.bRepBodies.count==26 and source_camera.bRepBodies.count==103
a_face=list(next(s for s in source_design.selectionSets if s.name=='選択セットA').entities)[0]
def fingerprint():
    return {'modified':source_doc.isModified,'timeline':[source_design.timeline.markerPosition,source_design.timeline.count],
        'occurrences':[{'name':o.name,'transform':list(o.transform2.asArray()),'visible':o.isVisible,
            'bodies':[(b.name,b.volume*1000) for b in o.bRepBodies]} for o in source_design.rootComponent.occurrences],
        'sets':[(s.name,[e.entityToken for e in s.entities]) for s in source_design.selectionSets]}
before=fingerprint()
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def norm(a):return math.sqrt(dot(a,a))
def unit(a):return scale(a,1/norm(a))
def clip(body,on_plane,outward):
    n=unit(outward); seed=EX if abs(n[0])<.8 else EY
    u=unit(cross(seed,n)); v=cross(n,u)
    return subtract(body,[obox(plus(on_plane,scale(n,100)),(u,v),(300,300,200))])
def hull(points):
    planes={}
    for p,q,r in itertools.combinations(points,3):
        n=cross(plus(q,scale(p,-1)),plus(r,scale(p,-1))); length=norm(n)
        if length<1e-7:continue
        n=scale(n,1/length); d=dot(n,p); distances=[dot(n,v)-d for v in points]
        if max(distances)<=1e-6:pass
        elif min(distances)>=-1e-6:n=scale(n,-1); d=-d
        else:continue
        planes[tuple(round(x,6) for x in (*n,d))]=(p,n)
    lo=[min(p[i] for p in points)-.01 for i in range(3)]
    hi=[max(p[i] for p in points)+.01 for i in range(3)]
    b=box(lo[0],hi[0],lo[1],hi[1],lo[2],hi[2])
    for p,n in planes.values():clip(b,p,n)
    assert b.isSolid and b.volume>1e-8
    return b
def vertices(b):return [tuple(q*10 for q in v.geometry.asArray()) for v in b.vertices]
def translated(b,delta):
    q=T.copy(b); m=adsk.core.Matrix3D.create(); m.translation=vec(scale(delta,.1)); T.transform(q,m); return q

prior=json.loads((ROOT/'output/print_camera_hx711_v5/checks/design_check.json').read_text())
oldA=tuple(prior['camera_basis']['A']); oldB=tuple(prior['camera_basis']['B']); CN=tuple(prior['camera_basis']['N'])
oldCO=tuple(prior['parameters']['camera_pcb_origin_mm'])
inspection=json.loads((OUT/'current_camera_inspection.json').read_text())
rotation=next(d for d in inspection['documents'] if 'V4' in d['document'])['transform']
def rvector(p):return tuple(sum(rotation[i*4+j]*p[j] for j in range(3)) for i in range(3))
currentA=rvector(oldA); currentN=rvector(CN); currentB=rvector(oldB)
currentCO=plus(rvector(oldCO),tuple(rotation[i*4+3]*10 for i in range(3)))
# Keep the original lens position AND axis, rotating only about its optical axis.
CA=unit(plus(currentA,scale(CN,-dot(currentA,CN)))); CB=cross(CA,CN)
lens_local=(6.9458413144,-.6386000446,13.9599999851)
eye=plus(oldCO,plus(scale(oldA,lens_local[0]),plus(scale(oldB,lens_local[1]),scale(CN,lens_local[2]))))
CO=plus(eye,scale(plus(scale(CA,lens_local[0]),plus(scale(CB,lens_local[1]),scale(CN,lens_local[2]))),-1))
mm=adsk.core.Matrix3D.create()
assert mm.setToAlignCoordinateSystems(point(currentCO),vec(currentA),vec(currentN),vec(currentB),point(CO),vec(CA),vec(CN),vec(CB))
PARAM={'printer':'Bambu Lab A1 mini','nozzle_mm':.4,'filament':'PLA','printed_piece_count':4,
    'attachment':'selection A, same slot and two axes; short outward side',
    'board_retention':'rigid sliding edge rails + screw-captured common end gate; no glue, snaps or PCB screws',
    'camera_retention':'rigid edge rails, fixed stop on socket, keyed tongue blocked by common gate',
    'screw_clearance_mm':3.4,'nut_pocket_AF_mm':5.8,'clamp_head_seat_y_mm':42.,
    'clamp_bolt_tip_y_mm':30.,'clamp_bolt_axes_xz_mm':[[22,35],[34,35]],'clamp_nut_faces_y_mm':[30.5,32.9],
    'camera_pcb_origin_mm':CO,'camera_down_angle_deg':prior['parameters']['camera_down_angle_deg'],
    'camera_inward_yaw_deg':prior['parameters']['camera_inward_yaw_deg'],
    'original_lens_position_mm':eye,'USB_direction_before':currentA,'USB_direction_after':CA,
    'USB_change_deg':math.degrees(math.acos(max(-1,min(1,dot(CA,currentA))))),
    'camera_optical_axis_preserved':True,'PCB_slot_thickness_mm':2.05,'PCB_assumed_thickness_mm':1.6,
    'PCB_rear_solder_clearance_min_mm':2.0,'physical_validation':False}
progress('building_four_flat_prints')

# Main carrier: every ordinary support grows upwards from the flat Y=35.75 face.
main_pieces=[box(8,44,35.75,38.75,20.5,78),box(-18,10,35.75,38.75,45,78)]
def edge_rails(x0,x1,z0,z1,narrow=False):
    out=[]
    for low in (True,False):
        z=z0-.25 if low else z1+.25
        za,zb=(z-1.45,z) if low else (z,z+1.45)
        out.append(box(x0-.25,x1+.25,38.75,47,za,zb))
        dz=.85 if low else -.85
        # Leading chamfer: no unsupported broad shelf above the board groove.
        lip_x=(x0+3.5,x1-3.5) if narrow else (x0-.25,x1+.25)
        out.append(hull([(x,y,zz) for x in lip_x
            for y,zz in ((45.85,z),(47,z),(47,z+dz))]))
    pads=((x0+4,x1-4),) if narrow else ((x0,x0+.8),(x1-.8,x1))
    for xa,xb in pads:
        for za,zb in ((z0,z0+.6),(z1-.6,z1)):
            out.append(box(xa,xb,38.75,43.8,za,zb))
    return out
main_pieces+=edge_rails(10,40,47,69)
main_pieces+=edge_rails(-12.7,0,47,74.94,True)
main_pieces += [box(8.25,9.75,38.75,45.6,48,68),
                box(.25,1.75,38.75,45.6,48,74)]
socket=cbox(-11,11,11,27.0,-5.8,1.6)
socket_points=vertices(socket)
sb=bbox(socket)
anchor=[(x,y,z) for x in (28,38) for y in (35.75,38.5) for z in (18.5,37.5)]
# A low solid wedge, instead of long diagonal flying ribs.
back=cbox(-11,11,11,27,-5.8,-3.7)
main_pieces += [hull(anchor+vertices(back)),socket,cbox(10.75,12.8,5.5,12.5,-1,2.8)]
main=union(main_pieces)
subtract(main,[box(13,37,35,43.79,50,66),box(-10.2,-2.5,35,43.79,50,71.9),
    cbox(-9.3,9.3,9.5,24.8,-3.7,-.55),cbox(-12.1,12.1,-20,11,-3.7,3.1)])
main=union([main,cbox(10.75,12.8,5.5,12.5,-1,2.8),cbox(8.8,10.75,7.1,8.7,1.55,2.85)])

# Common removable gate: ordinary rigid printed stops. Both existing M3 axes
# capture it. No brittle PLA latch and no extra PCB screws or heat are needed.
gate_boxes=[box(17.5,43.25,38.75,42,30,40),box(40.25,43.25,38.75,47,38,81),
    box(-15.95,-12.95,38.75,47,46,83),box(-15.95,43.25,38.75,42,78,83)]
nose=box(43,45,48,54.5,23.8,25.8)
nb=bbox(nose)
gate_anchor=[(x,y,z) for x in (33.5,43.25) for y in (38.75,42)
             for z in (18.5,38)]
gate_arm=hull(gate_anchor+vertices(nose))
gate=union(gate_boxes+[gate_arm])
# Give its arm a straight outside (+Y) assembly path through the socket.
gate_sweeps=[]
for dx,dz in ((0,0),(.2,0),(-.2,0),(0,.2),(0,-.2)):
    pts=[plus(p,(dx,0,dz)) for p in vertices(gate_arm)]
    swept=hull(pts+[plus(p,(0,35,0)) for p in pts])
    gate_sweeps.append(swept)
    subtract(main,[swept])
subtract(main,[box(17.3,43.45,38.75,90,29.8,40.2)])

tray_pieces=[cbox(-11.8,11.8,-10.3,10.3,-3.4,-1),cbox(-9,9,9.8,24.5,-3.4,-.8)]
for b0,b1 in ((-10.3,-9.15),(9.15,10.3)):
    tray_pieces.append(cbox(-11.8,10.7,b0,b1,-1,.6))
    tray_pieces.append(cbox(-11.8,-8.8,b0,b1,.6,3))
for b0,b1 in ((-9.15,-8.1),(8.1,9.15)):
    tray_pieces.append(cbox(-10.8,-8.8,b0,b1,1.55,2.85))
tray_pieces.append(cbox(-11.8,-10.75,-9.15,9.15,-1,1.4))
for a in (-8.5,8.5):
    for b in (-6.5,6.5):tray_pieces.append(cbox(a-.6,a+.6,b-.6,b+.6,-1,0))
tray=union(tray_pieces)
subtract(tray,[cbox(10.5,13,5.4,12.6,-1.1,3.1),cbox(9.3,12.1,5.4,11,-4,0)])
subtract(tray,gate_sweeps)

inner=union([box(17.5,39,25.25,27.05,22.5,45.5),box(22,34,27,34.8,30.5,39.5)]+
    [cylinder((x,27,35),(x,34.8,35),9) for x in (22,34)])
for x in (22,34):
    subtract(main,[cylinder((x,35,35),(x,44,35),3.4),cylinder((x,42,35),(x,90,35),6.2)])
    subtract(gate,[cylinder((x,38,35),(x,43,35),3.4),cylinder((x,42,35),(x,80,35),6.2)])
    subtract(inner,[cylinder((x,24.8,35),(x,35,35),3.4),hex_prism((x,28.95,35),EX,EZ,7.9,5.8)])
parts={'01_flat_carrier_socket_V6':main,'02_slot_backing_V6':inner,
       '03_common_screw_locked_gate_V6':gate,'04_slide_in_camera_tray_V6':tray}
geometry={k:{'volume_mm3':b.volume*1000,'lumps':b.lumps.count,'bbox_mm':bbox(b)} for k,b in parts.items()}
(OUT/'candidate_geometry.json').write_text(json.dumps({'parameters':PARAM,'parts':geometry},ensure_ascii=False,indent=2))
assert all(r['lumps']==1 for r in geometry.values()),geometry

fixed=[]; moving=[]
for i,b in enumerate(source_ref.bRepBodies):
    q=T.copy(b); item=(f'existing_body_{i+1}',q,bbox(q)); (fixed if i<17 else moving).append(item)
xiao=[]
for i,b in enumerate(source_camera.bRepBodies):
    q=T.copy(b); T.transform(q,mm); xiao.append((f'XIAO_reference_{i+1}',q,bbox(q)))
# Verify the real manufacturer lens cylinder follows the intended axis.
axes=[f.geometry.axis.asArray() for f in xiao[101][1].faces
      if f.geometry.surfaceType==adsk.core.SurfaceTypes.CylinderSurfaceType]
assert axes and abs(dot(axes[0],CN)-1)<1e-8,(axes,CN)
for a in (-7.62,-5.08,-2.54,0,2.54,5.08,7.62):
    for sign in (-1,1):
        q=cylinder(cp(a,sign*8.9,1.25),cp(a,sign*12.5,2.8),.8)
        xiao.append((f'GPIO_wire_keepout_{a}_{sign}',q,bbox(q)))
electronics=[('HX711_PCB',box(10,40,44,45.6,47,69)),
    ('HX711_components_keepout',box(11.5,38.5,45.6,56.6,48,68)),
    ('HX711_terminal_blocks',box(10,16.5,45.6,56.6,47.8,68.2)),
    ('HX711_wires_keepout',box(1,11,50,59,48,68)),
    ('TXS0108E_PCB',box(-12.7,0,44,45.6,47,74.94)),
    ('TXS0108E_leads_left_keepout',box(-12.2,-10.1,45.6,50.2,47.4,74.54)),
    ('TXS0108E_leads_right_keepout',box(-2.6,-.5,45.6,50.2,47.4,74.54)),
    ('TXS0108E_IC_keepout',box(-10,-2.7,45.6,47.5,52,69))]
electronics=[(k,b,bbox(b)) for k,b in electronics]
hardware=[]; seats=[]
for x in (22,34):
    head=cylinder((x,42,35),(x,45,35),5.5)
    screw=union([head,cylinder((x,30,35),(x,42,35),3)])
    hardware.append((f'M3x12_A_{x}',screw,bbox(screw))); seats.append((f'M3x12_A_{x}',head,EY))
    q=hex_prism((x,31.7,35),EX,EZ,2.4,5.5)
    subtract(q,[cylinder((x,30.2,35),(x,33.2,35),3.1)])
    hardware.append((f'M3_nut_A_{x}',q,bbox(q)))
part_items=[(k,b,geometry[k]['bbox_mm']) for k,b in parts.items()]
progress('checking_static_fit')
issues=[]
for k,b,bb in part_items:
    for q,qb,qbb in fixed+moving+xiao+electronics+hardware:
        if (v:=hit(b,qb,bb,qbb))>.01:issues.append([k,q,round(v,6)])
for i,(k,b,bb) in enumerate(part_items):
    for q,qb,qbb in part_items[i+1:]:
        if (v:=hit(b,qb,bb,qbb))>.01:issues.append([k,q,round(v,6)])
(OUT/'static_check.json').write_text(json.dumps({'issues':issues},indent=2))
diagnostic=[]
lookup={k:b for k,b,_ in part_items+fixed+moving+xiao+electronics+hardware}
for name,other,volume in issues:
    q=T.copy(lookup[name]); T.booleanOperation(q,lookup[other],I)
    diagnostic.append({'parts':[name,other],'volume_mm3':volume,'overlap_bbox_mm':bbox(q)})
(OUT/'interference_diagnostic.json').write_text(json.dumps(diagnostic,indent=2))
assert not issues,issues

progress('checking_rotation')
def transformed_box(bb,m):
    ps=[]
    for p in itertools.product(*[(bb[0][i],bb[1][i]) for i in range(3)]):
        q=point(p); q.transformBy(m); ps.append(tuple(v*10 for v in q.asArray()))
    return [[min(p[i] for p in ps) for i in range(3)],[max(p[i] for p in ps) for i in range(3)]]
rotary=[]
for angle in range(-180,181,5):
    m=adsk.core.Matrix3D.create(); m.setToRotation(math.radians(angle),vec(EY),point((-2,0,34)))
    hits=[]
    for k,b,bb in part_items+hardware+xiao+electronics:
        mbb=transformed_box(bb,m); possible=[(q,qb,qbb) for q,qb,qbb in fixed if boxes_overlap(mbb,qbb)]
        if not possible:continue
        rb=T.copy(b); T.transform(rb,m)
        for q,qb,qbb in possible:
            if (v:=hit(rb,qb))>.01:hits.append([k,q,round(v,6)])
    rotary.append({'angle_deg':angle,'hits':hits})
(OUT/'rotation_check.json').write_text(json.dumps(rotary,indent=2))
assert not any(r['hits'] for r in rotary),[r for r in rotary if r['hits']]

tip=(62,2.76294620236,-52); ray=cylinder(eye,tip,.5); raybb=bbox(ray)
ray_hits=[[k,v] for k,b,bb in moving+part_items if (v:=hit(ray,b,raybb,bb))>.01]
ray_rotary=[]
for angle in range(-180,181,5):
    m=adsk.core.Matrix3D.create(); m.setToRotation(math.radians(angle),vec(EY),point((-2,0,34)))
    q=T.copy(ray); T.transform(q,m); qb=bbox(q)
    ray_rotary.append({'angle_deg':angle,'hits':[[k,v] for k,b,bb in fixed if (v:=hit(q,b,qb,bb))>.01]})
assert not ray_hits and not any(r['hits'] for r in ray_rotary)
(OUT/'camera_sightline.json').write_text(json.dumps({'eye_mm':eye,'assumed_tip_mm':tip,'optical_axis':CN,
    'relative_hits':ray_hits,'rotation':ray_rotary,'actual_FOV_focus_not_tested':True},indent=2))
seat_report=[]
for name,head,axis in seats:
    q=translated(head,scale(axis,-.1)); overlap=sum(hit(q,b) for _,b,_ in part_items)
    seat_report.append({'name':name,'pushed_0p1mm_overlap_mm3':overlap})
assert all(r['pushed_0p1mm_overlap_mm3']>.05 for r in seat_report)
(OUT/'fastener_check.json').write_text(json.dumps({'passed':True,'head_stops':seat_report,
    'stock':{'M3x12':2,'M3_nut':2},'shaft_clearance_diameter_mm':3.4,'head_diameter_max_mm':5.5,
    'head_height_max_mm':3,'head_seat_y_mm':42,'tip_y_mm':30,'nut_faces_y_mm':[30.5,32.9],
    'nominal_nut_engagement_mm':2.4,'nominal_tip_protrusion_mm':.5},indent=2))
assert fingerprint()==before,'Existing V5 changed'
progress('creating_separate_glueless_document')
doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
design=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType')); root=design.rootComponent
def add_component(name,items):
    o=root.occurrences.addNewComponent(adsk.core.Matrix3D.create()); c=o.component; c.name=name
    base=c.features.baseFeatures.add(); base.name=name+'_editable_solid'; base.startEdit()
    for label,body in items:c.bRepBodies.add(body,base)
    base.finishEdit()
    for b,(label,_) in zip(c.bRepBodies,items):b.name=label
    return o
for k,b in parts.items():add_component(k,[(k,b)])
ref=add_component('REFERENCE_SO101_unchanged',[(k,b) for k,b,_ in fixed+moving])
camera_ref=add_component('REFERENCE_XIAO_Sense_1pc',[(k,b) for k,b,_ in xiao])
for i,b in enumerate(camera_ref.component.bRepBodies):
    if i>=103:b.isLightBulbOn=False
hx=add_component('REFERENCE_HX711_1pc',[(k,b) for k,b,_ in electronics if k.startswith('HX')])
tx=add_component('REFERENCE_TXS0108E_5V_3V3_translator_1pc',[(k,b) for k,b,_ in electronics if k.startswith('TXS')])
add_component('REFERENCE_M3_hardware_do_not_print',[(k,b) for k,b,_ in hardware])
for o in (hx,tx):
    for b in o.component.bRepBodies:
        if 'keepout' in b.name:b.isLightBulbOn=False
basebody=ref.component.bRepBodies.item(25)
faces=[f for f in basebody.faces if f.geometry.surfaceType==adsk.core.SurfaceTypes.PlaneSurfaceType
       and abs(f.geometry.origin.y*10-35.5)<1e-6 and abs(f.area-a_face.area)<.0001]
assert len(faces)==1
design.selectionSets.add([faces[0].createForAssemblyContext(ref)],'選択セットA')
archive=OUT/'SO101_Glueless_Camera_HX711_V6_assembly.f3d'
assert design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(archive)))
report={'passed':True,'parameters':PARAM,'geometry':geometry,'source_document':source_doc.name,
    'source_fingerprint_before':before,'source_fingerprint_after':fingerprint(),'source_preserved':True,
    'new_document':doc.name,'archive':str(archive),'rotation_samples':len(rotary),
    'hardware':{'M3x12':2,'M3_hex_nut':2},'camera_basis':{'A':CA,'B':CB,'N':CN},
    'current_camera_basis':{'A':currentA,'B':currentB,'N':currentN},
    'physical_print_fit_strength_and_electrical_function_not_tested':True}
(OUT/'design_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
progress('assembly_created',archive=str(archive))
print(json.dumps({'parts':geometry,'camera':PARAM,'archive':str(archive)},ensure_ascii=False,indent=2))
