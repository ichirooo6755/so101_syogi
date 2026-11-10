#!/usr/bin/env python3
"""Audit six printable meshes and make a checksum-verified addon ZIP."""
from collections import Counter
from datetime import datetime,timezone
from hashlib import sha256
import json
from pathlib import Path
import struct
import zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/print_camera_hx711_v1'
ZIP=ROOT/'output/so101_camera_hx711_V1_print_files.zip'
assert not ZIP.exists(),'Keep previous archives intact'
report=json.loads((OUT/'export_report.json').read_text())
mesh=json.loads((OUT/'mesh_verification.json').read_text())
cad=json.loads((OUT/'checks/cad_reopen_verification.json').read_text())
rotation=json.loads((OUT/'checks/rotation_check.json').read_text())
paths=json.loads((OUT/'checks/assembly_paths.json').read_text())
fasteners=json.loads((OUT/'checks/fastener_check.json').read_text())
assert len(report['exports'])==len(mesh)==6
assert cad['passed'] and len(cad['files'])==12
assert len(rotation)==73 and not any(r['hits'] for r in rotation)
assert paths['passed'] and not any(r['hits'] for r in paths['paths']+paths['cartridge_removal'])
assert report['source_geometry_poses_materials_preserved']
assert all(m['watertight'] and m['consistent_winding'] for m in mesh)
assert all(s['head_pushed_0p1mm_overlap_mm3']>.05 for s in fasteners['head_stops'])
assert {p.name for p in OUT.glob('*.stl')}=={p['stem']+'.stl' for p in report['exports']}
connectivity=[]
for part in report['exports']:
    p=OUT/(part['stem']+'.stl'); raw=p.read_bytes()
    assert sha256(raw).hexdigest()==part['stl_sha256']
    parent={}
    def find(a):
        parent.setdefault(a,a)
        while parent[a]!=a:
            parent[a]=parent[parent[a]]; a=parent[a]
        return a
    for i in range(struct.unpack_from('<I',raw,80)[0]):
        vals=struct.unpack_from('<12fH',raw,84+i*50)
        vs=[tuple(round(x,5) for x in vals[a:a+3]) for a in (3,6,9)]
        for a,b in zip(vs,vs[1:]+vs[:1]):
            a=find(a); b=find(b)
            if a!=b: parent[a]=b
    shells=len({find(v) for v in parent})
    assert shells==1,(p.name,shells)
    connectivity.append({'file':p.name,'surface_components':shells,'quantity':1})
summary={'created_utc':datetime.now(timezone.utc).isoformat(),'passed':True,
    'printable_part_types':6,'printed_piece_count':6,'connectivity':connectivity,
    'new_fasteners':{'M3x8_socket_cap':5,'M3x10_socket_cap':1,'M3_hex_nut':6},
    'native_cad_reopened':12,'sampled_rotation_poses':73,'rotation_collisions':0,
    'source_version_preserved':26,'source_timeline_preserved':[520,520],
    'physical_fit_strength_or_electrical_test_performed':False}
(OUT/'package_verification.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name!='SHA256SUMS')
assert all(not p.is_symlink() for p in files)
(OUT/'SHA256SUMS').write_text(''.join(sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(OUT).as_posix()+'\n' for p in files))
files.append(OUT/'SHA256SUMS')
with zipfile.ZipFile(ZIP,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in files: z.write(p,Path(OUT.name)/p.relative_to(OUT))
with zipfile.ZipFile(ZIP) as z:
    assert z.testzip() is None
    assert len(z.namelist())==len(files)
    for p in files:
        assert sha256(z.read((Path(OUT.name)/p.relative_to(OUT)).as_posix())).digest()==sha256(p.read_bytes()).digest()
print(json.dumps({'folder':str(OUT),'zip':str(ZIP),'zip_bytes':ZIP.stat().st_size,
    'file_count':len(files),'zip_sha256':sha256(ZIP.read_bytes()).hexdigest(),
    'verification':summary},ensure_ascii=False,indent=2))
