"""Additive SO101 electronics saddle, using only the user's spare M3 hardware.

Runs inside Fusion. Dimensions are mm. Existing document geometry is read-only.
No expensive BRep bounding boxes in point loops: cache boxes once.
"""
import adsk.core
import adsk.fusion
import json
import math
from pathlib import Path

ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
OUT=ROOT/'output/camera_mount_v1'
OUT.mkdir(parents=True,exist_ok=True)
T=adsk.fusion.TemporaryBRepManager.get()
U=adsk.fusion.BooleanTypes.UnionBooleanType
C=adsk.fusion.BooleanTypes.DifferenceBooleanType
I=adsk.fusion.BooleanTypes.IntersectionBooleanType
EX=(1,0,0); EY=(0,1,0); EZ=(0,0,1)
PARAM={
    'camera_angle_deg':25., 'camera_pcb_origin_mm':[23.,0.,26.],
    'xiao_board_mm':[21.,17.8,1.25], 'xiao_height_allowance_mm':15.,
    'hx711_board_mm':[30.,22.,1.6], 'hx711_terminal_height_assumed_mm':11.,
    'txs0108e_board_mm':[27.94,12.7,1.6],
    'screw_shaft_clearance_mm':3.4,'nut_AF_clearance_mm':5.8,
    'saddle_floor_gap_mm':0.2522949432,
    'saddle_front_gap_mm':0.2372512121,
    'saddle_rear_gap_mm':0.25,
}
def progress(phase,**extra):
    (OUT/'build_progress.json').write_text(json.dumps({'phase':phase,**extra},ensure_ascii=False,indent=2))
def point(v): return adsk.core.Point3D.create(*(q/10 for q in v))
def vec(v): return adsk.core.Vector3D.create(*v)
def plus(a,b): return tuple(x+y for x,y in zip(a,b))
def scale(a,s): return tuple(x*s for x in a)
def obox(center,axes,dims):
    return T.createBox(adsk.core.OrientedBoundingBox3D.create(point(center),vec(axes[0]),vec(axes[1]),*(x/10 for x in dims)))
def box(x0,x1,y0,y1,z0,z1):
    return obox(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(EX,EY,EZ),(x1-x0,y1-y0,z1-z0))
def cylinder(a,b,d): return T.createCylinderOrCone(point(a),d/20,point(b),d/20)
def union(items):
    b=T.copy(items[0])
    for q in items[1:]: assert T.booleanOperation(b,q,U),'Union failed'
    return b
def subtract(body,tools):
    for tool in tools: assert T.booleanOperation(body,tool,C),'Cut failed'
    return body
def hex_prism(center,ax1,ax2,length,af):
    pieces=[]
    for angle in (0,60,120):
        a=math.radians(angle)
        u=plus(scale(ax1,math.cos(a)),scale(ax2,math.sin(a)))
        v=plus(scale(ax1,-math.sin(a)),scale(ax2,math.cos(a)))
        pieces.append(obox(center,(u,v),(af,af*3,length)))
    h=pieces[0]
    for q in pieces[1:]: assert T.booleanOperation(h,q,I)
    return h
def bbox(body):
    b=body.boundingBox
    return [[getattr(p,c)*10 for c in ('x','y','z')] for p in (b.minPoint,b.maxPoint)]
def boxes_overlap(a,b): return all(a[0][i]<b[1][i]+1e-7 and b[0][i]<a[1][i]+1e-7 for i in range(3))
def hit(a,b,ab=None,bb=None):
    if ab is not None and bb is not None and not boxes_overlap(ab,bb): return 0.
    q=T.copy(a); assert T.booleanOperation(q,b,I),'Intersection failed'
    return q.volume*1000
an=math.radians(PARAM['camera_angle_deg'])
CA=(0,-1,0); CB=(math.cos(an),0,math.sin(an)); CN=(math.sin(an),0,-math.cos(an))
CO=tuple(PARAM['camera_pcb_origin_mm'])
KEEPER_A=-15.0
def cp(a,b,h): return plus(CO,plus(scale(CA,a),plus(scale(CB,b),scale(CN,h))))
def cbox(a0,a1,b0,b1,h0,h1):
    return obox(cp((a0+a1)/2,(b0+b1)/2,(h0+h1)/2),(CA,CB),(a1-a0,b1-b0,h1-h0))
def ccyl(a,b,h0,h1,dia): return cylinder(cp(a,b,h0),cp(a,b,h1),dia)

progress('building_temporary_geometry')
# Fixed-side saddle lower shoe: two rails leave the central cable passage open.
shoe=[]
for y0,y1 in ((-18,-12),(12,18)):
    shoe.extend([box(-24.5,16,y0,y1,-7.0,-4.75),
                 box(-24.5,-20.25,y0,y1,-4.75,1.3)])
for y in (-14,14): shoe.append(box(11.95,16,y-4,y+4,-4.75,4))
shoe.append(box(12,16,-18,18,-7.0,-4.75))
shoe=union(shoe)
shoe_cuts=[]
for y in (-14,14):
    shoe_cuts += [cylinder((11.5,y,0),(16.5,y,0),3.4),
                  hex_prism((13.35,y,0),EY,EZ,2.8,5.8)]
subtract(shoe,shoe_cuts)

# Fore frame: screws pull the two halves in X; small top toes stop vertical lift.
frame=[]
for y in (-14,14): frame.append(box(16.6,20.3,y-4,y+4,-4.75,12))
frame += [box(16.4,20.3,-21,21,7.95,12),
          box(11.9,20.3,-9.8,9.8,-3.7,7.96),
          box(11.1,16.5,-17.4,17.4,7.95,10)]
frame += [box(13,17,-21,-17,10,34),
          box(12.2,14.0,17,21,10,34),
          box(13.8,17,17,21,10,14)]
# HX711 back and 2 mm rear solder clearance. Dimensions from Akizuki drawing.
frame += [box(13,15,-17.5,17.5,32.5,67.5),
          box(15,17,-15.4,-14.2,34.6,57.4),
          box(15,17,14.2,15.4,34.6,57.4),
          box(15,18.7,-15.4,15.4,33.6,34.6),
          box(15,18.7,-15.4,15.4,57.4,58.4)]
for y in (-19.2,19.2): frame.append(box(13,19,y-4,y+4,41.8,50.2))
# TXS0108E rear rails: no header sockets; direct-soldered flexible leads.
for y0,y1 in ((-16,-14.2),(14.2,16)):
    frame.append(box(10.2,13.1,y0,y1,45.7,58.7))
for y0,y1 in ((-14.2,-13.4),(13.4,14.2)):
    frame.append(box(10.0,10.4,y0,y1,45.7,58.7))
frame += [box(10.0,13.1,-16,16,44.7,45.7),
          box(13,16.8,-4,4,59,67.5)]

# Camera cradle. Lips touch only the edge, not the camera/USB/expansion connector.
frame.append(cbox(-18.8,11.8,-10.3,10.3,-3,-1.8))
for b0,b1 in ((-10.3,-9.15),(9.15,10.3)):
    frame.append(cbox(-10.8,11.8,b0,b1,-1.8,1.65))
for a in (-9.7,9.7):
    for b in (-7.7,7.7): frame.append(cbox(a-.6,a+.6,b-.6,b+.6,-1.8,0))
for b0,b1 in ((-9.55,-7.8),(7.8,9.55)):
    frame += [cbox(7.0,10.3,b0,b1,1.65,2.85),
              cbox(-11.2,-10.75,b0,b1,-1.8,1.2)]
frame += [cbox(10.7,11.8,-9.15,-5.8,-1.8,1.65),
          cbox(10.7,11.8,5.8,9.15,-1.8,1.65),
          cbox(-18.5,-12.5,-10.3,-5.8,-4,-2),
          cbox(11,18.5,-10.3,-5.8,-4,-2),
          cbox(-18.8,-11.2,-4.2,4.2,-6,-1.8),
          ccyl(KEEPER_A,0,-1.8,1.65,7.2)]
for b in (-7.5,7.5): frame.append(ccyl(KEEPER_A,b,-3,1.65,4))
frame=union(frame)
frame_cuts=[]
for y in (-14,14): frame_cuts.append(cylinder((10.8,y,0),(23.5,y,0),3.4))
for y in (-19.2,19.2):
    frame_cuts += [cylinder((12.5,y,46),(21.5,y,46),3.4),
                   hex_prism((14.1,y,46),EY,EZ,2.8,5.8)]
frame_cuts += [ccyl(KEEPER_A,0,-6.5,2,3.4),
    hex_prism(cp(KEEPER_A,0,-4.65),CA,CB,2.7,5.8),
    cylinder((12.6,0,63.3),(17.5,0,63.3),3.4)]
for b in (-7.5,7.5): frame_cuts.append(ccyl(KEEPER_A,b,.45,1.8,2.4))
for y in (-10,10): frame_cuts.append(cylinder((12.5,y,63.3),(14.6,y,63.3),2.4))
subtract(frame,frame_cuts)

camera_cap=[cbox(-18.8,-11.2,-10.3,10.3,1.65,3.65)]
for b0,b1 in ((-9.6,-7.8),(7.8,9.6)):
    camera_cap.append(cbox(-11.4,-9.4,b0,b1,1.65,2.85))
for b in (-7.5,7.5): camera_cap.append(ccyl(KEEPER_A,b,.65,1.75,2))
camera_cap=union(camera_cap)
subtract(camera_cap,[ccyl(KEEPER_A,0,.5,4.0,3.4)])

hx_clips=[]
for sign in (-1,1):
    if sign<0:
        q=box(19,20.6,-23.2,-14.3,35,57)
    else:
        q=union([box(19,20.6,15.4,23.2,35,57),
                 box(19,20.6,14.3,15.4,35,35.4),
                 box(19,20.6,14.3,15.4,56.6,57)])
    subtract(q,[cylinder((18.5,sign*19.2,46),(21,sign*19.2,46),3.4)])
    hx_clips.append(q)

tx_cap=union([box(9.4,12.7,-16,16,59,67.5),
              box(10.0,13.0,-16,-13.4,58.95,60.2),
              box(10.0,13.0,13.4,16,58.95,60.2)]+[
              cylinder((12.7,y,63.3),(14.2,y,63.3),2) for y in (-10,10)])
subtract(tx_cap,[cylinder((9,0,63.3),(13,0,63.3),3.4),
                hex_prism((10.65,0,63.3),EY,EZ,2.7,5.8)])

# Conformal relief is cut only into the NEW saddle, never into the user's wrist.
# Axis-offset copies provide 0.25 mm relief on planar mating faces.
source_doc=next(x for x in app.documents if x.name.startswith('so101書道'))
source_design=adsk.fusion.Design.cast(source_doc.products.itemByProductType('DesignProductType'))
source_wrist=source_design.rootComponent.occurrences.itemByName('Wrist_Roll_Clearance_V8_元取付対応:1').bRepBodies.item(0)
for delta in ((0,0,0),(.25,0,0),(-.25,0,0),(0,.25,0),(0,-.25,0),(0,0,.25),(0,0,-.25)):
    relief=T.copy(source_wrist)
    m=adsk.core.Matrix3D.create(); m.translation=vec(tuple(x/10 for x in delta)); T.transform(relief,m)
    subtract(frame,[relief]); subtract(shoe,[relief])

parts={'01_fixed_electronics_frame':frame,'02_wrist_lower_shoe':shoe,
       '03_camera_end_keeper':camera_cap,'04_hx711_edge_keeper_L':hx_clips[0],
       '05_hx711_edge_keeper_R':hx_clips[1],'06_level_shifter_top_keeper':tx_cap}
geometry={k:{'volume_mm3':v.volume*1000,'lumps':v.lumps.count,'bbox_mm':bbox(v)} for k,v in parts.items()}
(OUT/'candidate_geometry.json').write_text(json.dumps({'parameters':PARAM,'parts':geometry},indent=2))
assert all(x['lumps']==1 for x in geometry.values()),geometry
progress('temporary_geometry_built',parts=geometry)

# Source geometry copies only. Keep its document, history, materials and poses.
main=next(x for x in app.documents if x.name.startswith('so101書道'))
sd=adsk.fusion.Design.cast(main.products.itemByProductType('DesignProductType'))
sr=sd.rootComponent
fixed=[]; moving=[]
for o in sr.allOccurrences:
    if not o.isVisible: continue
    group=None
    if o.fullPathName.startswith('STS3215_c:1+'):
        group=moving if '+Axes:' in o.fullPathName else fixed
    elif o.fullPathName=='Wrist_Roll_Clearance_V8_元取付対応:1': group=fixed
    elif o.fullPathName in ('部品１_V8_元取付形状保持:1','Brush_Load_Carrier_Compact_V5:1','Brush_Cartridge_Symmetric_15mm_V5:1') or o.fullPathName.startswith('SC616C_1kg_Fusion:1+'):
        group=moving
    if group is not None:
        for b in o.bRepBodies:
            if b.isSolid and b.volume>1e-6:
                q=T.copy(b); group.append((o.fullPathName+'/'+b.name,q,bbox(q)))

# Fasteners: stock M3x8 five screws and M3x10 one screw, six M3 nuts.
hardware=[]; fastener_seats=[]
def bolt(name,p,axis,length):
    shaft=cylinder(plus(p,scale(axis,-length)),p,3)
    head=cylinder(p,plus(p,scale(axis,3)),5.5)
    q=union([shaft,head]); hardware.append((name,q,bbox(q)))
    fastener_seats.append((name,head,p,axis))
for y in (-14,14): bolt('M3x8_saddle_'+str(y),(20.3,y,0),EX,8)
for y in (-19.2,19.2): bolt('M3x8_HX_'+str(y),(20.6,y,46),EX,8)
bolt('M3x8_level',(16.8,0,63.3),EX,8)
bolt('M3x10_camera',cp(KEEPER_A,0,3.65),CN,10)
def nut(name,center,ax1,ax2,axis):
    q=hex_prism(center,ax1,ax2,2.4,5.5)
    subtract(q,[cylinder(plus(center,scale(axis,-1.5)),plus(center,scale(axis,1.5)),3.1)])
    hardware.append((name,q,bbox(q)))
for y in (-14,14): nut('M3_nut_saddle_'+str(y),(13.55,y,0),EY,EZ,EX)
for y in (-19.2,19.2): nut('M3_nut_HX_'+str(y),(14.3,y,46),EY,EZ,EX)
nut('M3_nut_level',(10.8,0,63.3),EY,EZ,EX)
nut('M3_nut_camera',cp(KEEPER_A,0,-4.5),CA,CB,CN)

# Reference XIAO populated model. Model revision is 2023, so no close lens cover.
refdoc=next(x for x in app.documents if any(o.component.name.startswith('Seeed Studio XIAO-ESP32-S3') for o in adsk.fusion.Design.cast(x.products.itemByProductType('DesignProductType')).rootComponent.occurrences))
rd=adsk.fusion.Design.cast(refdoc.products.itemByProductType('DesignProductType'))
mm=adsk.core.Matrix3D.create()
origin=plus(CO,plus(scale(CA,-1.8041586855864145),plus(scale(CN,.249999985098839),scale(CB,6.1113999554125))))
mm.setWithCoordinateSystem(point(origin),vec(CA),vec(CN),vec(CB))
xiao=[]
for o in rd.rootComponent.allOccurrences:
    for b in o.bRepBodies:
        if b.isSolid:
            q=T.copy(b); assert T.transform(q,mm)
            xiao.append((o.fullPathName+'/'+b.name,q,bbox(q)))
# Full component/wiring volumes, deliberately larger than the PCB alone.
electronics=[('HX711_PCB',box(17,18.6,-15,15,35,57)),
             ('HX711_components_keepout',box(18.6,29.6,-13.5,13.5,36,56)),
             ('HX711_terminal_blocks_keepout',box(18.6,29.6,8.5,15,35.8,56.2)),
             ('HX711_terminals_wires_keepout',box(23,32,14,24,36,56)),
             ('TXS0108E_PCB',box(10.6,12.2,-13.97,13.97,46,58.7)),
             ('TXS_components_leads_keepout',box(6,10.6,-13.2,13.2,46.5,58.2))]
electronics=[(k,b,bbox(b)) for k,b in electronics]
part_items=[(k,b,geometry[k]['bbox_mm']) for k,b in parts.items()]

progress('static_checks')
issues=[]
for k,b,bb in part_items:
    for q,fb,fbbox in fixed+xiao+electronics:
        v=hit(b,fb,bb,fbbox)
        if v>.01: issues.append([k,q,round(v,6)])
    for q,h,hbb in hardware:
        v=hit(b,h,bb,hbb)
        if v>.01: issues.append([k,q,round(v,6)])
for i,(k,b,bb) in enumerate(part_items):
    for q,fb,fbbox in part_items[i+1:]:
        v=hit(b,fb,bb,fbbox)
        if v>.01: issues.append([k,q,round(v,6)])
(OUT/'static_check.json').write_text(json.dumps({'issues':issues,'source_modified':main.isModified},ensure_ascii=False,indent=2))
assert not issues,issues
seat_checks=[]
for name,head,p,axis in fastener_seats:
    m=adsk.core.Matrix3D.create(); m.translation=vec(scale(axis,-.01))
    q=T.copy(head); T.transform(q,m)
    penetration=sum(hit(q,b) for _,b,_ in part_items)
    seat_checks.append({'name':name,'head_pushed_0p1mm_overlap_mm3':penetration})
assert all(x['head_pushed_0p1mm_overlap_mm3']>.05 for x in seat_checks),seat_checks
(OUT/'fastener_check.json').write_text(json.dumps({'head_diameter_mm':5.5,'shaft_diameter_mm':3,
    'shaft_clearance_mm':3.4,'nut_AF_mm':5.5,'nut_pocket_AF_mm':5.8,
    'full_nominal_nut_engagement_mm':2.4,'head_stops':seat_checks},indent=2))

progress('rotation_check')
rotary=[]
targets=part_items+hardware+xiao+electronics
def transformed_box(bb,m):
    points=[]
    for x in (bb[0][0],bb[1][0]):
        for y in (bb[0][1],bb[1][1]):
            for z in (bb[0][2],bb[1][2]):
                p=point((x,y,z)); p.transformBy(m); points.append((p.x*10,p.y*10,p.z*10))
    return [[min(p[i] for p in points) for i in range(3)],
            [max(p[i] for p in points) for i in range(3)]]
for angle in range(-180,181,5):
    m=adsk.core.Matrix3D.create(); m.setToRotation(math.radians(angle),vec(EY),point((-2,0,34)))
    hits=[]
    for k,b,bb in moving:
        mbbox=transformed_box(bb,m)
        possible=[(q,fb,fbbox) for q,fb,fbbox in targets if boxes_overlap(mbbox,fbbox)]
        if not possible: continue
        mb=T.copy(b); assert T.transform(mb,m)
        for q,fb,fbbox in possible:
            v=hit(mb,fb)
            if v>.01: hits.append([k,q,round(v,5)])
    rotary.append({'angle_deg':angle,'hits':hits})
    if angle%30==0:
        progress('rotation_check',last_angle_deg=angle,hits=sum(len(a['hits']) for a in rotary))
(OUT/'rotation_check.json').write_text(json.dumps(rotary,ensure_ascii=False,indent=2))
assert not any(row['hits'] for row in rotary),[row for row in rotary if row['hits']]
progress('clearance_passed')

# Persist the new assembly in a new document, leaving the user's original untouched.
doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
design=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
root=design.rootComponent
def add_component(name,items):
    occ=root.occurrences.addNewComponent(adsk.core.Matrix3D.create()); c=occ.component; c.name=name
    base=c.features.baseFeatures.add(); base.name=name+'_editable_solid'; base.startEdit()
    for index,body in enumerate(items):
        new=c.bRepBodies.add(body,base); new.name=name+'_'+str(index+1)
    base.finishEdit()
    return occ
for name,b in parts.items(): add_component(name,[b])
add_component('REFERENCE_existing_SO101_do_not_print',[b for _,b,_ in fixed+moving])
add_component('REFERENCE_XIAO_2023_do_not_print',[b for _,b,_ in xiao])
add_component('REFERENCE_HX711_TXS_envelopes_do_not_print',[b for _,b,_ in electronics])
add_component('REFERENCE_screws_do_not_print',[b for _,b,_ in hardware])
archive=OUT/'SO101_Camera_HX711_Addon_V1_assembly.f3d'
assert design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(archive)))
cam=app.activeViewport.camera; cam.viewOrientation=adsk.core.ViewOrientations.IsoTopRightViewOrientation; cam.isFitView=True
app.activeViewport.camera=cam; app.activeViewport.refresh()
app.activeViewport.saveAsImageFile(str(OUT/'addon_assembly.png'),1600,1200)
report={'passed':True,'parameters':PARAM,'geometry':geometry,'source_document':main.name,
        'source_timeline':[sd.timeline.markerPosition,sd.timeline.count],
        'source_modified':main.isModified,'source_geometry_modified':False,
        'new_document':doc.name,'archive':str(archive),'rotation_samples':len(rotary),
        'hardware':{'M3x8':5,'M3x10':1,'M3_hex_nut':6},
        'limitations':['5 degree sampled rotation, not a continuous sweep',
            'upstream arm, cables, print tolerances, stiffness and physical retention untested',
            'XIAO camera STEP is 2023; 15 mm allowance, lens left open',
            'HX711 terminal/component heights conservatively assumed, not measured',
            'saddle is a prototype; hand tighten and confirm no slip before robot use']}
(OUT/'design_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
progress('assembly_created',archive=str(archive))
print(json.dumps(report,ensure_ascii=False,indent=2))
