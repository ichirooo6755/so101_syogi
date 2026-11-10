"""Revise the independent V7 prototype to clear the cartridge envelope."""
import adsk.core
import adsk.fusion
import json

root = '/Users/sugawaraichirou/Documents/ChatGPT/so101'
out = root + '/output/v7'
assert ui.activeCommand == 'SelectCommand'
doc = next(doc for doc in app.documents if doc.name == '部品１_V7_閉断面台座補強')
doc.activate()
ui.workspaces.itemById('FusionSolidEnvironment').activate()
d = adsk.fusion.Design.cast(app.activeProduct)
r = d.rootComponent
assert d.timeline.markerPosition == d.timeline.count
# Remove only our four prototype additions; the imported V6 history stays.
remove = [f for f in r.features if f.name.startswith('V7_')]
assert len(remove) == 4
for f in reversed(remove): assert f.deleteMe()
assert abs(r.bRepBodies.item(0).volume*1000 - 34383.20028727208) < 1e-4
namespace = {}
with open(root + '/scripts/fusion_shapes.py', encoding='utf-8') as f:
    exec(compile(f.read(), '<shapes>', 'exec'), namespace)
h = namespace['Shapes'](d)
# Solid 4 mm deep web below the existing closed upper box. Its X=50 face
# leaves 1 mm to the nominal X=51 cartridge envelope, unlike a 7 mm deep box.
h.box(r, 'V7_deep_web_clear_of_cartridge', 46, 50, -36.5, 35.5, 21, '14.5 mm')
h.box(r, 'V7_full_fixed_socket_undersupport', 47, 69.2, 23.46294620236,
      41.56294620236, 21, '18.5 mm')
s = h.sketch(r, 'V7_fixed_M3_access_revised', 20.9)
for y in (26.96294620236, 34.36294620236): h.circle(s, (62, y, 20.9), '6.2 mm')
h.extrude(r, s, '11.8 mm', h.CUT, 'V7_M3_head_access_original_seats')
body = r.bRepBodies.item(0)
body.name = 'V7_closed_upper_box_deep_web_full_socket_support'
assert r.bRepBodies.count == 1 and body.isSolid
assert all(int(f.healthState) == 0 for f in r.features)
t = adsk.fusion.TemporaryBRepManager.get()
copy = t.copy(body)
volume = body.volume*1000
assert doc.save('V7 prototype adjusted to maintain 1 mm cartridge envelope gap; deep web plus closed upper box')
simdoc = next(doc for doc in app.documents if doc.name.startswith('so101_V7_閉断面補強_筆圧検証'))
simdoc.activate()
ui.workspaces.itemById('FusionSolidEnvironment').activate()
sd = adsk.fusion.Design.cast(app.activeProduct)
occ = sd.rootComponent.occurrences.itemByName('base:1')
old = occ.component.bRepBodies.item(0)
material = old.material
assert old.deleteMe()
b = occ.component.bRepBodies.add(copy)
b.name = 'base'
b.material = material
entities = adsk.core.ObjectCollection.create()
for o in sd.rootComponent.occurrences:
    for b in o.bRepBodies: entities.add(b)
inp = sd.createInterferenceInput(entities)
inp.areCoincidentFacesIncluded = False
inter = sd.analyzeInterference(inp)
hits = [{'one': x.entityOne.name, 'two': x.entityTwo.name, 'mm3': x.interferenceBody.volume*1000} for x in inter]
assert not hits, hits
assert sd.exportManager.execute(sd.exportManager.createSTEPExportOptions(out+'/analysis/base.step', occ.component))
assert simdoc.save('V7 source body corrected; native static interference count zero')
with open(out+'/created.json', encoding='utf-8') as f: made = json.load(f)
made.update(base_volume_mm3=volume, healthy_features=r.features.count,
    static_interference_count=0, revision='Closed upper box with cartridge-clearing deep web',
    document_cloud_id=doc.dataFile.id, simulation_cloud_id=simdoc.dataFile.id)
with open(out+'/created.json', 'w', encoding='utf-8') as f: json.dump(made, f, ensure_ascii=False, indent=2)
with open(out+'/analysis/geometry_audit.json', encoding='utf-8') as f: audit=json.load(f)
audit['parts']['base']['volume_mm3'] = volume
with open(out+'/analysis/geometry_audit.json', 'w', encoding='utf-8') as f: json.dump(audit, f, ensure_ascii=False, indent=2)
print('V7 revised', volume, 'mm3; native interference:', inter.count)
print('Main assembly not edited')
