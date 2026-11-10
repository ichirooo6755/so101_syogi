import adsk.core
import adsk.fusion
import json
import math
import os
d=adsk.fusion.Design.cast(app.activeProduct)
r=d.rootComponent
yoke=r.occurrences.itemByName('部品１:1')
cell=r.occurrences.itemByName('SC616C_1kg_Fusion:1')
sensor_occ=next(o for o in r.allOccurrences if o.fullPathName.startswith('SC616C_1kg_Fusion:1+') and o.bRepBodies.count)
sensor=sensor_occ.bRepBodies.item(0)
base=yoke.bRepBodies.item(0)
def pt(p): return [c*10 for c in p.asArray()]
def cylinder_axes(body,radius):
    axes=[]
    for f in body.faces:
        g=f.geometry
        if isinstance(g,adsk.core.Cylinder) and abs(g.radius*10-radius)<1e-5 and abs(g.axis.z)>.99:
            axes.append({'x':g.origin.x*10,'y':g.origin.y*10,'radius':g.radius*10,
                         'z_range':[f.boundingBox.minPoint.z*10,f.boundingBox.maxPoint.z*10]})
    return sorted(axes,key=lambda a:a['y'])
sensor_holes=cylinder_axes(sensor,1.5)
mount_holes=cylinder_axes(base,1.7)
head_recesses=cylinder_axes(base,3.1)
assert len(sensor_holes)==4 and len(mount_holes)==2 and len(head_recesses)==2
errors=[math.hypot(a['x']-b['x'],a['y']-b['y']) for a,b in zip(sensor_holes[2:],mount_holes)]
assert max(errors)<1e-5, errors
assert abs(sensor_holes[3]['y']-sensor_holes[2]['y']-7.4)<1e-5
brush_y=(sensor_holes[0]['y']+sensor_holes[1]['y'])/2
assert abs(brush_y-1.26294620236)<1e-5
with open('/Users/sugawaraichirou/Documents/ChatGPT/so101/tmp/fusion_inspection.json') as f: baseline=json.load(f)
original=next(o['transform'] for o in baseline['occurrences'] if o['name']==cell.name)
current=list(cell.transform2.asArray())
rotation_error=max(abs(current[i]-original[i]) for i in (0,1,2,4,5,6,8,9,10))
assert rotation_error<1e-10
new_features=[{'name':f.name,'parametric':f.isParametric,'health':int(f.healthState)}
              for f in yoke.component.features.extrudeFeatures if f.name.startswith('SC616C')]
assert all(f['parametric'] and f['health']==0 for f in new_features)
assert base.isSolid and yoke.component.bRepBodies.count==1
tmp=adsk.fusion.TemporaryBRepManager.get()
overlap=tmp.copy(base)
tool=tmp.copy(sensor)
before=overlap.volume*1000
ok=tmp.booleanOperation(overlap,tool,adsk.fusion.BooleanTypes.DifferenceBooleanType)
print('temporary_difference',ok,pt(overlap.boundingBox.minPoint),pt(tool.boundingBox.minPoint))
assert ok
overlap_volume=before-overlap.volume*1000
assert abs(overlap_volume)<1e-5, overlap_volume

# Test an envelope around the entire floating end and strain-relief region,
# expanded 1 mm to either side and 2 mm below/above the sensor. No base material
# may occupy this envelope; only the far fixed end is allowed to contact.
free_y_min=sensor.boundingBox.minPoint.y*10-1
free_y_max=23.46294620236-0.1
center=adsk.core.Point3D.create(3,(free_y_min+free_y_max)/20,2.75)
box=adsk.core.OrientedBoundingBox3D.create(center,adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),1.1,(free_y_max-free_y_min)/10,1.0)
envelope=tmp.createBox(box)
candidate=tmp.copy(base)
before=candidate.volume*1000
hit=tmp.booleanOperation(candidate,envelope,adsk.fusion.BooleanTypes.DifferenceBooleanType)
print('temporary_clearance_envelope_difference',hit)
assert hit
free_envelope_volume=before-candidate.volume*1000
assert abs(free_envelope_volume)<1e-5,free_envelope_volume
entities=adsk.core.ObjectCollection.create()
entities.add(base)
entities.add(sensor)
native_input=d.createInterferenceInput(entities)
native_input.areCoincidentFacesIncluded=False
native_results=d.analyzeInterference(native_input)
assert native_results is not None and native_results.count==0

report={'passed':True,'sensor_holes':sensor_holes,'mount_holes':mount_holes,
        'head_recesses':head_recesses,'axis_alignment_error_mm':errors,
        'rotation_error':rotation_error,'future_brush_center_y_mm':brush_y,
        'sensor_base_interference_mm3':overlap_volume,
        'free_end_and_flexure_clearance_envelope_interference_mm3':free_envelope_volume,
        'native_interference_count':native_results.count,
        'features':new_features,'timeline_marker':d.timeline.markerPosition,'timeline_count':d.timeline.count}
with open('/Users/sugawaraichirou/Documents/ChatGPT/so101/tmp/sc616c_mount_verified.json','w') as f:
    json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps(report,ensure_ascii=False,indent=2))
