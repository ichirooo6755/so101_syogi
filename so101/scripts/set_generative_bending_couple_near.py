"""Use an explicit force couple, not a centered-only base load."""
import adsk.core
import adsk.fusion
import builtins
import json
wm=builtins._so101_v8_generative_model
b=next(b for b in wm.rootComponent.bRepBodies if b.name.startswith('PRESERVE_03'))
planes=[f for f in b.faces if isinstance(f.geometry,adsk.core.Plane)]
seat=max((f for f in planes if abs(f.geometry.normal.z)>.99 and abs(f.geometry.origin.z*10-39.5)<1e-5),key=lambda f:f.area)
heads=sorted((f for f in planes if abs(f.geometry.normal.z)>.99 and abs(f.geometry.origin.z*10-32.7)<1e-5),key=lambda f:f.centroid.y)
assert len(heads)==2
Mx=6*(2.762946202-seat.centroid.y*10)
F=-Mx/((heads[1].centroid.y-heads[0].centroid.y)*10)
builtins._so101_v8_couple_force_N=F
normal=heads[0].evaluator.getNormalAtPoint(heads[0].centroid)[1]
magnitude=-F/normal.z
ui.activeSelections.clear(); assert ui.activeSelections.add(heads[0])
assert ui.commandDefinitions.itemById('GenLoadsCommand').execute()
report={'main_force_N':[0,0,6],'main_force_point_mm':[v*10 for v in seat.centroid.asArray()],
    'bending_couple_N':F,'moment_X_Nmm':Mx,'pair_y_mm':[f.centroid.y*10 for f in heads],
    'near_default_normal_force_input_N':magnitude,
    'far_default_normal_force_input_N':-magnitude,
    'resultant_force_N':[0,0,6], 'equivalent_axial_application_y_mm':2.762946202,
    'local_load_distribution_note':'Ideal base-design equivalent wrench, not a detailed bolt/contact solve'}
with open('/Users/sugawaraichirou/Documents/ChatGPT/so101/output/v8/generative_equivalent_load.json','w',encoding='utf-8') as f:
    json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps(report,ensure_ascii=False,indent=2))
