"""Two printed pieces, two M3 bolts and two nuts; open glued PCB trays.

Inspired by the SO101 hex-nut wrist adapter's simple one-piece support concept,
but preserves the user's A-slot clamp and compact outward position, not its
different 32x32 camera interface. All existing documents remain read-only.
"""
import adsk.core
import adsk.fusion
import json
import math
from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
helper=(ROOT/'scripts/build_camera_addon_v1.py').read_text().split("progress('building_temporary_geometry')",1)[0]
exec(compile(helper,'mm_brep_helpers','exec'),globals())
OUT=ROOT/'output/camera_mount_v4'; OUT.mkdir(parents=True,exist_ok=True)
source_doc=next(d for d in app.documents if d.name=='so101_SelectionA_Compact_Camera_HX711_V3')
source_design=adsk.fusion.Design.cast(source_doc.products.itemByProductType('DesignProductType'))
source_ref=source_design.rootComponent.occurrences.itemByName('REFERENCE_SO101_unchanged:1')
source_camera=source_design.rootComponent.occurrences.itemByName('REFERENCE_XIAO_Sense_1pc:1')
assert source_ref.bRepBodies.count==26 and source_camera.bRepBodies.count==103
a_face=adsk.fusion.BRepFace.cast(list(next(s for s in source_design.selectionSets if s.name=='選択セットA').entities)[0])
assert abs(a_face.geometry.origin.y*10-35.5)<1e-6
assert abs(a_face.body.volume*1000-38550.50206478457)<1e-6
def fingerprint():
    return {'modified':source_doc.isModified,'timeline':[source_design.timeline.markerPosition,source_design.timeline.count],
        'occurrences':[{'name':o.name,'transform':list(o.transform2.asArray()),'visible':o.isVisible,
            'bodies':[(b.name,b.volume*1000) for b in o.bRepBodies]} for o in source_design.rootComponent.occurrences],
        'sets':[(s.name,[e.entityToken for e in s.entities]) for s in source_design.selectionSets]}
before=fingerprint()
backup=OUT/'source_V3_before_simplification.f3d'
if not backup.exists():
    assert source_design.exportManager.execute(source_design.exportManager.createFusionArchiveExportOptions(str(backup)))
prior=json.loads((ROOT/'output/print_camera_hx711_v3/checks/design_check.json').read_text())
CA=tuple(prior['camera_basis']['A']); CB=tuple(prior['camera_basis']['B']); CN=tuple(prior['camera_basis']['N'])
CO=tuple(prior['parameters']['camera_pcb_origin_mm'])
request_view=json.loads((ROOT/'output/print_camera_hx711_v3/checks/selection_A_request_view.json').read_text())
(OUT/'selection_A_request_view.json').write_text(json.dumps(request_view,indent=2))
REFERENCE_URL='https://github.com/TheRobotStudio/SO-ARM100/blob/main/Optional/SO101_Wrist_Cam_Hex-Nut_Mount_32x32_UVC_Module/README.md'
PARAM={'attachment':'選択セットAの長穴を2本のM3で挟み、選択セット2の外側方向へ短く張り出す',
    'reference_design':REFERENCE_URL,'printed_piece_count':2,
    'board_retention':'shallow locating trays and small hot-glue dots at PCB edges; no PCB screws or separate keepers',
    'screw_clearance_mm':3.4,'nut_pocket_AF_mm':5.8,'clamp_head_access_mm':6.2,
    'clamp_bolt_axes_xz_mm':[[22,35],[34,35]],'clamp_outer_head_seat_y_mm':39,
    'clamp_nut_faces_y_mm':[30.5,32.9],'plate_thickness_mm':2.,'foot_thickness_mm':3.,
    'camera_pcb_origin_mm':CO,'camera_down_angle_deg':prior['parameters']['camera_down_angle_deg'],
    'camera_inward_yaw_deg':prior['parameters']['camera_inward_yaw_deg'],
    'xiao_board_mm':[21,17.8,1.25],'hx711_board_mm':[30,22,1.6],'txs0108e_board_mm':[27.94,12.7,1.6],
    'HX711_rear_clearance_mm':2.,'TXS_rear_clearance_mm':2.,'TXS_outward_y_shift_mm':-1.2}
def ep(p):
    x,y,z=p; return (28-y,34.75+x,z)
def ebox(x0,x1,y0,y1,z0,z1):
    return obox(ep(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2)),(EY,(-1,0,0)),(x1-x0,y1-y0,z1-z0))
def txbox(*dims):
    b=ebox(*dims); m=adsk.core.Matrix3D.create(); m.translation=vec((0,-.12,0)); T.transform(b,m); return b

progress('building_two_piece_simple_bracket')
# A flat L-shaped support replaces the box beam and four screw-on retainers.
pieces=[box(17.5,39,35.75,39,22.5,45.5),box(12,44,38.5,49.75,22.5,25.5),
        box(11.5,44.5,47.75,49.75,25,61)]
# HX711 open-front shallow tray; its component side and terminals remain open.
for x0,x1 in ((11.5,12.6),(43.4,44.5)):
    pieces.append(box(x0,x1,49.75,53.35,34.6,57.4))
for z0,z1 in ((33.6,34.6),(57.4,58.4)):
    pieces.append(box(11.5,44.5,49.75,53.35,z0,z1))
for x0,x1 in ((13,14),(42,43)):
    for z0,z1 in ((35,35.8),(56.2,57)):
        pieces.append(box(x0,x1,49.75,51.65,z0,z1))
# TXS0108E open rear tray; no header sockets. Keep 2 mm solder clearance.
for y0,y1 in ((-16,-14.2),(14.2,16)):
    pieces.append(ebox(9,13.1,y0,y1,45.7,58.7))
for z0,z1 in ((44.7,45.7),(59,60)):
    pieces.append(ebox(9,13.1,-16,16,z0,z1))
for x0,x1 in ((14.03,14.83),(41.17,41.97)):
    for z0,z1 in ((46,46.4),(58.3,58.7)):
        pieces.append(box(x0,x1,45.85,47.75,z0,z1))
# Small angled camera tray: no cantilever latch, cover, screw ear or nut pocket.
pieces += [cbox(-11.8,11.8,-10.3,10.3,-3,-1.8),cbox(-10.8,4,-17,-9,-5,-2)]
for b0,b1 in ((-10.3,-9.15),(9.15,10.3)):
    pieces.append(cbox(-10.8,11.8,b0,b1,-1.8,1.4))
pieces.append(cbox(-11.8,-10.9,-9.15,9.15,-1.8,1.4))
for b0,b1 in ((-9.15,-5.8),(5.8,9.15)):
    pieces.append(cbox(10.9,11.8,b0,b1,-1.8,1.4))
for a in (-9.7,9.7):
    for b in (-7.7,7.7): pieces.append(cbox(a-.6,a+.6,b-.6,b+.6,-1.8,0))
frame=union(pieces)
cuts=[]
for x in (22,34):
    cuts += [cylinder((x,35.2,35),(x,42.5,35),3.4),cylinder((x,39.1,35),(x,56,35),6.2)]
subtract(frame,cuts)
inner=union([box(17.5,39,25.25,27.05,22.5,45.5)]+
    [cylinder((x,27,35),(x,34.8,35),9) for x in (22,34)])
for x in (22,34):
    subtract(inner,[cylinder((x,24.8,35),(x,35,35),3.4),hex_prism((x,28.95,35),EX,EZ,7.9,5.8)])
parts={'01_simple_camera_HX711_bracket_V4':frame,'02_A_slot_backing_V4':inner}
geometry={k:{'volume_mm3':b.volume*1000,'lumps':b.lumps.count,'bbox_mm':bbox(b)} for k,b in parts.items()}
(OUT/'candidate_geometry.json').write_text(json.dumps({'parameters':PARAM,'parts':geometry},ensure_ascii=False,indent=2))
assert all(row['lumps']==1 for row in geometry.values()),geometry

# Reuse the proven static, fastener, rotation and sightline checks, with only
# the two clamp bolts present. The V3 camera reference is already positioned.
tail=(ROOT/'scripts/build_selection_a_left_camera_v2.py').read_text().split('# Classifications follow',1)[1]
tail='# Classifications follow'+tail
start=tail.index('oldA=(0,-1,0)'); end=tail.index('xiao=[]',start)
tail=tail[:start]+tail[end:]
tail=tail.replace('q=T.copy(b); T.transform(q,mm); xiao.append','q=T.copy(b); xiao.append')
tail=tail.replace("('TXS0108E_PCB',ebox(","('TXS0108E_PCB',txbox(")
tail=tail.replace("('TXS0108E_leads_keepout',ebox(","('TXS0108E_leads_keepout',txbox(")
start=tail.index('for y in (-19.2,19.2):\n    bolt('); end=tail.index("progress('static_checks')",start)
tail=tail[:start]+tail[end:]
tail=tail.replace("'stock':{'M3x8':3,'M3x10':3,'M3_nut':6}","'stock':{'M3x8':0,'M3x10':2,'M3_nut':2}")
tail=tail.replace("'hardware':{'M3x8':3,'M3x10':3,'M3_hex_nut':6}","'hardware':{'M3x8':0,'M3x10':2,'M3_hex_nut':2}")
tail=tail.replace('translation (-45,22.75,0)','translation (28,34.75,0); TXS moves another -1.2 mm in Y')
tail=tail.replace('_V2','_V4').replace('SelectionA_Left','SelectionA_Simple')
exec(compile(tail,'simple_v4_verified_assembly','exec'),globals())
assert fingerprint()==before
frame_occ=root.occurrences.itemByName('01_simple_camera_HX711_bracket_V4:1')
faces=[f for f in frame_occ.component.bRepBodies.item(0).faces
    if f.geometry.surfaceType==adsk.core.SurfaceTypes.PlaneSurfaceType and abs(f.geometry.origin.y*10-49.75)<1e-6]
face=max(faces,key=lambda f:f.area)
design.selectionSets.add([face.createForAssemblyContext(frame_occ)],'選択セット2_外側方向')
assert design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(archive)))
(OUT/'simplification_check.json').write_text(json.dumps({'passed':True,'printed_parts':2,
    'bolts':{'M3x10':2},'nuts':{'M3_hex':2},'separate_PCB_keepers':0,
    'hot_glue_required_for_PCB_retention':True,'existing_assembly_preserved':True,
    'reference':REFERENCE_URL},ensure_ascii=False,indent=2))
