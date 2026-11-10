"""Compare local slicer estimates and verify a two-object A1 mini 3MF release."""
from collections import defaultdict
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'output/camera_mount_v5/slicer'
OUT=ROOT/'output/print_camera_hx711_v5'
def summarize(variant):
    folder=BASE/variant
    invocation=json.loads((folder/'invocation.json').read_text())
    result=json.loads((folder/'result.json').read_text()); assert result['return_code']==0
    plates=result['sliced_plates']; assert len(plates)==1
    p=plates[0]; assert len(p['objects'])==2
    assert not p['warning_message'],p['warning_message']
    assert result['wall_loops']==6 and abs(result['layer_height']-.2)<1e-6
    for obj in p['objects']:
        bb=obj['bbox']
        assert abs(bb['z'])<1e-5 and bb['height']<180
        assert 0<=bb['x'] and 0<=bb['y'] and bb['x']+bb['width']<=180 and bb['y']+bb['depth']<=180
    role='Unknown'; last_e=0.; relative=False; role_e=defaultdict(float)
    for line in (folder/'plate_1.gcode').read_text().splitlines():
        if line.startswith('; FEATURE:'):
            role=line.split(':',1)[1].strip(); continue
        code=line.split(';',1)[0].strip()
        if code=='M83':relative=True
        elif code=='M82':relative=False
        values={k:float(v) for k,v in re.findall(r'([A-Z])([-+]?(?:\d+(?:\.\d*)?|\.\d+))',code)}
        if code.startswith('G92 ') and 'E' in values:last_e=values['E']
        if re.match(r'^G(?:0|1|2|3)\s',code) and 'E' in values:
            delta=values['E'] if relative else values['E']-last_e
            last_e=last_e+delta if relative else values['E']
            if delta>0 and ('X' in values or 'Y' in values):role_e[role]+=delta
    support_e=sum(v for k,v in role_e.items() if k.lower().startswith('support'))
    # This is derived from tagged toolpath extrusion, not a weighed physical print.
    support_g=support_e*math.pi*(1.75/2)**2*1.24/1000
    features=p['feature_type_times']; support_seconds=sum(v for k,v in features.items() if k.lower().startswith('support'))
    return {'variant':variant,'slicer_success':True,'warnings':p['warning_message'],
        'total_estimated_seconds':p['total_predication'],'total_estimated_filament_g':sum(f['total_used_g'] for f in p['filaments']),
        'support_toolpath_filament_mm':support_e,'support_toolpath_estimated_g':support_g,
        'support_estimated_seconds':support_seconds,'objects':p['objects'],
        'source_stl_sha256':{m.name:sha256(m.read_bytes()).hexdigest() for m in sorted((ROOT/'output'/('print_camera_hx711_'+variant)).glob('*.stl'))},
        'invocation':invocation}

old=summarize('v4'); new=summarize('v5')
report={'passed':True,'printer':'Bambu Lab A1 mini','nozzle_mm':.4,'material':'Generic PLA',
    'actual_spool_and_bed_conditions_unverified':True,'layer_mm':.2,'walls':6,'infill':'25% gyroid',
    'brim_mm':5,'organic_support_enabled':True,'support_threshold_deg_from_horizontal':40,
    'v4':old,'v5':new,
    'support_extrusion_reduction_fraction':1-new['support_toolpath_filament_mm']/old['support_toolpath_filament_mm'],
    'support_time_reduction_fraction':1-new['support_estimated_seconds']/old['support_estimated_seconds'],
    'total_time_reduction_fraction':1-new['total_estimated_seconds']/old['total_estimated_seconds'],
    'physical_print_or_strength_test_performed':False,'printer_job_sent':False}
assert report['support_extrusion_reduction_fraction']>0,'Do not claim improvement unless measured in the same slicer settings'
project=BASE/'v5/SO101_A1mini_PLA_v5.3mf'
with zipfile.ZipFile(project) as z:
    assert z.testzip() is None
    assert any(n.endswith('.model') for n in z.namelist())
    report['three_mf_members']=len(z.namelist())
shutil.copy2(project,OUT/'A1mini_0.4_PLA_V5.3mf')
for name in ('machine.json','process.json','filament.json'):
    shutil.copy2(BASE/name,OUT/'checks'/('A1mini_'+name))
shutil.copy2(BASE/'v5/result.json',OUT/'checks/A1mini_slicer_result.json')
shutil.copy2(BASE/'v5/invocation.json',OUT/'checks/A1mini_slicer_invocation.json')
(OUT/'checks/A1mini_slicing_comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in report.items() if k not in ('v4','v5')},ensure_ascii=False,indent=2))
print(json.dumps({'v4_seconds':old['total_estimated_seconds'],'v5_seconds':new['total_estimated_seconds'],
    'v4_support_g_estimate':old['support_toolpath_estimated_g'],'v5_support_g_estimate':new['support_toolpath_estimated_g'],
    'v5_total_g_estimate':new['total_estimated_filament_g']},indent=2))
