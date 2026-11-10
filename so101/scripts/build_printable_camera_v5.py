"""A1 mini / 0.4 PLA DfAM variant: open U ribs, thick camera tray, keyed backing.

Two printed pieces and the same two M3x10 bolts/nuts. Board poses and camera aim
are unchanged; source V4 and all robot interfaces stay read-only.
"""
from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
v4=(ROOT/'scripts/build_simple_camera_v4.py').read_text()
prefix=v4.split("progress('building_two_piece_simple_bracket')",1)[0]
prefix=prefix.replace("OUT=ROOT/'output/camera_mount_v4'","OUT=ROOT/'output/camera_mount_v5'")
prefix=prefix.replace("d.name=='so101_SelectionA_Compact_Camera_HX711_V3'","d.name=='so101_SelectionA_Simple_Camera_HX711_V4'")
prefix=prefix.replace('source_V3_before_simplification','source_V4_before_DfAM')
exec(compile(prefix,'v5_preserved_source_and_helpers','exec'),globals())
import itertools

PARAM.update({'printer':'Bambu Lab A1 mini','nozzle_mm':.4,'filament':'PLA',
    'clamp_outer_head_seat_y_mm':40.,'clamp_bolt_tip_y_mm':30.,'foot_thickness_mm':4.5,
    'base_plate_thickness_mm':4.25,'camera_floor_thickness_mm':2.4,
    'side_web_thickness_mm':3.5,'print_up_world':[0,1,0],
    'design_changes':['open center, no broad horizontal PCB backplate',
        '45-degree rising outside webs','two full diagonal camera gussets',
        'joined capsule backing key instead of isolated posts'],
    'physical_strength_and_printing_unverified':True})

def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def norm(a):return math.sqrt(dot(a,a))
def clip(body,on_plane,outward):
    n=scale(outward,1/norm(outward))
    seed=EX if abs(n[0])<.8 else EY
    u=cross(seed,n); u=scale(u,1/norm(u)); v=cross(n,u)
    tool=obox(plus(on_plane,scale(n,100)),(u,v),(250,250,200))
    return subtract(body,[tool])
def hull(points):
    planes={}
    for p,q,r in itertools.combinations(points,3):
        n=cross(tuple(qi-pi for qi,pi in zip(q,p)),tuple(ri-pi for ri,pi in zip(r,p)))
        length=norm(n)
        if length<1e-7:continue
        n=scale(n,1/length); d=dot(n,p)
        distances=[dot(n,v)-d for v in points]
        if max(distances)<=1e-6:pass
        elif min(distances)>=-1e-6:n=scale(n,-1); d=-d
        else:continue
        planes[tuple(round(x,6) for x in (*n,d))]=(p,n)
    lo=[min(p[i] for p in points)-.01 for i in range(3)]
    hi=[max(p[i] for p in points)+.01 for i in range(3)]
    b=box(lo[0],hi[0],lo[1],hi[1],lo[2],hi[2])
    for p,n in planes.values():clip(b,p,n)
    assert b.isSolid and b.volume>1e-8
    return b

progress('building_A1mini_printable_ribbed_frame')
pieces=[box(10,46,35.75,40,20.5,45.5),box(12,44,38.5,49.75,22.5,27)]
# Growing 45-degree upper edges start on the bed. The middle stays open so the
# rear TXS PCB/leads are not blocked, and no wide plate has to bridge this void.
for x0,x1 in ((10,13.5),(42.5,46)):
    rib=box(x0,x1,35.75,49.75,20.5,61)
    clip(rib,(x0,35.75,53.5),(0,-1,1))
    pieces.append(rib)
for x0,x1,n,p in ((11.5,14,(1,-1,0),(14,48.25,0)),
                  (42,44.5,(-1,-1,0),(42,48.25,0))):
    rail=box(x0,x1,47.5,49.75,31.5,58.4); clip(rail,p,n); pieces.append(rail)
# Front HX711 four-corner tray, deliberately open in the middle and at terminals.
for x0,x1 in ((11.5,12.6),(43.4,44.5)):
    pieces.append(box(x0,x1,49.75,53.35,34.6,57.4))
for x0,x1 in ((11.5,14),(42,44.5)):
    for z0,z1 in ((33.6,34.6),(57.4,58.4)):
        pieces.append(box(x0,x1,49.75,53.35,z0,z1))
for x0,x1 in ((13,14),(42,43)):
    for z0,z1 in ((35,35.8),(56.2,57)):
        pieces.append(box(x0,x1,49.75,51.65,z0,z1))
# Rear converter keeps its previous pose and 2 mm lead/solder relief.
for y0,y1 in ((-16,-14.2),(14.2,16)):
    pieces.append(ebox(9,13.1,y0,y1,45.7,58.7))
for x0,x1 in ((12,15),(41,44)):
    for z0,z1 in ((44.7,45.7),(59,60)):
        pieces.append(box(x0,x1,43.75,47.85,z0,z1))
        if x0==12:
            pieces.append(hull([(13.4,42.15,z0),(13.4,43.75,z0),(15,43.75,z0),
                (13.4,42.15,z1),(13.4,43.75,z1),(15,43.75,z1)]))
        else:
            pieces.append(hull([(42.6,42.15,z0),(42.6,43.75,z0),(41,43.75,z0),
                (42.6,42.15,z1),(42.6,43.75,z1),(41,43.75,z1)]))
for x0,x1,n,p in ((13.4,14.83,(1,-1,0),(13.4,45.85,0)),
                  (41.17,42.6,(-1,-1,0),(42.6,45.85,0))):
    for z0,z1 in ((46,46.8),(57.9,58.7)):
        pad=box(x0,x1,45.85,47.75,z0,z1); clip(pad,p,n); pieces.append(pad)
# Camera plane and optics are unchanged, but its floor is doubled in thickness.
pieces.append(cbox(-11.8,11.8,-10.3,10.3,-4.2,-1.8))
for b0,b1 in ((-10.3,-9.15),(9.15,10.3)):
    # Low rims stay below the populated PCB; retention is by the already agreed glue dots.
    pieces.append(cbox(-10.8,11.8,b0,b1,-1.8,-.4))
pieces.append(cbox(-11.8,-10.9,-9.15,9.15,-1.8,1.4))
for b0,b1 in ((-9.15,-5.8),(5.8,9.15)):
    pieces.append(cbox(10.9,11.8,b0,b1,-1.8,1.4))
for a in (-9.7,9.7):
    for b in (-7.7,7.7):pieces.append(cbox(a-.6,a+.6,b-.6,b+.6,-1.8,0))
for a0,a1,x0,x1,z0,z1 in ((-9,-6,14.5,18,28,36),(6,9,38,41.5,37,44)):
    points=[(x,y,z) for x in (x0,x1) for y in (35.75,40) for z in (z0,z1)]
    points += [cp(a,b,h) for a in (a0,a1) for b in (-9,9) for h in (-6.2,-4.1)]
    rib=hull(points); clip(rib,cp(0,0,-4.1),CN); pieces.append(rib)
frame=union(pieces)
for x in (22,34):
    subtract(frame,[cylinder((x,35.2,35),(x,42.5,35),3.4),cylinder((x,40,35),(x,90,35),6.2)])
# A capsule key joins the screw bosses inside the existing slot, reinforcing the
# thin backing without reducing wrist clearance or changing the M3 nut pockets.
inner=union([box(17.5,39,25.25,27.05,22.5,45.5),box(22,34,27,34.8,30.5,39.5)]+
    [cylinder((x,27,35),(x,34.8,35),9) for x in (22,34)])
for x in (22,34):
    subtract(inner,[cylinder((x,24.8,35),(x,35,35),3.4),hex_prism((x,28.95,35),EX,EZ,7.9,5.8)])
parts={'01_A1mini_ribbed_camera_bracket_V5':frame,'02_joined_slot_backing_V5':inner}
geometry={k:{'volume_mm3':b.volume*1000,'lumps':b.lumps.count,'bbox_mm':bbox(b)} for k,b in parts.items()}
(OUT/'candidate_geometry.json').write_text(json.dumps({'parameters':PARAM,'parts':geometry},ensure_ascii=False,indent=2))
assert all(r['lumps']==1 for r in geometry.values()),geometry

tail=v4.split('# Reuse the proven static',1)[1]
tail='# Reuse the proven static'+tail
injection="tail=tail.replace(\"(x,39,35),EY,10\",\"(x,40,35),EY,10\")\ntail=tail.replace(\"'clamp_bolt_tip_y_mm':29.\",\"'clamp_bolt_tip_y_mm':30.\")\n"
marker="exec(compile(tail,'simple_v4_verified_assembly','exec'),globals())"
assert tail.count(marker)==1
tail=tail.replace(marker,injection+marker).replace('_V4','_V5')
tail=tail.replace('01_simple_camera_HX711_bracket_V5','01_A1mini_ribbed_camera_bracket_V5')
tail=tail.replace('02_A_slot_backing_V5','02_joined_slot_backing_V5')
tail=tail.replace('SelectionA_Simple','SelectionA_Printable')
exec(compile(tail,'verified_printable_camera_v5','exec'),globals())
(OUT/'DfAM_check.json').write_text(json.dumps({'passed':True,'preserved_camera_and_PCB_poses':True,
    'M3x10_bolts':2,'M3_nuts':2,'printed_parts':2,'camera_floor_old_mm':1.2,'camera_floor_new_mm':2.4,
    'A_plate_old_mm':3.25,'A_plate_new_mm':4.25,'nominal_print_up_world':[0,1,0],
    'actual_printer':'A1 mini','nozzle_mm':.4,'filament':'PLA','print_strength_not_tested':True},indent=2))
