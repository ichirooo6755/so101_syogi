"""Sphere-grid numerical sanity tests; not a convergence or fidelity proof."""
import numpy as np
from sphere_grid import GridFilm, GridParams
f=GridFilm(GridParams(grid_width=256,swirl=0,gravity=0,marangoni=0))
errors=[]
for field in (f.xyz[...,0],f.xyz[...,2]):
 psi=f.solve_poisson(2*field);psi-=np.sum(psi*f.weights)/np.sum(f.weights)
 errors.append(float(np.sqrt(np.sum((psi-field)**2*f.weights)/np.sum(f.weights))))
assert max(errors)<2e-4,errors
h=f.h.copy();gamma=f.gamma.copy();f.step()
assert np.max(np.abs(f.h-h))<1e-8
assert np.max(np.abs(f.gamma-gamma))<1e-8
field=f.xyz[...,0]+2*f.xyz[...,1]+3*f.xyz[...,2]
p=np.array([[-1,1e-8,0],[-1,-1e-8,0],[1e-8,0,1],[-1e-8,0,1],[1e-8,0,-1],[-1e-8,0,-1]],float);p/=np.linalg.norm(p,axis=1)[:,None]
v=f._sample(field,p)
assert abs(v[0]-v[1])<1e-5 and abs(v[2]-v[3])<1e-5 and abs(v[4]-v[5])<1e-5
assert np.max(np.abs(v-(p[:,0]+2*p[:,1]+3*p[:,2])))<.002
f=GridFilm(GridParams(grid_width=256));h=f.h.copy();mass=f.h_mass;g=f.gamma_mass
for _ in range(50):f.step()
assert np.isfinite(f.h).all() and f.h.min()>0
assert abs(f.integral(f.h)/mass-1)<1e-12
assert abs(f.integral(f.gamma)/g-1)<1e-12
assert abs(f.integral(f.omega))<1e-8
assert np.mean(np.abs(f.h-h))>1e-3
print('spherical coordinate Poisson RMS:',errors)
print('seam difference:',abs(v[0]-v[1]),'north/south pole difference:',abs(v[2]-v[3]),abs(v[4]-v[5]))
print('50-step thickness relative mass error with global correction:',abs(f.integral(f.h)/mass-1),'range nm:',f.h.min(),f.h.max())
