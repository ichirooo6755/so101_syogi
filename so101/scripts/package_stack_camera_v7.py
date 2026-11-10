"""Package validated V7 output without overwriting earlier print sets."""
from pathlib import Path
import json
import shutil
import zipfile
ROOT=Path(__file__).resolve().parents[1]
candidate=ROOT/'output/camera_mount_v7/print_candidate'
sliced=ROOT/'output/camera_mount_v7/slicer'
dest=ROOT/'output/print_camera_hx711_v7'
archive=ROOT/'output/so101_camera_hx711_V7_stacked_print_files.zip'
assert not dest.exists() and not archive.exists(), 'Will not overwrite an existing print set'
assert json.loads((candidate/'checks/assembly_paths.json').read_text())['passed']
assert json.loads((candidate/'checks/release_native_check.json').read_text())['passed']
assert len(json.loads((candidate/'mesh_verification.json').read_text()))==6
result=json.loads((sliced/'v7_final/result.json').read_text())
assert result['return_code']==0 and len(result['sliced_plates'])==1
assert not result['sliced_plates'][0]['warning_message']
shutil.copytree(candidate,dest)
shutil.copy2(sliced/'v7_final/SO101_A1mini_PLA_v7.3mf',dest/'SO101_A1mini_PLA_v7.3mf')
for source in (sliced/'v7_final/result.json',sliced/'v7_final/invocation.json',sliced/'machine.json',sliced/'process.json',sliced/'filament.json'):
    shutil.copy2(source,dest/'checks'/('slicer_'+source.name))
report=json.loads((dest/'export_report.json').read_text())
report['assembly_archive']=str(dest/'source_cad/SO101_XIAO_SEN13879_perfboard_V7_assembly_DO_NOT_PRINT.f3d')
(dest/'export_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
    for f in sorted(dest.rglob('*')):
        if f.is_file():z.write(f,f.relative_to(dest.parent))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print(json.dumps({'folder':str(dest),'archive':str(archive),'files':sum(1 for p in dest.rglob('*') if p.is_file())},ensure_ascii=False,indent=2))
