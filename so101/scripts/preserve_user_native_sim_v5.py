import adsk.fusion
import os
doc=next(doc for doc in app.documents if doc.name=='so101_V5_筆圧検証_理想接触')
d=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
assert doc.save('Preserve user native static-stress setup/result before shortening; result viewer reports incomplete data')
path='/Users/sugawaraichirou/Documents/ChatGPT/so101/reference/so101_V5_user_native_study_before_v6.f3d'
assert not os.path.exists(path)
assert d.exportManager.execute(d.exportManager.createFusionArchiveExportOptions(path))
print('Saved user study',doc.dataFile.versionNumber,'archive bytes',os.path.getsize(path))
