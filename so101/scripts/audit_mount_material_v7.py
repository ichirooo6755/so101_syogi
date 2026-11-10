"""Read-only source/reference and user material audit."""
import adsk.core
import adsk.fusion
import json

def material(m):
    result={'name':m.name,'id':m.id,'properties':{}}
    for p in m.materialProperties:
        if p.objectType == 'adsk::core::FloatProperty' and any(k in p.id.lower()
            for k in ('young','poisson','yield','tensile','density','shear')):
            result['properties'][p.id]={'value':p.value,'units':p.units}
    return result
result={'active_document':app.activeDocument.name,'active_command':ui.activeCommand,
        'active_product':app.activeProduct.objectType,'selections':[], 'documents':[]}
for s in ui.activeSelections:
    e=s.entity
    row={'type':e.objectType,'name':getattr(e,'name','')}
    try:
        b=e.body if e.objectType=='adsk::fusion::BRepFace' else e
        row['design']=b.parentComponent.parentDesign.objectType
    except: pass
    result['selections'].append(row)
for doc in app.documents:
    d=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    if not d: continue
    row={'name':doc.name,'modified':doc.isModified,'root_bodies':[], 'occurrences':[]}
    def body(b):
        return {'name':b.name,'volume_mm3':b.volume*1000,'material':material(b.material),
            'bbox_mm':[[x*10 for x in p.asArray()] for p in (b.boundingBox.minPoint,b.boundingBox.maxPoint)]}
    row['root_bodies']=[body(b) for b in d.rootComponent.bRepBodies]
    for o in d.rootComponent.allOccurrences:
        if doc.name.startswith('so101書道'):
            entry={'name':o.fullPathName,'visible':o.isVisible,
                   'body_count':o.bRepBodies.count,'mesh_count':o.component.meshBodies.count}
            if any(k in o.name.lower() for k in ('gripper','部品','sc616','wrist_roll')):
                entry['bodies']=[body(b) for b in o.bRepBodies]
        else:
            entry={'name':o.fullPathName,'bodies':[body(b) for b in o.bRepBodies]}
        row['occurrences'].append(entry)
    result['documents'].append(row)
with open('/Users/sugawaraichirou/Documents/ChatGPT/so101/output/v7/user_material_and_mount_audit.json','w',encoding='utf-8') as f:
    json.dump(result,f,ensure_ascii=False,indent=2)
print('active',result['active_document'],result['active_command'],result['active_product'])
print('selected',result['selections'])
for doc in result['documents']:
    print('DOCUMENT',doc['name'])
    for o in doc['occurrences']:
        if doc['name'].startswith('so101書道'):
            print(o['name'], 'visible',o['visible'],'bodies',o['body_count'],'meshes',o['mesh_count'])
        else:
            for b in o.get('bodies',[]): print(o['name'],b['material']['name'],b['material']['properties'])
