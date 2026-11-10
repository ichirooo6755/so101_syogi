import adsk.fusion
assert app.activeDocument.name.startswith('so101_V8_元取付部保持_ジェネレーティブ')
print('libraries',[(x.id,x.name) for x in app.materialLibraries])
print('favoriteMaterials',getattr(app,'favoriteMaterials',None))
if hasattr(app,'favoriteMaterials'):
    fav=app.favoriteMaterials
    print('public API',[x for x in dir(fav) if not x.startswith('_')])
    print('ADD_DOC',getattr(getattr(fav,'add',None),'__doc__',None))
    print('favorites',[(x.id,x.name) for x in fav])
    d=adsk.fusion.Design.cast(app.activeDocument.products.itemByProductType('DesignProductType'))
    material=d.materials.itemByName('PRINT_ASSUMED_E1500MPa_ISOTROPIC_NOT_TESTED')
    assert material
    added=fav.itemByName(material.name) or material.copyTo(fav)
    assert added
    print('READY_FOR_STUDY',added.id,added.name)
