"""Restore only the v2 carrier nut pockets; keep all current base/lid edits."""
import adsk.core
import adsk.fusion
import json
import os

root='/Users/sugawaraichirou/Documents/ChatGPT/so101'
d=adsk.fusion.Design.cast(app.activeProduct)
doc=app.activeDocument
assert doc.name=='so101書道'
r=d.rootComponent
o=r.occurrences.itemByName('Brush_Load_Carrier:1')
c=o.component
marker=d.timeline.markerPosition
count=d.timeline.count
with open(root+'/output/v2/verification.json') as f: original=json.load(f)
other_names=('部品１:1','Brush_Cartridge_15mm:1','SC616C_Slide_In_Top_Cover:1')
others={name:{'volume_mm3':r.occurrences.itemByName(name).bRepBodies.item(0).volume*1000,
              'transform':list(r.occurrences.itemByName(name).transform2.asArray()),
              'visible':r.occurrences.itemByName(name).isLightBulbOn}
        for name in other_names}
cell_transform=list(r.occurrences.itemByName('SC616C_1kg_Fusion:1').transform2.asArray())
targets=[f for f in c.features.threadFeatures if f.name.startswith('V3_cartridge_M3x0p5_modeled')]
targets += [f for f in c.features.extrudeFeatures if f.name.startswith(('V3_cartridge_thread_pilots','V3_replace_nut_pocket_'))]
assert len(targets)==4,[(f.name,f.isSuppressed) for f in targets]
assert len([f for f in c.features.extrudeFeatures if f.name.startswith('M3_captive_nut_pockets')])==1
checkpoint=root+'/reference/so101_before_restoring_carrier_nut_pockets.f3d'
if not os.path.exists(checkpoint):
    assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(checkpoint))

# Suppression is reversible and leaves the original nut-pocket features intact.
# Do not move the timeline marker: later rolled-out user features must stay so.
for f in sorted(targets,key=lambda f:f.timelineObject.index,reverse=True):
    if not f.isSuppressed: f.isSuppressed=True
    assert f.isSuppressed,f.name
assert d.timeline.markerPosition==marker and d.timeline.count==count
b=o.bRepBodies.item(0)
assert b.isSolid and c.bRepBodies.count==1
expected=original['part_volumes_mm3'][o.name]
assert abs(b.volume*1000-expected)<1e-4,(b.volume*1000,expected)

holes=[]; hex_faces=[]
for face in b.faces:
    g=face.geometry
    if isinstance(g,adsk.core.Cylinder) and abs(g.axis.z)>.99 and abs(g.radius*20-3.4)<1e-5 and abs(g.origin.x*10-50)<1e-5:
        holes.append({'x_mm':g.origin.x*10,'y_mm':g.origin.y*10,
                      'z_mm':[face.boundingBox.minPoint.z*10,face.boundingBox.maxPoint.z*10]})
    if isinstance(g,adsk.core.Plane) and abs(g.normal.z)<1e-7 and abs(face.boundingBox.minPoint.z*10-15.9)<1e-5 and abs(face.boundingBox.maxPoint.z*10-18.5)<1e-5:
        hex_faces.append(face)
assert len(holes)==2,holes
assert len(hex_faces)==12,len(hex_faces)
for h in holes:
    assert abs(h['z_mm'][0]-12.5)<1e-5 and abs(h['z_mm'][1]-15.9)<1e-5,h
assert abs(d.userParameters.itemByName('brush_nut_af').value*10-5.8)<1e-6
assert abs(d.userParameters.itemByName('brush_nut_depth').value*10-2.6)<1e-6
for f in c.features.extrudeFeatures:
    if not f.isSuppressed: assert int(f.healthState)==0,(f.name,f.errorOrWarningMessage)
assert all(f.isSuppressed for f in c.features.threadFeatures)
for name,old in others.items():
    other=r.occurrences.itemByName(name)
    assert abs(other.bRepBodies.item(0).volume*1000-old['volume_mm3'])<1e-4,name
    assert max(abs(a-b) for a,b in zip(other.transform2.asArray(),old['transform']))<1e-9,name
    assert other.isLightBulbOn==old['visible'],name
assert max(abs(a-b) for a,b in zip(r.occurrences.itemByName('SC616C_1kg_Fusion:1').transform2.asArray(),cell_transform))<1e-9
b.name='Brush_Load_Carrier_M3_Captive_Nuts_FDM'
d.attributes.add('so101_calligraphy','carrier_retention','Restored v2: 2 M3 hex nut pockets AF5.8 depth2.6; phi3.4 clearance; printed threads suppressed')
assert doc.save('Restore carrier M3 captive hex nut pockets only; retain current base and cover geometry')
report={'restored':True,'part':o.name,'M3_nut_pockets':2,'nut_AF_mm':5.8,'nut_pocket_depth_mm':2.6,
        'clearance_diameter_mm':3.4,'screws':'2x M3x10 + 2x standard M3 hex nuts',
        'suppressed_features':[f.name for f in targets],
        'carrier_volume_mm3':b.volume*1000,'matches_v2_carrier_volume':True,
        'clearance_holes':holes,'hex_vertical_faces':len(hex_faces),
        'other_parts_preserved':others,'sensor_transform_preserved':True,
        'timeline_marker':marker,'timeline_count':count,
        'saved':not doc.isModified,'assembly_interference_not_resolved':True}
with open(root+'/tmp/carrier_nut_pockets_restored.json','w') as f: json.dump(report,f,ensure_ascii=False,indent=2)
app.activeViewport.refresh()
print(json.dumps(report,ensure_ascii=False,indent=2))
