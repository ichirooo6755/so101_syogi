import adsk.core
import adsk.fusion
import adsk.sim
import builtins
print('doc',app.activeDocument.name,'active',ui.activeCommand)
print('selections',[(ui.activeSelections.item(i).entity.objectType) for i in range(ui.activeSelections.count)])
commands=[(c.id,c.name) for c in ui.commandDefinitions if 'selectall' in c.id.lower()]
print('commands',commands)
print('supported',app.supportedProductTypes)
print('active_product',app.activeProduct.objectType,type(app.activeProduct))
for name in app.supportedProductTypes:
    if 'sim' not in name.lower(): continue
    try:
        p=app.activeDocument.products.itemByProductType(name)
        print('product',name,p,p.objectType if p else None)
        if p and isinstance(p,adsk.sim.Simulations):
            builtins._so101_v6_simulations=p
            print('models',p.simulationModels.count,'studies',p.studies.count)
            wm=p.simulationModels.item(0).modelComponents
            builtins._so101_v6_sim_design=wm
            print('working_model',wm.objectType,[(o.name,o.bRepBodies.count) for o in wm.rootComponent.occurrences])
    except Exception as e: print(name,type(e).__name__,str(e))
