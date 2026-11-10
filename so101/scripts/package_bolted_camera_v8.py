"""Package the validated V8 files separately; never overwrite prior sets."""
from pathlib import Path
import json
import shutil
import zipfile
ROOT=Path(__file__).resolve().parents[1]
work=ROOT/'output/camera_mount_v8'
candidate=work/'print_candidate'
sliced=work/'slicer'
dest=ROOT/'output/print_camera_hx711_v8'
archive=ROOT/'output/so101_camera_hx711_V8_bolted_print_files.zip'
assert not dest.exists() and not archive.exists()
assert json.loads((work/'assembly_paths.json').read_text())['passed']
assert json.loads((candidate/'checks/release_native_check.json').read_text())['passed']
mesh=json.loads((candidate/'mesh_verification.json').read_text())
assert len(mesh)==5 and all(r['watertight'] and r['consistent_winding'] for r in mesh)
result=json.loads((sliced/'v8_final/result.json').read_text())
assert result['return_code']==0 and len(result['sliced_plates'])==1
assert not result['sliced_plates'][0]['warning_message']
shutil.copytree(candidate,dest)
shutil.copy2(work/'assembly_paths.json',dest/'checks/assembly_paths.json')
shutil.copy2(sliced/'v8_final/SO101_A1mini_PLA_v8.3mf',dest/'SO101_A1mini_PLA_v8.3mf')
for source in (sliced/'v8_final/result.json',sliced/'v8_final/invocation.json',sliced/'machine.json',sliced/'process.json',sliced/'filament.json'):
    shutil.copy2(source,dest/'checks'/('slicer_'+source.name))
report=json.loads((dest/'export_report.json').read_text())
report['assembly_archive']=str(dest/'source_cad/SO101_XIAO_SEN13879_bolted_V8_assembly_DO_NOT_PRINT.f3d')
assert Path(report['assembly_archive']).is_file()
(dest/'export_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
    for f in sorted(dest.rglob('*')):
        if f.is_file():z.write(f,f.relative_to(dest.parent))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print(json.dumps({'folder':str(dest),'zip':str(archive),'files':sum(1 for p in dest.rglob('*') if p.is_file())},ensure_ascii=False,indent=2))
