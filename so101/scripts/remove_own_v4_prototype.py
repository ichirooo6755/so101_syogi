"""Remove only our just-created, unverified trial replacement components."""
import adsk.core
import adsk.fusion
import json
root='/Users/sugawaraichirou/Documents/ChatGPT/so101'
with open(root+'/tmp/v4_created.json',encoding='utf-8') as f: trial=json.load(f)
d=adsk.fusion.Design.cast(app.activeProduct); r=d.rootComponent
targets=[r.occurrences.itemByName(name) for name in trial['part_volumes_mm3']]
assert all(targets)
for o in targets:
    assert abs(o.bRepBodies.item(0).volume*1000-trial['part_volumes_mm3'][o.name])<1e-5,('trial was edited',o.name)
assert abs(r.occurrences.itemByName('部品１:1').bRepBodies.item(0).volume*1000-trial['base_volume_mm3'])<1e-5
for name in ('V4_centered_cartridge_to_carrier','V4_sensor_to_centered_carrier'):
    j=r.asBuiltJoints.itemByName(name)
    assert j and j.deleteMe()
for o in reversed(targets): assert o.deleteMe()
tag=d.attributes.itemByName('so101_calligraphy','centered_v4')
assert tag and tag.deleteMe()
print('Removed only the two unverified V4 trial components; source parts and user base edits retained.')
