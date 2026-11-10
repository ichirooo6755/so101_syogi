import adsk.core
import adsk.fusion
import json

design = adsk.fusion.Design.cast(app.activeProduct)
root = design.rootComponent

def point(p):
    return [round(v * 10, 6) for v in p.asArray()]

def bbox(obj):
    b = obj.boundingBox
    return [point(b.minPoint), point(b.maxPoint)]

def body_info(body):
    faces = []
    for f in body.faces:
        g = f.geometry
        data = {"index": f.tempId, "type": g.objectType, "area_mm2": round(f.area*100, 3),
                "bbox_mm": bbox(f), "centroid_mm": point(f.centroid)}
        if isinstance(g, adsk.core.Plane):
            data.update(origin_mm=point(g.origin), normal=list(g.normal.asArray()))
        if isinstance(g, adsk.core.Cylinder):
            data.update(origin_mm=point(g.origin), axis=list(g.axis.asArray()), radius_mm=g.radius*10)
        faces.append(data)
    return {"name": body.name, "solid": body.isSolid, "bbox_mm": bbox(body),
            "volume_mm3": body.volume*1000, "faces": faces}

data = {"document": app.activeDocument.name, "design_type": int(design.designType),
        "timeline_count": design.timeline.count, "timeline_marker": design.timeline.markerPosition,
        "root_bodies": [body_info(b) for b in root.bRepBodies], "occurrences": []}
for occ in root.occurrences:
    data["occurrences"].append({"name":occ.name, "component":occ.component.name,
        "visible":occ.isLightBulbOn, "referenced":occ.isReferencedComponent,
        "transform":list(occ.transform2.asArray()),
        "bodies":[body_info(b) for b in occ.bRepBodies]})
data["parameters"]=[{"name":p.name,"expression":p.expression,"unit":p.unit} for p in design.userParameters]
with open('/Users/sugawaraichirou/Documents/ChatGPT/so101/tmp/fusion_inspection.json','w') as out:
    json.dump(data,out,ensure_ascii=False,indent=2)
print(json.dumps({"document":data["document"],"design_type":data["design_type"],
    "timeline":[data["timeline_marker"],data["timeline_count"]],
    "occurrences":[{k:v for k,v in o.items() if k!='bodies'} | {"bodies":[{k:v for k,v in b.items() if k!='faces'} for b in o['bodies']]} for o in data['occurrences']],
    "parameters":data['parameters']},ensure_ascii=False,indent=2))
