"""Summarize visual statistics against a user-specified reference clip.

Only statistics are written; the reference video/frames are never exported.
Requires opencv-python-headless in addition to the app dependencies.
"""
import argparse, json
import cv2
import numpy as np
from PIL import Image

SIZE=(720,360)
SCALES=(1,2,4,8,16,32)
def metrics(im):
    if isinstance(im,Image.Image): im=np.asarray(im.convert('RGB').resize(SIZE,Image.Resampling.LANCZOS))
    else: im=cv2.cvtColor(cv2.resize(im,SIZE,interpolation=cv2.INTER_AREA),cv2.COLOR_BGR2RGB)
    a=im.astype(np.float32)/255
    pieces=np.array_split(a,6,axis=0)
    means=np.asarray([x.mean((0,1)) for x in pieces])
    chroma=np.asarray([(x.max(2)-x.min(2)).mean() for x in pieces])
    edges=np.asarray([np.abs(a[:,k:]-a[:,:-k]).mean() for k in SCALES])
    # Measure detail at several pixel separations within each latitude band.
    # These statistics do not identify the shape or correspondence of eddies.
    band_edges=np.asarray([[np.abs(x[:,k:]-x[:,:-k]).mean() for k in SCALES] for x in pieces])
    return means,chroma,edges,band_edges

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--reference',required=True);ap.add_argument('candidates',nargs='+');ap.add_argument('--json');args=ap.parse_args()
    cap=cv2.VideoCapture(args.reference)
    if not cap.isOpened(): raise RuntimeError('Cannot open reference video')
    fps=cap.get(cv2.CAP_PROP_FPS); count=cap.get(cv2.CAP_PROP_FRAME_COUNT);duration=count/fps
    refs=[]
    for t in np.linspace(0,max(0,duration-.4),6):
        cap.set(cv2.CAP_PROP_POS_MSEC,float(t*1000));ok,frame=cap.read()
        if not ok:raise RuntimeError(f'Cannot decode reference at {t}s')
        refs.append(metrics(frame))
    target=[np.mean(np.stack([r[i] for r in refs]),axis=0) for i in range(4)]
    out={'reference':{'duration_seconds':duration,'fps':fps,'sample_times':'six evenly spaced frames','width':int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),'height':int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),'band_mean_rgb':target[0].tolist(),'band_mean_chroma':target[1].tolist(),'horizontal_difference_scales':list(SCALES),'horizontal_difference':target[2].tolist()},'candidates':[]}
    out['reference']['band_horizontal_difference']=target[3].tolist()
    for path in args.candidates:
        means,chroma,edges,band_edges=metrics(Image.open(path)); dmean=float(np.mean(np.abs(means-target[0]))); dchroma=float(np.mean(np.abs(chroma-target[1])));dedge=float(np.mean(np.abs(edges-target[2])));dband=float(np.mean(np.abs(band_edges-target[3])))
        out['candidates'].append({'image':path,'mean_rgb_error':dmean,'mean_chroma_error':dchroma,'mean_horizontal_difference_error':dedge,'band_horizontal_difference_error':dband,'band_mean_rgb':means.tolist(),'band_mean_chroma':chroma.tolist(),'horizontal_difference':edges.tolist(),'band_horizontal_difference':band_edges.tolist()})
        print(f'{path}: band RGB MAE={dmean:.4f}, chroma MAE={dchroma:.4f}, texture MAE={dedge:.4f}, band texture MAE={dband:.4f}')
    if args.json:
        with open(args.json,'w') as f:json.dump(out,f,indent=2)
if __name__=='__main__':main()
