"""Verify the archived V7 assembly and preserve the prior V5 document."""
import adsk.core
import adsk.fusion
import json
from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
OUT=ROOT/'output/camera_mount_v7/print_candidate'
build=json.loads((OUT/'checks/design_check.json').read_text())
report=json.loads((OUT/'export_report.json').read_text())
source_doc=next(d for d in app.documents if d.name==build['source_document'])
sd=adsk.fusion.Design.cast(source_doc.products.itemByProductType('DesignProductType'))
actual={'modified':source_doc.isModified,'timeline':[sd.timeline.markerPosition,sd.timeline.count],
    'occurrences':[{'name':o.name,'transform':list(o.transform2.asArray()),'visible':o.isVisible,
        'bodies':[(b.name,b.volume*1000) for b in o.bRepBodies]} for o in sd.rootComponent.occurrences],
    'sets':[(s.name,[e.entityToken for e in s.entities]) for s in sd.selectionSets]}
assert json.loads(json.dumps(actual))==build['source_fingerprint_before'],'Source V5 changed'
owned=[]
for d in app.documents:
    dd=adsk.fusion.Design.cast(d.products.itemByProductType('DesignProductType'))
    if dd and dd.rootComponent.occurrences.itemByName('01_A_slot_socket_V7:1'):owned.append((d,dd))
current_doc,current_design=owned[-1]
doc=app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(report['assembly_archive']))
try:
    d=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    assert d.rootComponent.occurrences.count==13,d.rootComponent.occurrences.count
    for part in report['exports']:
        o=d.rootComponent.occurrences.itemByName(part['part']+':1')
        assert o and o.bRepBodies.count==1 and abs(o.bRepBodies.item(0).volume*1000-part['volume_mm3'])<1e-5
    sets=[s.name for s in d.selectionSets]
    assert '選択セットA' in sets and '選択セット2_外側方向' in sets
    references={o.component.name:o.bRepBodies.count for o in d.rootComponent.occurrences if o.component.name.startswith('REFERENCE_')}
    assert references['REFERENCE_SparkFun_SEN13879_HX711_1pc']==3
    assert references['REFERENCE_perfboard_same_size_1pc']==3
finally:
    doc.close(False);current_doc.activate()
result={'passed':True,'source_V5_preserved':True,'assembly_archive_reopened':True,
        'assembly_root_occurrences':13,'reference_body_counts':references,'selection_sets':sets,
        'physical_print_and_fit_unverified':True}
(OUT/'checks/release_native_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False,indent=2))
