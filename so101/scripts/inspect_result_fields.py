import json
print('document',app.activeDocument.name)
print(json.dumps([{'id':c.id,'name':c.name} for c in ui.commandDefinitions
    if any(s in c.id.lower() for s in ('dora','result','displacement','stress','deformation')) and
       any(s in c.name for s in ('変位','応力','結果','しきい','プローブ','レポート'))],ensure_ascii=False,indent=2))
