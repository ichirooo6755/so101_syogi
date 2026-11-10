"""Preserve our intermediate V3 and rebuild its main frame with bolt-access holes."""
import adsk.core
import adsk.fusion
from pathlib import Path
ROOT=Path('/Users/sugawaraichirou/Documents/ChatGPT/so101')
owned=[]
for doc in app.documents:
    d=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    if d and d.rootComponent.occurrences.itemByName('01_A_left_arm_frame_V3:1'):
        owned.append((doc,d))
assert len(owned)==1
doc,d=owned[0]
assert d.rootComponent.occurrences.count==11
path=ROOT/'output/camera_mount_v3/intermediate_before_tool_access.f3d'
assert not path.exists()
assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(str(path)))
doc.close(False)
exec(compile((ROOT/'scripts/build_compact_selection2_camera_v3.py').read_text(),'compact_camera_v3','exec'),globals())
