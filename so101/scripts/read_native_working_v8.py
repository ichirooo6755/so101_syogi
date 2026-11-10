import builtins
print('Selections',ui.activeSelections.count)
for s in ui.activeSelections:
    e=s.entity
    if e.objectType=='adsk::fusion::Occurrence': wm=e.component.parentDesign
    elif hasattr(e,'body'): wm=e.body.parentComponent.parentDesign
    else: continue
    if wm.objectType=='adsk::fusion::WorkingModel':
        builtins._so101_v8_sim_design=wm
        context=e.body.assemblyContext if hasattr(e,'body') else e
        print('SELECTED_CONTEXT',context.fullPathName,'parent_context',context.assemblyContext.fullPathName if context.assemblyContext else None)
        builtins._so101_v8_sim_outer_context=context.assemblyContext
        print('WM_READY',[(o.name,o.bRepBodies.count) for o in wm.rootComponent.occurrences])
        break
else: raise RuntimeError('No selected simulation working model')
