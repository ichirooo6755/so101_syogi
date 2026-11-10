import adsk.fusion
name='SO101_PRINT_ASSUMED_E1500_Y20_NOT_TESTED'
fav=app.favoriteMaterials.itemByName(name)
assert fav
for title in ('部品１_V8_元取付形状保持','Wrist_Roll_Clearance_V8_元取付対応'):
    doc=next(d for d in app.documents if d.name==title); doc.activate()
    d=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    m=d.materials.itemByName(name) or d.materials.addByCopy(fav,name)
    for b in d.rootComponent.bRepBodies: b.material=m
    assert doc.save('Printed PLA/PETG screening assumption only: isotropic E1500MPa, yield20MPa; not filament-certified. Source original user parts and steel cell unchanged.')
    print('NEW_PRINTED_SOURCE',title,m.name)
