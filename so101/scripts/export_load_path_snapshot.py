"""Freeze current world-space solids for analysis, without modifying the source."""
import adsk.core
import adsk.fusion
import datetime
import itertools
import json
import os

out='/Users/sugawaraichirou/Documents/ChatGPT/so101/output/load_path_analysis'
os.makedirs(out,exist_ok=True)
doc=app.activeDocument
d=adsk.fusion.Design.cast(app.activeProduct); r=d.rootComponent
assert doc.name=='so101書道'
names=[('base','部品１:1'),('carrier','Brush_Load_Carrier:1'),
       ('cartridge','Brush_Cartridge_15mm:1'),('old_separate_cover','SC616C_Slide_In_Top_Cover:1')]
parts={label:r.occurrences.itemByName(name) for label,name in names}
parts['sensor']=next(o for o in r.allOccurrences if o.fullPathName.startswith('SC616C_1kg_Fusion:1+') and o.bRepBodies.count)
tmp=adsk.fusion.TemporaryBRepManager.get()
bodies={label:o.bRepBodies.item(0) for label,o in parts.items()}
source_state={'modified':doc.isModified,'timeline_marker':d.timeline.markerPosition,'timeline_count':d.timeline.count,
              'volumes':{label:b.volume*1000 for label,b in bodies.items()},
              'transforms':{label:list(o.transform2.asArray()) for label,o in parts.items()}}
def pts(box): return [[v*10 for v in p.asArray()] for p in (box.minPoint,box.maxPoint)]
def removed_volume(body,tool):
    copy=tmp.copy(body); before=copy.volume
    assert tmp.booleanOperation(copy,tool,adsk.fusion.BooleanTypes.DifferenceBooleanType)
    return (before-copy.volume)*1000
def box(x0,x1,y0,y1,z0,z1):
    bound=adsk.core.OrientedBoundingBox3D.create(adsk.core.Point3D.create((x0+x1)/20,(y0+y1)/20,(z0+z1)/20),
        adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),(x1-x0)/10,(y1-y0)/10,(z1-z0)/10)
    return tmp.createBox(bound)

entities=adsk.core.ObjectCollection.create()
for b in bodies.values(): entities.add(b)
inp=d.createInterferenceInput(entities); inp.areCoincidentFacesIncluded=False
native=d.analyzeInterference(inp)
overlaps=[]
for result in native:
    overlaps.append({'one':result.entityOne.name,'two':result.entityTwo.name,
                     'volume_mm3':result.interferenceBody.volume*1000,'bbox_mm':pts(result.interferenceBody.boundingBox)})
pairs=[]
for (la,a),(lb,b) in itertools.combinations(bodies.items(),2):
    distance=app.measureManager.measureMinimumDistance(a,b)
    pairs.append({'one':la,'two':lb,'minimum_gap_mm':distance.value*10,
                  'overlap_mm3':removed_volume(a,b)})
# A rectangular exclusion envelope, deliberately larger than the strain zone.
gauge_keepout=box(24.65,35.35,9.56,23.36,23.5,32)
gauge_intersections={label:removed_volume(b,gauge_keepout) for label,b in bodies.items() if label!='sensor'}
faces={}
for label,b in bodies.items():
    rows=[]
    for face in b.faces:
        g=face.geometry
        row={'type':g.objectType,'bbox_mm':pts(face.boundingBox),'area_mm2':face.area*100,
             'centroid_mm':[v*10 for v in face.centroid.asArray()]}
        if isinstance(g,adsk.core.Plane): row.update(normal=list(g.normal.asArray()),origin_mm=[v*10 for v in g.origin.asArray()])
        if isinstance(g,adsk.core.Cylinder): row.update(axis=list(g.axis.asArray()),origin_mm=[v*10 for v in g.origin.asArray()],diameter_mm=g.radius*20)
        rows.append(row)
    faces[label]=rows
report={'captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'source':source_state,'parts':{label:{'occurrence':o.fullPathName,'visible':o.isVisible,
                'bbox_mm':pts(bodies[label].boundingBox),'volume_mm3':bodies[label].volume*1000} for label,o in parts.items()},
        'native_interferences':overlaps,'pairs':pairs,'sensing_keepout_intersections_mm3':gauge_intersections,
        'brush_axis_mm':[d.userParameters.itemByName('sc_brush_axis_x').value*10,d.userParameters.itemByName('sc_brush_axis_y').value*10],
        'sensor_model_note':'Approximate aluminium solid; gauge, resin, cable and actual bolt pretension not modeled',
        'faces':faces}
copies={label:tmp.copy(b) for label,b in bodies.items()}
analysis_doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
try:
    ad=adsk.fusion.Design.cast(app.activeProduct); ad.designType=adsk.fusion.DesignTypes.DirectDesignType
    for label,body in copies.items():
        o=ad.rootComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        o.component.name=label
        o.component.bRepBodies.add(body).name=label
        assert ad.exportManager.execute(ad.exportManager.createSTEPExportOptions(out+'/'+label+'.step',o.component))
finally:
    assert analysis_doc.close(False)
    doc.activate()
for label,o in parts.items():
    assert abs(o.bRepBodies.item(0).volume*1000-source_state['volumes'][label])<1e-5,label
    assert max(abs(a-b) for a,b in zip(o.transform2.asArray(),source_state['transforms'][label]))<1e-9,label
assert d.timeline.markerPosition==source_state['timeline_marker'] and d.timeline.count==source_state['timeline_count']
report['source_geometry_preserved']=True
with open(out+'/geometry_audit.json','w',encoding='utf-8') as f: json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps({key:value for key,value in report.items() if key!='faces'},ensure_ascii=False,indent=2))
