"""Mesh integrity and an A1 mini flat-orientation bounding-box estimate."""
from pathlib import Path
import json
import numpy as np
import trimesh
from scipy.spatial import ConvexHull

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'output/upper_arm_extension'
reports=[]
for length in (50,58,75):
    path=out/f'Upper_arm_SO101_plus{length}.stl'
    mesh=trimesh.load_mesh(path)
    # Mounting face parallel to the build plate: project model X,Z. This is
    # only a 2-D bounding box, not a slicer, support, or printability test.
    vertices=mesh.vertices[:,[0,2]]
    hull=vertices[ConvexHull(vertices).vertices]
    best=None
    for degrees in np.linspace(0,90,901):
        angle=np.deg2rad(degrees)
        rotation=np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
        span=np.ptp(hull@rotation.T,axis=0)
        record=(float(max(span)),float(degrees),span.tolist())
        if best is None or record[0]<best[0]: best=record
    reports.append({'extension_mm':length,'watertight':bool(mesh.is_watertight),
                    'components':len(mesh.split()),'volume_mm3':round(float(mesh.volume),3),
                    'extents_mm':np.ptp(mesh.vertices,axis=0).round(3).tolist(),
                    'flat_best_rotation_deg':best[1],
                    'flat_bounding_box_mm':[round(x,2) for x in best[2]],
                    'fits_180mm_square_flat_without_margin':bool(best[0]<=180)})
(out/'mesh_check.json').write_text(json.dumps(reports,indent=2)+'\n')
print(json.dumps(reports,indent=2))
