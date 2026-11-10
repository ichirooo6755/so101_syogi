#!/usr/bin/env python3
"""Modify the supplied STEP models in separate output files (millimetres).

XIAO model is a 2023 Seeed reference; measure the actual module before use.
This script intentionally leaves the original robot and base/top hole interfaces intact.
"""
import json, math
from pathlib import Path
import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/camera_xiao';OUT.mkdir(parents=True,exist_ok=True)
base=cq.importers.importStep(str(ROOT/'camera_mount_base.step')).val()
top=cq.importers.importStep(str(ROOT/'camera_mount_top.step')).val()
outer=next(f for f in top.Faces() if f.geomType()=='PLANE' and 550<f.Area()<552)
face_point=outer.Center();normal=outer.normalAt()
axis=next(f for f in top.Faces() if f.geomType()=='CYLINDER' and abs(BRepAdaptor_Surface(f.wrapped).Cylinder().Radius()-15)<.01)
cyl=BRepAdaptor_Surface(axis.wrapped).Cylinder(); p=cyl.Location()
line=cq.Vector(p.X(),p.Y(),p.Z())
origin=line+normal*((face_point-line).dot(normal))
plane=cq.Plane(origin=origin,xDir=(1,0,0),normal=normal)
loc=cq.Location(plane)

# Opening is 30 mm diameter; two transverse bridges anchor a central board plate
# to the original annulus without touching its 28 x 28 mm camera screw holes.
plate=cq.Workplane('XY').box(22.4,18.6,2.4,centered=(True,True,False)).translate((0,0,-.2))
for y in (-7.0,7.0):
    bridge=cq.Workplane('XY').box(32.0,3.5,2.4,centered=(True,True,False)).translate((0,y,-.2))
    plate=plate.union(bridge)
# Side lands align the board; gap accommodates a nominal 17.78-mm PCB.
for side in (-1,1):
    land=cq.Workplane('XY').box(22.6,1.5,1.4,centered=(True,True,False)).translate((0,side*10.1,2.2))
    plate=plate.union(land)
    for x in (-8,8):
        boss=cq.Workplane('XY').circle(2.55).extrude(3.8).translate((x,side*11.7,-.2))
        plate=plate.union(boss)
        # Nominal pilot for M2 heat inserts, verify insert outside diameter first.
        bore=cq.Workplane('XY').circle(1.6).extrude(3.3).translate((x,side*11.7,.35))
        plate=plate.cut(bore)
# End stop is opposite the USB connector. There is no wall at the USB end.
stop=cq.Workplane('XY').box(1.6,17.0,1.3,centered=(True,True,False)).translate((-11.9,0,2.2))
plate=plate.union(stop)
addition=plate.val().located(loc)
new_top=top.fuse(addition).clean()
# Shallow, central cable guide on the outside of the base: 3.6 wide, 0.8 deep.
groove=cq.Workplane('XY').box(3.6,1.1,15.0).translate((0,13.15,13.5)).val()
new_base=base.cut(groove).clean()
# Pair of identical removable rails. Each spans one PCB edge and is screwed down.
keeper=cq.Workplane('XY').box(24.2,5.3,1.8,centered=(True,True,False)).translate((0,11.15,0))
for x in (-8,8):
    keeper=keeper.cut(cq.Workplane('XY').circle(1.15).extrude(3).translate((x,11.7,-.2)))
keeper=keeper.val().clean()
if len(new_top.Solids())!=1 or len(new_base.Solids())!=1 or len(keeper.Solids())!=1: raise RuntimeError('part is not a single solid')
for name,shape in [('01_base_xiao',new_base),('02_top_xiao',new_top),('03_pcb_keeper',keeper)]:
    cq.exporters.export(shape,str(OUT/(name+'.step')))
    print_shape=shape.translate((0,0,-shape.BoundingBox().zmin))
    cq.exporters.export(print_shape,str(OUT/(name+'.stl')),tolerance=.03,angularTolerance=.08)
# Determine interference with the actual 103-solid Seeed STEP reference in cradle coordinates.
ref=cq.importers.importStep(str(Path.home()/'Documents/ChatGPT/so101/reference/camera_electronics/xiao_official/Seeed Studio XIAO-ESP32-S3-Sense.step'))
# The official CAD PCB spans x=-8.67..12.28, z=-15..2.78, y=-.25..1.
# Map it to local XYZ: board centered in XY, bottom on the z=2.2 support.
board=ref.translate((-1.805,2.45,6.11)).rotate((0,0,0),(1,0,0),90)
keepers=[keeper.translate((0,0,3.60)),keeper.mirror('XZ').translate((0,0,3.60))]
clamp=cq.Compound.makeCompound([k for k in keepers])
collisions=[]
for i,s in enumerate(board.solids().vals()):
    # Excludes very small shared tolerances at the bottom support face.
    v=plate.val().intersect(s).Volume();vk=clamp.intersect(s).Volume()
    vtop=new_top.intersect(s.moved(loc)).Volume()
    if v>1e-4 or vk>1e-4 or vtop>1e-4: collisions.append({'solid':i,'tray_mm3':round(v,5),'keepers_mm3':round(vk,5),'full_top_mm3':round(vtop,5)})
# Verify no material was removed in the original interface and new guide avoids holes.
base_added=base.cut(new_base).Volume(); top_removed=top.cut(new_top).Volume()
# In the original assembly, the top's lower face z=-3 meets base top z=29.
mounting_offset=cq.Location(cq.Vector(0,9.435481726767,32))
top_on_base=new_top.moved(mounting_offset)
base_top_overlap=new_base.intersect(top_on_base).Volume()
# Clearance check for an assumed straight USB-C plug shell, not a measured cable.
plug_local=cq.Workplane('XY').box(13,10,7).translate((18.6,0,6)).val()
plug_overlap=new_top.intersect(plug_local.moved(loc)).Volume()
# Assembly-position mesh is for inspection only, not a fused printable object.
assembly=[new_base,top_on_base]
assembly += [k.moved(loc).moved(mounting_offset) for k in keepers]
assembly += [x.moved(loc).moved(mounting_offset) for x in board.solids().vals()]
cq.exporters.export(cq.Compound.makeCompound(assembly),str(OUT/'00_assembly_reference.step'))
# Temporary separate meshes retain the colours used in the inspection preview.
preview=Path('/tmp/syogi_mount_preview');preview.mkdir(exist_ok=True)
for name,shapes in [('base',[assembly[0]]),('top',[assembly[1]]),('keepers',assembly[2:4]),('xiao',assembly[4:])]:
    cq.exporters.export(cq.Compound.makeCompound(shapes),str(preview/(name+'.stl')),tolerance=.08,angularTolerance=.12)
report={'plane_origin_mm':[round(v,4) for v in origin.toTuple()], 'plane_normal':[round(v,6) for v in normal.toTuple()],
        'base_removed_volume_mm3':round(base_added,4),'original_top_removed_mm3':round(top_removed,6),
        'reference_solids':len(board.solids().vals()),'reference_intersections':collisions,
        'board_seat_mm':[22.4,18.7,2.2],'keeper_clearance_bores_mm':2.3,'insert_pilot_mm':3.2,
        'base_top_intersection_mm3':round(base_top_overlap,6), 'assumed_usb_plug_intersection_mm3':round(plug_overlap,6),
        'usb_plug_envelope_mm':[13,10,7], 'usb_plug_is_assumed':True,
        'physical_module_tested':False,'servo_sweep_tested':False}
(OUT/'geometry_check.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
