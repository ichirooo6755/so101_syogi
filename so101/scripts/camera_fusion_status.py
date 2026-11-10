import adsk.fusion
import json
print(json.dumps({'documents':[[d.name,d.isModified] for d in app.documents],
                  'command':ui.activeCommand},ensure_ascii=False))
