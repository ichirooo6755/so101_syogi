#!/usr/bin/env python3
"""Train and physically evaluate an open-loop, simulation-only imitation policy.

Demonstrations come from the existing IK/physics controller; a policy rollout
never calls that controller. Features include simulator source/goal coordinates
and an external phase clock, so this is NOT a camera policy or a real-arm model.
"""
from __future__ import annotations
import argparse,json,os,sys,time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
import torch

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from pick_place import run
DIRS=np.array([[.04,0],[0,.33/9],[0,-.33/9],[-.04,0]])
N_PHASES=16
CORES=os.cpu_count() or 8

def feature(source,target,phase,progress):
    one=np.zeros(N_PHASES,dtype=np.float32);one[min(int(phase),N_PHASES-1)]=1
    return np.concatenate([np.asarray(source,dtype=np.float32),np.asarray(target,dtype=np.float32),[np.float32(progress)],one]).astype(np.float32)

def layouts(seed,n):
    rng=np.random.default_rng(seed);out=[]
    for i in range(n):
        source=np.array([rng.uniform(.18,.23),rng.uniform(-.11,-.03)])+rng.uniform(-.012,.012,2)
        target=source+DIRS[i%4]
        out.append((source,target))
    return out

class Net(torch.nn.Module):
    def __init__(self):
        super().__init__();self.net=torch.nn.Sequential(torch.nn.Linear(5+N_PHASES,128),torch.nn.ReLU(),
            torch.nn.Linear(128,128),torch.nn.ReLU(),torch.nn.Linear(128,128),torch.nn.ReLU(),torch.nn.Linear(128,6))
    def forward(self,x):return self.net(x)

class Policy:
    def __init__(self,model,xmean,xstd,ymean,ystd):
        self.model=model.eval();self.xmean=xmean;self.xstd=xstd;self.ymean=ymean;self.ystd=ystd
    def __call__(self,source,target,phase,progress):
        x=feature(source,target,phase,progress)
        with torch.no_grad():y=self.model(torch.from_numpy((x-self.xmean)/self.xstd)).numpy()
        return y*self.ystd+self.ymean

def clean(report):return {k:v for k,v in report.items() if k!='trace'}

def _rollout(job):
    torch.set_num_threads(1)
    source,target,board_x,promote=job
    r=run(source,target,neighbors=True,board_x=board_x,promote=promote)
    frames=[]
    if r['success']:
        frames=[(feature(source,target,f['phase_index'],f['phase_progress']),f['action_rad']) for f in r['trace']]
    return clean(r),frames

def _learned(job):
    torch.set_num_threads(1)
    source,target,board_x,blob=job
    net=Net();net.load_state_dict(blob['state'])
    policy=Policy(net,blob['xmean'],blob['xstd'],blob['ymean'],blob['ystd'])
    return clean(run(source,target,neighbors=True,policy=policy,board_x=board_x))

def main():
    p=argparse.ArgumentParser();p.add_argument('--demos',type=int,default=32);p.add_argument('--eval',type=int,default=12)
    p.add_argument('--steps',type=int,default=1200);p.add_argument('--seed',type=int,default=20261031);p.add_argument('--board-x',type=float,default=.265);p.add_argument('--out',type=Path,default=HERE/'runs/imitation')
    p.add_argument('--jobs',type=int,default=CORES);a=p.parse_args()
    if a.demos<4 or a.eval<1 or a.steps<1:raise ValueError('Not enough demos, evaluation layouts or optimizer steps')
    if not 1<=a.jobs<=CORES:raise ValueError('jobs must be between 1 and CPU count')
    a.out.mkdir(parents=True,exist_ok=True);np.random.seed(a.seed);torch.manual_seed(a.seed);torch.set_num_threads(CORES)
    train_layouts=layouts(a.seed,a.demos);test_layouts=layouts(a.seed+1000,a.eval)
    train_ids={tuple(np.round(np.r_[s,t],8)) for s,t in train_layouts};test_ids={tuple(np.round(np.r_[s,t],8)) for s,t in test_layouts}
    if train_ids & test_ids:raise RuntimeError('training and held-out layouts overlap')
    xs=[];ys=[];attempts=[];start=time.monotonic()
    jobs=[(s,t,a.board_x,False) for s,t in train_layouts]
    with ProcessPoolExecutor(max_workers=a.jobs) as pool:
        for i,((report,frames),job) in enumerate(zip(pool.map(_rollout,jobs),jobs)):
            attempts.append(report)
            for x,y in frames: xs.append(x);ys.append(y)
            print(f"expert {i+1}/{a.demos}: {'success' if report['success'] else 'failed'} promote={job[3]}",flush=True)
    if not xs:
        (a.out/'training_failed.json').write_text(json.dumps({'error':'No physically successful demonstrations','attempts':attempts},indent=2))
        raise SystemExit('No successful demonstrations: training is not meaningful')
    x=np.asarray(xs,dtype=np.float32);y=np.asarray(ys,dtype=np.float32)
    np.savez_compressed(a.out/'demonstrations.npz',features=x,actions=y)
    xm=x.mean(0);xd=np.maximum(x.std(0),1e-5);ym=y.mean(0);yd=np.maximum(y.std(0),1e-5)
    xt=torch.from_numpy((x-xm)/xd);yt=torch.from_numpy((y-ym)/yd)
    net=Net();opt=torch.optim.Adam(net.parameters(),lr=.001);gen=torch.Generator().manual_seed(a.seed)
    loss_values=[]
    for step in range(a.steps):
        ids=torch.randint(len(xt),(min(512,len(xt)),),generator=gen)
        pred=net(xt[ids]);loss=torch.mean((pred-yt[ids])**2)
        opt.zero_grad();loss.backward();opt.step()
        if (step+1)%200==0 or step==0:
            loss_values.append({'step':step+1,'loss':float(loss.detach())});print('train',step+1,'loss',round(loss_values[-1]['loss'],6),flush=True)
    torch.save({'model':net.state_dict(),'xmean':torch.tensor(xm),'xstd':torch.tensor(xd),
                'ymean':torch.tensor(ym),'ystd':torch.tensor(yd),'seed':a.seed,'input':'privileged source/target and scheduled phase, simulation only'},a.out/'policy.pt')
    # Re-load our own checkpoint before rollout, to test persistence.
    ck=torch.load(a.out/'policy.pt',map_location='cpu',weights_only=True)
    blob={'state':{k:v.cpu() for k,v in ck['model'].items()},
          'xmean':ck['xmean'].numpy(),'xstd':ck['xstd'].numpy(),'ymean':ck['ymean'].numpy(),'ystd':ck['ystd'].numpy()}
    evaluation=[]
    eval_jobs=[(s,t,a.board_x,False) for s,t in test_layouts]
    learned_jobs=[(s,t,a.board_x,blob) for s,t in test_layouts]
    with ProcessPoolExecutor(max_workers=a.jobs) as pool:
        experts=list(pool.map(_rollout,eval_jobs))
        learned_rows=list(pool.map(_learned,learned_jobs))
    for i,((expert,_),learned) in enumerate(zip(experts,learned_rows)):
        evaluation.append({'layout':i,'expert':expert,'learned':learned})
        print(f"held-out {i+1}/{a.eval}: expert={expert['success']} learned={learned['success']}",flush=True)
    summary={'seed':a.seed,'sim_only':True,'device':'cpu','jobs':a.jobs,'cores':CORES,'board_center_x_m':a.board_x,'demonstrations_attempted':a.demos,
        'demonstrations_successful':sum(bool(v['success']) for v in attempts),'training_frames':len(x),
        'optimizer_steps':a.steps,'losses':loss_values,'train_eval_layout_overlap':len(train_ids&test_ids),
        'heldout_count':a.eval,'heldout_expert_successes':sum(v['expert']['success'] for v in evaluation),
        'heldout_learned_successes':sum(v['learned']['success'] for v in evaluation),
        'no_expert_fallback':all(v['learned'].get('controller')=='learned_policy_no_ik_fallback' and v['learned'].get('policy_calls',0)>0 for v in evaluation),
        'elapsed_s':round(time.monotonic()-start,1),'demonstrations':attempts,'evaluation':evaluation}
    (a.out/'report.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('demonstrations','evaluation')},indent=2),flush=True)
    return 0
if __name__=='__main__':raise SystemExit(main())
