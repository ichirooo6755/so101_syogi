"""Offline geometric twin of the guarded Fusion V6 builder; not a Fusion edit.

Useful while Fusion is blocked. All dimensions mm; gmsh OpenCASCADE BRep.
"""
from pathlib import Path
import json
import math
import gmsh

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/v6/offline_candidate'
OUT.mkdir(parents=True,exist_ok=True)
gmsh.initialize()
try:
    gmsh.option.setNumber('General.Terminal',0)
    gmsh.model.add('V6_short_stiff_candidate')
    occ=gmsh.model.occ
    def box(x0,x1,y0,y1,z0,z1): return (3,occ.addBox(x0,y0,z0,x1-x0,y1-y0,z1-z0))
    def cy(x,z,y0,y1,dia): return (3,occ.addCylinder(x,y0,z,0,y1-y0,0,dia/2))
    solids=[cy(-2,34,-36.5,-17.05,26),box(-2,54,-36.5,-28.5,21,47),
            box(47,54,-36.5,35.5,35.5,47),box(-2,54,27.5,35.5,21,47),
            cy(-2,34,20.2,35.5,26),box(47,69.2,27.5,35.5,21,39.5),
            box(54.8,69.2,23.46294620236,41.56294620236,29.5,39.5),
            box(54.8,57.3,23.46294620236,41.56294620236,39.5,49.5),
            box(66.7,69.2,23.46294620236,41.56294620236,39.5,49.5),
            box(54.8,69.2,27.46294620236,41.56294620236,45.9,49.5),
            box(57.3,66.7,38.86294620236,41.56294620236,39.5,45.9)]
    body,_=occ.fuse(solids[:1],solids[1:])
    assert len(body)==1,body
    cuts=[]
    for y0,y1 in ((-36.6,-28.4),(27.4,35.6)):
        cuts.extend([box(19,36,y0,y1,26,42),cy(19,34,y0,y1,16),cy(36,34,y0,y1,16)])
    cuts.append(box(49,52,-28.5,27.5,38,44.5))
    cuts.extend([cy(-2,34,-36.6,-16.95,6.5),cy(-2,34,20.1,35.6,6.5),
                 cy(-2,34,-18.9,-17,8),cy(-2,34,-18.2,-17,11),cy(-2,34,20.1,22.2,8)])
    for y0,y1,head0,head1 in ((-36.6,-16.95,-36.6,-27),(20.1,35.6,28,35.6)):
        for i in range(4):
            x=-2+7*math.cos(i*math.pi/2); z=34+7*math.sin(i*math.pi/2)
            cuts.extend([cy(x,z,y0,y1,3.2),cy(x,z,head0,head1,6.2)])
    for y in (26.96294620236,34.36294620236):
        cuts.append((3,occ.addCylinder(62,y,29.5,0,0,10,1.7)))
        cuts.append((3,occ.addCylinder(62,y,29.5,0,0,3.2,3.1)))
    body,_=occ.cut(body,cuts)
    occ.synchronize(); assert len(body)==1 and body[0][0]==3,body
    volume=occ.getMass(*body[0])
    gmsh.write(str(OUT/'base.step'))
    gmsh.clear()
    for label in ('sensor','carrier','cartridge'):
        gmsh.model.add(label)
        entities=occ.importShapes(str(ROOT/'output/v5/analysis'/f'{label}.step'),highestDimOnly=True)
        assert len(entities)==1
        occ.translate(entities,-16,0,0); occ.synchronize()
        gmsh.write(str(OUT/f'{label}.step'))
        gmsh.clear()
    audit=json.loads((ROOT/'output/v5/analysis/geometry_audit.json').read_text())
    audit.update(brush_axis_mm=[62,audit['brush_axis_mm'][1]],base_included=True,
                 source='OFFLINE candidate geometric twin; Fusion edit blocked and unverified',
                 native_Fusion_updated=False)
    audit['parts']['base']['volume_mm3']=volume
    (OUT/'geometry_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
    print(json.dumps({'base_volume_mm3':volume,'candidate_dir':str(OUT),'Fusion_updated':False}))
finally:
    gmsh.finalize()
