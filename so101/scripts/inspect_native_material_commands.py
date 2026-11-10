for line in app.executeTextCommand('TextCommands.List /hidden').splitlines():
    if any(k in line.lower() for k in ('material','physmat')): print(line)
print('UI_COMMANDS',[(c.id,c.name) for c in ui.commandDefinitions if any(k in c.id.lower() for k in ('material','physmat'))])
