"""A fixed-sphere finite-volume film experiment, not the 2024 paper solver."""
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import numpy as np
from scipy.spatial import ConvexHull, cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import factorized
from PIL import Image

@dataclass
class Params:
    subdivision: int = 4
    dt: float = 0.015
    swirl: float = 2.0
    drainage: float = 0.035
    thickness_nm: float = 450.0
    variation_nm: float = 130.0
    seed: int = 12


def icosphere(level):
    phi = (1 + np.sqrt(5)) / 2
    p = np.array([(-1,phi,0),(1,phi,0),(-1,-phi,0),(1,-phi,0),(0,-1,phi),(0,1,phi),(0,-1,-phi),(0,1,-phi),(phi,0,-1),(phi,0,1),(-phi,0,-1),(-phi,0,1)], float)
    p /= np.linalg.norm(p, axis=1)[:,None]
    faces = ConvexHull(p).simplices
    verts = p.tolist()
    for _ in range(level):
        cache = {}
        def midpoint(a,b):
            key = tuple(sorted((int(a),int(b))))
            if key not in cache:
                v = np.array(verts[a]) + np.array(verts[b]); v /= np.linalg.norm(v)
                cache[key] = len(verts); verts.append(v.tolist())
            return cache[key]
        new=[]
        for a,b,c in faces:
            ab,bc,ca=midpoint(a,b),midpoint(b,c),midpoint(c,a)
            new.extend(((a,ab,ca),(b,bc,ab),(c,ca,bc),(ab,bc,ca)))
        faces=np.array(new, dtype=int)
    verts=np.asarray(verts); faces=np.asarray(faces, dtype=int)
    a,b,c=(verts[faces[:,i]] for i in range(3))
    flip=np.einsum('ij,ij->i', np.cross(b-a,c-a),a)<0
    faces[flip] = faces[flip][:,[0,2,1]]
    return verts,faces


class Film:
    def __init__(self, params):
        self.p=params
        if not 1 <= params.subdivision <= 6: raise ValueError('subdivision must be 1..6')
        if not (params.dt > 0 and params.thickness_nm > abs(params.variation_nm) and params.drainage >= 0):
            raise ValueError('dt must be positive, drainage nonnegative, and thickness greater than variation')
        self.v,self.f=icosphere(params.subdivision)
        tri=self.v[self.f]; self.centers=tri.mean(axis=1); self.centers/=np.linalg.norm(self.centers,axis=1)[:,None]
        cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]); self.area=np.linalg.norm(cross,axis=1)/2
        self.norm=cross/(2*self.area[:,None]); self.tree=cKDTree(self.centers)
        # Gradients of P1 basis functions on each planar triangle.
        self.grad=np.stack([np.cross(self.norm,tri[:,2]-tri[:,1]),np.cross(self.norm,tri[:,0]-tri[:,2]),np.cross(self.norm,tri[:,1]-tri[:,0])],axis=1)/(2*self.area[:,None,None])
        ii=np.repeat(self.f,3,axis=1).ravel(); jj=np.tile(self.f,(1,3)).ravel()
        vals=(self.area[:,None,None]*np.einsum('fik,fjk->fij',self.grad,self.grad)).ravel()
        lap=coo_matrix((vals,(ii,jj)),shape=(len(self.v),len(self.v))).tocsc()
        self.solve=factorized(lap[1:,1:])
        self.vertex_area=np.bincount(self.f.ravel(),weights=np.repeat(self.area/3,3),minlength=len(self.v))
        # Pair adjacent faces; oriented edge (a,b) has its first face on the left.
        edges={}
        for fi, (a,b,c) in enumerate(self.f):
            for x,y in ((a,b),(b,c),(c,a)):
                key=tuple(sorted((x,y)))
                if key in edges: edges[key].append((fi,x,y))
                else: edges[key]=[(fi,x,y)]
        if any(len(e)!=2 for e in edges.values()): raise ValueError('mesh is not closed')
        pairs=list(edges.values()); self.left=np.array([x[0][0] for x in pairs]); self.right=np.array([x[1][0] for x in pairs]); self.ea=np.array([x[0][1] for x in pairs]); self.eb=np.array([x[0][2] for x in pairs])
        edgevec=self.v[self.eb]-self.v[self.ea]; self.edge_len=np.linalg.norm(edgevec,axis=1)
        mid=self.v[self.ea]+self.v[self.eb]; mid/=np.linalg.norm(mid,axis=1)[:,None]
        out=np.cross(edgevec,mid); out/=np.linalg.norm(out,axis=1)[:,None]
        # Tangential gravity towards negative z. It is an explicitly prescribed mobility model.
        gravity=np.array([0.,0.,-1.]); tangent=gravity-mid*(mid@gravity)[:,None]
        self.gravity_flux=params.drainage*np.einsum('ij,ij->i',out,tangent)*self.edge_len
        # Limited piecewise-linear reconstruction on the face adjacency graph.
        neighbors=[[] for _ in self.f]
        for l,r in zip(self.left,self.right):
            neighbors[l].append(r); neighbors[r].append(l)
        self.neighbors=np.asarray(neighbors)
        axis=np.cross(self.centers,np.array([0.,0.,1.]))
        near=np.linalg.norm(axis,axis=1)<1e-8
        axis[near]=np.cross(self.centers[near],np.array([0.,1.,0.]))
        axis/=np.linalg.norm(axis,axis=1)[:,None]
        axis2=np.cross(self.centers,axis)
        delta=self.centers[self.neighbors]-self.centers[:,None,:]
        matrix=np.stack((np.einsum('fki,fi->fk',delta,axis),np.einsum('fki,fi->fk',delta,axis2)),axis=2)
        self.reconstruct=np.linalg.pinv(matrix)
        edgemid=(self.v[self.ea]+self.v[self.eb])/2
        def offsets(face):
            d=edgemid-self.centers[face]
            return np.stack((np.sum(d*axis[face],axis=1),np.sum(d*axis2[face],axis=1)),axis=1)
        self.offset_left=offsets(self.left); self.offset_right=offsets(self.right)
        rng=np.random.default_rng(params.seed)
        centers=rng.normal(size=(600,3)); centers/=np.linalg.norm(centers,axis=1)[:,None]
        strengths=rng.normal(size=600); widths=rng.uniform(0.035,0.11,600)
        # Chunking prevents the initialization from allocating faces x 600 floats at once.
        self.omega=np.zeros(len(self.f))
        for j in range(0,len(centers),40):
            angular=self.centers@centers[j:j+40].T
            self.omega+=np.exp((angular-1)/widths[j:j+40]**2)@strengths[j:j+40]
        self.omega-=np.average(self.omega,weights=self.area)
        # Remove global spin so the initially imposed flow is dominated by smaller vortices.
        spin=np.sum(self.omega[:,None]*self.centers*self.area[:,None],axis=0)*3/np.sum(self.area)
        self.omega-=self.centers@spin
        self.omega*=params.swirl/(np.sqrt(np.average(self.omega**2,weights=self.area))+1e-20)
        z=self.centers[:,2]
        x,y=self.centers[:,0],self.centers[:,1]
        self.h=params.thickness_nm + params.variation_nm*(
            0.40*z+0.15*np.sin(7*x+3*y)+0.10*np.sin(13*y-4*z)
            +0.08*np.sin(18*x+7*z)+0.07*np.sin(32*x-15*y+5*z)
            +0.06*np.sin(17*x+36*y-6*z))
        self.time=0.; self.velocity=np.zeros_like(self.centers)
        self.update_velocity()
    def vertex_average(self,x):
        return np.bincount(self.f.ravel(),weights=np.repeat(x*self.area/3,3),minlength=len(self.v))/self.vertex_area
    def update_velocity(self):
        ov=self.vertex_average(self.omega); ov-=np.sum(ov*self.vertex_area)/np.sum(self.vertex_area)
        rhs=ov*self.vertex_area
        psi=np.zeros(len(self.v)); psi[1:]=self.solve(rhs[1:])
        gradient=np.einsum('fi,fij->fj',psi[self.f],self.grad)
        # edge flux is consistent with v = n cross grad(psi).
        self.velocity=np.cross(self.norm,gradient)
        self.velocity+=self.p.drainage*(np.array([0.,0.,-1.])-self.centers*(-self.centers[:,2])[:,None])
        self.flux=(psi[self.ea]-psi[self.eb])+self.gravity_flux
    def step(self, duration=None):
        remaining=self.p.dt if duration is None else duration
        if remaining <= 0: raise ValueError('duration must be positive')
        while remaining>1e-12:
            self.update_velocity(); q=self.flux
            outgoing=np.bincount(self.left,weights=np.maximum(q,0),minlength=len(self.f))+np.bincount(self.right,weights=np.maximum(-q,0),minlength=len(self.f))
            safe=np.min(self.area/(outgoing+1e-30))*0.22
            dt=min(remaining,safe)
            if dt<1e-10: raise RuntimeError('CFL time step too small')
            def euler(field,positive=False):
                difference=field[self.neighbors]-field[:,None]
                grad=np.einsum('fij,fj->fi',self.reconstruct,difference)
                low=np.minimum(field,np.min(field[self.neighbors],axis=1)); high=np.maximum(field,np.max(field[self.neighbors],axis=1))
                dl=np.sum(grad[self.left]*self.offset_left,axis=1); dr=np.sum(grad[self.right]*self.offset_right,axis=1)
                left=np.clip(field[self.left]+dl,low[self.left],high[self.left])
                right=np.clip(field[self.right]+dr,low[self.right],high[self.right])
                transfer=dt*q*np.where(q>=0,left,right)
                if positive:
                    # Limit each cell's total outgoing mass, preserving pairwise conservation.
                    outgoing_mass=np.bincount(self.left,weights=np.maximum(transfer,0),minlength=len(self.f))+np.bincount(self.right,weights=np.maximum(-transfer,0),minlength=len(self.f))
                    factor=np.minimum(1.,np.maximum(field,0)*self.area/(outgoing_mass+1e-30))
                    transfer*=np.where(transfer>=0,factor[self.left],factor[self.right])
                delta=np.bincount(self.right,weights=transfer,minlength=len(self.f))-np.bincount(self.left,weights=transfer,minlength=len(self.f))
                return field+delta/self.area
            def transport(field,positive=False):
                first=euler(field,positive)
                return 0.5*(field+euler(first,positive))
            self.h=transport(self.h,True); self.omega=transport(self.omega)
            remaining-=dt; self.time+=dt
        self.update_velocity()
    def sample(self, points):
        # Ray intersection with nearby mesh triangles; interpolated vertex values.
        _,ids=self.tree.query(points,k=8); t=self.v[self.f[ids]]
        a,b,c=t[:,:,0,:],t[:,:,1,:],t[:,:,2,:]
        n=np.cross(b-a,c-a); den=np.einsum('nki,ni->nk',n,points)
        scale=np.einsum('nki,nki->nk',n,a)/den
        x=points[:,None,:]*scale[:,:,None]; v0=b-a; v1=c-a; v2=x-a
        d00=np.sum(v0*v0,axis=2); d01=np.sum(v0*v1,axis=2); d11=np.sum(v1*v1,axis=2); d20=np.sum(v2*v0,axis=2); d21=np.sum(v2*v1,axis=2)
        det=d00*d11-d01*d01; wb=(d11*d20-d01*d21)/det; wc=(d00*d21-d01*d20)/det; wa=1-wb-wc
        bary=np.stack([wa,wb,wc],axis=2); best=np.argmax(np.min(bary,axis=2),axis=1); row=np.arange(len(points))
        chosen=ids[row,best]; weights=bary[row,best];
        if np.min(weights)<-1e-5: raise RuntimeError('failed to locate mesh triangle')
        return self.f[chosen], weights
    def maps(self,width=1024):
        if width<32 or width%2: raise ValueError('width must be an even integer >= 32')
        height=width//2; h=np.empty((height,width),np.float32); vel=np.empty((height,width,3),np.float32)
        hv=self.vertex_average(self.h); vv=np.stack([self.vertex_average(self.velocity[:,i]) for i in range(3)],axis=1)
        lon=(np.arange(width)+.5)/width*2*np.pi-np.pi
        for y in range(height):
            lat=np.pi/2-(y+.5)/height*np.pi
            pts=np.stack([np.cos(lat)*np.cos(lon),np.cos(lat)*np.sin(lon),np.full(width,np.sin(lat))],axis=1)
            faces,w=self.sample(pts); h[y]=np.sum(hv[faces]*w,axis=1)
            vec=np.einsum('nki,nk->ni',vv[faces],w); vec-=pts*np.sum(vec*pts,axis=1)[:,None]; vel[y]=vec
        return h,vel


def interference(h, exposure=1.7, saturation=1.0):
    # Equal-energy white illumination, normal-incidence air/film/air interference.
    # Analytic fits to CIE color-matching curves; tabulation keeps 8K memory bounded.
    wave=np.arange(380.,781.,5.)
    def gauss(mu,left,right):
        a=(wave-mu)*np.where(wave<mu,left,right)
        return np.exp(-0.5*a*a)
    x=0.362*gauss(442.,.0624,.0374)+1.056*gauss(599.8,.0264,.0323)-0.065*gauss(501.1,.0490,.0382)
    y=0.821*gauss(568.8,.0213,.0247)+0.286*gauss(530.9,.0613,.0322)
    z=1.217*gauss(437.,.0845,.0278)+0.681*gauss(459.,.0385,.0725)
    cmf=np.stack((x,y,z),axis=1); cmf/=y.sum()
    upper=int(np.ceil(np.clip(np.max(h),0,65535)))
    thickness=np.arange(upper+1)[:,None]
    reflect=(1-np.cos(4*np.pi*1.33*thickness/wave))/2
    xyz=reflect@cmf
    transform=np.array([[3.2406,-1.5372,-.4986],[-.9689,1.8758,.0415],[.0557,-.2040,1.0570]])
    rgb=np.maximum(xyz@transform.T,0)
    luminance=rgb@np.array([.2126,.7152,.0722])
    rgb=np.clip((luminance[:,None]+saturation*(rgb-luminance[:,None]))*exposure,0,1)
    rgb=np.where(rgb<=.0031308,12.92*rgb,1.055*np.power(rgb,1/2.4)-.055)
    lut=np.uint8(np.clip(rgb,0,1)*255+.5)
    return lut[np.uint16(np.clip(h,0,65535)+.5)]


def export(film,directory,frame,width,velocity_range=1.0):
    if velocity_range<=0: raise ValueError('velocity_range must be positive')
    out=Path(directory); out.mkdir(parents=True,exist_ok=True); h,v=film.maps(width)
    speed=np.linalg.norm(v,axis=2); u=v/(speed[...,None]+1e-20)
    # RGB vectors in global XYZ, signed [-range,+range] maps to [0,255].
    files={ 'color':interference(h), 'velocity':np.uint8(np.clip(v/velocity_range*.5+.5,0,1)*255+.5), 'direction':np.uint8(np.clip(u*.5+.5,0,1)*255+.5), 'thickness_nm':np.uint16(np.clip(h,0,65535)+.5) }
    for name,arr in files.items(): Image.fromarray(arr).save(out/f'{name}_{frame:04d}.png')
    np.savez_compressed(out/f'state_{frame:04d}.npz',vertices=film.v,faces=film.f,thickness_nm=film.h,vorticity=film.omega,velocity_xyz=film.velocity,time=film.time)
    meta={'params':asdict(film.p),'time':film.time,'width':width,'height':width//2,'thickness_png':'uint16 nanometers; clamped to 0..65535','velocity_png':f'RGB global XYZ: decode (RGB/255*2-1)*{velocity_range}; components outside range clipped','direction_png':'RGB global XYZ: decode RGB/255*2-1; zero-speed pixels encode 128,128,128','color':'approximate normal-incidence spectral thin-film interference under equal-energy illumination, sRGB','coordinate':'x=cos(lat)cos(lon), y=cos(lat)sin(lon), z=sin(lat); top=north; pixel centers; seam at lon=+/-pi'}
    (out/f'metadata_{frame:04d}.json').write_text(json.dumps(meta,indent=2))
    return h,v
