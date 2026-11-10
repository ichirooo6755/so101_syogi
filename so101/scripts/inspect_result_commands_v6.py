import json
print(json.dumps([{'id':c.id,'name':c.name} for c in ui.commandDefinitions if any(s in c.name for s in ('結果を終了','ソルバー','解析の詳細','荷重ケース属性'))],ensure_ascii=False,indent=2))
print('active',ui.activeCommand)
