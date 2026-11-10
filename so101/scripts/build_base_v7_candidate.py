"""Improve the V6 load-path junction in an independent editable copy.

Never rolls or edits the user's assembly timeline. The sensor seating plane,
orientation, brush center, horn holes, and fixed screw head seats are preserved.
"""
import adsk.core
import adsk.fusion
import json
import os

root = '/Users/sugawaraichirou/Documents/ChatGPT/so101'
out = root + '/output/v7'
os.makedirs(out + '/analysis', exist_ok=True)
assert ui.activeCommand == 'SelectCommand', ui.activeCommand
main = next(doc for doc in app.documents if doc.name.startswith('so101書道'))
md = adsk.fusion.Design.cast(main.products.itemByProductType('DesignProductType'))
mr = md.rootComponent
main_timeline = (md.timeline.markerPosition, md.timeline.count)
names = {'base': '部品１_V5_短縮補強_16mm:1',
         'carrier': 'Brush_Load_Carrier_Compact_V5:1',
         'cartridge': 'Brush_Cartridge_Symmetric_15mm_V5:1',
         'wrist': 'Wrist_Roll_Clearance_V5:1'}
before = {k: {'volumes_mm3': [b.volume * 1000 for b in mr.occurrences.itemByName(n).bRepBodies],
              'transform': list(mr.occurrences.itemByName(n).transform2.asArray())}
          for k, n in names.items()}
assert abs(before['base']['volumes_mm3'][0] - 34383.20028727208) < 1e-4
t = adsk.fusion.TemporaryBRepManager.get()
sources = {k: t.copy(mr.occurrences.itemByName(names[k]).bRepBodies.item(0))
           for k in ('carrier', 'cartridge')}
sources['sensor'] = t.copy(next(o.bRepBodies.item(0) for o in mr.allOccurrences
    if o.fullPathName.startswith('SC616C_1kg_Fusion:1+') and o.bRepBodies.count))

doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(
    root + '/output/v6/01_yoke_short_stiff_V6_editable.f3d'))
assert doc
d = adsk.fusion.Design.cast(app.activeProduct)
r = d.rootComponent
assert r.bRepBodies.count == 1 and d.timeline.markerPosition == d.timeline.count
assert abs(r.bRepBodies.item(0).volume * 1000 - before['base']['volumes_mm3'][0]) < 1e-4
namespace = {}
with open(root + '/scripts/fusion_shapes.py', encoding='utf-8') as f:
    exec(compile(f.read(), '<shapes>', 'exec'), namespace)
h = namespace['Shapes'](d)
# Give the transverse member the same 26 mm structural depth as the rails.
# X >= 47 lies outside the audited complete wrist rotational envelope.
h.box(r, 'V7_deep_closed_crossmember', 47, 54, -36.5, 35.5, 21, '14.5 mm')
# Join the new cavity into the old cavity, keeping a 3 mm bottom, 2 mm walls.
h.box(r, 'V7_extend_closed_box_core', 49, 52, -28.5, 27.5, 24, '14.1 mm', h.CUT)
# Support the whole fixed socket footprint rather than an 8 mm-wide strip.
# Do NOT bridge to the free load-cell end, carrier, or strain-gauge keepout.
h.box(r, 'V7_full_fixed_socket_undersupport', 47, 69.2, 23.46294620236,
      41.56294620236, 21, '18.5 mm')
# Restore bottom-up M3 driver/head access after extending the underside.
# Seat stays Z=32.7, so the existing M3x12 screw engagement is unchanged.
s = h.sketch(r, 'V7_fixed_M3_bottom_access', 20.9)
for y in (26.96294620236, 34.36294620236):
    h.circle(s, (62, y, 20.9), '6.2 mm')
h.extrude(r, s, '11.8 mm', h.CUT, 'V7_extend_head_access_keep_original_seat')
body = r.bRepBodies.item(0)
body.name = 'V7_deep_box_full_socket_support'
assert r.bRepBodies.count == 1 and body.isSolid
assert all(int(f.healthState) == 0 for f in r.features)
sources['base'] = t.copy(body)
assert doc.saveAs('部品１_V7_閉断面台座補強', main.dataFile.parentFolder, '',
    'Native 6 N result reviewed. Deepen closed crossmember and support full fixed socket. Preserve wrist sweep, cell orientation and M3 head seats.')
made = {'document': doc.name, 'cloud_id': doc.dataFile.id,
        'base_volume_mm3': body.volume * 1000, 'original_base_volume_mm3': before['base']['volumes_mm3'][0],
        'healthy_features': r.features.count, 'before_assembly': before,
        'original_assembly_untouched': True, 'preserved_assembly_timeline': list(main_timeline),
        'native_solved': False,
        'brush_axis_mm': [62, md.userParameters.itemByName('sc_brush_axis_y').value * 10]}

# Material-correct, independent four-part native simulation document.
simdoc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
sd = adsk.fusion.Design.cast(app.activeProduct)
sd.designType = adsk.fusion.DesignTypes.DirectDesignType
lib = app.materialLibraries.itemById('C1EEA57C-3F56-45FC-B8CB-A9EC46A9994C')
plastic = sd.materials.addByCopy(lib.materials.itemById('PrismMaterial-022'),
    'PRINT_ASSUMED_E1500MPa_ISOTROPIC_NOT_TESTED')
al = sd.materials.addByCopy(lib.materials.itemById('PrismMaterial-002'),
    'SC616C_APPROX_Al_E69000MPa_ALLOY_UNKNOWN')
for material, young, nu, density, sy, st in (
        (plastic, 1500000, .35, 1240, 20000, 25000),
        (al, 69000000, .33, 2700, 55000, 90000)):
    for p in material.materialProperties:
        if p.objectType != 'adsk::core::FloatProperty':
            continue
        if p.id.startswith('structural_Young_modulus'): p.value = young
        elif p.id.startswith('structural_Poisson_ratio'): p.value = nu
        elif p.id.startswith('structural_Shear_modulus'): p.value = young / (2 * (1 + nu))
        elif p.id in ('structural_Density', 'thermal_Density'): p.value = density
        elif p.id == 'structural_Minimum_yield_stress': p.value = sy
        elif p.id == 'structural_Minimum_tensile_strength': p.value = st
for label, source in sources.items():
    occ = sd.rootComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    occ.component.name = label
    b = occ.component.bRepBodies.add(source)
    b.name = label
    b.material = al if label == 'sensor' else plastic
    assert sd.exportManager.execute(sd.exportManager.createSTEPExportOptions(
        out + '/analysis/' + label + '.step', occ.component))
with open(root + '/output/v6/v6_short/geometry_audit.json', encoding='utf-8') as f:
    audit = json.load(f)
audit['source'] = 'Actual Fusion V7 independent candidate, not installed in main assembly yet'
audit['parts']['base']['volume_mm3'] = made['base_volume_mm3']
with open(out + '/analysis/geometry_audit.json', 'w', encoding='utf-8') as f:
    json.dump(audit, f, ensure_ascii=False, indent=2)
assert simdoc.saveAs('so101_V7_閉断面補強_筆圧検証', main.dataFile.parentFolder, '',
    'Four-body native Fusion simulation, same material and load assumptions as V6; electrical bridge not modeled')
made['simulation_document'] = simdoc.name
made['simulation_cloud_id'] = simdoc.dataFile.id
with open(out + '/created.json', 'w', encoding='utf-8') as f:
    json.dump(made, f, ensure_ascii=False, indent=2)
cam = app.activeViewport.camera
cam.viewOrientation = adsk.core.ViewOrientations.IsoTopRightViewOrientation
cam.isFitView = True
app.activeViewport.camera = cam
app.activeViewport.refresh()
assert (md.timeline.markerPosition, md.timeline.count) == main_timeline
print(json.dumps(made, ensure_ascii=False, indent=2))
