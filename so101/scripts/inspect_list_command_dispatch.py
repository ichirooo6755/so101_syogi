value=app.executeTextCommand('TextCommands.List /hidden')
for line in value.splitlines():
    low=line.lower()
    if any(word in low for word in ('dropdown','listitem','listcontrol','executecommand','invokecommand','selectlist','selectitem')):
        print(line)
print('result_selected',ui.commandDefinitions.itemById('SimResultTypeGroupCmd').controlDefinition.lastSelected.name)
print('report_open',ui.commandDefinitions.itemById('SimReportCmd').execute())
