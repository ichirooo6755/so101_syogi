"""Offline Bambu Studio A1 mini test slice; never connects to a printer."""
import json,struct,subprocess,xml.etree.ElementTree as ET,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];out=R/'output/camera_xiao';dest=out/'slice';dest.mkdir(exist_ok=True)
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';ET.register_namespace('',ns)
def t(n):return '{'+ns+'}'+n
model=ET.Element(t('model'),{'unit':'millimeter','{http://www.w3.org/XML/1998/namespace}lang':'en-US'});resources=ET.SubElement(model,t('resources'));build=ET.SubElement(model,t('build'))
rows=[('01_base_xiao.stl',(35,35)),('02_top_xiao.stl',(95,40)),('03_pcb_keeper.stl',(145,30)),('03_pcb_keeper.stl',(145,55))]
for index,(name,pos) in enumerate(rows,1):
 data=(out/name).read_bytes();count=struct.unpack_from('<I',data,80)[0];vertices=[];triangles=[];lookup={}
 for i in range(count):
  row=struct.unpack_from('<12fH',data,84+i*50);tri=[]
  for j in (3,6,9):
   p=tuple(row[j:j+3]);
   if p not in lookup:lookup[p]=len(vertices);vertices.append(p)
   tri.append(lookup[p])
  triangles.append(tri)
 obj=ET.SubElement(resources,t('object'),{'id':str(index),'type':'model','name':f'{index}_{name}'}); mesh=ET.SubElement(obj,t('mesh'));vs=ET.SubElement(mesh,t('vertices'));ts=ET.SubElement(mesh,t('triangles'))
 for p in vertices:ET.SubElement(vs,t('vertex'),dict(zip(('x','y','z'),map(str,p))))
 for tri in triangles:ET.SubElement(ts,t('triangle'),dict(zip(('v1','v2','v3'),map(str,tri))))
 ET.SubElement(build,t('item'),{'objectid':str(index),'transform':f'1 0 0 0 1 0 0 0 1 {pos[0]} {pos[1]} 0'})
layout=dest/'input.3mf'
with zipfile.ZipFile(layout,'w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True))
 z.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
 z.writestr('_rels/.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
P=Path('/Applications/BambuStudio.app/Contents/Resources/profiles/BBL')
def preset(folder,name):
 row=json.loads((P/folder/(name+'.json')).read_text());merged={}
 if row.get('inherits'):merged.update(preset(folder,row['inherits']))
 for inc in row.get('include',[]):merged.update(preset(folder,inc))
 merged.update(row)
 for k in ('inherits','include'):merged.pop(k,None)
 return merged
machine=preset('machine','Bambu Lab A1 mini 0.4 nozzle');process=preset('process','0.20mm Strength @BBL A1M');filament=preset('filament','Generic PLA @BBL A1M')
process.update({'wall_loops':'4','sparse_infill_density':'25%','sparse_infill_pattern':'gyroid','curr_bed_type':'Textured PEI Plate','enable_support':'1','support_type':'tree(auto)','support_threshold_angle':'40','support_on_build_plate_only':'1','bridge_no_support':'1','brim_type':'outer_only','brim_width':'5'})
for name,value in [('machine',machine),('process',process),('filament',filament)]:(dest/(name+'.json')).write_text(json.dumps(value,indent=2))
cmd=['/Applications/BambuStudio.app/Contents/MacOS/BambuStudio','--debug','2','--datadir',str(dest/'isolated_config'),'--load-settings',str(dest/'machine.json')+';'+str(dest/'process.json'),'--load-filaments',str(dest/'filament.json'),'--arrange','0','--orient','0','--slice','0','--mstpp','60','--outputdir',str(dest),'--export-3mf','xiao_mount_A1mini.3mf','--export-slicedata',str(dest/'slicedata'),str(layout)]
p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=120)
(dest/'slicer.log').write_text(p.stdout);(dest/'result.json').write_text(json.dumps({'returncode':p.returncode,'machine':'Bambu Lab A1 mini','nozzle_mm':.4,'material':'Generic PLA','layer_mm':.2,'support':'tree automatic','hardware_printed':False,'printer_connected':False},indent=2))
print('exit',p.returncode);print(p.stdout[-4000:]);raise SystemExit(p.returncode)
