"""Find a shogi-board quad in a photo. OpenCV contour, no trained model."""
import cv2
import numpy as np


def _order(pts):
    pts=np.asarray(pts,dtype=np.float32)
    s=pts.sum(axis=1); d=np.diff(pts,axis=1).reshape(-1)
    tl,br=pts[np.argmin(s)],pts[np.argmax(s)]
    tr,bl=pts[np.argmin(d)],pts[np.argmax(d)]
    return np.array([tl,tr,br,bl],dtype=np.float32)


def detect_corners(image):
    """Return 4 corners in GUI order 9a,1a,1i,9i (tl,tr,br,bl from the camera)."""
    if image is None or image.size==0: raise ValueError('画像がありません')
    gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    blur=cv2.GaussianBlur(gray,(5,5),0)
    edges=cv2.Canny(blur,40,120)
    edges=cv2.dilate(edges,None)
    contours,_=cv2.findContours(edges,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    h,w=gray.shape
    best=None; best_area=0
    for c in contours:
        peri=cv2.arcLength(c,True)
        approx=cv2.approxPolyDP(c,0.02*peri,True)
        if len(approx)!=4 or not cv2.isContourConvex(approx): continue
        area=abs(cv2.contourArea(approx))
        if area<0.08*w*h or area>0.95*w*h: continue
        if area>best_area: best,best_area=approx.reshape(4,2),area
    if best is None: raise ValueError('盤の四隅を自動では見つけられません。手で指定してください')
    ordered=_order(best)
    return [[float(x),float(y)] for x,y in ordered]
