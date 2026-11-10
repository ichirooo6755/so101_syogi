import adsk.fusion
q=adsk.fusion.ThreadDataQuery.create(False)
t=q.defaultMetricThreadType
sizes=q.allSizes(t)
size=next(s for s in sizes if abs(float(s)-3)<1e-9)
designations=q.allDesignations(t,size)
print('thread_type',t,'size',size,'designations',designations)
for name in designations:
    if '0.5' in name: print(name,'internal classes',q.allClasses(True,t,name))
