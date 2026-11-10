import json
rows=[]
for id in ('SimResultTypeGroupCmd','SimResultTypeCmd','SimResultUnitsCmd','SimReportCmd'):
    command=ui.commandDefinitions.itemById(id)
    cd=command.controlDefinition
    row={'id':id,'type':cd.objectType,'properties':[v for v in dir(cd) if not v.startswith('_')]}
    if hasattr(cd,'listItems'):
        row['items']=[{'index':i,'name':v.name,'selected':v.isSelected,'separator':v.isSeparator} for i,v in enumerate(cd.listItems)]
    rows.append(row)
print(json.dumps(rows,ensure_ascii=False,indent=2))
