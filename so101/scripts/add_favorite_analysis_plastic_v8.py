import adsk.fusion
assert app.activeDocument.name.startswith('so101_V8_元取付部保持_ジェネレーティブ')
d=adsk.fusion.Design.cast(app.activeDocument.products.itemByProductType('DesignProductType'))
lib=app.materialLibraries.itemById('C1EEA57C-3F56-45FC-B8CB-A9EC46A9994C')
choices=[(m.id,m.name) for m in lib.materials if any(k in m.name.lower() for k in ('poly','pla','pet','プラスチック','ポリ','ナイロン'))]
print('PLASTIC_TEMPLATES',choices)
name='SO101_PRINT_ASSUMED_E1500_Y20_NOT_TESTED'
fav=app.favoriteMaterials.itemByName(name)
if not fav:
    assert app.favoriteMaterials.itemById('PrismMaterial-279') is None
    mat=d.materials.itemByName(name) or d.materials.addByCopy(lib.materials.itemById('PrismMaterial-279'),name)
    for p in mat.materialProperties:
        if p.objectType!='adsk::core::FloatProperty': continue
        if p.id.startswith('structural_Young_modulus'): p.value=1500000
        elif p.id.startswith('structural_Poisson_ratio'): p.value=.35
        elif p.id.startswith('structural_Shear_modulus'): p.value=1500000/2.7
        elif p.id in ('structural_Density','thermal_Density'): p.value=1240
        elif p.id=='structural_Minimum_yield_stress': p.value=20000
        elif p.id=='structural_Minimum_tensile_strength': p.value=25000
    mat.description='Assumed isotropic printed PLA/PETG screening material; E1500MPa, yield20MPa, rho1240kg/m3. Not filament test data; not FDM strength certification.'
    fav=app.favoriteMaterials.add(mat)
    assert fav
print('FAVORITE_READY',fav.id,fav.name)
print('VERIFIED_PROPERTIES',[(p.id,p.value) for p in fav.materialProperties if p.objectType=='adsk::core::FloatProperty' and ('Young' in p.id or 'Poisson' in p.id or 'yield' in p.id or 'Density' in p.id)])
