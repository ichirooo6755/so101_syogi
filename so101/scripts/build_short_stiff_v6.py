import adsk.core
import adsk.fusion
import importlib.util
import json
import math
import os

root='/Users/sugawaraichirou/Documents/ChatGPT/so101'; out=root+'/output/v6'
doc=next(doc for doc in app.documents if doc.name=='so101書道')
assert ui.activeCommand=='SelectCommand','Leave any active editing command untouched'
assert doc.activate()
d=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType')); r=d.rootComponent
assert not d.attributes.itemByName('so101_calligraphy','short_stiff_v6')
assert d.timeline.count-d.timeline.markerPosition==31
with open(root+'/tmp/v6_user_revision.json',encoding='utf-8') as f: before=json.load(f)
prev=next(x for x in before['documents'] if x['name']=='so101書道')
for name in ('部品１_V5可動域改善:1','Wrist_Roll_Clearance_V5:1','Brush_Load_Carrier_Compact_V5:1','Brush_Cartridge_Symmetric_15mm_V5:1'):
    old=next(o for o in prev['occurrences'] if o['name']==name); live=r.occurrences.itemByName(name)
    assert abs(sum(b.volume*1000 for b in live.bRepBodies)-sum(b['volume_mm3'] for b in old['bodies']))<1e-4,name
assert os.path.exists(root+'/reference/so101_before_user_requested_shortening_v6.f3d')
spec=importlib.util.spec_from_file_location('so101_fusion_shapes',root+'/scripts/fusion_shapes.py')
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); h=module.Shapes(d)
cx=62.; cy=d.userParameters.itemByName('sc_brush_axis_y').value*10
o,c=h.component('部品１_V5_短縮補強')
h.cylinder_y(c,'V6_negative_horn_pad',-2,34,-36.5,-17.05,'26 mm',h.NEW)
h.box(c,'V6_deep_negative_rail',-2,54,-36.5,-28.5,21,'26 mm')
h.box(c,'V6_low_box_crossmember',47,54,-36.5,35.5,35.5,'11.5 mm')
h.box(c,'V6_deep_positive_rail',-2,54,27.5,35.5,21,'26 mm')
h.cylinder_y(c,'V6_positive_horn_pad',-2,34,20.2,35.5,'26 mm')
# Broad support under the fixed end, not a thin side-wall overlap.
h.box(c,'V6_full_width_under_socket_gusset',47,69.2,27.5,35.5,21,'18.5 mm')
h.box(c,'V6_fixed_cell_floor',54.8,69.2,23.46294620236,41.56294620236,29.5,'10 mm')
for x0,x1 in ((54.8,57.3),(66.7,69.2)):
    h.box(c,'V6_fixed_socket_wall_'+str(x0),x0,x1,23.46294620236,41.56294620236,39.5,'10 mm')
h.box(c,'V6_fixed_socket_roof',54.8,69.2,27.46294620236,41.56294620236,45.9,'3.6 mm')
h.box(c,'V6_fixed_socket_end_stop',57.3,66.7,38.86294620236,41.56294620236,39.5,'6.4 mm')
# Rounded lightening slots retain 5 mm upper/lower chords and 8 mm depth.
for name,y0,y1 in [('negative',-36.6,-28.4),('positive',27.4,35.6)]:
    h.capsule_cut_y(c,'V6_rounded_rail_window_'+name,11,44,26,42,y0,y1)
# Closed box tie: retain 2 mm side walls and 2.5/3 mm top/bottom skin.
s=h.sketch(c,'V6_box_beam_core',-28.5,'XZ')
h.polygon(s,[(49,-28.5,38),(52,-28.5,38),(52,-28.5,44.5),(49,-28.5,44.5)])
h.extrude(c,s,'56 mm',h.CUT,'V6_box_beam_hollow_core')
for side,y0,y1 in [('negative',-36.5,-17.05),('positive',20.2,35.5)]:
    h.cylinder_y(c,'V6_'+side+'_central_key',-2,34,y0-.1,y1+.1,'6.5 mm',h.CUT)
    if side=='negative':
        h.cylinder_y(c,'V6_negative_center_head_relief',-2,34,-18.9,-17.0,'8 mm',h.CUT)
        h.cylinder_y(c,'V6_fixed_boss_clearance',-2,34,-18.2,-17.0,'11 mm',h.CUT)
    else:
        h.cylinder_y(c,'V6_positive_center_head_relief',-2,34,20.1,22.2,'8 mm',h.CUT)
    s=h.sketch(c,'V6_'+side+'_horn_M3',y0-.1,'XZ')
    for a in range(4): h.circle(s,(-2+7*math.cos(a*math.pi/2),y0-.1,34+7*math.sin(a*math.pi/2)),'3.2 mm')
    h.extrude(c,s,f'{y1-y0+.2:.10f} mm',h.CUT,'V6_'+side+'_M3_shanks')
    start,end=(-36.6,-27.) if side=='negative' else (28.,35.6)
    s=h.sketch(c,'V6_'+side+'_head_recesses',start,'XZ')
    for a in range(4): h.circle(s,(-2+7*math.cos(a*math.pi/2),start,34+7*math.sin(a*math.pi/2)),'6.2 mm')
    h.extrude(c,s,f'{end-start:.10f} mm',h.CUT,'V6_'+side+'_deep_M3_heads')
for diameter,depth,label in [('sc_screw_clearance','10 mm','clearance'),('sc_head_dia','sc_head_depth','heads')]:
    s=h.sketch(c,'V6_fixed_M3_'+label,29.5)
    for yy in (26.96294620236,34.36294620236): h.circle(s,(cx,yy,29.5),diameter)
    h.extrude(c,s,depth,h.CUT,'V6_fixed_M3_'+label)
c.bRepBodies.item(0).name='V6_short_deep_rails_closed_tie_supported_socket'
assert c.bRepBodies.count==1 and c.bRepBodies.item(0).isSolid

# Move the sensor and its two moving printed parts together, with no rotation.
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
d.userParameters.add('v6_tool_translation_x',h.vi('-16 mm'),'mm','V6 occurrence translation; cell and brush remain in the same load plane')
d.userParameters.add('v6_brush_axis_x',h.vi('v5_brush_axis_x + v6_tool_translation_x'),'mm','Current assembled brush and cell center X')
d.attributes.add('so101_calligraphy','short_stiff_v6','16 mm shorter; 26x8 rounded-window rails; low box tie; broad under-socket gusset; wrist user edits preserved')
assert d.timeline.count-d.timeline.markerPosition==31
report={'base_occurrence':o.name,'base_volume_mm3':c.bRepBodies.item(0).volume*1000,
        'previous_base_volume_mm3':29688.678172181015,'brush_axis_mm':[cx,cy],
        'tool_translation_from_V5_mm':[-16,0,0],'load_cell_orientation_unchanged':True,
        'rail_span_mm':56,'previous_rail_span_mm':74,'rail_section_mm':[8,26],
        'previous_rail_section_mm':[4,22],'rounded_window_mm':[33,16],
        'box_tie_outer_section_mm':[7,11.5],'box_tie_void_section_mm':[3,6.5],
        'poses':poses,'user_wrist_kept':True,'future_timeline_features':31,
        'generative_design_used':False,'native_FEA_complete':False}
os.makedirs(out,exist_ok=True)
with open(out+'/created.json','w',encoding='utf-8') as f: json.dump(report,f,ensure_ascii=False,indent=2)
app.activeViewport.refresh()
print(json.dumps(report,ensure_ascii=False,indent=2))
