import adsk.core
import adsk.fusion
import builtins
import json
import os

root='/Users/sugawaraichirou/Documents/ChatGPT/so101'
path=root+'/tmp/v6_user_revision.json'
assert not os.path.exists(path),'Keep first user revision snapshot'
def bb(b): return [[v*10 for v in p.asArray()] for p in (b.minPoint,b.maxPoint)]
def entity(e):
    row={'type':e.objectType,'name':getattr(e,'name','')}
    try: row['bbox_mm']=bb(e.boundingBox)
    except: pass
    try: row['body']=e.body.name; row['component']=e.body.parentComponent.name; row['area_mm2']=e.area*100
    except: pass
    try: row['centroid_mm']=[v*10 for v in e.centroid.asArray()]
    except: pass
    try: row['token']=e.entityToken
    except: pass
    return row
result={'active_doc':app.activeDocument.name,'active_product':app.activeProduct.productType,'active_command':ui.activeCommand,
        'current_selections':[entity(s.entity) for s in ui.activeSelections],'documents':[]}
designs=[]
for doc in app.documents:
    try: d=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    except: continue
    if not d: continue
    designs.append((doc,d))
    row={'name':doc.name,'modified':doc.isModified,'selection_sets':[], 'occurrences':[]}
    if d.designType==adsk.fusion.DesignTypes.ParametricDesignType:
        row.update(marker=d.timeline.markerPosition,count=d.timeline.count)
        row['parameters']={p.name:p.expression for p in d.userParameters}
    for ss in d.selectionSets:
        row['selection_sets'].append({'name':ss.name,'entities':[entity(e) for e in ss.entities]})
    for o in d.rootComponent.allOccurrences:
        if not o.isVisible and 'V5' not in o.name: continue
        row['occurrences'].append({'name':o.fullPathName,'visible':o.isVisible,'transform':list(o.transform2.asArray()),
            'bodies':[{'name':b.name,'solid':b.isSolid,'volume_mm3':b.volume*1000,'bbox_mm':bb(b.boundingBox)} for b in o.bRepBodies],
            'features':[(f.name,int(f.healthState)) for f in o.component.features] if 'V5' in o.name else []})
    result['documents'].append(row)
if hasattr(builtins,'_so101_v5_sim_design'):
    sd=builtins._so101_v5_sim_design
    try:
        result['working_model']={'name':sd.rootComponent.name,'selection_sets':[{'name':ss.name,'entities':[entity(e) for e in ss.entities]} for ss in sd.selectionSets]}
    except Exception as e: result['working_model_error']=str(e)
with open(path,'w',encoding='utf-8') as f: json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result,ensure_ascii=False,indent=2))
for doc,d in designs:
    if doc.name=='so101書道':
        archive=root+'/reference/so101_before_user_requested_shortening_v6.f3d'
        assert not os.path.exists(archive)
        assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(archive))
        print('backup',archive)
