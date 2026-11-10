"""A1 mini fit/slicer experiments for extended arms. No printer connection."""
import argparse
from pathlib import Path
import json
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile
import numpy as np
import trimesh

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--length-mm',type=int,choices=(58,75),default=58)
parser.add_argument('--pitch-deg',type=float,help='Tilt the long axis above the build plate')
args=parser.parse_args()
pitch=args.pitch_deg if args.pitch_deg is not None else (42.5 if args.length_mm==75 else 0.)
if not 0<=pitch<=60: raise ValueError('Pitch must be between 0 and 60 degrees')
suffix=f'{args.length_mm}' if pitch==0 else f'{args.length_mm}_tilted'
dest=ROOT/f'output/upper_arm_extension/slice_{suffix}'
dest.mkdir(parents=True,exist_ok=True)
mesh=trimesh.load_mesh(ROOT/f'output/upper_arm_extension/Upper_arm_SO101_plus{args.length_mm}.stl')
v=mesh.vertices.copy();angle=np.deg2rad(pitch); s=2**-.5
long_axis=np.array([np.cos(angle)*s,np.cos(angle)*s,np.sin(angle)])
width_axis=np.array([s,-s,0.]);thickness_axis=np.cross(width_axis,long_axis)
vertices=v@np.stack((long_axis,thickness_axis,width_axis))
vertices[:,:2]+=90-(vertices[:,:2].min(axis=0)+vertices[:,:2].max(axis=0))/2
vertices[:,2]-=vertices[:,2].min()
rotated=dest/f'rotated_plus{args.length_mm}.stl'
trimesh.Trimesh(vertices=vertices,faces=mesh.faces,process=False).export(rotated)
profiles=Path('/Applications/BambuStudio.app/Contents/Resources/profiles/BBL')
def preset(folder,name):
    row=json.loads((profiles/folder/(name+'.json')).read_text()); merged={}
    if row.get('inherits'): merged.update(preset(folder,row['inherits']))
    for include in row.get('include',[]): merged.update(preset(folder,include))
    merged.update(row)
    for k in ('inherits','include'): merged.pop(k,None)
    return merged
machine=preset('machine','Bambu Lab A1 mini 0.4 nozzle')
process=preset('process','0.20mm Strength @BBL A1M')
filament=preset('filament','Generic PLA @BBL A1M')
process.update({'wall_loops':'4','sparse_infill_density':'25%','sparse_infill_pattern':'gyroid',
                'curr_bed_type':'Textured PEI Plate','enable_support':'1','support_type':'tree(auto)',
                'support_on_build_plate_only':'1','brim_type':'no_brim','brim_width':'0'})
for name,settings in [('machine',machine),('process',process),('filament',filament)]:
    (dest/(name+'.json')).write_text(json.dumps(settings,indent=2))
cmd=['/Applications/BambuStudio.app/Contents/MacOS/BambuStudio','--debug','2','--datadir',str(dest/'isolated_config'),
     '--load-settings',str(dest/'machine.json')+';'+str(dest/'process.json'),
     '--load-filaments',str(dest/'filament.json'),'--arrange','0','--orient','0','--slice','0',
     '--outputdir',str(dest),'--export-3mf',f'arm_{suffix}_a1mini.3mf','--export-slicedata',str(dest/'slicedata'),str(rotated)]
run=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=180)
(dest/'slicer.log').write_text(run.stdout)
report={'returncode':run.returncode,'hardware_printed':False,'printer_connected':False,
        'machine':'Bambu Lab A1 mini, 0.4 mm nozzle','material':'Generic PLA',
        'extension_mm':args.length_mm,'pitch_deg':pitch,'yaw_deg':45,
        'bounding_box_mm':np.ptp(vertices,axis=0).round(2).tolist(),
        'layer_mm':0.2,'walls':4,'infill_percent':25,'support':'organic, build plate only',
        'brim':'none','notes':'Slicing only; support removal, strength and assembly remain untested.'}
if run.returncode==0:
    with zipfile.ZipFile(dest/f'arm_{suffix}_a1mini.3mf') as sliced:
        plate=ET.fromstring(sliced.read('Metadata/slice_info.config')).find('plate')
        metadata={e.get('key'):e.get('value') for e in plate.findall('metadata')}
        report.update(outside=metadata.get('outside'), support_used=metadata.get('support_used'),
                      estimated_seconds=metadata.get('prediction'),estimated_grams=metadata.get('weight'))
        (dest.parent/f'slice_preview_{suffix}.png').write_bytes(sliced.read('Metadata/top_1.png'))
    # This is filament length in the generated first-layer G-code, not
    # measured adhesion area. It helps identify support-dominated placement.
    relative=False; layer=0; feature=''; extrusion={'support':0.,'model':0.}
    with (dest/'plate_1.gcode').open() as fp:
        for line in fp:
            if line.startswith('M83'): relative=True
            elif line.startswith('M82'): relative=False
            elif line.startswith('; CHANGE_LAYER'):
                layer+=1
                if layer>1: break
            elif line.startswith('; FEATURE:'): feature=line.split(':',1)[1].strip()
            if layer==1 and relative and line.startswith(('G1 ','G2 ','G3 ')):
                match=re.search(r'(?:^|\s)E(-?\d*\.?\d+)',line)
                if match and float(match.group(1))>0 and feature and feature!='Custom':
                    key='support' if 'support' in feature.lower() else 'model'
                    extrusion[key]+=float(match.group(1))
    report['first_layer_filament_mm']={key:round(value,2) for key,value in extrusion.items()}
(dest.parent/f'slicer_check_{suffix}.json').write_text(json.dumps(report,indent=2)+'\n')
print('return code',run.returncode,flush=True)
print(run.stdout[-2500:],flush=True)
raise SystemExit(run.returncode)
