import adsk.core
import adsk.fusion
import builtins
workspace=ui.workspaces.itemById('GenerativeEnvironment')
if not workspace.isActive: workspace.activate()
class Created(adsk.core.CommandCreatedEventHandler):
    def notify(self,args):
        command=adsk.core.CommandCreatedEventArgs.cast(args).command
        builtins._so101_gen_native_command=command
        print('NATIVE_CREATED',[(i.id,i.name,i.objectType) for i in command.commandInputs])
handler=Created()
builtins._so101_gen_load_created_handler=handler
definition=ui.commandDefinitions.itemById('GenLoadsCommand')
definition.commandCreated.add(handler)
wm=builtins._so101_v8_generative_model
b=next(b for b in wm.rootComponent.bRepBodies if b.name.startswith('PRESERVE_03'))
face=max((f for f in b.faces if isinstance(f.geometry,adsk.core.Plane) and abs(f.geometry.normal.x)>.99 and abs(f.geometry.origin.x*10-69.2)<1e-5),key=lambda f:f.area)
ui.activeSelections.clear(); ui.activeSelections.add(face)
definition.execute()
print('COMMANDINFO',app.executeTextCommand('UI.CurrentCommandInfo'))
print('Active',ui.activeCommand)
