import adsk.core
import adsk.fusion
d=adsk.fusion.Design.cast(app.activeProduct); r=d.rootComponent
assert app.activeDocument.name=='so101書道'
assert not d.attributes.itemByName('so101_calligraphy','motion_v5')
o=r.occurrences.itemByName('部品１_V5可動域改善:1')
assert o and o.component.features.count==9
volumes=sorted(b.volume*1000 for b in o.bRepBodies)
assert len(volumes)==2
assert max(abs(a-b) for a,b in zip(volumes,[5999.499490560685,24077.4953367611]))<1e-5
assert o.deleteMe()
for name in ('v5_brush_stop_z','v5_brush_axis_x','v5_brush_sleeve_length','v5_cartridge_flange_z','v5_rotary_axis_x','v5_rotary_axis_z'):
    assert d.userParameters.itemByName(name).deleteMe(),name
print('Removed only the verified incomplete V5 prototype and its unused new parameters; source parts unchanged.')
