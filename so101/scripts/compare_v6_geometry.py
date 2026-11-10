from pathlib import Path
import json
import gmsh

root=Path(__file__).resolve().parents[1]; out=root/'output/v6'
gmsh.initialize()
rows=[]
try:
    gmsh.option.setNumber('General.Terminal',0)
    # Sensor's imported coincident curved faces make OCC common unreliable;
    # solve the actual Fusion-exported four-part assembly independently instead.
    for label in ('base',):
        gmsh.model.add(label)
        a=gmsh.model.occ.importShapes(str(out/'offline_candidate'/f'{label}.step'),highestDimOnly=True)
        b=gmsh.model.occ.importShapes(str(out/'v6_short'/f'{label}.step'),highestDimOnly=True)
        assert len(a)==len(b)==1,(label,a,b)
        av=gmsh.model.occ.getMass(*a[0]); bv=gmsh.model.occ.getMass(*b[0])
        common,_=gmsh.model.occ.intersect(a,b)
        cv=sum(gmsh.model.occ.getMass(*c) for c in common if c[0]==3)
        difference=av+bv-2*cv
        assert abs(difference)<1e-3,(label,difference)
        rows.append({'part':label,'offline_volume_mm3':av,'Fusion_volume_mm3':bv,'symmetric_difference_mm3':difference})
        gmsh.clear()
finally:
    gmsh.finalize()
(out/'base_geometry_identity.json').write_text(json.dumps({'passed':True,'comparison':rows,'scope':'Base only. Other bodies solved from actual Fusion exports.'},indent=2))
print(json.dumps(rows,indent=2))
