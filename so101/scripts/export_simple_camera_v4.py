"""Export two pieces; validate populated-PCB approach paths and the two bolts."""
from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
script=(ROOT/'scripts/export_selection_a_camera_v2.py').read_text()
script=script.replace('camera_mount_v2','camera_mount_v4').replace('print_camera_hx711_v2','print_camera_hx711_v4')
script=script.replace('V2','V4').replace('01_A_left_arm_frame_V4','01_simple_camera_HX711_bracket_V4')
script=script.replace('02_A_slot_inner_jaw_V4','02_A_slot_backing_V4').replace('SelectionA_Left','SelectionA_Simple')
script=script.replace('seated[:6]','seated[:len(cached)]')
script=script.replace('01_requested_left_view','01_selected_side_view').replace('02_clamp_and_left_beam','02_simple_bracket_side')
marker="(CHECK/'assembly_paths.json').write_text"
assert script.count(marker)==1
extra='''bolt_access=[]
hardware_occ=root.occurrences.itemByName('REFERENCE_M3_hardware_do_not_print:1')
for screw in hardware_occ.bRepBodies:
    if not screw.name.startswith('M3x10_A_'): continue
    for distance in (.1,1,3,7,10,15,30):
        bolt_access.append({'screw':screw.name,'outward_mm':distance,
            'printed_part_hits':collisions(translate(screw,(0,distance,0)),cached)})
assert len(bolt_access)==14 and not any(p['printed_part_hits'] for p in bolt_access),bolt_access
path_report['clamp_complete_bolt_insertion_before_PCB']=bolt_access
path_report['install_HX711_PCB_only_after_clamp_bolts_tightened']=True
pcb_approach=[]
for module,axis,preassemble in (
    ('REFERENCE_XIAO_Sense_1pc',tuple(build['camera_basis']['N']),False),
    ('REFERENCE_HX711_1pc',EY,False),('REFERENCE_TXS0108E_level_shifter_1pc',(0,-1,0),True)):
    occurrence=root.occurrences.itemByName(module+':1')
    obstacles=cached if preassemble else cached+existing
    for distance in (.1,1,3,5,10,20):
        hits=[]
        for b in occurrence.bRepBodies:
            hits += [[b.name,*r] for r in collisions(translate(b,scale(axis,distance)),obstacles)]
        pcb_approach.append({'module':module,'offset_mm':distance,'direction':axis,
            'before_mounting_to_robot':preassemble,'hits':hits})
assert not any(row['hits'] for row in pcb_approach),pcb_approach
path_report['populated_PCB_approach']=pcb_approach
path_report['hot_glue_required_for_PCB_retention']=True
'''
script=script.replace(marker,extra+marker)
target="    if name.startswith('02_'):"
replacement="""    if name.startswith('01_'):
        rows=(EX,(0,0,-1),EY); description='A contact face on bed; removable open support under PCB tray and angled camera ledge required'
    elif name.startswith('02_'):"""
assert script.count(target)==1
script=script.replace(target,replacement)
script=script.replace("'Selected A slot sandwich, left extension; original servo, wrist and load-cell interfaces unchanged. Prototype.'",
    "'Simple one-piece PCB support plus backing; two M3 bolts/nuts; hot glue PCB edges. Original interfaces unchanged. Prototype.'")
exec(compile(script,'export_simple_camera_v4','exec'),globals())
shutil.copy2(CHECK/'simplification_check.json',OUT/'checks/simplification_check.json')
preview('02_simple_bracket_side',(-120,140,105))
