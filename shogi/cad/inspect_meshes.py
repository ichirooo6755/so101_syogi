import json
from pathlib import Path
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
root=Path(__file__).resolve().parents[1]; out=root/'output/camera_xiao';(out/'preview').mkdir(exist_ok=True)
checks={}
for path in sorted(out.glob('0[1-3]*.stl')):
 m=trimesh.load(path,force='mesh');checks[path.name]={'watertight':bool(m.is_watertight),'winding_consistent':bool(m.is_winding_consistent),'components':len(m.split(only_watertight=False)),'volume_mm3':round(float(m.volume),3),'size_mm':[round(float(x),2) for x in m.extents],'min_z_mm':round(float(m.bounds[0,2]),3),'triangles':len(m.faces)}
(out/'mesh_check.json').write_text(json.dumps(checks,indent=2)+'\n')
print(json.dumps(checks,indent=2))
fig=plt.figure(figsize=(12,6)); models=[]
for name,color in [('base','#81968c'),('top','#77a8bd'),('keepers','#e4ac56'),('xiao','#25582e')]:
 m=trimesh.load('/tmp/syogi_mount_preview/'+name+'.stl',force='mesh');models.append((name,color,m))
for k,ang in enumerate([(-60,25),(70,12)]):
 ax=fig.add_subplot(1,2,k+1,projection='3d')
 for name,color,m in models:
  collection=Poly3DCollection(m.triangles,facecolor=color,edgecolor='none',alpha=1)
  ax.add_collection3d(collection)
 bounds=[m.bounds for _,_,m in models]
 import numpy as np
 lo=np.min([b[0] for b in bounds],axis=0);hi=np.max([b[1] for b in bounds],axis=0)
 ax.auto_scale_xyz([lo[0],hi[0]],[lo[1],hi[1]],[lo[2],hi[2]]);ax.set_box_aspect((hi-lo).copy());ax.view_init(ang[1],ang[0]);ax.set_xlabel('X mm');ax.set_ylabel('Y mm');ax.set_zlabel('Z mm')
ax.set_title('assembled reference');fig.suptitle('SO-101 mount and XIAO 2023 reference — inspection only');fig.tight_layout();fig.savefig(out/'preview/assembly.png',dpi=140)
