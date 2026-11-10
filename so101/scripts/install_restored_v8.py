"""Install reversible V8 manual baseline, leaving originals and all poses intact."""
import adsk.core
import adsk.fusion
import json
root='/Users/sugawaraichirou/Documents/ChatGPT/so101'; out=root+'/output/v8'
assert ui.activeCommand=='SelectCommand'
main=next(doc for doc in app.documents if doc.name=='so101書道')
main.activate()
d=adsk.fusion.Design.cast(main.products.itemByProductType('DesignProductType')); r=d.rootComponent
assert not d.attributes.itemByName('so101_calligraphy','restored_v8')
with open(out+'/clearance.json',encoding='utf-8') as f: checks=json.load(f)
assert checks['passed'] and len(checks['rotary_poses'])==73
assert [d.timeline.markerPosition,d.timeline.count]==checks['main_timeline']
base_doc=next(doc for doc in app.documents if doc.name=='部品１_V8_元取付形状保持')
wrist_doc=next(doc for doc in app.documents if doc.name=='Wrist_Roll_Clearance_V8_元取付対応')
assert base_doc.dataFile.isComplete and wrist_doc.dataFile.isComplete
expected={'部品１_V5_短縮補強_16mm:1':34383.2002872724,
    'Wrist_Roll_Clearance_V5:1':22072.992902446946,
    'Brush_Load_Carrier_Compact_V5:1':6573.7249355018075,
    'Brush_Cartridge_Symmetric_15mm_V5:1':6846.800123811137}
for n,v in expected.items():
    assert abs(max(b.volume*1000 for b in r.occurrences.itemByName(n).bRepBodies)-v)<.001,n
names=('SC616C_1kg_Fusion:1','Brush_Load_Carrier_Compact_V5:1','Brush_Cartridge_Symmetric_15mm_V5:1','Wrist_Roll_Clearance_V5:1','STS3215_c:1')
poses={n:list(r.occurrences.itemByName(n).transform2.asArray()) for n in names}
assert main.save('Checkpoint before V8 insertion; prior V6, original 部品１, and all user wrist edits retained.')
base=r.occurrences.addByInsert(base_doc.dataFile,adsk.core.Matrix3D.create(),True)
wrist=r.occurrences.addByInsert(wrist_doc.dataFile,adsk.core.Matrix3D.create(),True)
assert base and wrist
oldjoint=r.asBuiltJoints.itemByName('V6_fixed_sensor_to_short_yoke')
assert oldjoint and not oldjoint.isSuppressed
oldjoint.isSuppressed=True
pairs=[('V8_fixed_sensor_to_original_mount_yoke',base,r.occurrences.itemByName('SC616C_1kg_Fusion:1')),
    ('V8_free_sensor_to_unchanged_carrier',r.occurrences.itemByName('SC616C_1kg_Fusion:1'),r.occurrences.itemByName('Brush_Load_Carrier_Compact_V5:1')),
    ('V8_cartridge_to_captive_nut_carrier',r.occurrences.itemByName('Brush_Load_Carrier_Compact_V5:1'),r.occurrences.itemByName('Brush_Cartridge_Symmetric_15mm_V5:1'))]
for name,one,two in pairs:
    inp=r.asBuiltJoints.createInput(one,two,None); inp.setAsRigidJointMotion()
    j=r.asBuiltJoints.add(inp); j.name=name; j.isLightBulbOn=False
r.occurrences.itemByName('部品１_V5_短縮補強_16mm:1').isLightBulbOn=False
r.occurrences.itemByName('Wrist_Roll_Clearance_V5:1').isLightBulbOn=False
for n,prior in poses.items():
    after=list(r.occurrences.itemByName(n).transform2.asArray())
    assert max(abs(a-b) for a,b in zip(prior,after))<1e-9,(n,prior,after)
assert abs(base.bRepBodies.item(0).volume*1000-38550.50206478457)<.001
assert abs(wrist.bRepBodies.item(0).volume*1000-22025.213051512656)<.001
d.attributes.add('so101_calligraphy','restored_v8','Original inner diagonal servo interface copied without redesign; supported deep-web base, matching shallow-clearance wrist copy; original user wrist and V6 hidden, not deleted. Generative outcome not yet adopted.')
assert main.save('V8 manual reinforced baseline installed with original servo details and matching wrist relief; old parts preserved, brush/cell/carrier poses unchanged; generative job pending separately.')
report={'base_occurrence':base.name,'wrist_occurrence':wrist.name,'base_volume_mm3':base.bRepBodies.item(0).volume*1000,
    'wrist_volume_mm3':wrist.bRepBodies.item(0).volume*1000,'old_parts_hidden_not_deleted':True,
    'original_wrist_geometry_and_history_unchanged':True,'load_cell_rotation_and_translation_unchanged':True,
    'tool_pose_unchanged':True,'prior_poses':poses,'new_joints':[n for n,_,_ in pairs],
    'timeline_after':[d.timeline.markerPosition,d.timeline.count],'generative_outcome_adopted':False,
    'native_Fusion_V8_analysis':'submitted at 0 credits, result pending','local_FEA_8_cases_aluminum_and_steel_complete':True}
with open(out+'/installed.json','w',encoding='utf-8') as f: json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps(report,ensure_ascii=False,indent=2))
cam=app.activeViewport.camera; cam.viewOrientation=adsk.core.ViewOrientations.IsoTopRightViewOrientation
cam.isFitView=True; app.activeViewport.camera=cam; app.activeViewport.refresh()
