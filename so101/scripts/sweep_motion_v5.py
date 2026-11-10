"""Read-only BRep rotary sweep; no occurrence is moved in the user's design."""
import adsk.core
import adsk.fusion
import json
import math
import os

root = '/Users/sugawaraichirou/Documents/ChatGPT/so101'
d = adsk.fusion.Design.cast(app.activeProduct)
r = d.rootComponent
tmp = adsk.fusion.TemporaryBRepManager.get()
out = root + '/output/v5'
os.makedirs(out, exist_ok=True)
moving_names = ['部品１:1', 'Brush_Load_Carrier_Centered:1', 'Brush_Cartridge_Centered_15mm:1']
moving = [(n, r.occurrences.itemByName(n).bRepBodies.item(0)) for n in moving_names]
sensor = next(o for o in r.allOccurrences if o.fullPathName.startswith('SC616C_1kg_Fusion:1+') and o.bRepBodies.count)
moving.append(('SC616C', sensor.bRepBodies.item(0)))
fixed = []
axes = {}
for o in r.allOccurrences:
    if not o.isVisible:
        continue
    if o.name == '部品１:1' or o.name.startswith('Wrist_Roll') or o.fullPathName in ('STS3215_c:1+Top:1', 'STS3215_c:1+Bottom:1'):
        rows = []
        for b in o.bRepBodies:
            for f in b.faces:
                g = f.geometry
                if isinstance(g, adsk.core.Cylinder) and abs(g.axis.y) > .99 and g.radius * 10 > 2:
                    row = [round(g.origin.x * 10, 7), round(g.origin.z * 10, 7), round(g.radius * 20, 5)]
                    if row not in rows:
                        rows.append(row)
        axes[o.fullPathName] = rows
    if o.fullPathName.startswith('Wrist_Roll_Follower_SO101 v1:3') or (o.fullPathName.startswith('STS3215_c:1+') and '+Axes:' not in o.fullPathName):
        for b in o.bRepBodies:
            if b.isSolid and b.volume > 1e-6:
                fixed.append((o.fullPathName + '/' + b.name, tmp.copy(b)))
def intersects(a, b):
    if not a.boundingBox.intersects(b.boundingBox):
        return 0.0
    c = tmp.copy(a)
    if not tmp.booleanOperation(c, b, adsk.fusion.BooleanTypes.IntersectionBooleanType):
        raise RuntimeError('BRep intersection failed')
    return c.volume * 1000

center = [-1.622628494696552, 2.7629462023601, 33.8955681132288]
def check(angle):
    matrix = adsk.core.Matrix3D.create()
    matrix.setToRotation(math.radians(angle), adsk.core.Vector3D.create(0, 1, 0),
                         adsk.core.Point3D.create(*(v / 10 for v in center)))
    hits = []
    for name, b in moving:
        b = tmp.copy(b)
        assert tmp.transform(b, matrix)
        for obstacle, fb in fixed:
            v = intersects(b, fb)
            if v > .01:
                hits.append({'moving': name, 'fixed': obstacle, 'volume_mm3': round(v, 5)})
    return {'angle_deg': angle, 'hits': hits}

rows = [check(a) for a in range(-180, 181, 5)]
limits = []
for direction in (-1, 1):
    first = next((abs(row['angle_deg']) for row in (rows if direction > 0 else reversed(rows))
                  if row['angle_deg'] * direction > 0 and row['hits']), None)
    if first is None:
        limits.append(None)
        continue
    lo, hi = max(0, first - 5), first
    for _ in range(7):
        mid = (lo + hi) / 2
        if check(mid * direction)['hits']:
            hi = mid
        else:
            lo = mid
    limits.append({'sign': direction, 'first_collision_deg': hi * direction,
                   'last_clear_deg': lo * direction, 'collision': check(hi * direction)['hits']})
result = {'type': 'read_only_native_temporary_BRep_sweep', 'rotation_axis_world': [0, 1, 0],
          'axis_origin_mm': center, 'axis_candidates_x_z_diameter_mm': axes,
          'fixed_obstacles_count': len(fixed), 'brush_shaft_included': False,
          'collision_threshold_mm3': .01, 'near_zero_connected_interval_limits': limits, 'sweep': rows}
path = out + '/motion_before.json'
assert not os.path.exists(path)
with open(path, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(json.dumps({k: v for k, v in result.items() if k != 'sweep'}, ensure_ascii=False, indent=2))
