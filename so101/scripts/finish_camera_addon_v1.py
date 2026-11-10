"""Native CAD reopen QA, clearer previews and separate saved addon document."""
import adsk.core
import adsk.fusion
import json
from pathlib import Path

ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
OUT=ROOT/'output/print_camera_hx711_v1'
report=json.loads((OUT/'export_report.json').read_text())
main=next(x for x in app.documents if x.name.startswith('so101書道'))
md=adsk.fusion.Design.cast(main.products.itemByProductType('DesignProductType'))
owned=[]
for doc in app.documents:
    d=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    if d and d.rootComponent.occurrences.itemByName('01_fixed_electronics_frame:1'): owned.append((doc,d))
document,design=owned[-1]; document.activate(); root=design.rootComponent
geometry=json.loads((OUT/'checks/candidate_geometry.json').read_text())['parts']
checks=[]
for part in report['exports']:
    for ext in ('_editable.f3d','.step'):
        path=OUT/'source_cad'/(part['stem']+ext)
        opts=(app.importManager.createFusionArchiveImportOptions(str(path)) if ext.endswith('f3d')
              else app.importManager.createSTEPImportOptions(str(path)))
        doc=app.importManager.importToNewDocument(opts)
        try:
            d=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            bodies=list(d.rootComponent.bRepBodies)+[b for o in d.rootComponent.allOccurrences for b in o.bRepBodies]
            bodies=[b for b in bodies if b.isSolid and b.volume>1e-8]
            assert len(bodies)==1 and bodies[0].lumps.count==1,path.name
            b=bodies[0]; err=abs(b.volume*1000-part['volume_mm3'])
            assert err<max(.01,part['volume_mm3']*.001),[path.name,err]
            bb=b.boundingBox; dims=[(hi-lo)*10 for hi,lo in zip(bb.maxPoint.asArray(),bb.minPoint.asArray())]
            if ext.endswith('f3d'):
                bounds=geometry[part['part']]['bbox_mm']; expected=[bounds[1][i]-bounds[0][i] for i in range(3)]
            else: expected=part['size_mm']
            assert max(abs(a-b) for a,b in zip(dims,expected))<.01,[path.name,dims,expected]
            checks.append({'file':str(path.relative_to(OUT)),'solid_count':1,'lumps':1,
                           'volume_error_mm3':err,'size_mm':dims,'reopened_in_Fusion':True})
        finally:
            doc.close(False); document.activate()
(OUT/'checks/cad_reopen_verification.json').write_text(json.dumps({'passed':True,'files':checks},indent=2))

# All appearance edits below affect only the separate add-on copy.
lib=app.materialLibraries.itemByName('Fusion 外観ライブラリ')
source=lib.appearances.itemByName('ABS(白)')
colorlog=[]
def color(name,rgb):
    a=design.appearances.addByCopy(source,name)
    p=a.appearanceProperties.itemById('opaque_albedo')
    if p:
        adsk.core.ColorProperty.cast(p).value=adsk.core.Color.create(*rgb,255)
        colorlog.append([name,p.id])
    else:
        props=[adsk.core.ColorProperty.cast(p) for p in a.appearanceProperties]
        props=[p for p in props if p]
        assert props,name
        props[0].value=adsk.core.Color.create(*rgb,255); colorlog.append([name,props[0].id])
    return a
blue=color('NEW_frame_blue',(60,145,225)); orange=color('NEW_keeper_orange',(245,160,55))
gray=color('EXISTING_reference_gray',(165,170,175)); green=color('PCB_reference_green',(40,135,85))
black=color('Camera_reference_dark',(50,55,60))
for o in root.occurrences:
    name=o.component.name
    a=blue if name.startswith(('01_','02_')) else orange if name.startswith(('03_','04_','05_','06_')) else black if 'XIAO' in name else green if 'envelopes' in name else gray
    for b in o.bRepBodies: b.appearance=a
envelopes=root.occurrences.itemByName('REFERENCE_HX711_TXS_envelopes_do_not_print:1')
for i in (1,3,5): envelopes.component.bRepBodies.item(i).isLightBulbOn=False
try: app.activeViewport.visualStyle=adsk.core.VisualStyles.ShadedWithVisibleEdgesOnlyVisualStyle
except Exception: pass

cloud={}
try:
    assert document.saveAs('so101_Camera_HX711_V1_追加台座',main.dataFile.parentFolder,
        'Additive camera / HX711 saddle. Existing V8 interfaces unchanged. Prototype, physical fit untested.','')
    cloud={'document':document.name,'id':document.dataFile.id,'version':document.dataFile.versionNumber,'modified':document.isModified}
except Exception as exc: cloud={'local_archives_available':True,'cloud_save_error':str(exc)}
archive=OUT/'source_cad/SO101_Camera_HX711_Addon_V1_assembly_DO_NOT_PRINT.f3d'
assert design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(archive)))
for part in report['exports']:
    c=root.occurrences.itemByName(part['part']+':1').component
    assert design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(OUT/'source_cad'/(part['stem']+'_editable.f3d')),c))

def preview(label,eye):
    cam=app.activeViewport.camera; cam.eye=adsk.core.Point3D.create(*(x/10 for x in eye)); cam.target=adsk.core.Point3D.create(2.5,0,2.5)
    cam.upVector=adsk.core.Vector3D.create(0,0,1); cam.isFitView=True
    app.activeViewport.camera=cam; app.activeViewport.refresh()
    app.activeViewport.saveAsImageFile(str(OUT/'preview'/f'{label}.png'),1600,1200)
preview('assembly_front',(120,-125,-65)); preview('assembly_rear',(-90,120,95))
for o in root.occurrences:
    if o.component.name.startswith('REFERENCE_'): o.isLightBulbOn=False
preview('printed_addon_only',(120,-125,-65))
for o in root.occurrences:
    if o.component.name.startswith('REFERENCE_'): o.isLightBulbOn=True
preview('assembly_front',(120,-125,-65))
# Restore the saved assembly visibility and persist the final appearance state.
if cloud.get('id'):
    try:
        if document.isModified: document.save('Clearer reference display; printed geometry unchanged')
        cloud['final_version']=document.dataFile.versionNumber
    except Exception as exc: cloud['final_save_note']=str(exc)
report['appearance_log']=colorlog; report['cloud_copy']=cloud
(OUT/'export_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
assert not main.isModified and md.timeline.count==520 and main.dataFile.versionNumber==26
for old,_ in owned[:-1]: old.close(False)
document.activate()
print(json.dumps({'cad_files_reopened':len(checks),'passed':True,'color_properties':colorlog,
                  'cloud_copy':cloud,'original_unchanged':True},ensure_ascii=False,indent=2))
