assert ui.activeCommand=='SimGenerativeObjectivesCommand'
for command in ('Commands.SetBool infoObjectivesMaximizeStiffness 1',
                'Commands.SetBool infoDisplacement 1',
                'Commands.SetBool infoGlobalDisplacement 1'):
    print(command,app.executeTextCommand(command))
