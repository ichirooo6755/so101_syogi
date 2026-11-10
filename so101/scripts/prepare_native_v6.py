import adsk.core
import adsk.fusion
import json
import os

root='/Users/sugawaraichirou/Documents/ChatGPT/so101'; out=root+'/output/v6'
with open(out+'/verification.json',encoding='utf-8') as f: checked=json.load(f)
assert checked['passed']
main=next(doc for doc in app.documents if doc.name=='so101書道'); main.activate()
d=adsk.fusion.Design.cast(main.products.itemByProductType('DesignProductType')); r=d.rootComponent
assert d.timeline.count-d.timeline.markerPosition==31
assert main.save('部品１を16mm短縮・補強。独立編集部品をリンク。ユーザーの手首切削と31件の未来履歴を保持')
folder=main.dataFile.parentFolder
t=adsk.fusion.TemporaryBRepManager.get()
sources={k:t.copy(r.occurrences.itemByName(checked['parts'][k]).bRepBodies.item(0)) for k in ('base','carrier','cartridge')}
sources['sensor']=t.copy(next(o.bRepBodies.item(0) for o in r.allOccurrences
    if o.fullPathName.startswith('SC616C_1kg_Fusion:1+') and o.bRepBodies.count))
doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
sd=adsk.fusion.Design.cast(app.activeProduct); sd.designType=adsk.fusion.DesignTypes.DirectDesignType
lib=app.materialLibraries.itemById('C1EEA57C-3F56-45FC-B8CB-A9EC46A9994C')
plastic=sd.materials.addByCopy(lib.materials.itemById('PrismMaterial-022'),'PRINT_ASSUMED_E1500MPa_ISOTROPIC_NOT_TESTED')
al=sd.materials.addByCopy(lib.materials.itemById('PrismMaterial-002'),'SC616C_APPROX_Al_E69000MPa_ALLOY_UNKNOWN')
for material,young,nu,density,yield_kpa,tensile in ((plastic,1500000,.35,1240,20000,25000),(al,69000000,.33,2700,55000,90000)):
    for p in material.materialProperties:
        if p.objectType!='adsk::core::FloatProperty': continue
        if p.id.startswith('structural_Young_modulus'): p.value=young
        elif p.id.startswith('structural_Poisson_ratio'): p.value=nu
        elif p.id.startswith('structural_Shear_modulus'): p.value=young/(2*(1+nu))
        elif p.id in ('structural_Density','thermal_Density'): p.value=density
        elif p.id=='structural_Minimum_yield_stress': p.value=yield_kpa
        elif p.id=='structural_Minimum_tensile_strength': p.value=tensile
for label,b in sources.items():
    o=sd.rootComponent.occurrences.addNewComponent(adsk.core.Matrix3D.create()); o.component.name=label
    body=o.component.bRepBodies.add(b); body.name=label
    body.material=al if label=='sensor' else plastic
assert doc.saveAs('so101_V6_短縮補強_筆圧検証',folder,'','Native Fusion static stress; approximate isotropic materials; not electrical output or FDM certification')
cam=app.activeViewport.camera; cam.viewOrientation=adsk.core.ViewOrientations.IsoTopRightViewOrientation; cam.isFitView=True
app.activeViewport.camera=cam; app.activeViewport.refresh()
report={'main_saved':not main.isModified,'main_cloud_version':main.dataFile.versionNumber,
        'native_simulation_document':doc.name,'native_cloud_id':doc.dataFile.id,
        'parts':{k:b.volume*1000 for k,b in sources.items()},'native_solved':False}
with open(out+'/native_preparation.json','w',encoding='utf-8') as f: json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps(report,ensure_ascii=False,indent=2))
