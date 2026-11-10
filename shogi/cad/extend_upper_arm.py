"""Extend only the SO-101 upper arm using the upstream parametric STEP.

Experimental: retains both mounting ends and extrudes the x=0 cross section.
No physical strength, fit, wiring, motor load or collision guarantees.
"""
import argparse
from pathlib import Path
import json
import cadquery as cq

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--length-mm',type=int,default=58,choices=(50,58,75,100,125))
args=parser.parse_args()
LENGTH_MM=float(args.length_mm)
source=ROOT/'cad/upstream/Upper_arm_SO101.step'
output=ROOT/'output/upper_arm_extension'
output.mkdir(parents=True, exist_ok=True)
original=cq.importers.importStep(str(source)).val().Solids()[0]

# Split at x=0, in the link web, not through the motor mounting ends.
left_box=cq.Solid.makeBox(300,300,300,cq.Vector(-300,-150,-150))
right_box=cq.Solid.makeBox(300,300,300,cq.Vector(0,-150,-150))
left=original.intersect(left_box)
right=original.intersect(right_box)
section=cq.Workplane('YZ').newObject([original]).section().val()
faces=section.Faces()
if len(faces)!=1:
    raise RuntimeError(f'Unexpected section face count: {len(faces)}')
cross=faces[0]
middle=cq.Solid.extrudeLinear(cross.outerWire(),cross.innerWires(),cq.Vector(LENGTH_MM,0,0))
extended=left.fuse(middle,right.translate(cq.Vector(LENGTH_MM,0,0))).clean()
solids=extended.Solids()
if len(solids)!=1 or not extended.isValid():
    raise RuntimeError('The resulting extended arm is not a single valid solid')
cq.exporters.export(extended,str(output/f'Upper_arm_SO101_plus{args.length_mm}.step'))
cq.exporters.export(extended,str(output/f'Upper_arm_SO101_plus{args.length_mm}.stl'),tolerance=0.05,angularTolerance=0.1)
b0=original.BoundingBox(); b1=extended.BoundingBox()
report={'source':'TheRobotStudio/SO-ARM100 STEP/SO101/Upper_arm_SO101.step',
        'source_commit':'a758567c3978dfeefe282ede0500085a48fe8f78',
        'extension_mm':LENGTH_MM,'cut_x_mm':0,'section_faces':len(faces),
        'section_area_mm2':round(cross.Area(),3),'single_valid_solid':True,
        'original_bounds_mm':[b0.xmin,b0.xmax,b0.ymin,b0.ymax,b0.zmin,b0.zmax],
        'extended_bounds_mm':[b1.xmin,b1.xmax,b1.ymin,b1.ymax,b1.zmin,b1.zmax],
        'original_volume_mm3':round(original.Volume(),3),'extended_volume_mm3':round(extended.Volume(),3),
        'warning':'Concept only: no fit, physical print, torque, collision, reach or cable validation.'}
(output/f'geometry_check_{args.length_mm}.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2),flush=True)
