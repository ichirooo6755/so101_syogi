"""Slice local meshes with A1 mini / 0.4 PLA; never connect to or send to a printer."""
import argparse
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/camera_mount_v5/slicer'
PROFILE=Path('/Applications/BambuStudio.app/Contents/Resources/profiles/BBL')
CLI='/Applications/BambuStudio.app/Contents/MacOS/BambuStudio'
parser=argparse.ArgumentParser(); parser.add_argument('variant',choices=['v4','v5']); args=parser.parse_args()
OUT.mkdir(parents=True,exist_ok=True)
def preset(folder,name):
    p=PROFILE/folder/(name+'.json'); row=json.loads(p.read_text()); merged={}
    if row.get('inherits'):merged.update(preset(folder,row['inherits']))
    for include in row.get('include',[]):merged.update(preset(folder,include))
    merged.update(row)
    for key in ('inherits','include'):merged.pop(key,None)
    return merged
machine=preset('machine','Bambu Lab A1 mini 0.4 nozzle')
process=preset('process','0.20mm Strength @BBL A1M')
filament=preset('filament','Generic PLA @BBL A1M')
process.update({'wall_loops':'6','sparse_infill_density':'25%','sparse_infill_pattern':'gyroid',
    'curr_bed_type':'Textured PEI Plate',
    'top_shell_layers':'6','bottom_shell_layers':'6','enable_support':'1',
    'support_type':'tree(auto)','support_threshold_angle':'40','support_on_build_plate_only':'1',
    'bridge_no_support':'1','brim_type':'outer_only','brim_width':'5'})
for name,data in (('machine',machine),('process',process),('filament',filament)):
    (OUT/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2))
destination=OUT/args.variant; destination.mkdir(exist_ok=True)
meshes=sorted((ROOT/'output'/('print_camera_hx711_'+args.variant)).glob('*.stl'))
assert len(meshes)==2,meshes
command=[CLI,'--debug','2','--datadir',str(destination/'isolated_config'),
    '--load-settings',str(OUT/'machine.json')+';'+str(OUT/'process.json'),
    '--load-filaments',str(OUT/'filament.json'),'--arrange','1','--orient','0',
    '--slice','0','--mstpp','60','--outputdir',str(destination),
    '--export-3mf','SO101_A1mini_PLA_'+args.variant+'.3mf',
    '--export-slicedata',str(destination/'slicedata'),*[str(p) for p in meshes]]
result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=120)
(destination/'slicer.log').write_text(result.stdout)
(destination/'invocation.json').write_text(json.dumps({'command':command,'returncode':result.returncode,
    'printer':'A1 mini','nozzle_mm':.4,'filament':'Generic PLA (actual spool unspecified)',
    'layer_height_mm':.2,'walls':6,'infill':'25% gyroid','support_threshold_from_horizontal_deg':40,
    'printer_connection_or_print_job_sent':False},ensure_ascii=False,indent=2))
print(result.stdout[-14000:])
raise SystemExit(result.returncode)
