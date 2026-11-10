"""Short outward bracket toward the user's current V2 selection set 2.

Reuses the V2 temporary-BRep construction/check code with explicit, checked
layout substitutions. No existing V1/V2/source document is edited or overwritten.
"""
import adsk.core
import adsk.fusion
import json
from pathlib import Path

ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
OUT3=ROOT/'output/camera_mount_v3'; OUT3.mkdir(parents=True,exist_ok=True)
previous_doc=next(d for d in app.documents if d.name=='so101_SelectionA_Left_Camera_HX711_V2')
previous_design=adsk.fusion.Design.cast(previous_doc.products.itemByProductType('DesignProductType'))
direction_set=next(s for s in previous_design.selectionSets if s.name=='選択セット2')
direction_face=adsk.fusion.BRepFace.cast(list(direction_set.entities)[0]); assert direction_face
assert abs(direction_face.geometry.origin.y*10-42.75)<1e-6,'Reinspect the new direction if this selection changes'
direction_record={'document':previous_doc.name,'selection':'選択セット2',
    'plane_y_mm':direction_face.geometry.origin.y*10,'direction_from_A_world':[0,1,0],
    'reason':'Extend a short distance outward from A, not 60 mm along -X'}
def previous_fingerprint():
    return {'timeline':[previous_design.timeline.markerPosition,previous_design.timeline.count],
        'components':[(o.name,list(o.transform2.asArray()),o.isVisible,
            [(b.name,b.volume*1000) for b in o.bRepBodies]) for o in previous_design.rootComponent.occurrences],
        'sets':[(s.name,[e.entityToken for e in s.entities]) for s in previous_design.selectionSets]}
previous_before=previous_fingerprint()
backup=OUT3/'source_V2_with_selection_2_before_compaction.f3d'
if not backup.exists():
    assert previous_design.exportManager.execute(previous_design.exportManager.createFusionArchiveExportOptions(str(backup)))
(OUT3/'selection_2_direction.json').write_text(json.dumps(direction_record,ensure_ascii=False,indent=2))

source=(ROOT/'scripts/build_selection_a_left_camera_v2.py').read_text()
def change(old,new):
    global source
    assert source.count(old)==1,('Expected one template location',old,source.count(old))
    source=source.replace(old,new)
change("OUT=ROOT/'output/camera_mount_v2'", "OUT=ROOT/'output/camera_mount_v3'")
change("'attachment':'選択セットA / 部品１側面の既存長穴を内外2部品で挟む'",
       "'attachment':'選択セットAの既存長穴を挟み、選択セット2側へ短く張り出す'")
change("'extension_direction_world':[-1,0,0]", "'extension_direction_world':[0,1,0]")
change("'arm_bounds_mm':[[-64,35.75,21.5],[23,42.75,31.5]]",
       "'arm_bounds_mm':[[14,35.75,21.5],[42,49.75,31.5]]")
change("'board_module_center_x_mm':-45.", "'board_module_center_x_mm':28.")
change("'camera_pcb_origin_mm':[-45.,45.,10.], 'camera_down_angle_deg':30.,'camera_inward_yaw_deg':25.",
       "'camera_pcb_origin_mm':[28.,57.,10.], 'camera_aim':'toward assumed brush tip from actual reference lens position'")
change("yaw=math.radians(25); down=math.radians(30)\nCA=(math.sin(yaw),math.cos(yaw),0)\nCN=(math.cos(down)*math.cos(yaw),-math.cos(down)*math.sin(yaw),-math.sin(down))\nCB=tuple(vec(CA).crossProduct(vec(CN)).asArray())",
'''tip_aim=(62.,2.76294620236,-52.)
def unit(v):
    length=math.sqrt(sum(q*q for q in v)); return tuple(q/length for q in v)
CN=unit(tuple(a-b for a,b in zip(tip_aim,CO)))
for _ in range(20):
    CA=unit((-CN[1],CN[0],0))
    CB=tuple(vec(CA).crossProduct(vec(CN)).asArray())
    lateral=plus(scale(CA,6.9458413144),scale(CB,-.6386000446))
    CN=unit(tuple(t-c-l for t,c,l in zip(tip_aim,CO,lateral)))
CA=unit((-CN[1],CN[0],0)); CB=tuple(vec(CA).crossProduct(vec(CN)).asArray())
PARAM['camera_down_angle_deg']=math.degrees(math.asin(-CN[2]))
PARAM['camera_inward_yaw_deg']=math.degrees(math.atan2(-CN[1],CN[0]))''')
change("return (-45-y,22.75+x,z)", "return (28-y,34.75+x,z)")
change("frame=[box(17.5,39,35.75,39,22.5,45.5),box(-64,23,35.75,42.75,21.5,31.5)]",
       "frame=[box(17.5,39,35.75,39,22.5,45.5),box(14,42,35.75,49.75,21.5,31.5)]")
change("for y0,y1 in ((-14,-10),(10,14)): frame.append(ebox(13,15,y0,y1,30,35))",
       "for y0,y1 in ((-14,-8),(8,14)): frame.append(ebox(13,15,y0,y1,30,35))")
change("frame.append(cbox(-10.8,4,-13.5,-9,-4,-2))",
       "frame.append(cbox(-10.8,4,-17,-9,-5,-2))")
change("cuts=[box(-64.1,17.5,37.75,40.75,23.5,29.5)]",
       "cuts=[box(16,40,39,49.85,23.5,29.5)]")
change("for x in (22,34): cuts.append(cylinder((x,35.2,35),(x,42.5,35),3.4))",
       "for x in (22,34): cuts.append(cylinder((x,35.2,35),(x,42.5,35),3.4))\n"
       "# Install the clamp BEFORE the HX711 PCB: heads and driver pass through these two access openings.\n"
       "for x in (22,34): cuts.append(cylinder((x,39.1,35),(x,56,35),6.2))\n"
       "PARAM['clamp_head_and_tool_access_dia_mm']=6.2")
change("translation (-45,22.75,0)", "translation (28,34.75,0)")
source=source.replace('_V2','_V3').replace('01_A_left_arm_frame_V3','01_A_compact_outward_frame_V3')
source=source.replace('SelectionA_Left','SelectionA_Compact')
exec(compile(source,'build_compact_selection_2_v3','exec'),globals())
assert previous_fingerprint()==previous_before,'V2 user source changed while building'

# Carry the user's direction reference onto the compact beam's corresponding face.
new_frame=root.occurrences.itemByName('01_A_compact_outward_frame_V3:1')
outward_faces=[f for f in new_frame.component.bRepBodies.item(0).faces
    if f.geometry.surfaceType==adsk.core.SurfaceTypes.PlaneSurfaceType
    and abs(f.geometry.origin.y*10-49.75)<1e-6 and f.area*100>100]
assert outward_faces
face=max(outward_faces,key=lambda f:f.area)
design.selectionSets.add([face.createForAssemblyContext(new_frame)],'選択セット2_外側方向')
assert design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(archive)))
compact_report={'passed':True,'direction':direction_record,'previous_V2_preserved':True,
    'board_center_previous_mm':[-45.,40.55,46.], 'board_center_compact_mm':[28.,52.55,46.],
    'extension_beam_previous_length_mm':87.,'extension_beam_compact_outward_length_mm':14.,
    'approximate_frame_x_width_previous_mm':107.2,
    'frame_x_width_compact_mm':geometry['01_A_compact_outward_frame_V3']['bbox_mm'][1][0]-geometry['01_A_compact_outward_frame_V3']['bbox_mm'][0][0]}
(OUT/'compaction_check.json').write_text(json.dumps(compact_report,ensure_ascii=False,indent=2))
print(json.dumps(compact_report,ensure_ascii=False,indent=2))
