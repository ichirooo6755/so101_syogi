import builtins
import adsk.fusion
print('SELECTIONS',ui.activeSelections.count)
for s in ui.activeSelections:
    e=s.entity
    b=e.body if hasattr(e,'body') else adsk.fusion.BRepBody.cast(e)
    if not b:
        print('OTHER',e.objectType); continue
    design=b.parentComponent.parentDesign
    wm=builtins._so101_v8_generative_model
    print('BODY',b.name,b.objectType,'volume',b.volume*1000,'parent',design.objectType,'sameDesign',design==wm,
        'native',getattr(b,'nativeObject',None),'context',getattr(b,'assemblyContext',None))
    print('SELECTED_DESIGN_BODIES',[(x.name,round(x.volume*1000,3)) for x in design.rootComponent.bRepBodies])
    builtins._so101_v8_selected_generative_design=design
    builtins._so101_v8_generative_context=b.assemblyContext
    print('ASSEMBLY_CONTEXT',b.assemblyContext.fullPathName,b.assemblyContext.component.name,b.assemblyContext.objectType)
    proxy=next(x for x in wm.rootComponent.bRepBodies if x.name==b.name).createForAssemblyContext(b.assemblyContext)
    print('PROXY_EQUALS',proxy==b,'context',proxy.assemblyContext.fullPathName)
