import adsk.core
import adsk.fusion
import json
assert ui.activeCommand=='SelectCommand'
doc=next(doc for doc in app.documents if doc.name=='so101_V6_短縮補強_筆圧検証')
assert doc.activate()
print('workspace',[(w.id,w.name) for w in ui.workspaces if w.isActive])
print('commands',[(c.id,c.name) for c in ui.commandDefinitions if any(v in c.name for v in ('結果の詳細','結果を表示','結果プローブ','結果を開','結果を検査','ジョブ ステータス'))])
assert ui.commandDefinitions.itemById('SimSolveDetailsCmd').execute()
