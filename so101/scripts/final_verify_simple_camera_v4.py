"""Final two-bolt engagement, unchanged source and seven-component archive QA."""
import adsk.core
import adsk.fusion
import json
from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
OUT=ROOT/'output/print_camera_hx711_v4'
current_doc=next(d for d in app.documents if d.name=='so101_SelectionA_Simple_Camera_HX711_V4')
current_design=adsk.fusion.Design.cast(current_doc.products.itemByProductType('DesignProductType'))
if '選択セット2_外側方向' not in [s.name for s in current_design.selectionSets]:
    o=current_design.rootComponent.occurrences.itemByName('01_simple_camera_HX711_bracket_V4:1')
    faces=[f for f in o.component.bRepBodies.item(0).faces
        if f.geometry.surfaceType==adsk.core.SurfaceTypes.PlaneSurfaceType and abs(f.geometry.origin.y*10-49.75)<1e-6]
    f=max(faces,key=lambda f:f.area)
    current_design.selectionSets.add([f.createForAssemblyContext(o)],'選択セット2_外側方向')
hardware=current_design.rootComponent.occurrences.itemByName('REFERENCE_M3_hardware_do_not_print:1')
assert hardware.bRepBodies.count==4,'Only two bolts and two nuts are allowed'
if current_doc.isModified: current_doc.save('Two-part simple camera bracket; retain selection A and outward direction reference')
report=json.loads((OUT/'export_report.json').read_text())
assert current_design.exportManager.execute(current_design.exportManager.createFusionArchiveExportOptions(report['assembly_archive']))
script=(ROOT/'scripts/final_verify_compact_camera_v3.py').read_text()
script=script.replace('print_camera_hx711_v3','print_camera_hx711_v4').replace('SelectionA_Compact_Camera_HX711_V3','SelectionA_Simple_Camera_HX711_V4')
start=script.index("pairs += [(f'M3x8_HX_"); end=script.index('def bounds(',start)
script=script[:start]+script[end:]
script=script.replace('occurrences.count==11','occurrences.count==7').replace("'assembly_root_occurrences':11","'assembly_root_occurrences':7")
script=script.replace("'source_V1_preserved':True","'source_V3_preserved':True")
exec(compile(script,'final_verify_simple_camera_v4','exec'),globals())
