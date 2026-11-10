"""One frame from the Mac camera. Same-view board tracking when XIAO is absent."""
import cv2


def grab():
    cam=cv2.VideoCapture(0)
    if not cam.isOpened(): raise ValueError('Mac カメラを開けません')
    try:
        frame=None
        for _ in range(12):
            ok,frame=cam.read()
            if ok and frame is not None and frame.size and float(frame.mean())>1:
                if frame.size>20_000_000: raise ValueError('画像が大きすぎます')
                return frame
        if frame is None or not frame.size: raise ValueError('Mac カメラの画像がありません')
        raise ValueError('Mac カメラが真っ黒です。システム設定のカメラ権限を確認してください')
    finally:
        cam.release()
