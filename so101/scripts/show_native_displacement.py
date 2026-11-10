assert '筆圧検証' in app.activeDocument.name
definition=ui.commandDefinitions.itemById('SimResultTypeGroupCmd')
items=definition.controlDefinition.listItems
target=next(item for item in items if item.name=='変位')
target.isSelected=True
print('Selected result',target.name,target.isSelected)
print('Execute',definition.execute())
