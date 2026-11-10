import json
value=app.executeTextCommand('TextCommands.List /hidden')
lines=[line for line in value.splitlines() if 'simresults' in line.lower() or any(v in line.lower() for v in ('currentcommand','dumpcommand','commandinput','listinputs'))]
lines.extend(str((c.id,c.name)) for c in ui.commandDefinitions if 'レポート' in c.name or '結果タイプ' in c.name)
print('\n'.join(lines))
with open('/Users/sugawaraichirou/Documents/ChatGPT/so101/output/v6/native_result_commands.txt','w',encoding='utf-8') as f: f.write('\n'.join(lines))
