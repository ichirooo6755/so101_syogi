"""Keep the user's rolled-back timeline untouched while authoring the new part."""
import adsk.core
import adsk.fusion
import json
import os

root='/Users/sugawaraichirou/Documents/ChatGPT/so101'; out=root+'/output/v6'
assert ui.activeCommand=='SelectCommand'
main=next(doc for doc in app.documents if doc.name=='so101書道')
md=adsk.fusion.Design.cast(main.products.itemByProductType('DesignProductType'))
assert md.timeline.count-md.timeline.markerPosition==31
assert not md.attributes.itemByName('so101_calligraphy','short_stiff_v6')
with open(root+'/tmp/v6_user_revision.json',encoding='utf-8') as f: prior=json.load(f)
old=next(x for x in prior['documents'] if x['name']=='so101書道')
for name in ('部品１_V5可動域改善:1','Wrist_Roll_Clearance_V5:1','Brush_Load_Carrier_Compact_V5:1','Brush_Cartridge_Symmetric_15mm_V5:1'):
    previous=next(o for o in old['occurrences'] if o['name']==name)
    live=md.rootComponent.occurrences.itemByName(name)
    assert abs(sum(b.volume*1000 for b in live.bRepBodies)-sum(b['volume_mm3'] for b in previous['bodies']))<1e-4,name
doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
d=adsk.fusion.Design.cast(app.activeProduct); r=d.rootComponent
for name in ('sc_brush_axis_y','sc_screw_clearance','sc_head_dia','sc_head_depth'):
    source=md.userParameters.itemByName(name)
    d.userParameters.add(name,adsk.core.ValueInput.createByReal(source.value),'mm',source.comment)
ns={}
with open(root+'/scripts/fusion_shapes.py',encoding='utf-8') as f: helper=f.read()
exec(compile(helper,'<inline-shape-helpers>','exec'),ns)
h=ns['Shapes'](d)
h.component=lambda name:(None,r)
with open(root+'/scripts/build_short_stiff_v6.py',encoding='utf-8') as f: builder=f.read()
geometry=builder[builder.index('cx=62.'):builder.index('# Move the sensor and its two moving printed parts')]
import math
exec(compile(geometry,'<isolated-V6-base-geometry>','exec'),globals())
assert r.bRepBodies.count==1
volume=r.bRepBodies.item(0).volume*1000
assert abs(volume-34383.2002872724)<1e-4,volume
assert all(int(f.healthState)==0 for f in r.features)
assert doc.saveAs('部品１_V5_短縮補強_16mm',main.dataFile.parentFolder,'','16mm shorter, deep rounded-window rails, low closed box tie, supported fixed socket; preserves main document timeline')
assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(out+'/01_yoke_short_stiff_V6_editable.f3d'))
assert d.exportManager.execute(d.exportManager.createSTEPExportOptions(out+'/01_yoke_short_stiff_V6.step'))
report={'document_name':doc.name,'cloud_id':doc.dataFile.id,'cloud_version':doc.dataFile.versionNumber,
        'volume_mm3':volume,'feature_count':r.features.count,'main_untouched':True,
        'native_features_healthy':True,'geometry_matches_offline_candidate':True}
with open(out+'/independent_base.json','w',encoding='utf-8') as f: json.dump(report,f,ensure_ascii=False,indent=2)
main.activate()
print(json.dumps(report,ensure_ascii=False,indent=2))
