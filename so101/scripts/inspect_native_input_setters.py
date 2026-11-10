value=app.executeTextCommand('TextCommands.List /hidden')
for line in value.splitlines():
    if any(k in line.lower() for k in ('commands.set','commands.select','commands.commit','commands.get','commands.current')):
        print(line)
