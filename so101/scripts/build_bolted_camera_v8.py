"""V8 replaces the cut-through socket and snap arms with bolted flat parts.

The V7 design is read as a template only; a new document and output are made.
"""
from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
script=(ROOT/'scripts/build_stack_camera_v7.py').read_text()
script=script.replace('camera_mount_v7','camera_mount_v8').replace('_V7','_V8').replace('V7_assembly','V8_assembly')
script=script.replace("PARAM.update({'printed_piece_count':6", "PARAM.update({'printed_piece_count':5")
script=script.replace("'board_retention':'sliding rigid rails, removable printed end cap with two deflecting PLA arms; no glue'", "'board_retention':'sliding rigid rails with removable bolted rigid end plate; no glue'")
script=script.replace("'camera_retention':'rigid edge rails and removable snap-in side key'", "'camera_retention':'rigid bolted tongue, two M3 through bolts and nuts'")
start=script.index('# The only robot fasteners')
end=script.index('geometry={k:',start)
new=r'''
# Full rectangular bolt-bearing plate: no open slit crosses either M3 hole.
back=cbox(-11,11,11,27,-8.5,-5.25)
anchor=[(x,y,z) for x in (28,38) for y in (35.75,38.5) for z in (18.5,37.5)]
main=union([box(17.5,43.5,35.75,42,20.5,45.5),hull(anchor+vertices(back)),back,
    cbox(-11,11,14,23,-11.5,-8.5)])
subtract(main,[cbox(-20,20,-25,13.8,-40,4),cbox(-10.3,10.3,13.8,24.8,-5.20,4)])
inner=union([box(17.5,39,25.25,27.05,22.5,45.5),box(22,34,27,34.8,30.5,39.5)]+
    [cylinder((x,27,35),(x,34.8,35),9) for x in (22,34)])
for x in (22,34):
    subtract(main,[cylinder((x,35,35),(x,44,35),3.4),cylinder((x,42,35),(x,90,35),6.2)])
    subtract(inner,[cylinder((x,24.8,35),(x,35,35),3.4),hex_prism((x,28.95,35),EX,EZ,7.9,5.8)])
for a in (-6,6):
    subtract(main,[ccyl(a,18,-14,4,3.4),ccyl(a,18,-.8,9,6.2),
        hex_prism(cp(a,18,-10.3),CA,CB,2.5,5.8)])

# XIAO tray: open header windows, rails and a broad two-bolt tongue.
tray_pieces=[cbox(-11.8,11.8,-10.3,10.3,-3.4,-1),cbox(-10,10,9.8,24.5,-3.4,-.8),
    cbox(-10,10,14,24.5,-5,-3.4),
    cbox(-11.8,10.3,-2.8,2.8,-4.3,-3.4),cbox(-11.8,10.3,-4.2,4.2,-6.1,-4.3)]
for b0,b1 in ((-10.3,-9.15),(9.15,10.3)):
    tray_pieces += [cbox(-11.8,10.7,b0,b1,-1,.6),cbox(-11.8,-8.8,b0,b1,.6,3)]
for b0,b1 in ((-9.15,-8.1),(8.1,9.15)):
    tray_pieces.append(cbox(-10.8,-8.8,b0,b1,1.55,2.85))
tray_pieces.append(cbox(-11.8,-10.75,-9.15,9.15,-1,1.4))
for a in (-8.5,8.5):
    for b in (-4.4,4.4):tray_pieces.append(cbox(a-.6,a+.6,b-.6,b+.6,-1,0))
tray=union(tray_pieces)
subtract(tray,[cbox(10.5,13,5.4,12.6,-1.1,3.1),cbox(9.3,12.1,5.4,11,-4,0),
    cbox(-9.4,12.5,6.05,9.2,-7,0.05),cbox(-9.4,12.5,-9.2,-6.05,-7,0.05)]+
    [ccyl(a,18,-5.1,3.5,3.4) for a in (-6,6)])

# Two-board cassette: broad, rigid bolt lugs replace the fragile snap arms.
frame_pieces=[cbox(-16.5,15.24,-13.5,-11.68,-33.3,-6.4),
    cbox(-16.5,15.24,11.68,13.5,-33.3,-6.4),cbox(-16.5,-15.49,-13.5,13.5,-33.3,-6.4),
    cbox(-16.5,-12.05,-13.5,13.5,-8.8,-6.4),cbox(-16.5,-12.05,-4.5,4.5,-6.4,-4.05),
    cbox(-12.05,15.24,-5.8,5.8,-8.8,-6.4)]
for b0,b1 in ((-5.8,-4.45),(4.45,5.8)):
    frame_pieces.append(cbox(-12.1,15.24,b0,b1,-6.4,-3.65))
for b0,b1 in ((-4.5,-3.3),(3.3,4.5)):
    frame_pieces.append(cbox(-12.1,15.24,b0,b1,-4.10,-3.65))
for z0,z1 in ((-23.1,-21.5),(-31.6,-30.0)):
    for b0,b1 in ((-11.68,-10.8),(10.8,11.68)):
        frame_pieces += [cbox(-15.49,15.24,b0,b1,z0-1.05,z0-.25),
                         cbox(-15.49,15.24,b0,b1,z1+.25,z1+1.3)]
for b0,b1 in ((13.4,20.2),(-20.2,-13.4)):
    frame_pieces.append(cbox(5,15.24,b0,b1,-28,-20))
frame=union(frame_pieces)
subtract(frame,[cbox(-12,8.5,-13.7,-11.5,-19,-14),cbox(-12,8.5,-13.7,-11.5,-28,-24.5)])
for b in (-16.4,16.4):
    subtract(frame,[cylinder(cp(4,b,-24),cp(16,b,-24),3.4),
        hex_prism(cp(7.2,b,-24),CB,CN,2.5,5.8),
        cbox(5.9,8.5,min(b,(-21 if b<0 else b)),max(b,(21 if b>0 else b)),-27.4,-20.6)])
cap=union([cbox(15.49,17.49,-13.5,13.5,-33.3,-6.4),
    cbox(10.55,17.49,-2.6,2.6,-6.1,-4.3),cbox(15.49,17.49,-2.6,2.6,-7.5,-4.3),
    cbox(15.49,17.49,13.5,20.2,-28,-20),cbox(15.49,17.49,-20.2,-13.5,-28,-20)])
for b in (-16.4,16.4):subtract(cap,[cylinder(cp(15,b,-24),cp(18,b,-24),3.4)])
parts={'01_bolted_mount_V8':main,'02_slot_backing_V8':inner,
    '03_XIAO_header_tray_V8':tray,'04_HX711_perf_stack_V8':frame,'05_bolted_end_plate_V8':cap}
'''
script=script[:start]+new+script[end:]
marker="items=[(k,b,geometry[k]['bbox_mm']) for k,b in parts.items()]"
hardware=r'''
for a in (-6,6):
    head=cylinder(cp(a,18,-.8),cp(a,18,2.2),5.5)
    screw=union([head,cylinder(cp(a,18,-12.8),cp(a,18,-.8),3)])
    hardware.append((f'M3x12_tray_{a}',screw,bbox(screw)));seats.append((f'M3x12_tray_{a}',head,CN))
    nut=hex_prism(cp(a,18,-10.3),CA,CB,2.4,5.5)
    subtract(nut,[ccyl(a,18,-12,-8.5,3.1)])
    hardware.append((f'M3_nut_tray_{a}',nut,bbox(nut)))
for b in (-16.4,16.4):
    head=cylinder(cp(17.49,b,-24),cp(20.49,b,-24),5.5)
    screw=union([head,cylinder(cp(5.49,b,-24),cp(17.49,b,-24),3)])
    hardware.append((f'M3x12_cap_{b}',screw,bbox(screw)));seats.append((f'M3x12_cap_{b}',head,CA))
    nut=hex_prism(cp(7.2,b,-24),CB,CN,2.4,5.5)
    subtract(nut,[cylinder(cp(5.5,b,-24),cp(8.9,b,-24),3.1)])
    hardware.append((f'M3_nut_cap_{b}',nut,bbox(nut)))
'''
assert marker in script;script=script.replace(marker,hardware+'\n'+marker)
script=script.replace("'stock':{'M3x12':2,'M3_nut':2}","'stock':{'M3x12':6,'M3_nut':6}")
script=script.replace("'hardware':{'M3x12':2,'M3_hex_nut':2}","'hardware':{'M3x12':6,'M3_hex_nut':6}")
exec(compile(script,'bolted_camera_v8','exec'),globals())
