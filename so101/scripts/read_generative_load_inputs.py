import builtins
print('ACTIVE',ui.activeCommand)
print(app.executeTextCommand('UI.CurrentCommandInfo'))
if hasattr(builtins,'_so101_gen_native_command'):
    command=builtins._so101_gen_native_command
    print('INPUTS',[(i.id,i.name,i.objectType) for i in command.commandInputs])
else: print('Native commandCreated API event not exposed')
