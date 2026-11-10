import adsk.core
import adsk.fusion
import json

main=next(doc for doc in app.documents if doc.name.startswith('so101書道'))
d=adsk.fusion.Design.cast(main.products.itemByProductType('DesignProductType'))
original=d.rootComponent.occurrences.itemByName('部品１:1').bRepBodies.item(0)
newdoc=next(doc for doc in app.documents if doc.name=='部品１_V7_閉断面台座補強')
nd=adsk.fusion.Design.cast(newdoc.products.itemByProductType('DesignProductType'))
def bbox(b): return [[v*10 for v in p.asArray()] for p in (b.minPoint,b.maxPoint)]
def inspect(b):
    rows=[]
    for f in b.faces:
        g=f.geometry
        if isinstance(g,adsk.core.Cylinder):
            rows.append({'type':'cylinder','origin_mm':[v*10 for v in g.origin.asArray()],
                'axis':list(g.axis.asArray()),'diameter_mm':g.radius*20,'bounds_mm':bbox(f.boundingBox),'area_mm2':f.area*100})
        elif isinstance(g,adsk.core.Plane) and (abs(g.normal.y)>.99 or abs(g.normal.z)>.99):
            rows.append({'type':'plane','origin_mm':[v*10 for v in g.origin.asArray()],
                'normal':list(g.normal.asArray()),'bounds_mm':bbox(f.boundingBox),'area_mm2':f.area*100})
    return rows
report={'original_user_yoke':inspect(original),'candidate_V7':inspect(nd.rootComponent.bRepBodies.item(0))}
with open('/Users/sugawaraichirou/Documents/ChatGPT/so101/output/v7/mount_geometry.json','w',encoding='utf-8') as f:
    json.dump(report,f,ensure_ascii=False,indent=2)
for k,rows in report.items():
    print(k)
    for row in rows:
        if row['type']=='cylinder' and abs(row['axis'][1])>.99:
            if row['origin_mm'][0]<10: print(row)
        elif k=='original_user_yoke' and row['type']=='plane' and abs(row['normal'][1])>.99:
            print(row)
        elif k=='candidate_V7' and row['type']=='cylinder' and abs(row['axis'][2])>.99:
            print('LOADCELL_HOLE',row)
