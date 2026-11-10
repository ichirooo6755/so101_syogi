print('LIBS',[(x.name,x.appearances.count) for x in app.materialLibraries])
for x in app.materialLibraries:
    if x.appearances.count:
        print(x.name,[(x.appearances.item(i).name,x.appearances.item(i).id) for i in range(min(12,x.appearances.count))])
print('VISUAL',[(a,getattr(adsk.core.VisualStyles,a)) for a in dir(adsk.core.VisualStyles) if 'VisualStyle' in a])
