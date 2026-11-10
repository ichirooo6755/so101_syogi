"""Independent binary-STL manifold, dimensions, and volume checks (stdlib)."""
from pathlib import Path
from collections import Counter, defaultdict
import struct
import json
import sys
base=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]/'output'/'v2'
exports=json.loads((base/'export_report.json').read_text())
reports=[]
for part in exports.get('parts',exports.get('exports',[])):
    path=base/(part.get('stem',part['part'])+'.stl')
    data=path.read_bytes()
    count=struct.unpack_from('<I',data,80)[0]
    assert len(data)==84+50*count,(path,len(data),count)
    edges=Counter(); oriented=defaultdict(int); verts=set(); volume=0
    xyz=[[],[],[]]
    for i in range(count):
        row=struct.unpack_from('<12fH',data,84+i*50)
        ps=[tuple(row[j:j+3]) for j in (3,6,9)]
        keys=[tuple(round(v,5) for v in p) for p in ps]
        assert len(set(keys))==3,(path,'degenerate triangle',i)
        verts.update(keys)
        for p in ps:
            for axis in range(3): xyz[axis].append(p[axis])
        for a,b in zip(keys,keys[1:]+keys[:1]):
            e=tuple(sorted((a,b))); edges[e]+=1; oriented[e]+=1 if a<b else -1
        a,b,c=ps
        volume+=(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
    bad=sum(n!=2 for n in edges.values())
    winding=sum(n!=0 for n in oriented.values())
    assert bad==0 and winding==0,(path,bad,winding)
    dims=[max(v)-min(v) for v in xyz]
    # Native STL approximates circular edges with chords; allow 0.05 mm in
    # the overall bounds, comfortably below a typical FDM extrusion width.
    assert max(abs(a-b) for a,b in zip(dims,part['size_mm']))<0.05,(path,dims,part['size_mm'])
    relative=abs(abs(volume)-part['volume_mm3'])/part['volume_mm3']
    assert relative<0.002,(path,relative)
    reports.append({'file':path.name,'triangles':count,'watertight':True,'consistent_winding':True,
                    'size_mm':dims,'mesh_volume_mm3':volume,'cad_volume_error_fraction':relative})
print(json.dumps(reports,indent=2))
(base/'mesh_verification.json').write_text(json.dumps(reports,indent=2))
