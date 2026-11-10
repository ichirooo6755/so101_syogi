"""Slot-sandwich mount extending screen-left from the user's selection set A.

Runs in Fusion, all dimensions mm. Copies existing geometry into a NEW document.
V1, the user selection set, original servo interfaces and print release stay intact.
"""
import adsk.core
import adsk.fusion
import json
import math
from pathlib import Path

ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
# Reuse the tested mm temporary-BRep helpers only, not V1's build operations.
helpers=(ROOT/'scripts/build_camera_addon_v1.py').read_text().split("progress('building_temporary_geometry')",1)[0]
exec(compile(helpers,'camera_v1_geometry_helpers','exec'),globals())
OUT=ROOT/'output/camera_mount_v2'; OUT.mkdir(parents=True,exist_ok=True)
source_doc=next(doc for doc in app.documents if doc.name=='so101_Camera_HX711_V1_追加台座')
source_design=adsk.fusion.Design.cast(source_doc.products.itemByProductType('DesignProductType'))
assert source_design
ss=next(s for s in source_design.selectionSets if s.name=='選択セットA')
selected=list(ss.entities)
assert len(selected)==1
a_face=adsk.fusion.BRepFace.cast(selected[0]); assert a_face
assert abs(a_face.geometry.origin.y*10-35.5)<1e-6
assert abs(a_face.body.volume*1000-38550.50206478457)<.001
source_ref=source_design.rootComponent.occurrences.itemByName('REFERENCE_existing_SO101_do_not_print:1')
assert source_ref and source_ref.bRepBodies.count==26
source_camera=source_design.rootComponent.occurrences.itemByName('REFERENCE_XIAO_2023_do_not_print:1')
assert source_camera
request_view={'eye_mm':[184.7380823741102,-2055.266029121457,397.5406763597805],
    'target_mm':[-6.001298239992872,51.87909118031407,20.11085856011026],
    'up':[-.015832191361876725,.1749021343387739,.9844585238192732],
    'left_unit':[-.9959280457790872,-.09015169233380188,0.]}
(OUT/'selection_A_request_view.json').write_text(json.dumps(request_view,indent=2))
def fingerprint():
    return {'modified':source_doc.isModified,'timeline':[source_design.timeline.markerPosition,source_design.timeline.count],
        'occurrences':[{'name':o.name,'transform':list(o.transform2.asArray()),'visible':o.isVisible,
            'bodies':[(b.name,b.volume*1000) for b in o.bRepBodies]} for o in source_design.rootComponent.occurrences],
        'sets':[(s.name,[e.entityToken for e in s.entities]) for s in source_design.selectionSets]}
before=fingerprint()
backup=OUT/'source_V1_with_selection_A_before_revision.f3d'
if not backup.exists():
    assert source_design.exportManager.execute(source_design.exportManager.createFusionArchiveExportOptions(str(backup)))

# Current screen left is almost exactly -X. The arm is kept parallel to -X.
PARAM={'attachment':'選択セットA / 部品１側面の既存長穴を内外2部品で挟む',
    'extension_direction_world':[-1,0,0],'selected_plane_y_mm':35.5,
    'arm_bounds_mm':[[-64,35.75,21.5],[23,42.75,31.5]],
    'box_beam_wall_mm':2.,'clamp_bolt_axes_xz_mm':[[22,35],[34,35]],
    'clamp_outer_head_seat_y_mm':39.,'clamp_inner_jaw_y_mm':[25.25,27.05],
    'clamp_nut_faces_y_mm':[30.5,32.9],'board_module_center_x_mm':-45.,
    'camera_pcb_origin_mm':[-45.,45.,10.], 'camera_down_angle_deg':30.,'camera_inward_yaw_deg':25.,
    'xiao_board_mm':[21.,17.8,1.25],'xiao_height_allowance_mm':15.,
    'hx711_board_mm':[30.,22.,1.6],'hx711_component_height_assumed_mm':11.,
    'txs0108e_board_mm':[27.94,12.7,1.6],'screw_clearance_mm':3.4,'nut_pocket_AF_mm':5.8}
CO=tuple(PARAM['camera_pcb_origin_mm'])
yaw=math.radians(25); down=math.radians(30)
CA=(math.sin(yaw),math.cos(yaw),0)
CN=(math.cos(down)*math.cos(yaw),-math.cos(down)*math.sin(yaw),-math.sin(down))
CB=tuple(vec(CA).crossProduct(vec(CN)).asArray())
KEEPER_A=-15.
def ep(p):
    x,y,z=p
    return (-45-y,22.75+x,z)
def ebox(x0,x1,y0,y1,z0,z1):
    return obox(ep(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2)),(EY,(-1,0,0)),(x1-x0,y1-y0,z1-z0))
def ecyl(x0,x1,y,z,d): return cylinder(ep((x0,y,z)),ep((x1,y,z)),d)

progress('building_selected_slot_clamp')
frame=[box(17.5,39,35.75,39,22.5,45.5),box(-64,23,35.75,42.75,21.5,31.5)]
# Reusable board cassette, rotated so the PCB length is horizontal on the left.
frame += [ebox(13,15,-17.5,17.5,32.5,67.5),
          ebox(15,17,-15.4,-14.2,34.6,57.4),ebox(15,17,14.2,15.4,34.6,57.4),
          ebox(15,18.7,-15.4,15.4,33.6,34.6),ebox(15,18.7,-15.4,15.4,57.4,58.4)]
for y in (-19.2,19.2): frame.append(ebox(13,19,y-4,y+4,41.8,50.2))
for y0,y1 in ((-14,-10),(10,14)): frame.append(ebox(13,15,y0,y1,30,35))
for y0,y1 in ((-16,-14.2),(14.2,16)):
    frame.append(ebox(10.2,13.1,y0,y1,45.7,58.7))
for y0,y1 in ((-14.2,-13.7),(13.7,14.2)):
    frame.append(ebox(10.,10.4,y0,y1,45.7,58.7))
frame += [ebox(10.,13.1,-16,16,44.7,45.7),ebox(13,16.8,-4,4,59,67.5)]

# Open-lens XIAO cradle. Its upper rear edge joins the box beam below the HX711.
frame.append(cbox(-18.8,11.8,-10.3,10.3,-3,-1.8))
frame.append(cbox(-10.8,4,-13.5,-9,-4,-2))
for b0,b1 in ((-10.3,-9.15),(9.15,10.3)):
    frame.append(cbox(-10.8,11.8,b0,b1,-1.8,1.65))
for a in (-9.7,9.7):
    for b in (-7.7,7.7): frame.append(cbox(a-.6,a+.6,b-.6,b+.6,-1.8,0))
for b0,b1 in ((-9.55,-7.8),(7.8,9.55)):
    frame += [cbox(7,10.3,b0,b1,1.65,2.85),cbox(-11.2,-10.75,b0,b1,-1.8,1.2)]
frame += [cbox(10.7,11.8,-9.15,-5.8,-1.8,1.65),cbox(10.7,11.8,5.8,9.15,-1.8,1.65),
          cbox(-18.8,-11.2,-4.2,4.2,-6,-1.8),ccyl(KEEPER_A,0,-1.8,1.65,7.2)]
for b in (-7.5,7.5): frame.append(ccyl(KEEPER_A,b,-3,1.65,4))
frame=union(frame)
cuts=[box(-64.1,17.5,37.75,40.75,23.5,29.5)] # open-ended hollow beam; no sealed support cavity
for x in (22,34): cuts.append(cylinder((x,35.2,35),(x,42.5,35),3.4))
for y in (-19.2,19.2):
    cuts += [ecyl(12.5,21.5,y,46,3.4),hex_prism(ep((14.1,y,46)),(-1,0,0),EZ,2.8,5.8)]
cuts += [ccyl(KEEPER_A,0,-6.5,2,3.4),hex_prism(cp(KEEPER_A,0,-4.65),CA,CB,2.7,5.8),
         ecyl(12.6,17.5,0,63.3,3.4)]
for b in (-7.5,7.5): cuts.append(ccyl(KEEPER_A,b,.45,1.8,2.4))
for y in (-10,10): cuts.append(ecyl(12.5,14.6,y,63.3,2.4))
subtract(frame,cuts)

inner=[box(17.5,39,25.25,27.05,22.5,45.5)]
for x in (22,34): inner.append(cylinder((x,27.0,35),(x,34.8,35),9))
inner=union(inner)
for x in (22,34):
    subtract(inner,[cylinder((x,24.8,35),(x,35,35),3.4),hex_prism((x,28.95,35),EX,EZ,7.9,5.8)])

camera_cap=[cbox(-18.8,-11.2,-10.3,10.3,1.65,3.65)]
for b0,b1 in ((-9.6,-7.8),(7.8,9.6)): camera_cap.append(cbox(-11.4,-9.4,b0,b1,1.65,2.85))
for b in (-7.5,7.5): camera_cap.append(ccyl(KEEPER_A,b,.65,1.75,2))
camera_cap=union(camera_cap); subtract(camera_cap,[ccyl(KEEPER_A,0,.5,4,3.4)])
hx_clips=[]
for sign in (-1,1):
    q=(ebox(19,20.6,-23.2,-14.3,35,57) if sign<0 else union([
        ebox(19,20.6,15.4,23.2,35,57),ebox(19,20.6,14.3,15.4,35,35.4),ebox(19,20.6,14.3,15.4,56.6,57)]))
    subtract(q,[ecyl(18.5,21,sign*19.2,46,3.4)]); hx_clips.append(q)
tx_cap=union([ebox(9.4,12.7,-16,16,59,67.5),ebox(10.,13.,-16,-13.4,58.95,60.2),
    ebox(10.,13.,13.4,16,58.95,60.2)]+[ecyl(12.7,14.2,y,63.3,2) for y in (-10,10)])
subtract(tx_cap,[ecyl(9,13,0,63.3,3.4),hex_prism(ep((10.65,0,63.3)),(-1,0,0),EZ,2.7,5.8)])
parts={'01_A_left_arm_frame_V2':frame,'02_A_slot_inner_jaw_V2':inner,'03_camera_end_keeper_V2':camera_cap,
       '04_HX711_header_keeper_V2':hx_clips[0],'05_HX711_terminal_keeper_V2':hx_clips[1],
       '06_TXS0108E_top_keeper_V2':tx_cap}
geometry={k:{'volume_mm3':b.volume*1000,'lumps':b.lumps.count,'bbox_mm':bbox(b)} for k,b in parts.items()}
(OUT/'candidate_geometry.json').write_text(json.dumps({'parameters':PARAM,'parts':geometry},ensure_ascii=False,indent=2))
assert all(p['lumps']==1 for p in geometry.values()),geometry

# Classifications follow the V1 reference copy: first 17 fixed, remaining 9 rotor-side.
fixed=[]; moving=[]
for i,b in enumerate(source_ref.bRepBodies):
    q=T.copy(b); item=(f'existing_body_{i+1}',q,bbox(q))
    (fixed if i<17 else moving).append(item)
assert abs(moving[-1][1].volume*1000-a_face.body.volume*1000)<1e-6
oldA=(0,-1,0); oldN=(math.sin(math.radians(25)),0,-math.cos(math.radians(25))); oldB=(math.cos(math.radians(25)),0,math.sin(math.radians(25)))
mm=adsk.core.Matrix3D.create()
assert mm.setToAlignCoordinateSystems(point((23,0,26)),vec(oldA),vec(oldN),vec(oldB),point(CO),vec(CA),vec(CN),vec(CB))
xiao=[]
for i,b in enumerate(source_camera.bRepBodies):
    q=T.copy(b); T.transform(q,mm); xiao.append((f'XIAO_reference_{i+1}',q,bbox(q)))
electronics=[('HX711_PCB',ebox(17,18.6,-15,15,35,57)),
    ('HX711_components_keepout',ebox(18.6,29.6,-13.5,13.5,36,56)),
    ('HX711_terminal_blocks',ebox(18.6,29.6,8.5,15,35.8,56.2)),
    ('HX711_wires_keepout',ebox(23,32,14,24,36,56)),
    ('TXS0108E_PCB',ebox(10.6,12.2,-13.97,13.97,46,58.7)),
    ('TXS0108E_leads_keepout',ebox(6,10.6,-13.6,13.6,46.5,58.2))]
electronics=[(k,b,bbox(b)) for k,b in electronics]
hardware=[]; seats=[]
def bolt(name,p,axis,length):
    head=cylinder(p,plus(p,scale(axis,3)),5.5)
    q=union([head,cylinder(plus(p,scale(axis,-length)),p,3)])
    hardware.append((name,q,bbox(q))); seats.append((name,head,axis))
def nut(name,p,ax1,ax2,axis):
    q=hex_prism(p,ax1,ax2,2.4,5.5)
    subtract(q,[cylinder(plus(p,scale(axis,-1.5)),plus(p,scale(axis,1.5)),3.1)])
    hardware.append((name,q,bbox(q)))
for x in (22,34):
    bolt(f'M3x10_A_{x}',(x,39,35),EY,10); nut(f'M3_nut_A_{x}',(x,31.7,35),EX,EZ,EY)
for y in (-19.2,19.2):
    bolt(f'M3x8_HX_{y}',ep((20.6,y,46)),EY,8); nut(f'M3_nut_HX_{y}',ep((14.3,y,46)),(-1,0,0),EZ,EY)
bolt('M3x8_TXS',ep((16.8,0,63.3)),EY,8); nut('M3_nut_TXS',ep((10.8,0,63.3)),(-1,0,0),EZ,EY)
bolt('M3x10_camera',cp(KEEPER_A,0,3.65),CN,10); nut('M3_nut_camera',cp(KEEPER_A,0,-4.5),CA,CB,CN)

progress('static_checks')
part_items=[(k,b,geometry[k]['bbox_mm']) for k,b in parts.items()]
issues=[]
for k,b,bb in part_items:
    for q,qb,qbb in fixed+moving+xiao+electronics+hardware:
        v=hit(b,qb,bb,qbb)
        if v>.01: issues.append([k,q,round(v,6)])
for i,(k,b,bb) in enumerate(part_items):
    for q,qb,qbb in part_items[i+1:]:
        v=hit(b,qb,bb,qbb)
        if v>.01: issues.append([k,q,round(v,6)])
(OUT/'static_check.json').write_text(json.dumps({'issues':issues},ensure_ascii=False,indent=2))
assert not issues,issues
seat_report=[]
for name,head,axis in seats:
    q=T.copy(head); m=adsk.core.Matrix3D.create(); m.translation=vec(scale(axis,-.01)); T.transform(q,m)
    overlap=sum(hit(q,b) for _,b,_ in part_items)
    seat_report.append({'name':name,'head_pushed_0p1mm_overlap_mm3':overlap})
assert all(r['head_pushed_0p1mm_overlap_mm3']>.05 for r in seat_report),seat_report
(OUT/'fastener_check.json').write_text(json.dumps({'passed':True,'head_stops':seat_report,
    'stock':{'M3x8':3,'M3x10':3,'M3_nut':6},'nut_engagement_mm':2.4,'clamp_bolt_tip_y_mm':29.,
    'nut_inner_outer_y_mm':[30.5,32.9]},indent=2))

# New hardware travels WITH part 1. Its relative fit to the load-cell group is static.
progress('rotating_with_part_1')
def transformed_box(bb,m):
    pts=[]
    for x in (bb[0][0],bb[1][0]):
        for y in (bb[0][1],bb[1][1]):
            for z in (bb[0][2],bb[1][2]):
                p=point((x,y,z)); p.transformBy(m); pts.append(tuple(v*10 for v in p.asArray()))
    return [[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]
rotary=[]
for angle in range(-180,181,5):
    m=adsk.core.Matrix3D.create(); m.setToRotation(math.radians(angle),vec(EY),point((-2,0,34)))
    hits=[]
    for k,b,bb in part_items+hardware+xiao+electronics:
        mbb=transformed_box(bb,m)
        possible=[(q,qb,qbb) for q,qb,qbb in fixed if boxes_overlap(mbb,qbb)]
        if not possible: continue
        mb=T.copy(b); T.transform(mb,m)
        for q,qb,qbb in possible:
            v=hit(mb,qb)
            if v>.01: hits.append([k,q,round(v,5)])
    rotary.append({'angle_deg':angle,'hits':hits})
(OUT/'rotation_check.json').write_text(json.dumps(rotary,indent=2))
assert not any(r['hits'] for r in rotary),[r for r in rotary if r['hits']]

# Camera line of sight to an assumed brush tip; no claim about optical focus/FOV.
eye=cp(6.9458413144,-.6386000446,13.9599999851)
tip=(62,2.76294620236,-52)
ray=cylinder(eye,tip,.5); ray_hits=[]
for k,b,bb in moving:
    v=hit(ray,b,bbox(ray),bb)
    if v>.01: ray_hits.append([k,v])
ray_rotary=[]
raybb=bbox(ray)
for angle in range(-180,181,5):
    m=adsk.core.Matrix3D.create(); m.setToRotation(math.radians(angle),vec(EY),point((-2,0,34)))
    rb=transformed_box(raybb,m); hits=[]
    possible=[(k,b,bb) for k,b,bb in fixed if boxes_overlap(rb,bb)]
    if possible:
        q=T.copy(ray); T.transform(q,m)
        hits=[[k,v] for k,b,bb in possible if (v:=hit(q,b))>.01]
    ray_rotary.append({'angle_deg':angle,'hits':hits})
(OUT/'camera_sightline.json').write_text(json.dumps({'eye_mm':eye,'assumed_tip_mm':tip,
    'relative_tool_hits':ray_hits,'fixed_body_poses':ray_rotary,
    'optical_focus_and_actual_FOV_not_tested':True},indent=2))
assert not ray_hits and not any(r['hits'] for r in ray_rotary),'Sightline obstructed'
assert fingerprint()==before,'User source changed during checks'

progress('creating_separate_V2_document')
doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
design=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType')); root=design.rootComponent
def add_component(name,items):
    o=root.occurrences.addNewComponent(adsk.core.Matrix3D.create()); c=o.component; c.name=name
    base=c.features.baseFeatures.add(); base.name=name+'_editable_solid'; base.startEdit()
    for i,(label,body) in enumerate(items):
        new=c.bRepBodies.add(body,base); new.name=label
    base.finishEdit(); return o
for k,b in parts.items(): add_component(k,[(k,b)])
ref=add_component('REFERENCE_SO101_unchanged',[(k,b) for k,b,_ in fixed+moving])
add_component('REFERENCE_XIAO_Sense_1pc',[(k,b) for k,b,_ in xiao])
hx=add_component('REFERENCE_HX711_1pc',[(k,b) for k,b,_ in electronics if k.startswith('HX')])
tx=add_component('REFERENCE_TXS0108E_level_shifter_1pc',[(k,b) for k,b,_ in electronics if k.startswith('TXS')])
add_component('REFERENCE_M3_hardware_do_not_print',[(k,b) for k,b,_ in hardware])
for comp in (hx,tx):
    for b in comp.component.bRepBodies:
        if 'keepout' in b.name: b.isLightBulbOn=False
# Retain the same named selection in the V2 document on the copied part-1 face.
basebody=ref.component.bRepBodies.item(25)
faces=[f for f in basebody.faces if f.geometry.surfaceType==adsk.core.SurfaceTypes.PlaneSurfaceType
       and abs(f.geometry.origin.y*10-35.5)<1e-6 and abs(f.area*100-a_face.area*100)<.01]
if len(faces)==1:
    newset=design.selectionSets.add([faces[0].createForAssemblyContext(ref)],'選択セットA')
archive=OUT/'SO101_SelectionA_Left_Camera_HX711_V2_assembly.f3d'
assert design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(archive)))
cam=app.activeViewport.camera
cam.eye=point(request_view['eye_mm']); cam.target=point((-5,15,28)); cam.upVector=vec(request_view['up']); cam.isFitView=True
app.activeViewport.camera=cam; app.activeViewport.refresh()
app.activeViewport.saveAsImageFile(str(OUT/'selection_A_left_assembly.png'),1600,1200)
report={'passed':True,'parameters':PARAM,'geometry':geometry,'source_document':source_doc.name,
    'source_fingerprint_before':before,'source_fingerprint_after':fingerprint(),
    'source_preserved':True,'new_document':doc.name,'archive':str(archive),
    'attachment_moves_with_part_1':True,'rotation_samples':len(rotary),
    'hardware':{'M3x8':3,'M3x10':3,'M3_hex_nut':6},'camera_basis':{'A':CA,'B':CB,'N':CN},
    'electronics_transform':'old X->world +Y, old Y->world -X, old Z->world +Z; translation (-45,22.75,0)',
    'limits':['physical printing, clamp stiffness/friction and electrical function not tested',
              '5 degree sampled gripper sweep, upstream robot and cables not included',
              'camera 2023 CAD and assumed tip, actual optics/brush length not verified']}
(OUT/'design_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
progress('assembly_created',archive=str(archive))
print(json.dumps({k:v for k,v in report.items() if not k.startswith('source_fingerprint')},ensure_ascii=False,indent=2))
