"""Mesh-free spherical vorticity-grid experiment. See README.md for limitations."""
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import numpy as np
from scipy.ndimage import map_coordinates
from PIL import Image
from simulator import interference

@dataclass
class GridParams:
    grid_width:int=1024
    dt:float=.035
    swirl:float=5.
    fine_vortices:float=0.
    initial_detail_nm:float=0.
    gravity:float=.008
    marangoni:float=.008
    thickness_nm:float=600.
    variation_nm:float=300.
    surfactant_variation:float=.12
    exposure:float=.35
    saturation:float=1.0
    seed:int=12

class GridFilm:
    def __init__(self,p):
        self.p=p
        if p.grid_width not in (256,512,1024,2048) or not (0<p.dt<=.1 and 0<=p.swirl<=30 and 0<=p.fine_vortices<=1 and 0<=p.initial_detail_nm<=300 and 0<=p.gravity<=1 and 0<=p.marangoni<=1 and 0<p.variation_nm<p.thickness_nm<=10000 and 0<=p.surfactant_variation<=.5 and .05<=p.exposure<=4 and 0<=p.saturation<=3):raise ValueError('パラメータが範囲外です')
        self.W=p.grid_width;self.H=self.W//2;self.dlat=np.pi/self.H;self.dlon=2*np.pi/self.W
        self.lon=(np.arange(self.W)+.5)*self.dlon-np.pi
        self.lat=np.pi/2-(np.arange(self.H)+.5)*self.dlat
        lon,lat=np.meshgrid(self.lon,self.lat);self.coslat=np.cos(lat);self.sinlat=np.sin(lat)
        self.xyz=np.stack((self.coslat*np.cos(lon),self.coslat*np.sin(lon),self.sinlat),axis=-1)
        self.east=np.stack((-np.sin(lon),np.cos(lon),np.zeros_like(lon)),axis=-1)
        self.north=np.stack((-self.sinlat*np.cos(lon),-self.sinlat*np.sin(lon),self.coslat),axis=-1)
        self.weights=self.coslat
        self._prepare_poisson()
        rng=np.random.default_rng(p.seed)
        self.omega=self._initial_vorticity(rng)
        bands=self._initial_field(rng)
        self.h=p.thickness_nm+p.variation_nm*(-.85*self.sinlat+.45*(1-self.sinlat**6)*bands)
        # An optional, explicitly chosen initial condition, not a forcing or a
        # measurement of the reference film. Once initialized h is advected.
        if p.initial_detail_nm and p.swirl:
            rms=np.sqrt(self.integral(self.omega**2)/np.sum(self.weights))
            self.h+=p.initial_detail_nm*(1-self.sinlat**8)*np.sin(2*self.omega/(rms+1e-30))
        self.gamma=1+p.surfactant_variation*(.5*self.sinlat+.44*self._initial_field(rng))
        self.h=np.maximum(self.h,1.);self.gamma=np.maximum(self.gamma,.05)
        self.h_mass=self.integral(self.h);self.gamma_mass=self.integral(self.gamma)
        self.time=0.;self.update_velocity()
    def integral(self,x):return float(np.sum(x*self.weights))
    def _prepare_poisson(self):
        # Finite-volume -Laplace-Beltrami, FFT in longitude and tridiagonal in latitude.
        cos=np.cos(self.lat); north=np.cos(np.pi/2-np.arange(self.H)*self.dlat);south=np.cos(np.pi/2-(np.arange(self.H)+1)*self.dlat)
        a=north/(cos*self.dlat**2);c=south/(cos*self.dlat**2)
        a[0]=0;c[-1]=0
        freq=np.arange(self.W//2+1); lam=4*np.sin(np.pi*freq/self.W)**2/self.dlon**2
        diag=a[:,None]+c[:,None]+lam[None,:]/cos[:,None]**2
        lower=-np.broadcast_to(a[:,None],diag.shape).copy(); upper=-np.broadcast_to(c[:,None],diag.shape).copy()
        # Pin one latitude value for the singular constant mode; weighted zero-mean RHS is required.
        diag[0,0]=1.;upper[0,0]=0.
        self.lower=lower;self.cprime=np.empty_like(diag);self.invdiag=np.empty_like(diag)
        self.invdiag[0]=1/diag[0];self.cprime[0]=upper[0]*self.invdiag[0]
        for i in range(1,self.H):
            self.invdiag[i]=1/(diag[i]-lower[i]*self.cprime[i-1]);self.cprime[i]=upper[i]*self.invdiag[i]
        # Initial-only spherical smoothing, with no pinning of the constant mode.
        tau=1/72
        hd=(a[:,None]+c[:,None]+lam[None,:]/cos[:,None]**2)*tau+1
        hl=-np.broadcast_to(a[:,None],hd.shape)*tau;hu=-np.broadcast_to(c[:,None],hd.shape)*tau
        self.hlower=hl;self.hcprime=np.empty_like(hd);self.hinvdiag=np.empty_like(hd)
        self.hinvdiag[0]=1/hd[0];self.hcprime[0]=hu[0]*self.hinvdiag[0]
        for i in range(1,self.H):
            self.hinvdiag[i]=1/(hd[i]-hl[i]*self.hcprime[i-1]);self.hcprime[i]=hu[i]*self.hinvdiag[i]
    def solve_poisson(self,omega):
        rhs=np.fft.rfft(omega,axis=1);rhs[0,0]=0
        d=np.empty_like(rhs);d[0]=rhs[0]*self.invdiag[0]
        for i in range(1,self.H):d[i]=(rhs[i]-self.lower[i]*d[i-1])*self.invdiag[i]
        for i in range(self.H-2,-1,-1):d[i]-=self.cprime[i]*d[i+1]
        return np.fft.irfft(d,n=self.W,axis=1)
    def _smooth_sphere(self,field):
        rhs=np.fft.rfft(field,axis=1);d=np.empty_like(rhs);d[0]=rhs[0]*self.hinvdiag[0]
        for i in range(1,self.H):d[i]=(rhs[i]-self.hlower[i]*d[i-1])*self.hinvdiag[i]
        for i in range(self.H-2,-1,-1):d[i]-=self.hcprime[i]*d[i+1]
        return np.fft.irfft(d,n=self.W,axis=1)
    def _initial_field(self,rng):
        out=np.zeros((self.H,self.W))
        for frequency,amp in ((7,.30),(14,.30),(28,.32),(55,.40),(100,.35),(170,.24)):
            for _ in range(8):
                a=rng.normal(size=3);a/=np.linalg.norm(a)
                out+=amp*np.sin(frequency*np.einsum('...i,i->...',self.xyz,a)+rng.uniform(0,2*np.pi))
        return out/max(float(np.max(np.abs(out))),1e-12)
    def _initial_vorticity(self,rng):
        from scipy.spatial import cKDTree
        count=1400
        centers=rng.normal(size=(count,3));centers/=np.linalg.norm(centers,axis=1)[:,None]
        # Dipoles cancel their far fields, allowing smaller eddies to coexist.
        tang=rng.normal(size=(count,3));tang-=centers*np.sum(centers*tang,axis=1)[:,None];tang/=np.linalg.norm(tang,axis=1)[:,None]
        sep=rng.uniform(.03,.14,count);plus=centers*np.cos(sep[:,None]/2)+tang*np.sin(sep[:,None]/2);minus=centers*np.cos(sep[:,None]/2)-tang*np.sin(sep[:,None]/2)
        points=np.concatenate((plus,minus));widths=rng.uniform(.025,.10,count); widths=np.tile(widths,2)
        signed=rng.normal(size=count)*(1-centers[:,2]**4);strength=np.concatenate((signed,-signed))
        tree=cKDTree(points); grid=self.xyz.reshape(-1,3);out=np.empty(len(grid))
        for i in range(0,len(grid),16384):
            dist,idx=tree.query(grid[i:i+16384],k=32,workers=1)
            out[i:i+16384]=np.sum(strength[idx]*np.exp(-.5*(dist/widths[idx])**2),axis=1)
        out=out.reshape(self.H,self.W)
        if self.p.fine_vortices:
            # Twice removes large-scale components more strongly. Only the
            # initial condition is filtered; the evolving flow is unfiltered.
            for _ in range(2):out-=self.p.fine_vortices*self._smooth_sphere(out)
        out-=self.integral(out)/np.sum(self.weights)
        rms=np.sqrt(self.integral(out*out)/np.sum(self.weights));return out*(self.p.swirl/(rms+1e-30))
    def _pad(self,field):
        arr=np.concatenate((np.roll(field[:1],self.W//2,axis=1),field,np.roll(field[-1:],self.W//2,axis=1)),axis=0)
        return np.concatenate((arr[:,-1:],arr,arr[:,:1]),axis=1)
    def _sample(self,field,points,bounds=False):
        arr=self._pad(field)
        lon=np.arctan2(points[...,1],points[...,0]);lat=np.arcsin(np.clip(points[...,2],-1,1))
        x=(lon+np.pi)/self.dlon+.5;y=(np.pi/2-lat)/self.dlat+.5
        val=map_coordinates(arr,[y,x],order=1,mode='nearest',prefilter=False)
        if not bounds:return val
        ix=np.clip(np.floor(x).astype(int),0,self.W);iy=np.clip(np.floor(y).astype(int),0,self.H)
        z=np.stack((arr[iy,ix],arr[iy,ix+1],arr[iy+1,ix],arr[iy+1,ix+1]));return val,z.min(0),z.max(0)
    @staticmethod
    def _move(pos,vel,dt):
        speed=np.linalg.norm(vel,axis=-1);angle=dt*speed
        return np.cos(angle)[...,None]*pos+np.sin(angle)[...,None]*vel/(speed[...,None]+1e-30)
    def _dlat(self,a):
        north=np.concatenate((np.roll(a[:1],self.W//2,axis=1),a[:-1]),axis=0);south=np.concatenate((a[1:],np.roll(a[-1:],self.W//2,axis=1)),axis=0)
        return (north-south)/(2*self.dlat)
    def _dlon(self,a):return (np.roll(a,-1,axis=1)-np.roll(a,1,axis=1))/(2*self.dlon)
    def update_velocity(self):
        psi=self.solve_poisson(self.omega)
        self.u_east=-self._dlat(psi);self.u_north=self._dlon(psi)/self.coslat-self.p.gravity*self.coslat
        self.velocity=self.east*self.u_east[...,None]+self.north*self.u_north[...,None]
        self.divergence=2*self.p.gravity*self.sinlat
    def step(self,duration=None):
        dt=self.p.dt if duration is None else float(duration)
        if not np.isfinite(dt) or not 0<dt<=.3:raise ValueError('時間刻みは正の有限値にしてください')
        self.update_velocity();v=self.velocity
        back=self._move(self.xyz,v,-dt);forward=self._move(self.xyz,v,dt)
        def advect(field):
            a,lo,hi=self._sample(field,back,True); reverse=self._sample(a,forward)
            return np.clip(a+.5*(field-reverse),lo,hi)
        h=advect(self.h)*np.exp(np.clip(-self.divergence*dt,-.2,.2));gamma=advect(self.gamma)*np.exp(np.clip(-self.divergence*dt,-.2,.2))
        h=np.maximum(h,1e-6);gamma=np.maximum(gamma,1e-6);h*=self.h_mass/self.integral(h);gamma*=self.gamma_mass/self.integral(gamma)
        if not np.isfinite(h).all() or not np.isfinite(gamma).all() or h.min()<.02*self.p.thickness_nm or h.max()>20*self.p.thickness_nm or gamma.max()>20:raise RuntimeError('膜厚または界面活性剤が安定範囲を超えました')
        # -curl(-M grad Gamma / h): circulation forcing from misaligned concentration/thickness gradients.
        ge=self._dlon(gamma)/self.coslat;gn=self._dlat(gamma);scale=-self.p.marangoni/(h/self.p.thickness_nm)
        fe=scale*ge;fn=scale*gn
        curl=self._dlon(fn)/self.coslat-self._dlat(self.coslat*fe)/self.coslat
        omega=advect(self.omega)-dt*curl
        omega-=self.integral(omega)/np.sum(self.weights)
        if not np.isfinite(omega).all():raise RuntimeError('渦度が不安定になりました')
        self.h=h;self.gamma=gamma;self.omega=omega;self.time+=dt
    def maps(self,width):
        if width<32 or width%2:raise ValueError('画像幅は32以上の偶数にしてください')
        self.update_velocity();H=width//2;h=np.empty((H,width),np.float32);v=np.empty((H,width,3),np.float32)
        lon=(np.arange(width)+.5)*2*np.pi/width-np.pi
        x=(np.arange(width)+.5)*self.W/width+.5
        padded_h=self._pad(self.h);padded_v=[self._pad(self.velocity[:,:,j]) for j in range(3)]
        for row in range(H):
            lat=np.pi/2-(row+.5)*np.pi/H
            pts=np.stack((np.cos(lat)*np.cos(lon),np.cos(lat)*np.sin(lon),np.full(width,np.sin(lat))),axis=1)
            y=np.full(width,(row+.5)*self.H/H+.5)
            h[row]=map_coordinates(padded_h,[y,x],order=1,mode='nearest',prefilter=False)
            for j in range(3):v[row,:,j]=map_coordinates(padded_v[j],[y,x],order=1,mode='nearest',prefilter=False)
            v[row]-=pts*np.sum(v[row]*pts,axis=1)[:,None]
        return h,v

def export(film,directory,frame,width,velocity_range=8.):
    if not np.isfinite(velocity_range) or velocity_range<=0:raise ValueError('速度画像の最大値は正にしてください')
    out=Path(directory);out.mkdir(parents=True,exist_ok=True);h,v=film.maps(width);speed=np.linalg.norm(v,axis=2);direction=v/(speed[...,None]+1e-20)
    images={'color':interference(h,film.p.exposure,film.p.saturation),'thickness_nm':np.uint16(np.clip(h,0,65535)+.5),'velocity':np.uint8(np.clip(v/velocity_range*.5+.5,0,1)*255+.5),'direction':np.uint8(np.clip(direction*.5+.5,0,1)*255+.5)}
    for name,arr in images.items():Image.fromarray(arr).save(out/f'{name}_{frame:04d}.png')
    np.savez_compressed(out/f'state_{frame:04d}.npz',thickness_grid_nm=film.h,surfactant_grid=film.gamma,vorticity_grid=film.omega,velocity_xyz_grid=film.velocity,time=film.time)
    meta={'parameters':asdict(film.p),'time':film.time,'width':width,'height':width//2,'fluid_grid':[film.W,film.H],'velocity_png':f'RGB XYZ decode (value/255*2-1)*{velocity_range}','velocity_clipped_component_fraction':float(np.count_nonzero((v>velocity_range)|(v< -velocity_range))/v.size),'thickness_png':'uint16 nm','direction_png':'RGB XYZ, decode value/255*2-1','geometry':'unit sphere, equirectangular north up, pixel centers, seam +/-pi','model':'mesh-free finite-volume sphere vorticity grid; approximate gravity drainage and Marangoni curl; semi-Lagrangian scalars and global mass correction; not author original software'}
    (out/f'metadata_{frame:04d}.json').write_text(json.dumps(meta,indent=2))
