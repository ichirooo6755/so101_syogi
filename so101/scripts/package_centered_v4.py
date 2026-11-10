from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import json

root=Path(__file__).resolve().parents[1]
base=root/'output'/'v4'
verification=json.loads((base/'verification.json').read_text())
export=json.loads((base/'export_report.json').read_text())
assert verification['passed'] and export['saved_assembly_reopened_and_verified']
assert all(item['standalone_reopened_and_verified'] for item in export['editable_archives'])
assert all(row['watertight'] for row in json.loads((base/'mesh_verification.json').read_text()))
names=['01_centered_load_carrier.stl','01_centered_load_carrier.step','01_centered_load_carrier_editable.f3d',
       '02_centered_brush_cartridge_15mm.stl','02_centered_brush_cartridge_15mm.step','02_centered_brush_cartridge_15mm_editable.f3d',
       'README.md','verification.json','mesh_verification.json','export_report.json','assembly.png',
       'analysis/fea_coarse.json','analysis/geometry_audit.json',
       'analysis/carrier.step','analysis/cartridge.step','analysis/sensor.step']
path=root/'output'/'so101_calligraphy_v4_centered_print_files.zip'
with ZipFile(path,'w',ZIP_DEFLATED) as archive:
    for name in names:
        source=base/name
        assert source.is_file(),name
        archive.write(source,'v4/'+name)
with ZipFile(path) as archive:
    assert archive.testzip() is None
    assert len(archive.namelist())==len(names)
print(path)
print('bytes',path.stat().st_size,'files',len(names))
