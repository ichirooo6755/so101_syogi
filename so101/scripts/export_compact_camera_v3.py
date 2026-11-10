"""Export the short Selection 2-side variant; V1 and V2 releases stay intact."""
from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
script=(ROOT/'scripts/export_selection_a_camera_v2.py').read_text()
script=script.replace('camera_mount_v2','camera_mount_v3').replace('print_camera_hx711_v2','print_camera_hx711_v3')
script=script.replace('V2','V3').replace('01_A_left_arm_frame_V3','01_A_compact_outward_frame_V3')
script=script.replace('SelectionA_Left','SelectionA_Compact')
script=script.replace('01_requested_left_view','01_selected_side_view').replace('02_clamp_and_left_beam','02_compact_clamp_side')
marker="(CHECK/'assembly_paths.json').write_text"
assert script.count(marker)==1
check='''# Both complete bolts must pass the backplate BEFORE any PCB is fitted.
bolt_access=[]
hardware_occ=root.occurrences.itemByName('REFERENCE_M3_hardware_do_not_print:1')
for screw in hardware_occ.bRepBodies:
    if not screw.name.startswith('M3x10_A_'): continue
    for distance in (.1,1,3,7,10,15,30):
        q=translate(screw,(0,distance,0))
        bolt_access.append({'screw':screw.name,'outward_mm':distance,'printed_part_hits':collisions(q,cached)})
assert len(bolt_access)==14 and not any(p['printed_part_hits'] for p in bolt_access),bolt_access
path_report['clamp_complete_bolt_insertion_before_PCB']=bolt_access
path_report['install_HX711_PCB_only_after_clamp_bolts_tightened']=True
'''
script=script.replace(marker,check+marker)
exec(compile(script,'export_compact_camera_v3','exec'),globals())
for name in ('compaction_check.json','selection_2_direction.json'):
    shutil.copy2(CHECK/name,OUT/'checks'/name)
preview('02_compact_clamp_side',(-120,140,105))
