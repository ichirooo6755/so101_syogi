import adsk.core
import adsk.fusion
import json
import os

root='/Users/sugawaraichirou/Documents/ChatGPT/so101'; out=root+'/output/v6'
assert ui.activeCommand=='SelectCommand'
main=next(doc for doc in app.documents if doc.name=='so101書道')
source=next(doc for doc in app.documents if doc.name=='部品１_V5_短縮補強_16mm')
sd=adsk.fusion.Design.cast(source.products.itemByProductType('DesignProductType'))
assert sd.rootComponent.bRepBodies.count==1
assert abs(sd.rootComponent.bRepBodies.item(0).volume*1000-34383.2002872724)<1e-4
assert all(int(f.healthState)==0 for f in sd.rootComponent.features)
main.activate()
d=adsk.fusion.Design.cast(main.products.itemByProductType('DesignProductType')); r=d.rootComponent
assert not d.attributes.itemByName('so101_calligraphy','short_stiff_v6')
assert d.timeline.count-d.timeline.markerPosition==31
with open(root+'/tmp/v6_user_revision.json',encoding='utf-8') as f: prior=json.load(f)
old=next(x for x in prior['documents'] if x['name']=='so101書道')
for name in ('部品１_V5可動域改善:1','Wrist_Roll_Clearance_V5:1','Brush_Load_Carrier_Compact_V5:1','Brush_Cartridge_Symmetric_15mm_V5:1'):
    previous=next(o for o in old['occurrences'] if o['name']==name); live=r.occurrences.itemByName(name)
    assert abs(sum(b.volume*1000 for b in live.bRepBodies)-sum(b['volume_mm3'] for b in previous['bodies']))<1e-4,name
o=r.occurrences.addByInsert(source.dataFile,adsk.core.Matrix3D.create(),True)
assert o and o.bRepBodies.count==1
joint_names=('V5_sensor_fixed_end_to_yoke','V5_free_end_to_short_carrier','V5_cartridge_to_carrier')
for name in joint_names: r.asBuiltJoints.itemByName(name).isSuppressed=True
poses={}
for name in ('SC616C_1kg_Fusion:1','Brush_Load_Carrier_Compact_V5:1','Brush_Cartridge_Symmetric_15mm_V5:1'):
    occ=r.occurrences.itemByName(name); matrix=occ.transform2
    poses[name]={'before':list(matrix.asArray())}
    v=matrix.translation; v.x-=1.6; matrix.translation=v; occ.transform2=matrix
    poses[name]['after']=list(occ.transform2.asArray())
if d.snapshots.hasPendingSnapshot: d.snapshots.add().name='V6_translate_tool_16mm_toward_wrist'
for name in joint_names[1:]: r.asBuiltJoints.itemByName(name).isSuppressed=False
cell=r.occurrences.itemByName('SC616C_1kg_Fusion:1')
ji=r.asBuiltJoints.createInput(o,cell,None); ji.setAsRigidJointMotion()
j=r.asBuiltJoints.add(ji); j.name='V6_fixed_sensor_to_short_yoke'; j.isLightBulbOn=False
r.occurrences.itemByName('部品１_V5可動域改善:1').isLightBulbOn=False
d.userParameters.add('v6_tool_translation_x',adsk.core.ValueInput.createByString('-16 mm'),'mm','Tool occurrence translation, no sensor rotation')
d.userParameters.add('v6_brush_axis_x',adsk.core.ValueInput.createByString('v5_brush_axis_x + v6_tool_translation_x'),'mm','Current brush and sensor X center')
d.attributes.add('so101_calligraphy','short_stiff_v6','16 mm shorter; 26x8 rounded-window rails; low box tie; broad under-socket gusset; user wrist preserved')
assert d.timeline.count-d.timeline.markerPosition==31
report={'base_occurrence':o.name,'base_volume_mm3':o.bRepBodies.item(0).volume*1000,
        'previous_base_volume_mm3':29688.678172181015,'brush_axis_mm':[62,d.userParameters.itemByName('sc_brush_axis_y').value*10],
        'tool_translation_from_V5_mm':[-16,0,0],'load_cell_orientation_unchanged':True,
        'rail_span_mm':56,'previous_rail_span_mm':74,'rail_section_mm':[8,26],
        'previous_rail_section_mm':[4,22],'poses':poses,'user_wrist_kept':True,
        'future_timeline_features':31,'generative_design_used':False,'native_FEA_complete':False,
        'independent_editable_component':source.name,'independent_cloud_id':source.dataFile.id}
with open(out+'/created.json','w',encoding='utf-8') as f: json.dump(report,f,ensure_ascii=False,indent=2)
app.activeViewport.refresh()
print(json.dumps(report,ensure_ascii=False,indent=2))
