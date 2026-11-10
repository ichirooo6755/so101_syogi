"""Final native assembly reopen, axial nut engagement and untouched-source audit."""
import adsk.core
import adsk.fusion
import json
from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
OUT=ROOT/'output/print_camera_hx711_v3'
build=json.loads((OUT/'checks/design_check.json').read_text())
report=json.loads((OUT/'export_report.json').read_text())
source_doc=next(d for d in app.documents if d.name==build['source_document'])
sd=adsk.fusion.Design.cast(source_doc.products.itemByProductType('DesignProductType'))
actual={'modified':source_doc.isModified,'timeline':[sd.timeline.markerPosition,sd.timeline.count],
    'occurrences':[{'name':o.name,'transform':list(o.transform2.asArray()),'visible':o.isVisible,
        'bodies':[(b.name,b.volume*1000) for b in o.bRepBodies]} for o in sd.rootComponent.occurrences],
    'sets':[(s.name,[e.entityToken for e in s.entities]) for s in sd.selectionSets]}
assert json.loads(json.dumps(actual))==build['source_fingerprint_before'],'V1 source changed since construction'
main=next(d for d in app.documents if d.name=='so101書道')
md=adsk.fusion.Design.cast(main.products.itemByProductType('DesignProductType'))
assert not main.isModified and main.dataFile.versionNumber==26 and md.timeline.count==520
current_doc=next(d for d in app.documents if d.name=='so101_SelectionA_Compact_Camera_HX711_V3')
current_design=adsk.fusion.Design.cast(current_doc.products.itemByProductType('DesignProductType'))
hardware=current_design.rootComponent.occurrences.itemByName('REFERENCE_M3_hardware_do_not_print:1')
bodies={b.name:b for b in hardware.bRepBodies}
CN=build['camera_basis']['N']; EY=(0,1,0)
pairs=[(f'M3x10_A_{x}',f'M3_nut_A_{x}',EY) for x in (22,34)]
pairs += [(f'M3x8_HX_{y}',f'M3_nut_HX_{y}',EY) for y in (-19.2,19.2)]
pairs += [('M3x8_TXS','M3_nut_TXS',EY),('M3x10_camera','M3_nut_camera',CN)]
def bounds(b,axis):
    values=[sum(p*a*10 for p,a in zip(v.geometry.asArray(),axis)) for v in b.vertices]
    return min(values),max(values)
engagement=[]
for bolt,nut,axis in pairs:
    tip,head_end=bounds(bodies[bolt],axis); seat=head_end-3
    lo,hi=bounds(bodies[nut],axis); length=seat-tip
    engaged=max(0,min(hi,seat)-max(lo,tip))
    assert abs(engaged-2.4)<1e-6,(bolt,engaged)
    assert abs(length-(10 if 'x10' in bolt else 8))<1e-6,(bolt,length)
    engagement.append({'bolt':bolt,'nut':nut,'under_head_length_mm':length,
        'nut_axial_thickness_mm':hi-lo,'nominal_thread_engagement_mm':engaged,
        'tip_beyond_nut_mm':lo-tip,'thread_form_not_modeled':True})

archive=Path(report['assembly_archive'])
doc=app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(archive)))
try:
    d=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    assert d.rootComponent.occurrences.count==11
    for part in report['exports']:
        o=d.rootComponent.occurrences.itemByName(part['part']+':1'); assert o
        assert o.bRepBodies.count==1 and abs(o.bRepBodies.item(0).volume*1000-part['volume_mm3'])<1e-6
    sets=[s.name for s in d.selectionSets]
    assert '選択セットA' in sets and '選択セット2_外側方向' in sets
finally:
    doc.close(False); current_doc.activate()
result={'passed':True,'source_V1_preserved':True,'original_so101_version':26,
    'original_so101_timeline':[520,520],'original_so101_unmodified':True,
    'assembly_archive_reopened':True,'assembly_root_occurrences':11,
    'fastener_engagement':engagement,'selection_sets':sets,
    'active_document':current_doc.name,'current_document_modified':current_doc.isModified}
(OUT/'checks/release_native_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False,indent=2))
