"""Numerical sanity checks, not a substitute for convergence/physical validation."""
import numpy as np
from particle_film import ParticleFilm, ParticleParams

f=ParticleFilm(ParticleParams(subdivision=2,grid_width=256,particles_per_face=2,swirl=0,gravity=0,marangoni=0,damping=0))
h=f.h.copy();g=f.gamma.copy();f.step()
stationary=float(np.max(np.abs(f.h-h)))
assert stationary<1e-8, stationary
assert np.max(np.abs(f.gamma-g))<1e-8

field=f.xyz[...,0]+2*f.xyz[...,1]+3*f.xyz[...,2]
p=np.array([[-1,1e-8,0],[-1,-1e-8,0],[1e-8,0,1],[-1e-8,0,1]],float)
p/=np.linalg.norm(p,axis=1)[:,None]
v=f._sample_grid(field,p)
seam=float(abs(v[0]-v[1]));pole=float(abs(v[2]-v[3]))
assert seam<1e-5 and pole<1e-5,(seam,pole)
assert np.max(np.abs(v-(p[:,0]+2*p[:,1]+3*p[:,2])))<.002

f=ParticleFilm(ParticleParams(subdivision=2,grid_width=256,particles_per_face=3))
initial=f.h.copy();m=f.initial_h_mass;gamma=f.initial_gamma_mass
for _ in range(30):f.step()
assert abs(f.integral(f.h)/m-1)<1e-12
assert abs(f.integral(f.gamma)/gamma-1)<1e-12
assert abs(np.sum(f.circulation))<1e-10
assert np.max(np.abs(np.linalg.norm(f.particles,axis=1)-1))<1e-12
assert f.h.min()>0 and np.isfinite(f.h).all()
assert np.mean(np.abs(f.h-initial))>1e-3
print(f'stationary max error: {stationary:.3g}; seam: {seam:.3g}; pole: {pole:.3g}')
print(f'30-step thickness mass relative error: {abs(f.integral(f.h)/m-1):.3g}; circulation sum: {np.sum(f.circulation):.3g}; thickness range: {f.h.min():.1f}..{f.h.max():.1f} nm')
print('Mass check includes the explicit global correction. Convergence and physical fidelity remain unverified.')
