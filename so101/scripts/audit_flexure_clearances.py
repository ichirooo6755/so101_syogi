import adsk.core
import adsk.fusion
import json

root='/Users/sugawaraichirou/Documents/ChatGPT/so101/output/load_path_analysis'
with open(root+'/geometry_audit.json',encoding='utf-8') as f: snapshot=json.load(f)
d=adsk.fusion.Design.cast(app.activeProduct); r=d.rootComponent
parts={name:r.occurrences.itemByName(occ) for name,occ in [('base','部品１:1'),('carrier','Brush_Load_Carrier:1'),('cartridge','Brush_Cartridge_15mm:1')]}
parts['sensor']=next(o for o in r.allOccurrences if o.fullPathName.startswith('SC616C_1kg_Fusion:1+') and o.bRepBodies.count)
matches={label:abs(o.bRepBodies.item(0).volume*1000-snapshot['parts'][label]['volume_mm3'])<1e-5 for label,o in parts.items()}
tmp=adsk.fusion.TemporaryBRepManager.get()
bound=adsk.core.OrientedBoundingBox3D.create(adsk.core.Point3D.create(3,1.596294620236,2.75),
    adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),2,1.2,2)
clip=tmp.createBox(bound)
gauge=tmp.copy(parts['sensor'].bRepBodies.item(0))
assert tmp.booleanOperation(gauge,clip,adsk.fusion.BooleanTypes.IntersectionBooleanType)
gaps={label+'_to_sensor_flexure_mm':app.measureManager.measureMinimumDistance(o.bRepBodies.item(0),gauge).value*10
      for label,o in parts.items() if label!='sensor'}
report={'live_source_matches_analysis_snapshot':matches,'gaps':gaps,
        'flexure_y_range_mm':[9.96294620236,21.96294620236],
        'note':'Positive CAD distances only, not a claim that electrical accuracy is validated'}
with open(root+'/flexure_clearances.json','w',encoding='utf-8') as f: json.dump(report,f,indent=2)
print(json.dumps(report,indent=2))
