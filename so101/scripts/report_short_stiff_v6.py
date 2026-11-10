from pathlib import Path
import json

root=Path(__file__).resolve().parents[1]; out=root/'output/v6'
old=json.loads((root/'output/v5/analysis/fea_fine.json').read_text())
new=json.loads((out/'v6_short/fea_fine.json').read_text())
old_coarse=json.loads((root/'output/v5/analysis/fea_coarse.json').read_text())
new_coarse=json.loads((out/'offline_candidate/fea_coarse.json').read_text())
rows=[]
for a,b in zip(old['cases'],new['cases']):
    assert a['case']==b['case']
    ov=a['parts']['base']['max_displacement_mm']; nv=b['parts']['base']['max_displacement_mm']
    rows.append({'case':a['case'],'force_N':a['force_N'],'additional_torque_Nmm':a['additional_torque_Nmm'],
                 'V5_base_max_displacement_mm':ov,'V6_base_max_displacement_mm':nv,
                 'base_deflection_reduction_fraction':1-nv/ov,
                 'V5_assembly_max_displacement_mm':a['max_displacement_mm'],
                 'V6_assembly_max_displacement_mm':b['max_displacement_mm'],
                 'V5_base_peak_von_mises_MPa':a['parts']['base']['max_von_mises_MPa'],
                 'V6_base_peak_von_mises_MPa':b['parts']['base']['max_von_mises_MPa'],
                 'V6_equilibrium_residual_N':b['equilibrium_error_N']})
mesh=[]
for name,fine,coarse in (('V5',old,old_coarse),('V6',new,new_coarse)):
    f=fine['cases'][0]['parts']['base']['max_displacement_mm']
    c=coarse['cases'][0]['parts']['base']['max_displacement_mm']
    mesh.append({'version':name,'coarse_base_u_mm':c,'fine_base_u_mm':f,
                 'relative_change_from_coarse':f/c-1,
                 'fine_nodes':fine['mesh']['nodes'],'fine_tetrahedra':fine['mesh']['tetrahedra']})
report={'source':'Independent local FEA of actual Fusion-exported BRep solids, NOT Fusion cloud solver results',
        'printed_E_MPa':1500,'printed_nu':.35,'approx_sensor_E_MPa':69000,
        'boundary':'Both servo-horn mating faces fixed; real touching interfaces ideally bonded',
        'brush_total_length_mm':82.5,'brush_stop_z_mm':30.5,'brush_tip_z_mm':-52,
        'user_allows_brush_trimming':True,'reference_loads_are_assumed_test_cases':True,
        'base_length_reduction_mm':16,'rail_span_change_mm':[74,56],
        'base_volume_change_mm3':[29688.678172181015,34383.20028727208],
        'native_Fusion_base_matches_offline_candidate':True,'cases':rows,'mesh_sensitivity':mesh,
        'mesh_convergence_certified':False,
        'limitations':['First-order tetrahedra are mesh-sensitive; compare trends, not certified absolute values',
                       'No layer anisotropy, infill, creep, temperature, bolt preload, slip, contact separation or hot-glue compliance',
                       'Servo and user-cut wrist compliance excluded by clamped horn boundary',
                       'Brush treated as a rigid load application, not an elastic brush model',
                       'Approximate sensor solid has no measured gauges, bridge, adhesive, resin or electrical cross-sensitivity',
                       'Force equilibrium through sensor is not a validation of electrical accuracy'],
        'generative_design_used':False,'FDM_strength_certified':False,'electrical_output_validated':False}
(out/'comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({'normal_6N':rows[0],'mesh_sensitivity':mesh},ensure_ascii=False,indent=2))
