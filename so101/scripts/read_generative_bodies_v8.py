import adsk.fusion
import builtins
print('ACTIVE',app.activeDocument.name,ui.activeCommand,app.activeProduct.objectType)
wm=builtins._so101_v8_generative_model
print('WM',wm.objectType,wm.designType,wm.isValid)
print('BODIES',[(b.name,round(b.volume*1000,3)) for b in wm.rootComponent.bRepBodies])
print('OCCURRENCES',[(o.name,o.bRepBodies.count) for o in wm.rootComponent.allOccurrences])
