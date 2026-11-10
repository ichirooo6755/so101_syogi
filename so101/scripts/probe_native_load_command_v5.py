import adsk.core
import adsk.fusion
import builtins
import json

class Probe(adsk.core.CommandCreatedEventHandler):
    def __init__(self): super().__init__()
    def notify(self,args):
        def inputs(collection):
            rows=[]
            for v in collection:
                row={'id':v.id,'name':v.name,'type':v.objectType}
                for key in ('value','expression','selectionCount','isVisible','isEnabled'):
                    try: row[key]=getattr(v,key)
                    except: pass
                try: row['children']=inputs(v.children)
                except: pass
                try: row['items']=[{'name':x.name,'selected':x.isSelected} for x in v.listItems]
                except: pass
                rows.append(row)
            return rows
        builtins._so101_native_load_command=args.command
        result=inputs(args.command.commandInputs)
        with open('/Users/sugawaraichirou/Documents/ChatGPT/so101/tmp/native_load_command_probe_v5.json','w',encoding='utf-8') as f:
            json.dump(result,f,ensure_ascii=False,indent=2)
        print('native inputs',result)

ui.activeSelections.clear()
handler=Probe()
builtins._so101_native_load_handler=handler
cd=ui.commandDefinitions.itemById('SimLoadsCommand')
print('native',cd.isNative,'handler',cd.commandCreated.add(handler))
assert cd.execute()
print('handler_fired',hasattr(builtins,'_so101_native_load_command'))
