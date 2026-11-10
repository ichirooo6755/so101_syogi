"""Calibrated planar board tracking for a stationary wrist-camera pose.

The caller must supply measured robot-frame corners, camera intrinsics and
the actual joint angles at the reference observation pose. This module does
not connect to a robot and is not enabled for live movement.
"""
import math
import cv2
import numpy as np


def _points(points, name):
    points=np.asarray(points,dtype=np.float64)
    if points.shape!=(4,2) or not np.isfinite(points).all():
        raise ValueError(f'{name} requires four finite points')
    contour=points.astype(np.float32).reshape(-1,1,2)
    if not cv2.isContourConvex(contour) or abs(cv2.contourArea(contour))<1e-10:
        raise ValueError(f'{name} is not a convex quadrilateral')
    return points


class PlanarBoardCalibration:
    def __init__(self, image_corners, robot_corners_m, camera_matrix, distortion,
                 observation_joints_deg, *, max_joint_error_deg=0.5):
        image=_points(image_corners,'image corners')
        self.robot=_points(robot_corners_m,'robot corners')
        self.camera=np.asarray(camera_matrix,dtype=np.float64)
        self.distortion=np.asarray(distortion,dtype=np.float64).reshape(-1)
        self.joints=np.asarray(observation_joints_deg,dtype=np.float64)
        if (self.camera.shape!=(3,3) or not np.isfinite(self.camera).all()
            or self.camera[0,0]<=0 or self.camera[1,1]<=0 or abs(self.camera[2,2]-1)>1e-6
            or self.distortion.size not in (4,5,8,12,14) or not np.isfinite(self.distortion).all()):
            raise ValueError('Measured camera intrinsics and distortion are required')
        if self.joints.shape!=(5,) or not np.isfinite(self.joints).all():
            raise ValueError('Five measured observation joint angles are required')
        if not 0 < max_joint_error_deg <= 2:
            raise ValueError('Joint tolerance is outside the supported range')
        self.max_joint_error_deg=float(max_joint_error_deg)
        undistorted=self._undistort(image)
        self.homography=cv2.getPerspectiveTransform(undistorted.astype(np.float32),self.robot.astype(np.float32))
        if not np.isfinite(self.homography).all() or np.linalg.cond(self.homography)>1e12:
            raise ValueError('The camera-to-board calibration is degenerate')

    def _undistort(self, image):
        return cv2.undistortPoints(np.asarray(image,dtype=np.float64).reshape(-1,1,2),
                                   self.camera,self.distortion,P=self.camera).reshape(-1,2)

    def track(self, image_corners, observation_joints_deg, *, max_shift_m=.025,
              max_yaw_deg=10, max_residual_m=.002):
        joints=np.asarray(observation_joints_deg,dtype=np.float64)
        if joints.shape!=(5,) or not np.isfinite(joints).all():
            raise ValueError('Current observation joint angles are required')
        if np.max(np.abs(joints-self.joints))>self.max_joint_error_deg:
            raise ValueError('Camera is not at its calibrated observation pose')
        image=_points(image_corners,'image corners')
        undistorted=self._undistort(image)
        projected=cv2.perspectiveTransform(undistorted.reshape(1,-1,2),self.homography).reshape(4,2)
        _points(projected,'projected corners')
        a=self.robot-self.robot.mean(axis=0)
        b=projected-projected.mean(axis=0)
        u,_,vt=np.linalg.svd(a.T@b)
        rotation=vt.T@u.T
        if np.linalg.det(rotation)<0:
            raise ValueError('Board marker orientation is reversed')
        predicted=a@rotation.T+projected.mean(axis=0)
        residual=float(np.max(np.linalg.norm(projected-predicted,axis=1)))
        shift=projected.mean(axis=0)-self.robot.mean(axis=0)
        angle=math.atan2(rotation[1,0],rotation[0,0])
        if residual>max_residual_m:
            raise ValueError('Corners do not match a rigid board; check calibration or occlusion')
        if np.linalg.norm(shift)>max_shift_m or abs(math.degrees(angle))>max_yaw_deg:
            raise ValueError('Board moved outside the calibrated tracking range')
        return {'corners_robot_m':projected.tolist(),'shift_m':shift.tolist(),
                'yaw_deg':math.degrees(angle),'max_residual_m':residual}
