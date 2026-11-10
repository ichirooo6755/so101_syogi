import builtins
wm=builtins._so101_v8_generative_model
ui.activeSelections.clear()
for b in wm.rootComponent.bRepBodies:
    b.isLightBulbOn=b.name.startswith('PRESERVE_') or b.name.startswith('OBSTACLE_ACTUAL_carrier_')
app.activeViewport.fit(); app.activeViewport.refresh()
print('Visible native carrier and preserves; click a carrier face for context verification')
