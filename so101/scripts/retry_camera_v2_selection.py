"""Archive only our failed intermediate V2, then rebuild with corrected selection API."""
import adsk.core
import adsk.fusion
from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
owned=[]
for d in app.documents:
    design=adsk.fusion.Design.cast(d.products.itemByProductType('DesignProductType'))
    if design and design.rootComponent.occurrences.itemByName('01_A_left_arm_frame_V2:1'):
        owned.append((d,design))
assert len(owned)==1,len(owned)
document,design=owned[0]
assert design.rootComponent.occurrences.count==11
path=ROOT/'output/camera_mount_v2/intermediate_before_selection_API_fix.f3d'
assert not path.exists()
assert design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(path)))
document.close(False)
exec(compile((ROOT/'scripts/build_selection_a_left_camera_v2.py').read_text(),'build_camera_v2','exec'),globals())
