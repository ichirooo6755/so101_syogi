"""Report upstream STEP geometry to guide a link extension (millimetres)."""
from pathlib import Path
import cadquery as cq

for path in sorted((Path(__file__).parent / 'upstream').glob('*.step')):
    s = cq.importers.importStep(str(path)).val().Solids()[0]
    b = s.BoundingBox()
    print(path.name, 'bounds', *(round(v, 3) for v in (b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax)),
          'volume', round(s.Volume(),3), 'valid', s.isValid(), flush=True)
    for f in s.Faces():
        if f.geomType() == 'CYLINDER':
            c = f.Center(); fb = f.BoundingBox()
            print(' cylinder center', *(round(v,2) for v in (c.x,c.y,c.z)),
                  'bounds', *(round(v,2) for v in (fb.xlen,fb.ylen,fb.zlen)), flush=True)
