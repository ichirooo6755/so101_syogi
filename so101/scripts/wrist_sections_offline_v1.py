"""Fast section maps from the previously verified wrist STL, standard library only."""
import json
import struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
meta=json.loads((ROOT/'output/print_v8/export_report.json').read_text())
part=next(p for p in meta['exports'] if p['part']=='wrist')
raw=(ROOT/'output/print_v8'/f"{part['stem']}.stl").read_bytes()
triangles=[]
for i in range(struct.unpack_from('<I',raw,80)[0]):
    vals=struct.unpack_from('<12fH',raw,84+50*i)
    triangles.append([tuple(vals[3+j*3+k]-part['translation_from_assembly_mm'][k] for k in range(3)) for j in range(3)])

def slice_lines(y):
    lines=[]
    for tri in triangles:
        pts=[]
        for a,b in zip(tri,tri[1:]+tri[:1]):
            if (a[1]<=y<b[1]) or (b[1]<=y<a[1]):
                rat=(y-a[1])/(b[1]-a[1])
                pts.append((a[0]+rat*(b[0]-a[0]),a[2]+rat*(b[2]-a[2])))
        if len(pts)==2: lines.append(pts)
    return lines

def inside(lines,x,z):
    count=0
    for (ax,az),(bx,bz) in lines:
        if ((az<=z<bz) or (bz<=z<az)) and x<ax+(z-az)*(bx-ax)/(bz-az): count+=1
    return count%2==1

sections=[]
for y in (-12,0,12,16,19,23):
    lines=slice_lines(y+.003)
    rows=[]
    print('Y',y,'X -29..16')
    for z in range(8,-9,-1):
        line=''.join('W' if inside(lines,x+.003,z+.003) else '.' for x in range(-29,17))
        print('%3d'%z,line)
        rows.append([z,line])
    sections.append({'Y':y,'X_start':-29,'X_end':16,'rows':rows,'lines':lines})
(ROOT/'output/camera_mount_v1/wrist_sections_mesh.json').write_text(json.dumps(sections,indent=2))
