import os
root='/Users/sugawaraichirou/Documents/ChatGPT/so101/output/v6'
name=app.activeDocument.name
assert name in ('so101_V5_筆圧検証_理想接触','so101_V6_短縮補強_筆圧検証')
version='V5' if 'V5' in name else 'V6'
path=root+'/Fusion_native_'+version+'.vtu'
print('document',name,'active',ui.activeCommand)
print('command_help',app.executeTextCommand('TextCommands.List SimResults'))
print(app.executeTextCommand('SimResults.ExportActiveResults "'+path+'"'))
print('native_VTU',path,os.path.getsize(path) if os.path.exists(path) else None)
