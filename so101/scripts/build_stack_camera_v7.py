"""SO101: XIAO headers, SparkFun SEN-13879 and a same-size perfboard stack.

Separate Fusion document; four physical PCBs/assemblies in the clearance test:
XIAO including Sense, 2 x 7 XIAO pin headers, one HX711, one perfboard.
Units mm; experimental printed snap, not yet physically tested.
"""
import adsk.core
import adsk.fusion
import itertools
import json
import math
from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
source=(ROOT/'scripts/build_glueless_camera_v6.py').read_text()
prefix=source.split("progress('building_four_flat_prints')",1)[0]
prefix=prefix.replace("OUT=ROOT/'output/camera_mount_v6'","OUT=ROOT/'output/camera_mount_v7'")
prefix=prefix.replace("(OUT/'current_camera_inspection.json')","(ROOT/'output/camera_mount_v6/current_camera_inspection.json')")
exec(compile(prefix,'preserved_V5_camera_and_helpers','exec'),globals())
PARAM.update({'printed_piece_count':6,'PCB_stack_order':['XIAO ESP32S3 Sense','SparkFun SEN-13879 HX711','perfboard'],
    'HX711_PCB_size_mm':[30.48,22.86,1.6], 'HX711_board_face_h_mm':[-23.1,-21.5],
    'perfboard_size_mm':[30.48,22.86,1.6], 'perfboard_face_h_mm':[-31.6,-30.0],
    'header_rows':2,'header_pins_per_row':7,'header_pitch_mm':2.54,'header_body_width_mm':2.54,
    'header_depth_below_PCB_assumed_mm':15.,'header_slot_width_mm':3.15,
    'HX711_front_component_height_assumed_mm':3.,'perfboard_component_height_assumed_mm':3.,
    'board_retention':'sliding rigid rails, removable printed end cap with two deflecting PLA arms; no glue',
    'camera_retention':'rigid edge rails and removable snap-in side key',
    'power':'HX711 VCC and VDD at 3.3V, or VCC 5V and VDD 3.3V, shared GND; no TXS0108E',
    'actual_perfboard_cut_shape_pins_solder_and_snap_fit_unverified':True})
progress('building_stack')

# The only robot fasteners remain the existing two slot-sandwich M3 positions.
socket=union([cbox(-11,11,11,27,-5.8,1.6),cbox(-11,11,11,14,-6.1,-5.8),
              cbox(-11,11,14,27,-7.5,-5.8)])
anchor=[(x,y,z) for x in (28,38) for y in (35.75,38.5) for z in (18.5,37.5)]
back=cbox(-11,11,11,27,-5.8,-3.7)
main=union([box(17.5,43.5,35.75,42,20.5,45.5),
    hull(anchor+vertices(back)),socket,cbox(10.75,12.8,5.5,12.5,-1,2.8)])
subtract(main,[cbox(-9.3,9.3,9.5,24.8,-5.25,-.55),cbox(-12.1,12.1,-20,11,-5.25,3.1)])
main=union([main,cbox(10.75,12.8,5.5,12.5,-1,2.8),cbox(8.8,10.75,7.1,8.7,1.55,2.85)])
key_channel=cbox(-1,55,17.25,22.75,-4.05,-1.95)
key_release=cbox(-.7,1.2,22.45,40,-4.05,-1.95)
subtract(main,[key_channel,key_release,cbox(11,55,16.55,17.25,-4.05,-1.95),
    cbox(9.4,55,16.55,23.1,-25,-4.05)])
key=union([cbox(6,11.25,17.5,20.3,-3.8,-2.2),
    cbox(11.25,14.5,16.8,22.5,-3.8,-2.2),
    cbox(-.5,13,21.3,22.5,-3.8,-2.2),cbox(-.5,1,22.5,23,-3.8,-2.2)])

# Thin flat XIAO tray: the two large through-slots pass the pin-header housings.
tray_pieces=[cbox(-11.8,11.8,-10.3,10.3,-3.4,-1),cbox(-9,9,9.8,24.5,-3.4,-.8),
    cbox(-9,9,14,24.5,-5,-3.4),
    cbox(-11.8,10.3,-2.8,2.8,-4.3,-3.4),cbox(-11.8,10.3,-4.2,4.2,-6.1,-4.3)]
for b0,b1 in ((-10.3,-9.15),(9.15,10.3)):
    tray_pieces += [cbox(-11.8,10.7,b0,b1,-1,.6),cbox(-11.8,-8.8,b0,b1,.6,3)]
for b0,b1 in ((-9.15,-8.1),(8.1,9.15)):
    tray_pieces.append(cbox(-10.8,-8.8,b0,b1,1.55,2.85))
tray_pieces.append(cbox(-11.8,-10.75,-9.15,9.15,-1,1.4))
for a in (-8.5,8.5):
    for b in (-4.4,4.4):tray_pieces.append(cbox(a-.6,a+.6,b-.6,b+.6,-1,0))
tray=union(tray_pieces)
subtract(tray,[cbox(10.5,13,5.4,12.6,-1.1,3.1),cbox(9.3,12.1,5.4,11,-4,0),
    cbox(-9.4,12.5,6.05,9.2,-7,0.05),cbox(-9.4,12.5,-9.2,-6.05,-7,0.05),key_channel,key_release])

# Open two-board cassette; board edges slide in from +A, under the XIAO.
frame_pieces=[cbox(-16.5,15.24,-13.5,-11.68,-33.3,-6.4),
    cbox(-16.5,15.24,11.68,13.5,-33.3,-6.4),
    cbox(-16.5,-15.49,-13.5,13.5,-33.3,-6.4),
    cbox(-16.5,-12.05,-13.5,13.5,-8.8,-6.4),
    cbox(-16.5,-12.05,-4.5,4.5,-6.4,-4.05),
    cbox(-12.05,15.24,-5.8,5.8,-8.8,-6.4)]
for b0,b1 in ((-5.8,-4.45),(4.45,5.8)):
    frame_pieces.append(cbox(-12.10,15.24,b0,b1,-6.4,-3.65))
for b0,b1 in ((-4.5,-3.3),(3.3,4.5)):
    frame_pieces.append(cbox(-12.10,15.24,b0,b1,-4.10,-3.65))
for z0,z1 in ((-23.1,-21.5),(-31.6,-30.0)):
    for b0,b1 in ((-11.68,-10.8),(10.8,11.68)):
        frame_pieces += [cbox(-15.49,15.24,b0,b1,z0-1.05,z0-.25),
                         cbox(-15.49,15.24,b0,b1,z1+.25,z1+1.3)]
frame=union(frame_pieces)
# Shallow outside notches receive removable snap ends; neither PCB is notched.
subtract(frame,[cbox(2.75,5.25,12.95,13.75,-26.2,-22.3),
                cbox(2.75,5.25,-13.75,-12.95,-26.2,-22.3),
                cbox(-12,10,-13.7,-11.5,-19,-14),
                cbox(-12,10,-13.7,-11.5,-28,-24.5)])

# One removable end cap captures both PCBs and the tray's T tongue.
cap_pieces=[cbox(15.49,17.49,-13.5,13.5,-33.3,-6.4),
    cbox(10.55,17.49,-2.6,2.6,-6.1,-4.3),cbox(15.49,17.49,-2.6,2.6,-7.5,-4.3)]
for sign in (-1,1):
    b0,b1=(13.75,14.95) if sign>0 else (-14.95,-13.75)
    bridge0,bridge1=(13.5,14.95) if sign>0 else (-14.95,-13.5)
    hook0,hook1=(13.0,13.75) if sign>0 else (-13.75,-13.0)
    cap_pieces += [cbox(2.95,15.49,b0,b1,-26,-22.5),
        cbox(15.3,17.49,bridge0,bridge1,-26,-22.5),
        cbox(2.95,5.05,hook0,hook1,-26,-22.5)]
cap=union(cap_pieces)
inner=union([box(17.5,39,25.25,27.05,22.5,45.5),box(22,34,27,34.8,30.5,39.5)]+
    [cylinder((x,27,35),(x,34.8,35),9) for x in (22,34)])
for x in (22,34):
    subtract(main,[cylinder((x,35,35),(x,44,35),3.4),cylinder((x,42,35),(x,90,35),6.2)])
    subtract(inner,[cylinder((x,24.8,35),(x,35,35),3.4),hex_prism((x,28.95,35),EX,EZ,7.9,5.8)])
parts={'01_A_slot_socket_V7':main,'02_slot_backing_V7':inner,'03_removable_side_key_V7':key,
       '04_XIAO_header_tray_V7':tray,'05_HX711_perf_stack_V7':frame,'06_stack_end_cap_V7':cap}
geometry={k:{'volume_mm3':b.volume*1000,'lumps':b.lumps.count,'bbox_mm':bbox(b)} for k,b in parts.items()}
(OUT/'candidate_geometry.json').write_text(json.dumps({'parameters':PARAM,'parts':geometry},ensure_ascii=False,indent=2))
assert all(r['lumps']==1 for r in geometry.values()),geometry

fixed=[]; moving=[]
for i,b in enumerate(source_ref.bRepBodies):
    q=T.copy(b); item=(f'existing_body_{i+1}',q,bbox(q)); (fixed if i<17 else moving).append(item)
xiao=[]
for i,b in enumerate(source_camera.bRepBodies):
    q=T.copy(b); T.transform(q,mm); xiao.append((f'XIAO_reference_{i+1}',q,bbox(q)))
axes=[f.geometry.axis.asArray() for f in xiao[101][1].faces if f.geometry.surfaceType==adsk.core.SurfaceTypes.CylinderSurfaceType]
assert axes and abs(dot(axes[0],CN)-1)<1e-8
headers=[]; connectors=[]
for sign in (-1,1):
    b=sign*7.62
    q=cbox(-9.05,8.95,b-1.27,b+1.27,-2.54,0); headers.append((f'XIAO_header_housing_{sign}',q,bbox(q)))
    q=cbox(-9.05,8.95,b-1.27,b+1.27,-15,-2.54); connectors.append((f'connector_keepout_{sign}',q,bbox(q)))
    for i in range(7):
        a=-7.6835+i*2.54
        q=cbox(a-.32,a+.32,b-.32,b+.32,-15,-2.54); headers.append((f'XIAO_header_pin_{sign}_{i+1}',q,bbox(q)))
electronics=[('SEN13879_HX711_PCB',cbox(-15.24,15.24,-11.43,11.43,-23.1,-21.5)),
    ('SEN13879_components_keepout',cbox(-14.1,14.1,-10,10,-21.5,-18.5)),
    ('SEN13879_solder_keepout',cbox(-14.6,14.6,-10,10,-26.1,-23.1)),
    ('UNIVERSAL_PCB_30p48x22p86',cbox(-15.24,15.24,-11.43,11.43,-31.6,-30)),
    ('UNIVERSAL_front_components_keepout',cbox(-14.2,14.2,-10,10,-30,-27)),
    ('UNIVERSAL_rear_solder_keepout',cbox(-14.2,14.2,-10,10,-34.6,-31.6))]
electronics=[(k,b,bbox(b)) for k,b in electronics]
hardware=[]; seats=[]
for x in (22,34):
    head=cylinder((x,42,35),(x,45,35),5.5)
    screw=union([head,cylinder((x,30,35),(x,42,35),3)])
    hardware.append((f'M3x12_A_{x}',screw,bbox(screw))); seats.append((f'M3x12_A_{x}',head,EY))
    q=hex_prism((x,31.7,35),EX,EZ,2.4,5.5); subtract(q,[cylinder((x,30.2,35),(x,33.2,35),3.1)])
    hardware.append((f'M3_nut_A_{x}',q,bbox(q)))
items=[(k,b,geometry[k]['bbox_mm']) for k,b in parts.items()]
progress('checking_static_fit')
issues=[]
for k,b,bb in items:
    for q,qb,qbb in fixed+moving+xiao+headers+connectors+electronics+hardware:
        if (v:=hit(b,qb,bb,qbb))>.01:issues.append([k,q,round(v,5)])
for i,(k,b,bb) in enumerate(items):
    for q,qb,qbb in items[i+1:]:
        if (v:=hit(b,qb,bb,qbb))>.01:issues.append([k,q,round(v,5)])
diagnostic=[]; lookup={k:b for k,b,_ in items+fixed+moving+xiao+headers+connectors+electronics+hardware}
for k,q,v in issues:
    u=T.copy(lookup[k]); T.booleanOperation(u,lookup[q],I)
    ps=[tuple(w*10 for w in p.geometry.asArray()) for p in u.vertices]
    lp=[[dot(plus(p,scale(CO,-1)),axis) for axis in (CA,CB,CN)] for p in ps]
    diagnostic.append({'parts':[k,q],'volume':v,'bbox_mm':bbox(u),
        'local_bounds':[[min(p[i] for p in lp) for i in range(3)],[max(p[i] for p in lp) for i in range(3)]]})
(OUT/'static_check.json').write_text(json.dumps({'issues':issues,'diagnostic':diagnostic},indent=2))
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
    for k,b,bb in items+hardware+xiao+headers+connectors+electronics:
        mbb=transformed_box(bb,m); possible=[(q,qb,qbb) for q,qb,qbb in fixed if boxes_overlap(mbb,qbb)]
        if not possible:continue
        rb=T.copy(b); T.transform(rb,m)
        for q,qb,qbb in possible:
            if (v:=hit(rb,qb))>.01:hits.append([k,q,round(v,5)])
    rotary.append({'angle_deg':angle,'hits':hits})
(OUT/'rotation_check.json').write_text(json.dumps(rotary,indent=2))
assert not any(r['hits'] for r in rotary),[r for r in rotary if r['hits']]
tip=(62,2.76294620236,-52); ray=cylinder(eye,tip,.5); rb=bbox(ray)
rayhits=[[k,v] for k,b,bb in moving+items if (v:=hit(ray,b,rb,bb))>.01]
assert not rayhits,rayhits
seats_checked=[]
for name,head,axis in seats:
    q=translated(head,scale(axis,-.1)); overlap=sum(hit(q,b) for _,b,_ in items)
    seats_checked.append({'name':name,'pushed_0p1mm_overlap_mm3':overlap})
assert all(r['pushed_0p1mm_overlap_mm3']>.05 for r in seats_checked)
(OUT/'fastener_check.json').write_text(json.dumps({'passed':True,'head_stops':seats_checked,
    'stock':{'M3x12':2,'M3_nut':2},'shaft_clearance_diameter_mm':3.4,'head_diameter_max_mm':5.5,
    'head_height_max_mm':3,'head_seat_y_mm':42,'tip_y_mm':30,'nut_faces_y_mm':[30.5,32.9],
    'nominal_thread_engagement_mm':2.4,'tip_protrusion_mm':.5},indent=2))
(OUT/'camera_sightline.json').write_text(json.dumps({'eye_mm':eye,'assumed_tip_mm':tip,
    'relative_hits':rayhits,'actual_FOV_focus_not_tested':True},indent=2))
assert fingerprint()==before,'V5 source changed'
progress('creating_separate_stack_document')
doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
design=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType')); root=design.rootComponent
def add_component(name,items):
    o=root.occurrences.addNewComponent(adsk.core.Matrix3D.create()); c=o.component; c.name=name
    base=c.features.baseFeatures.add(); base.startEdit()
    for label,b in items:c.bRepBodies.add(b,base)
    base.finishEdit()
    for b,(label,_) in zip(c.bRepBodies,items):b.name=label
    return o
for k,b in parts.items():add_component(k,[(k,b)])
ref=add_component('REFERENCE_SO101_unchanged',[(k,b) for k,b,_ in fixed+moving])
add_component('REFERENCE_XIAO_Sense_1pc',[(k,b) for k,b,_ in xiao])
add_component('REFERENCE_XIAO_two_pin_headers',[(k,b) for k,b,_ in headers])
conn=add_component('REFERENCE_header_connector_clearance',[(k,b) for k,b,_ in connectors])
for b in conn.component.bRepBodies:b.isLightBulbOn=False
hx=add_component('REFERENCE_SparkFun_SEN13879_HX711_1pc',[(k,b) for k,b,_ in electronics if k.startswith('SEN')])
univ=add_component('REFERENCE_perfboard_same_size_1pc',[(k,b) for k,b,_ in electronics if k.startswith('UNIVERSAL')])
for o in (hx,univ):
    for b in o.component.bRepBodies:
        if 'keepout' in b.name:b.isLightBulbOn=False
add_component('REFERENCE_M3_hardware_do_not_print',[(k,b) for k,b,_ in hardware])
basebody=ref.component.bRepBodies.item(25)
faces=[f for f in basebody.faces if f.geometry.surfaceType==adsk.core.SurfaceTypes.PlaneSurfaceType
       and abs(f.geometry.origin.y*10-35.5)<1e-6 and abs(f.area-a_face.area)<.0001]
assert len(faces)==1
design.selectionSets.add([faces[0].createForAssemblyContext(ref)],'選択セットA')
archive=OUT/'SO101_XIAO_SEN13879_perfboard_V7_assembly.f3d'
assert design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(archive)))
report={'passed':True,'parameters':PARAM,'geometry':geometry,'source_document':source_doc.name,
    'source_fingerprint_before':before,'source_fingerprint_after':fingerprint(),'source_preserved':True,
    'archive':str(archive),'rotation_samples':len(rotary),'hardware':{'M3x12':2,'M3_hex_nut':2},
    'camera_basis':{'A':CA,'B':CB,'N':CN},'eye_mm':eye,'assumed_tip_mm':tip,'camera_ray_hits':rayhits,
    'head_stops':seats_checked,'physical_print_fit_snap_electronics_unverified':True}
(OUT/'design_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
progress('assembly_created',archive=str(archive))
print(json.dumps({'geometry':geometry,'parameters':PARAM,'archive':str(archive)},ensure_ascii=False,indent=2))
