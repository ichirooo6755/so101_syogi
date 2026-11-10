"""Reproducible, conditional linear-elastic load-path FEA of the CAD snapshot.

N, mm, MPa units.  This is NOT a calibrated model of SC616C electrical output.
The fixed sensor block is clamped; fastened mating faces are ideally bonded.
The base and the hidden old cover are excluded from this elastic solve, but
their actual CAD clearances are audited separately in geometry_audit.json.
"""
from pathlib import Path
import argparse
import json
import time

import gmsh
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import splu
from skfem import Basis, ElementVector, ElementTetP1, MeshTet, asm
from skfem.models.elasticity import linear_elasticity, lame_parameters
from skfem.helpers import sym_grad

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output'/'load_path_analysis'
INCLUDE_BASE=False
SENSOR_E=69000.
SENSOR_NU=.33
RESULT_TAG=''


def make_mesh(level):
    """Fragment touching solids into a conformal, material-tagged tetra mesh."""
    path=OUT/f'mesh_{level}.npz'
    if path.exists():
        data=np.load(path)
        return data['points'],data['tetra'],data['material'],json.loads(str(data['metadata']))
    gmsh.initialize()
    try:
        gmsh.option.setNumber('General.Terminal',0)
        gmsh.model.add('current_pen_load_path_'+level)
        labels=['sensor','carrier','cartridge']+(['base'] if INCLUDE_BASE else [])
        imported=[]
        initial_volumes=[]
        for label in labels:
            shapes=gmsh.model.occ.importShapes(str(OUT/(label+'.step')),highestDimOnly=True)
            vols=[(dim,tag) for dim,tag in shapes if dim==3]
            assert len(vols)==1,(label,vols)
            imported.extend(vols)
            initial_volumes.append(gmsh.model.occ.getMass(*vols[0]))
        shapes,maps=gmsh.model.occ.fragment(imported[:1],imported[1:])
        gmsh.model.occ.synchronize()
        tag_material={}
        for mat,group in enumerate(maps):
            for dim,tag in group:
                if dim==3:
                    assert tag not in tag_material,(tag,'initial volume overlap')
                    tag_material[tag]=mat
        assert set(tag_material)=={tag for dim,tag in gmsh.model.getEntities(3)}
        volumes=[sum(gmsh.model.occ.getMass(3,t) for t,m in tag_material.items() if m==i) for i in range(len(labels))]
        assert np.max(np.abs(np.array(volumes)/initial_volumes-1))<1e-5,(volumes,initial_volumes)
        # Sensor's approximate relief leaves thin ligaments; size those locally.
        global_h,sensor_h={'coarse':(2.5,.60),'fine':(1.7,.38),'refined':(1.2,.28)}[level]
        gmsh.option.setNumber('Mesh.MeshSizeMax',global_h)
        gmsh.option.setNumber('Mesh.MeshSizeMin',sensor_h*.55)
        gmsh.option.setNumber('Mesh.MeshSizeFromCurvature',20)
        gmsh.option.setNumber('Mesh.MeshSizeExtendFromBoundary',1)
        gmsh.option.setNumber('Mesh.Algorithm3D',1)
        gmsh.option.setNumber('Mesh.Optimize',1)
        gmsh.option.setNumber('General.NumThreads',4)
        gmsh.model.mesh.setSize(gmsh.model.getEntities(0),global_h)
        sensor_points=set()
        for tag,mat in tag_material.items():
            if mat==0:
                sensor_points.update(gmsh.model.getBoundary([(3,tag)],recursive=True))
        gmsh.model.mesh.setSize([p for p in sensor_points if p[0]==0],sensor_h)
        # Refine the entire sensor volume, not only its outside vertices.
        field=gmsh.model.mesh.field.add('Box')
        sensor_bounds=[gmsh.model.getBoundingBox(3,tag) for tag,mat in tag_material.items() if mat==0]
        lower=np.min(np.array(sensor_bounds)[:,:3],axis=0)-.5
        upper=np.max(np.array(sensor_bounds)[:,3:],axis=0)+.5
        for key,value in {'VIn':sensor_h,'VOut':global_h,'XMin':lower[0],'XMax':upper[0],
                          'YMin':lower[1],'YMax':upper[1],'ZMin':lower[2],'ZMax':upper[2],'Thickness':2}.items():
            gmsh.model.mesh.field.setNumber(field,key,value)
        gmsh.model.mesh.field.setAsBackgroundMesh(field)
        gmsh.model.mesh.generate(3)
        node_tags,coords,_=gmsh.model.mesh.getNodes()
        points=np.asarray(coords).reshape(-1,3)
        lookup={int(tag):i for i,tag in enumerate(node_tags)}
        tetra=[]; material=[]
        quality_tags=[]
        for tag,mat in sorted(tag_material.items()):
            types,element_tags,element_nodes=gmsh.model.mesh.getElements(3,tag)
            for typ,etags,enodes in zip(types,element_tags,element_nodes):
                assert typ==4,('expected first-order tetrahedra',typ)
                cells=np.array([lookup[int(v)] for v in enodes],dtype=np.int32).reshape(-1,4)
                tetra.extend(cells); material.extend([mat]*len(cells)); quality_tags.extend(etags)
        tetra=np.asarray(tetra,dtype=np.int32); material=np.asarray(material,dtype=np.int8)
        quality=gmsh.model.mesh.getElementQualities(quality_tags,'minSICN')
        assert np.min(quality)>0,('inverted elements',np.min(quality))
        # No detached island may be hidden by a solver's regularization.
        rows=np.repeat(tetra[:,0],3); cols=tetra[:,1:].reshape(-1)
        graph=sp.coo_matrix((np.ones(len(rows)),(rows,cols)),shape=(len(points),len(points)))
        components=sp.csgraph.connected_components(graph+graph.T)[0]
        assert components==1,('disconnected mesh',components)
        metadata={'labels':labels,'cad_volumes_mm3':volumes,'global_size_mm':global_h,
                  'sensor_size_mm':sensor_h,'nodes':len(points),'tetrahedra':len(tetra),
                  'minimum_scaled_jacobian':float(np.min(quality)),'connected_components':components,
                  'material_counts':{labels[i]:int(np.sum(material==i)) for i in range(len(labels))},
                  'include_base':INCLUDE_BASE}
        gmsh.write(str(OUT/f'mesh_{level}.msh'))
        np.savez_compressed(path,points=points,tetra=tetra,material=material,metadata=json.dumps(metadata))
        print('MESH',json.dumps(metadata),flush=True)
        return points,tetra,material,metadata
    finally:
        gmsh.finalize()


def skew(v):
    x,y,z=v
    return np.array([[0,-z,y],[z,0,-x],[-y,x,0]])


def equivalent_load(points,nodes,force,application_point,reference,moment=None):
    """Distributed bore load with exactly the prescribed force AND moment.

    Minimum Euclidean-norm nodal loads represent the rigid, intact glue joint.
    Negative nodal forces are allowed, i.e. this is a bonded joint, not contact.
    """
    levers=points[nodes]-reference
    a=np.zeros((6,3*len(nodes)))
    for i,lever in enumerate(levers):
        a[:3,3*i:3*i+3]=np.eye(3)
        a[3:,3*i:3*i+3]=skew(lever)
    target=np.r_[force,np.cross(application_point-reference,force)+(np.zeros(3) if moment is None else moment)]
    nodal=a.T@np.linalg.solve(a@a.T,target)
    assert np.max(np.abs(a@nodal-target))<1e-10
    f=np.zeros(3*len(points)); f[(3*nodes[:,None]+np.arange(3)).ravel()]=nodal
    return f,target


def analyze(level,only_soft=False):
    started=time.time()
    points,tetra,material,mesh_info=make_mesh(level)
    assert mesh_info.get('include_base',False)==INCLUDE_BASE,'Do not reuse an incompatible cached mesh'
    # Do not let MeshTet reorder elements, since material labels follow them.
    mesh=MeshTet(points.T,tetra.T,sort_t=False)
    assert np.array_equal(mesh.t,tetra.T)
    basis=Basis(mesh,ElementVector(ElementTetP1()),intorder=1)
    assert np.array_equal(basis.nodal_dofs,np.arange(3*len(points)).reshape(-1,3).T)
    part_elements=[np.flatnonzero(material==i) for i in range(len(mesh_info['labels']))]
    part_nodes=[np.unique(tetra[elems]) for elems in part_elements]
    # This isolates the approximate sensor's deforming region from the fixed
    # block; it is not a substitute for a measured bolt/contact stiffness.
    if INCLUDE_BASE:
        candidate=part_nodes[3]
        horn_radius=np.hypot(points[candidate,0]+2,points[candidate,2]-34)
        fixed_nodes=candidate[(horn_radius<=13.00001)&
            (np.isclose(points[candidate,1],-17.05,atol=1e-6)|np.isclose(points[candidate,1],20.2,atol=1e-6))]
    else:
        fixed_nodes=part_nodes[0][points[part_nodes[0],1]>=23.46294620236-1e-6]
    D=(3*fixed_nodes[:,None]+np.arange(3)).ravel()
    I=np.setdiff1d(np.arange(basis.N),D)
    assert len(fixed_nodes)>20
    audit=json.loads((OUT/'geometry_audit.json').read_text())
    cx,cy=map(float,audit['brush_axis_mm'])
    candidate=part_nodes[2]
    radial=np.hypot(points[candidate,0]-cx,points[candidate,1]-cy)
    load_nodes=candidate[(radial<8.01)&(points[candidate,2]>audit.get('bore_load_z_min_mm',10.5))
                         &(points[candidate,2]<audit.get('bore_load_z_max_mm',42.5))]
    assert len(load_nodes)>30,len(load_nodes)
    cap_nodes=None
    if 'brush_stop_z_mm' in audit:
        cap_nodes=candidate[(radial<7.71)&np.isclose(points[candidate,2],audit['brush_stop_z_mm'],atol=1e-6)]
        assert len(cap_nodes)>10,('brush stop load surface',len(cap_nodes))
    sensor_center=points[part_nodes[0]].min(axis=0)/2+points[part_nodes[0]].max(axis=0)/2
    reference=np.array([sensor_center[0],15.96294620236,sensor_center[2]])
    brush_tip=np.array([cx,cy,audit.get('assumed_brush_tip_z_mm',-40.)])
    cases=[('normal_1N',np.array([0.,0.,1.]),brush_tip),
           ('normal_5N',np.array([0.,0.,5.]),brush_tip),
           ('side_X_0p5N',np.array([.5,0,0]),brush_tip),
           ('side_Y_0p5N',np.array([0,.5,0]),brush_tip)]
    if INCLUDE_BASE:
        cases=[('normal_6N',np.array([0.,0.,6.]),brush_tip),
               ('normal_6N_side_X_0p5N',np.array([.5,0.,6.]),brush_tip),
               ('normal_6N_side_X_m0p5N',np.array([-.5,0.,6.]),brush_tip),
               ('normal_6N_side_Y_0p5N',np.array([0.,.5,6.]),brush_tip),
               ('normal_6N_side_Y_m0p5N',np.array([0.,-.5,6.]),brush_tip),
               ('normal_6N_twist_Z_10Nmm',np.array([0.,0.,6.]),brush_tip),
               ('normal_6N_twist_Z_m10Nmm',np.array([0.,0.,6.]),brush_tip),
               ('combined_6N_X0p5_Y0p5_twist_Z_10Nmm',np.array([.5,.5,6.]),brush_tip)]
    # The sensor-only cut uses all free-side sensor elements and evaluates
    # internal nodal forces at its artificial cut. No output-sensitivity model.
    centers=points[tetra].mean(axis=1)
    low_sensor=part_elements[0][centers[part_elements[0],1]<reference[1]]
    high_sensor=part_elements[0][centers[part_elements[0],1]>=reference[1]]
    cut_nodes=np.intersect1d(np.unique(tetra[low_sensor]),np.unique(tetra[high_sensor]))
    assert len(cut_nodes)>10
    reports=[]
    fields={}
    for printed_E in ((1500.,) if only_soft else (1500.,3000.)):
        print('ASSEMBLE',level,printed_E,'DOF',basis.N,flush=True)
        mats=[(SENSOR_E,SENSOR_NU)]+[(printed_E,.35)]*(len(part_elements)-1)
        Ks=[]
        for elems,(E,nu) in zip(part_elements,mats):
            lam,mu=lame_parameters(E,nu)
            Ks.append(asm(linear_elasticity(lam,mu),basis.with_elements(elems)))
        K=sum(Ks).tocsr()
        sym=sp.linalg.norm(K-K.T)/sp.linalg.norm(K)
        assert sym<1e-12,sym
        # Rigid translations must have zero strain energy (patch test).
        rigid_residual=[]
        diagscale=float(abs(K.diagonal()).max())
        for axis in range(3):
            trans=np.zeros(basis.N); trans[axis::3]=1
            rigid_residual.append(float(np.linalg.norm(K@trans,np.inf)/diagscale))
        assert max(rigid_residual)<1e-10,rigid_residual
        lam,mu=lame_parameters(*mats[0])
        Klow=asm(linear_elasticity(lam,mu),basis.with_elements(low_sensor)).tocsr()
        solver=splu(K[I][:,I].tocsc())
        for name,force,application_point in cases:
            used_nodes=cap_nodes if cap_nodes is not None and force[2]!=0 else load_nodes
            torque=10. if name.endswith('twist_Z_10Nmm') else -10. if name.endswith('twist_Z_m10Nmm') else 0.
            extra_moment=np.array([0.,0.,torque])
            distributed_side_or_torque=INCLUDE_BASE and (force[0]!=0 or force[1]!=0 or torque!=0)
            if distributed_side_or_torque:
                f,target=equivalent_load(points,cap_nodes,np.array([0.,0.,force[2]]),application_point,reference)
                side_f,side_target=equivalent_load(points,load_nodes,np.array([force[0],force[1],0.]),application_point,reference,extra_moment)
                f+=side_f; target+=side_target
            else:
                f,target=equivalent_load(points,used_nodes,force,application_point,reference,extra_moment)
            u=np.zeros(basis.N); u[I]=solver.solve(f[I])
            residual=K@u-f
            assert np.linalg.norm(residual[I])/np.linalg.norm(f[I])<1e-6
            displacement=u.reshape(-1,3)
            reaction=residual.reshape(-1,3)[fixed_nodes]
            resultant=reaction.sum(axis=0)
            reaction_moment=np.cross(points[fixed_nodes]-reference,reaction).sum(axis=0)
            assert np.linalg.norm(resultant+force)<1e-6,(name,resultant,force)
            assert np.linalg.norm(reaction_moment+target[3:])<1e-5,(name,reaction_moment,target)
            cut_force=(Klow@u).reshape(-1,3)[cut_nodes]
            cut_resultant=cut_force.sum(axis=0)
            cut_moment=np.cross(points[cut_nodes]-reference,cut_force).sum(axis=0)
            assert np.linalg.norm(cut_resultant+force)<1e-5,(name,cut_resultant,force)
            assert np.linalg.norm(cut_moment+target[3:])<1e-4,(name,cut_moment,target)
            strains=basis.interpolate(u).grad
            strain=.5*(strains+strains.swapaxes(0,1))
            stress=np.zeros_like(strain)
            for elems,(E,nu) in zip(part_elements,mats):
                lam,mu=lame_parameters(E,nu)
                se=strain[:,:,elems,:]
                stress[:,:,elems,:]=2*mu*se+lam*np.eye(3)[:,:,None,None]*np.einsum('iieq->eq',se)[None,None,:,:]
            s=stress[:,:,:,0]
            vm=np.sqrt(.5*((s[0,0]-s[1,1])**2+(s[1,1]-s[2,2])**2+(s[2,2]-s[0,0])**2)+3*(s[0,1]**2+s[1,2]**2+s[2,0]**2))
            norm=np.linalg.norm(displacement,axis=1)
            sensor_gauge=part_elements[0][(centers[part_elements[0],1]>9.96294620236)&(centers[part_elements[0],1]<21.96294620236)]
            report={'case':name,'printed_E_MPa':printed_E,'force_N':force.tolist(),
                    'load_surface':('butt stop plus bonded sleeve bore' if distributed_side_or_torque
                                    else 'brush butt stop' if used_nodes is cap_nodes else 'bonded sleeve bore'),
                    'additional_torque_Nmm':extra_moment.tolist(),
                    'assumed_brush_tip_mm':application_point.tolist(),
                    'gauge_reference_mm':reference.tolist(),'applied_resultant_N_Nmm':target.tolist(),
                    'fixed_reaction_N':resultant.tolist(),'fixed_reaction_moment_Nmm':reaction_moment.tolist(),
                    'sensor_cut_force_N':cut_resultant.tolist(),'sensor_cut_moment_Nmm':cut_moment.tolist(),
                    'equilibrium_error_N':float(np.linalg.norm(resultant+force)),
                    'free_DOF_relative_residual':float(np.linalg.norm(residual[I])/np.linalg.norm(f[I])),
                    'max_displacement_mm':float(norm.max()),
                    'brush_stop_mean_displacement_mm':displacement[cap_nodes].mean(axis=0).tolist() if cap_nodes is not None else None,
                    'parts':{label:{'max_displacement_mm':float(norm[nodes].max()),
                                     'max_von_mises_MPa':float(vm[elems].max()),
                                     'p95_von_mises_MPa':float(np.percentile(vm[elems],95))}
                             for label,nodes,elems in zip(mesh_info['labels'],part_nodes,part_elements)},
                    'sensor_gauge_p95_von_mises_MPa':float(np.percentile(vm[sensor_gauge],95)),
                    'max_printed_displacement_bound_mm':float(max(norm[part_nodes[1]].max(),norm[part_nodes[2]].max())),
                    'strain_energy_Nmm':float(.5*u@(K@u)),
                    'boundary_condition_note':('Ideal bonded contacts; both servo horn mating faces clamped; base compliance included; no bolt slip, glue creep, print anisotropy or electrical gauges'
                        if INCLUDE_BASE else 'Ideal bonded fastening faces; entire fixed sensor block clamped; no printed-base compliance, bolt slip, glue creep or electrical gauges')}
            reports.append(report)
            if printed_E==1500.:
                fields[name]={'u':displacement,'von_mises':vm,'strain_yy':strain[1,1,:,0]}
            print('SOLVED',level,printed_E,name,'max u',report['max_displacement_mm'],'cutF',cut_resultant.tolist(),flush=True)
        del solver,K,Ks
    # Export machine-readable fields with geometry, not an exaggerated result
    # silently substituting for the actual solid.
    import meshio
    for name,data in fields.items():
        meshio.write(OUT/f'{level}{RESULT_TAG}_{name}.vtu',meshio.Mesh(points,[('tetra',tetra)],
            point_data={'displacement_mm':data['u']},cell_data={'part_id':[material],
            'von_mises_MPa':[data['von_mises']],'strain_yy':[data['strain_yy']]}))
    result={'method':'Small-strain, isotropic, first-order tetrahedral linear elasticity',
            'sensor_E_MPa':SENSOR_E,'sensor_nu':SENSOR_NU,
            'not_a_prediction_of_electrical_readout':True,'source_geometry_file':'geometry_audit.json',
            'mesh':mesh_info,'DOF':int(basis.N),'fixed_nodes':len(fixed_nodes),'glue_load_nodes':len(load_nodes),
            'cases':reports,'runtime_seconds':time.time()-started}
    (OUT/f'fea_{level}{RESULT_TAG}.json').write_text(json.dumps(result,indent=2))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--level',choices=['coarse','fine','refined'],default='coarse')
    parser.add_argument('--only-soft',action='store_true')
    parser.add_argument('--input-dir',type=Path)
    parser.add_argument('--include-base',action='store_true')
    parser.add_argument('--sensor-e-mpa',type=float,default=69000.)
    parser.add_argument('--sensor-nu',type=float,default=.33)
    parser.add_argument('--result-tag',default='')
    args=parser.parse_args()
    if args.input_dir:
        OUT=args.input_dir.resolve()
    INCLUDE_BASE=args.include_base
    SENSOR_E=args.sensor_e_mpa
    SENSOR_NU=args.sensor_nu
    assert SENSOR_E>0 and 0<SENSOR_NU<.5
    assert not args.result_tag or all(c.isalnum() or c in '_-' for c in args.result_tag)
    RESULT_TAG=('_'+args.result_tag) if args.result_tag else ''
    analyze(args.level,args.only_soft)
