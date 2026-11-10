import json
import builtins
assert app.activeDocument.name.startswith('so101_V8_元取付部保持_ジェネレーティブ')
assert ui.activeCommand=='SelectCommand'
wm=builtins._so101_v8_generative_model
assert wm.rootComponent.bRepBodies.count==65
path='/Users/sugawaraichirou/Documents/ChatGPT/so101/output/v8/generative_obstacle_audit.json'
with open(path,encoding='utf-8') as f: report=json.load(f)
report['native_obstacle_count']=61
report['native_precheck']='Ready; only hidden-body visibility warning, no missing-obstacle warning'
report['native_role_reference']='All bodies assigned with Generative Model 1:1 assembly-context proxies'
assert app.activeDocument.save('61 native obstacles verified in precheck. Original servo details preserved; printed polymer assumption E1500 MPa; maximize stiffness 45g, displacement XYZ 0.1mm, SF2; additive Z+, minimum wall3mm. User authorized one 11-credit generation.')
with open(path,'w',encoding='utf-8') as f: json.dump(report,f,ensure_ascii=False,indent=2)
print('SAVED_VERIFIED_SETUP',app.activeDocument.name)
