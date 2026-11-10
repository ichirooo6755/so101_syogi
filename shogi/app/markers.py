"""Identify the four board corners from dedicated ArUco fiducials.

Markers 0, 1, 2 and 3 sit immediately outside 9a, 1a, 1i and 9i,
respectively. Their black inner corners meet the corresponding grid corners.
All markers must have the same printed orientation. This gives image points,
not a calibrated transform into the robot coordinate frame.
"""
import cv2
import numpy as np

MARKER_DICT = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)


def detect_marker_corners(image):
    if image is None or image.size == 0:
        raise ValueError('カメラ画像がありません')
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    detector = cv2.aruco.ArucoDetector(MARKER_DICT, cv2.aruco.DetectorParameters())
    corners, ids, _ = detector.detectMarkers(gray)
    if ids is None:
        raise ValueError('盤の四隅のマーカーが見つかりません')
    markers = {}
    for ident, points in zip(ids.ravel(), corners):
        ident = int(ident)
        if ident not in range(4):
            continue
        if ident in markers:
            raise ValueError('同じ番号のマーカーが複数見つかりました')
        markers[ident] = np.asarray(points, dtype=np.float32).reshape(4, 2)
    missing = [str(i) for i in range(4) if i not in markers]
    if missing:
        raise ValueError('マーカー ' + ', '.join(missing) + ' が見えていません')
    # Board-facing corner of each marker, in marker coordinate order.
    quad = np.array([markers[0][2], markers[1][3], markers[2][0], markers[3][1]], dtype=np.float32)
    contour = quad.reshape(-1, 1, 2)
    h, w = gray.shape
    if not cv2.isContourConvex(contour) or abs(cv2.contourArea(contour)) < 0.03 * w * h:
        raise ValueError('マーカーの配置が不正です。番号と向きを確認してください')
    # The printed arrows must point in approximately the same direction.
    headings = [p[1] - p[0] for p in markers.values()]
    headings = [v / max(float(np.linalg.norm(v)), 1e-6) for v in headings]
    if any(float(np.dot(headings[0], v)) < 0.5 for v in headings[1:]):
        raise ValueError('マーカーの上下を同じ向きにそろえてください')
    return quad.tolist()
