assert app.activeDocument.name=='so101_V5_筆圧検証_理想接触'
print('active_workspaces',[(w.id,w.name) for w in ui.workspaces if w.isActive])
print('finish',ui.commandDefinitions.itemById('FinishDoraCmd').execute())
