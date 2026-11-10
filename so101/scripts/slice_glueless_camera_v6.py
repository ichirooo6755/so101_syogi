"""Use installed Bambu A1 mini presets with an isolated config; no printer I/O."""
from pathlib import Path
import struct
import xml.etree.ElementTree as ET
import zipfile
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'output/camera_mount_v6/print_candidate'
layout=ROOT/'output/camera_mount_v6/one_plate_input.3mf'
namespace='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
ET.register_namespace('',namespace)
def tag(n):return '{'+namespace+'}'+n
model=ET.Element(tag('model'),{'unit':'millimeter','{http://www.w3.org/XML/1998/namespace}lang':'en-US'})
ET.SubElement(model,tag('metadata'),{'name':'Application'}).text='SO101 local print packaging'
resources=ET.SubElement(model,tag('resources')); build=ET.SubElement(model,tag('build'))
placements=[(8,8),(8,94),(104,8),(43,94)]
for index,(mesh_path,position) in enumerate(zip(sorted(folder.glob('*.stl')),placements),1):
    data=mesh_path.read_bytes(); count=struct.unpack_from('<I',data,80)[0]
    vertices=[]; triangles=[]; vertex_index={}
    for i in range(count):
        row=struct.unpack_from('<12fH',data,84+i*50); triangle=[]
        for j in (3,6,9):
            p=tuple(row[j:j+3])
            if p not in vertex_index:vertex_index[p]=len(vertices); vertices.append(p)
            triangle.append(vertex_index[p])
        triangles.append(triangle)
    obj=ET.SubElement(resources,tag('object'),{'id':str(index),'type':'model','name':mesh_path.stem})
    mesh=ET.SubElement(obj,tag('mesh')); vs=ET.SubElement(mesh,tag('vertices')); ts=ET.SubElement(mesh,tag('triangles'))
    for p in vertices:ET.SubElement(vs,tag('vertex'),dict(zip(('x','y','z'),[format(v,'.9g') for v in p])))
    for tri in triangles:ET.SubElement(ts,tag('triangle'),dict(zip(('v1','v2','v3'),map(str,tri))))
    ET.SubElement(build,tag('item'),{'objectid':str(index),'transform':f'1 0 0 0 1 0 0 0 1 {position[0]} {position[1]} 0'})
assert len(list(build))==4
with zipfile.ZipFile(layout,'w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True))
    z.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    z.writestr('_rels/.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
script=(ROOT/'scripts/check_A1mini_slicing_v5.py').read_text()
script=script.replace("parser.add_argument('variant',choices=['v4','v5'])","parser.add_argument('variant',choices=['v6'])")
script=script.replace('camera_mount_v5/slicer','camera_mount_v6/slicer')
script=script.replace("ROOT/'output'/('print_camera_hx711_'+args.variant)","ROOT/'output/camera_mount_v6/print_candidate'")
script=script.replace('assert len(meshes)==2','assert len(meshes)==4')
script=script.replace("destination=OUT/args.variant","destination=OUT/'v6_final'")
script=script.replace("'--arrange','1'","'--arrange','0'")
script=script.replace('*[str(p) for p in meshes]',repr(str(layout)))
exec(compile(script,'A1mini_V6_local_slice','exec'),globals())
