"""Independent copy of the latest user wrist with two shallow outer reliefs.

Do not alter the main wrist or its feature history. The inner radius 12mm is
left intact, so servo engagement, bolt circle and shaft/key details survive.
"""
import adsk.core
import adsk.fusion
import json
root='/Users/sugawaraichirou/Documents/ChatGPT/so101'; out=root+'/output/v8'
assert ui.activeCommand=='SelectCommand'
main=next(doc for doc in app.documents if doc.name=='so101書道')
md=adsk.fusion.Design.cast(main.products.itemByProductType('DesignProductType'))
o=md.rootComponent.occurrences.itemByName('Wrist_Roll_Clearance_V5:1')
source=max(o.bRepBodies,key=lambda b:b.volume)
t=adsk.fusion.TemporaryBRepManager.get()
def cylinder(y0,y1,r):
    return t.createCylinderOrCone(adsk.core.Point3D.create(-.2,y0/10,3.4),r/10,
        adsk.core.Point3D.create(-.2,y1/10,3.4),r/10)
shape=t.copy(source); before=shape.volume*1000
tools=[]
for side,y0,y1 in (('negative',-17.15,-15.45),('positive',18.6,20.3)):
    tool=cylinder(y0,y1,13.4)
    assert t.booleanOperation(tool,cylinder(y0-.01,y1+.01,10.8),adsk.fusion.BooleanTypes.DifferenceBooleanType)
    tools.append((side,tool))
    assert t.booleanOperation(shape,tool,adsk.fusion.BooleanTypes.DifferenceBooleanType)
assert shape.lumps.count==1
assert 0<before-shape.volume*1000<150
doc=next((x for x in app.documents if x.name=='Wrist_Roll_Clearance_V8_元取付対応'),None)
existing=doc is not None
if existing: doc.activate()
else: doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
d=adsk.fusion.Design.cast(app.activeProduct); r=d.rootComponent
bf=r.features.baseFeatures.item(0) if existing else r.features.baseFeatures.add()
assert bf.startEdit()
if existing: assert bf.updateBody(bf.bodies.item(0),shape)
else: r.bRepBodies.add(shape,bf)
assert bf.finishEdit()
body=r.bRepBodies.item(0)
bf.name='V8_latest_user_wrist_plus_outer_annular_reliefs_R10_8_to_R13_4'
body.name='Wrist_V8_latest_user_edits_plus_shallow_annular_reliefs'
body.material=d.materials.itemByName('USER_WRIST_'+source.material.name) or d.materials.addByCopy(source.material,'USER_WRIST_'+source.material.name)
if existing: assert doc.save('Refine outer annular relief to R10.8..13.4, preserving central functional details; original wrist untouched.')
else: assert doc.saveAs('Wrist_Roll_Clearance_V8_元取付対応',main.dataFile.parentFolder,'',
    'Independent copy of all current user wrist edits. Only 1.7mm-deep outer annular edge reliefs at R10.8..13.4; original remains unchanged.')
report={'document':doc.name,'original_wrist_volume_mm3':before,'new_volume_mm3':body.volume*1000,
    'removed_mm3':before-body.volume*1000,'user_features_copied_as_geometry':[f.name for f in o.component.features],
    'relief_y_intervals_mm':[[-17.15,-15.45],[18.6,20.3]],'relief_radii_mm':[10.8,13.4],
    'source_occurrence_transform':list(o.transform2.asArray()),
    'main_wrist_unchanged':True,'original_servo_interface_on_base_unchanged':True}
with open(out+'/wrist_edge_relief.json','w',encoding='utf-8') as f: json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps(report,ensure_ascii=False,indent=2))
print('MODEL_EDIT_COMMANDS',[(c.id,c.name) for c in ui.commandDefinitions if 'モデル' in c.name and any(k in c.name for k in ('編集','終了'))])
