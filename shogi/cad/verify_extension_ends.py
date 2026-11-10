"""Compare both mounting-end solids against the upstream CAD by volume."""
import argparse
from pathlib import Path
import json
import cadquery as cq

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'output/upper_arm_extension'
parser=argparse.ArgumentParser()
parser.add_argument('--length-mm',type=int,default=58,choices=(50,58,75,100,125))
length=parser.parse_args().length_mm
original=cq.importers.importStep(str(ROOT/'cad/upstream/Upper_arm_SO101.step')).val().Solids()[0]
extended=cq.importers.importStep(str(out/f'Upper_arm_SO101_plus{length}.step')).val().Solids()[0]
left_box=cq.Solid.makeBox(300,300,300,cq.Vector(-300,-150,-150))
right_box=cq.Solid.makeBox(300,300,300,cq.Vector(length,-150,-150))
orig_left=original.intersect(left_box)
new_left=extended.intersect(left_box)
orig_right=original.intersect(cq.Solid.makeBox(300,300,300,cq.Vector(0,-150,-150)))
new_right=extended.intersect(right_box).translate(cq.Vector(-length,0,0))

def volume(shape): return sum(x.Volume() for x in shape.Solids())

result={}
for name, a, b in [('fixed_end',orig_left,new_left),('translated_end',orig_right,new_right)]:
    missing=volume(a.cut(b)); added=volume(b.cut(a))
    result[name]={'missing_mm3':round(missing,6),'added_mm3':round(added,6)}
    print(name,result[name],flush=True)
result['scope']='Boolean volume comparison only; real fit and clearances not tested.'
(out/f'end_geometry_check_{length}.json').write_text(json.dumps(result,indent=2)+'\n')
