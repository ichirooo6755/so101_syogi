"""Research prototype: vortex particle/mesh flow on a fixed sphere.

This is NOT a full reproduction of Tao et al. 2024. See README_PARTICLE.md.
"""
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import numpy as np
from scipy.ndimage import map_coordinates
from scipy.special import sph_harm_y
from simulator import Film, Params, interference
from PIL import Image

@dataclass
class ParticleParams:
    subdivision:int=3
    grid_width:int=512
    particles_per_face:int=4
    fine_vortices:float=0.8
    dt:float=0.035
    swirl:float=12.0
    gravity:float=0.008
    marangoni:float=0.008
    damping:float=0.7
    thickness_nm:float=400.
    variation_nm:float=210.
    surfactant_variation:float=0.12
    exposure:float=0.7
    saturation:float=1.5
    seed:int=12

class ParticleFilm:
    def __init__(self,p):
        self.p=p
        if not 2<=p.subdivision<=5 or p.grid_width not in (256,512,1024,2048) or not 1<=p.particles_per_face<=12 or not 0<=p.fine_vortices<=1:
            raise ValueError('計算解像度が範囲外です')
        if not (0<p.dt<=.1 and 0<=p.swirl<=20 and 0<=p.gravity<=1 and 0<=p.marangoni<=1 and 0<=p.damping<=5 and 0<p.variation_nm<p.thickness_nm<=10000 and 0<=p.surfactant_variation<=.5 and 0.05<=p.exposure<=4 and 0<=p.saturation<=3):
            raise ValueError('物理パラメータが範囲外です')
        self.mesh=Film(Params(subdivision=p.subdivision,swirl=p.swirl,dt=p.dt,drainage=0,thickness_nm=p.thickness_nm,variation_nm=p.variation_nm,seed=p.seed))
        m=self.mesh; self.v=m.v; self.f=m.f; self.area=m.area
        self.W=p.grid_width; self.H=self.W//2
        lon=(np.arange(self.W)+.5)*2*np.pi/self.W-np.pi
        lat=np.pi/2-(np.arange(self.H)+.5)*np.pi/self.H
        lons,lats=np.meshgrid(lon,lat)
        self.xyz=np.stack((np.cos(lats)*np.cos(lons),np.cos(lats)*np.sin(lons),np.sin(lats)),axis=-1)
        self.grid_weights=np.cos(lats)
        # The geometry is static; cache the triangle/barycentric coordinates at grid pixel centers.
        self.grid_faces=np.empty((self.H*self.W,3),np.int32); self.grid_bary=np.empty((self.H*self.W,3),np.float32)
        xyzflat=self.xyz.reshape(-1,3)
        for i in range(0,len(xyzflat),4096):
            f,b=m.sample(xyzflat[i:i+4096]); self.grid_faces[i:i+4096]=f; self.grid_bary[i:i+4096]=b
        rng=np.random.default_rng(p.seed)
        n=len(m.f)*p.particles_per_face
        r=np.sqrt(rng.random(n)); t=rng.random(n)
        bary=np.stack((1-r,r*(1-t),r*t),axis=1)
        faceidx=np.repeat(np.arange(len(m.f)),p.particles_per_face)
        self.particles=np.einsum('ni,nij->nj',bary,m.v[m.f[faceidx]])
        self.particles/=np.linalg.norm(self.particles,axis=1)[:,None]
        # Initially localized counter-rotating vortex pairs; no animated noise forcing.
        coords=m.centers
        count=700
        anchor=rng.normal(size=(count,3));anchor/=np.linalg.norm(anchor,axis=1)[:,None]
        tangent=rng.normal(size=(count,3));tangent-=anchor*np.sum(anchor*tangent,axis=1)[:,None]
        tangent/=np.linalg.norm(tangent,axis=1)[:,None]
        sep=rng.uniform(.03,.12,count)
        plus=anchor*np.cos(sep[:,None]/2)+tangent*np.sin(sep[:,None]/2)
        minus=anchor*np.cos(sep[:,None]/2)-tangent*np.sin(sep[:,None]/2)
        widths=rng.uniform(.045,.12,count); strengths=rng.normal(size=count)
        # Smoothly taper the initial stirring toward the poles.
        strengths*=np.maximum(0,1-anchor[:,2]**4)
        omega=np.zeros(len(m.f))
        for i in range(0,count,32):
            sl=slice(i,i+32)
            omega+=(np.exp((coords@plus[sl].T-1)/widths[sl]**2)-np.exp((coords@minus[sl].T-1)/widths[sl]**2))@strengths[sl]
        theta=np.arccos(np.clip(coords[:,2],-1,1));azimuth=np.arctan2(coords[:,1],coords[:,0])
        components=[]
        for degree in range(9):
            components.append(sph_harm_y(degree,0,theta,azimuth).real)
            for order in range(1,degree+1):
                value=sph_harm_y(degree,order,theta,azimuth)
                components.extend((value.real,value.imag))
        basis=np.stack(components,axis=1);w=np.sqrt(m.area)
        projection=np.linalg.lstsq(basis*w[:,None],omega*w,rcond=1e-10)[0]
        omega-=p.fine_vortices*(basis@projection)
        omega-=np.average(omega,weights=m.area)
        omega*=p.swirl/(np.sqrt(np.average(omega**2,weights=m.area))+1e-20)
        self.circulation=omega[faceidx]*m.area[faceidx]/p.particles_per_face
        self.circulation-=np.sum(self.circulation)/len(self.circulation)
        self.phi=np.zeros(len(m.v)); self.time=0.
        # Static smooth initial conditions, generated once; all animation is advection and forces.
        z=self.xyz[...,2]
        bands=self._initial_structure(rng)
        self.h=p.thickness_nm + p.variation_nm*(-.85*z+.45*(1-z**6)*bands)
        self.gamma=1+p.surfactant_variation*(.50*z+.44*self._initial_structure(rng))
        self.h=np.maximum(self.h,1.); self.gamma=np.maximum(self.gamma,.05)
        self.initial_h_mass=self.integral(self.h); self.initial_gamma_mass=self.integral(self.gamma)
        self.update_velocity()
    def _initial_structure(self,rng):
        result=np.zeros((self.H,self.W),np.float64)
        for frequency,amp in ((7,.30),(14,.30),(28,.28),(55,.24),(100,.18),(170,.11)):
            for _ in range(8):
                axis=rng.normal(size=3); axis/=np.linalg.norm(axis)
                phase=rng.uniform(0,2*np.pi)
                result+=amp*np.sin(frequency*np.einsum('...i,i->...',self.xyz,axis)+phase)
        result/=max(np.max(np.abs(result)),1e-12)
        return result
    def integral(self,field):
        return float(np.sum(field*self.grid_weights))
    def _sample_grid(self,field,points,clamp_bounds=False):
        # Across a pole, the continuation is the reflected latitude with longitude shifted by pi.
        arr=np.concatenate((np.roll(field[:1],self.W//2,axis=1),field,np.roll(field[-1:],self.W//2,axis=1)),axis=0)
        arr=np.concatenate((arr[:,-1:],arr,arr[:,:1]),axis=1)
        lon=np.arctan2(points[...,1],points[...,0]); lat=np.arcsin(np.clip(points[...,2],-1,1))
        x=(lon+np.pi)*(self.W/(2*np.pi))-.5+1
        y=(np.pi/2-lat)*(self.H/np.pi)-.5+1
        values=map_coordinates(arr,[y,x],order=1,mode='nearest',prefilter=False)
        if not clamp_bounds:return values
        ix=np.floor(x).astype(int); iy=np.floor(y).astype(int)
        ix=np.clip(ix,0,self.W); iy=np.clip(iy,0,self.H)
        vals=np.stack((arr[iy,ix],arr[iy,ix+1],arr[iy+1,ix],arr[iy+1,ix+1]))
        return values,vals.min(axis=0),vals.max(axis=0)
    def _at_vertices(self,field):
        return self._sample_grid(field,self.v)
    def _grid_from_vertex(self,field):
        weights=self.grid_bary; return np.sum(field[self.grid_faces]*weights,axis=1).reshape(self.H,self.W)
    def _vertex_velocity(self):
        m=self.mesh
        return np.stack([m.vertex_average(self.velocity[:,j]) for j in range(3)],axis=1)
    def _face_interpolate(self,points,vertex_values):
        orig=points.shape[:-1]; pts=points.reshape(-1,3)
        out=np.empty((len(pts),3),float)
        for i in range(0,len(pts),4096):
            f,b=self.mesh.sample(pts[i:i+4096]); out[i:i+4096]=np.einsum('ni,nij->nj',b,vertex_values[f])
        out-=pts*np.sum(out*pts,axis=1)[:,None]
        return out.reshape(*orig,3)
    @staticmethod
    def _move(points,v,dt):
        speed=np.linalg.norm(v,axis=-1); angle=speed*dt
        return np.cos(angle)[...,None]*points + np.sin(angle)[...,None]*v/(speed[...,None]+1e-30)
    def _deposit(self):
        m=self.mesh; f,b=m.sample(self.particles)
        vtx=np.bincount(f.ravel(),weights=(b*self.circulation[:,None]).ravel(),minlength=len(m.v))
        vtx-=np.sum(vtx)*m.vertex_area/np.sum(m.vertex_area)
        return vtx,f,b
    def _solve(self,rhs):
        m=self.mesh; ans=np.zeros(len(m.v)); rhs=rhs-np.sum(rhs)*m.vertex_area/np.sum(m.vertex_area); ans[1:]=m.solve(rhs[1:]);return ans
    def update_velocity(self):
        m=self.mesh
        rhs,self.part_faces,self.part_bary=self._deposit()
        psi=self._solve(rhs)
        gradpsi=np.einsum('fi,fij->fj',psi[m.f],m.grad)
        gradphi=np.einsum('fi,fij->fj',self.phi[m.f],m.grad)
        self.velocity=np.cross(m.norm,gradpsi)+gradphi
        # weak Laplacian: div grad(phi) = -M^{-1} K phi
        face_grad=np.einsum('fi,fij->fj',self.phi[m.f],m.grad)
        weak=(m.area[:,None]*np.einsum('fij,fj->fi',m.grad,face_grad))
        kval=np.bincount(m.f.ravel(),weights=weak.ravel(),minlength=len(m.v))
        self.divergence=-kval/m.vertex_area
        self.vel_vertices=self._vertex_velocity()
    def _advance_fields(self,dt):
        v=np.einsum('ni,nij->nj',self.grid_bary,self.vel_vertices[self.grid_faces]).reshape(self.H,self.W,3)
        v-=self.xyz*np.sum(v*self.xyz,axis=-1)[...,None]
        back=self._move(self.xyz,v,-dt); forward=self._move(self.xyz,v,dt)
        div=self._grid_from_vertex(self.divergence)
        def advect(field,mass):
            first,lo,hi=self._sample_grid(field,back,True)
            rev=self._sample_grid(first,forward)
            corrected=np.clip(first+.5*(field-rev),lo,hi)
            corrected*=np.exp(np.clip(-div*dt,-.4,.4))
            corrected=np.maximum(corrected,1e-6)
            # Compensate semi-Lagrangian volume drift; this is global, not locally conservative.
            corrected*=mass/self.integral(corrected)
            return corrected
        self.h=advect(self.h,self.initial_h_mass)
        self.gamma=advect(self.gamma,self.initial_gamma_mass)
    def _forces(self,dt):
        m=self.mesh
        gv=self._at_vertices(self.gamma); hv=self._at_vertices(self.h)
        gradgamma=np.einsum('fi,fij->fj',gv[m.f],m.grad)
        gravity=np.array([0.,0.,-1.]); g=gravity-m.norm*np.sum(m.norm*gravity,axis=1)[:,None]
        force=self.p.gravity*g-self.p.marangoni*gradgamma/(np.mean(hv[m.f],axis=1)[:,None]/self.p.thickness_nm)
        def project(vector):
            value=m.area[:,None]*np.einsum('fij,fj->fi',m.grad,vector)
            return np.bincount(m.f.ravel(),weights=value.ravel(),minlength=len(m.v))
        # Potential projection of gravity and Marangoni acceleration; damping models unresolved drag.
        self.phi=np.exp(-self.p.damping*dt)*self.phi+dt*self._solve(project(force))
        # FLIP-like circulation update: distribute the rotational force increment through the same P2M weights.
        delta=dt*project(-np.cross(m.norm,force))
        weights=np.bincount(self.part_faces.ravel(),weights=self.part_bary.ravel(),minlength=len(m.v))
        normalized=delta/(weights+1e-20)
        self.circulation+=np.sum(self.part_bary*normalized[self.part_faces],axis=1)
        self.circulation-=np.sum(self.circulation)/len(self.circulation)
    def step(self):
        dt=self.p.dt
        self.update_velocity()
        self._advance_fields(dt)
        if (not np.isfinite(self.h).all() or not np.isfinite(self.gamma).all()
            or self.h.min()<0.02*self.p.thickness_nm or self.h.max()>20*self.p.thickness_nm
            or self.gamma.max()>20):
            raise RuntimeError('膜厚または界面活性剤が計算の安定範囲を超えました。時間刻みや力を小さくしてください。')
        self._forces(dt)
        # Midpoint RK2 follows the tangent velocity and projects onto the sphere analytically.
        v0=self._face_interpolate(self.particles,self.vel_vertices)
        middle=self._move(self.particles,v0,dt*.5)
        vmid=self._face_interpolate(middle,self.vel_vertices)
        # Reproject the midpoint velocity into the tangent plane at the old point.
        vmid-=self.particles*np.sum(vmid*self.particles,axis=1)[:,None]
        self.particles=self._move(self.particles,vmid,dt)
        self.particles/=np.linalg.norm(self.particles,axis=1)[:,None]
        self.time+=dt
    def maps(self,width):
        if width<32 or width%2: raise ValueError('width must be an even integer >= 32')
        self.update_velocity(); vv=self.vel_vertices; m=self.mesh
        h=np.empty((width//2,width),np.float32); vel=np.empty((width//2,width,3),np.float32)
        lon=(np.arange(width)+.5)/width*2*np.pi-np.pi
        for j in range(width//2):
            lat=np.pi/2-(j+.5)/(width//2)*np.pi
            pts=np.stack([np.cos(lat)*np.cos(lon),np.cos(lat)*np.sin(lon),np.full(width,np.sin(lat))],axis=1)
            h[j]=self._sample_grid(self.h,pts)
            vel[j]=self._face_interpolate(pts,vv)
        return h,vel

def export(film,directory,frame,width,velocity_range=2.):
    if not np.isfinite(velocity_range) or velocity_range<=0:
        raise ValueError('速度画像の最大値は正の有限値で指定してください')
    out=Path(directory);out.mkdir(parents=True,exist_ok=True)
    h,v=film.maps(width); speed=np.linalg.norm(v,axis=2); direction=v/(speed[...,None]+1e-20)
    imgs={'color':interference(h,film.p.exposure,film.p.saturation),'thickness_nm':np.uint16(np.clip(h,0,65535)+.5),'velocity':np.uint8(np.clip(v/velocity_range*.5+.5,0,1)*255+.5),'direction':np.uint8(np.clip(direction*.5+.5,0,1)*255+.5)}
    for name,image in imgs.items(): Image.fromarray(image).save(out/f'{name}_{frame:04d}.png')
    np.savez_compressed(out/f'state_{frame:04d}.npz',vertices=film.v,faces=film.f,thickness_grid_nm=film.h,surfactant_grid=film.gamma,particles=film.particles,circulation=film.circulation,phi=film.phi,velocity_face_xyz=film.velocity,time=film.time)
    clip_fraction=float(np.count_nonzero((v>velocity_range)|(v< -velocity_range))/v.size)
    metadata={'parameters':asdict(film.p),'time':film.time,'width':width,'height':width//2,'fluid_grid':[film.W,film.H],'particles':len(film.particles),'thickness_png':'uint16 nm','velocity_png':f'RGB XYZ, decode (value/255*2-1)*{velocity_range}; values clip outside range','velocity_clipped_component_fraction':clip_fraction,'direction_png':'RGB XYZ, decode value/255*2-1; near-zero speed direction has no meaning','color_png':'spectral interference approximation with exposure and saturation grading; sRGB','geometry':'unit sphere; equirectangular north up; pixel centers; seam +/-pi','model':'fixed sphere, vortex particle-mesh prototype with approximate projected force, semi-Lagrangian film/surfactant grid, global mass correction; not full Tao 2024 solver'}
    (out/f'metadata_{frame:04d}.json').write_text(json.dumps(metadata,indent=2))
