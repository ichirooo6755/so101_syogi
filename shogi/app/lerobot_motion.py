"""Prototype joint motion against LeRobot's SO101Follower interface.

This module never connects a robot, loads calibration, or starts a motion by
itself. It consumes validated LeRobot-degree targets and an already connected
robot. It is NOT connected to the shogi GUI: physical joint signs, the
extended arm, collision-free paths and safety behavior remain unverified.

A software hold is best-effort and cannot stop a device when communication is
lost or a serial call blocks. A supervised hardware stop remains necessary.
"""
from __future__ import annotations
import math
import time

NAMES=('shoulder_pan','shoulder_lift','elbow_flex','wrist_flex','wrist_roll','gripper')
KEYS=tuple(name+'.pos' for name in NAMES)


class MotionStopped(RuntimeError):
    pass


def _values(data,label):
    if not isinstance(data,dict) or not all(k in data for k in KEYS):
        raise ValueError(f'{label}: six joint positions are required')
    out={}
    for k in KEYS:
        v=data[k]
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v):
            raise ValueError(f'{label}: {k} must be finite')
        out[k]=float(v)
    return out


def _per_joint(values,label,*,positive=False):
    if not isinstance(values,dict) or set(values)!=set(KEYS):
        raise ValueError(f'{label}: exactly six joint values are required')
    result=_values(values,label)
    if positive and any(v<=0 for v in result.values()):
        raise ValueError(f'{label}: values must be positive')
    return result


class PositionController:
    """Bounded motion with measured feedback; requires caller-provided limits.

    Body joint values are degrees, gripper values are LeRobot's 0-100 units.
    Bounds are independent of LeRobot's relative-target clipping and must be
    checked against actual robot calibration and physical clearance separately.
    """
    def __init__(self,robot,limits,rates,tolerances,following_errors,*,period=.05,
                 max_tick_gap=.3,clock=time.monotonic,sleep=time.sleep):
        if not isinstance(limits,dict) or set(limits)!=set(KEYS):
            raise ValueError('Six joint limits are required')
        self.limits={}
        for k in KEYS:
            pair=limits[k]
            if not isinstance(pair,(list,tuple)) or len(pair)!=2:
                raise ValueError(f'Invalid limits for {k}')
            lo,hi=pair
            if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in pair) or lo>=hi:
                raise ValueError(f'Invalid limits for {k}')
            self.limits[k]=(float(lo),float(hi))
        self.rates=_per_joint(rates,'rates',positive=True)
        self.tolerances=_per_joint(tolerances,'tolerances',positive=True)
        self.following_errors=_per_joint(following_errors,'following errors',positive=True)
        if not isinstance(period,(int,float)) or not .01<=period<=.2:
            raise ValueError('Unsupported control period')
        if not isinstance(max_tick_gap,(int,float)) or not 2*period<=max_tick_gap<=1:
            raise ValueError('Unsupported tick gap')
        config=getattr(robot,'config',None)
        if getattr(config,'use_degrees',None) is not True:
            raise ValueError('LeRobot SO-101 must use degree-mode calibration')
        relative=getattr(config,'max_relative_target',None)
        if isinstance(relative,dict):
            relative={name+'.pos':value for name,value in relative.items()}
        elif isinstance(relative,(int,float)) and not isinstance(relative,bool):
            relative={k:relative for k in KEYS}
        self.relative=_per_joint(relative,'max_relative_target',positive=True)
        if not getattr(robot,'is_connected',False):
            raise ValueError('LeRobot SO-101 is not connected')
        self.robot=robot;self.period=float(period);self.max_tick_gap=float(max_tick_gap)
        self.clock=clock;self.sleep=sleep

    def _check_limits(self,values,label):
        for k,v in values.items():
            lo,hi=self.limits[k]
            if not lo<=v<=hi:
                raise ValueError(f'{label}: {k} outside validated limits')
        return values

    def _read(self):
        return self._check_limits(_values(self.robot.get_observation(),'observation'),'observation')

    def _hold(self):
        """Best effort only: re-read first; never command a stale pose."""
        try:
            observed=self._read()
            self.robot.send_action(dict(observed))
            return True
        except Exception:
            return False

    def move_to(self,target,*,timeout,cancel=lambda:False):
        target=self._check_limits(_per_joint(target,'target'),'target')
        if not isinstance(timeout,(int,float)) or not math.isfinite(timeout) or not .1<=timeout<=120:
            raise ValueError('Invalid timeout')
        if cancel(): raise MotionStopped('Motion cancelled before reading the robot')
        observed=self._read();last=observed.copy();start=self.clock();previous=start
        stable=0
        try:
            while True:
                if cancel(): raise MotionStopped('Motion cancelled')
                now=self.clock()
                if now-start>timeout: raise MotionStopped('Target was not reached before timeout')
                if now-previous>self.max_tick_gap: raise MotionStopped('Control loop was delayed')
                observed=self._read()
                if any(abs(observed[k]-last[k])>self.following_errors[k] for k in KEYS):
                    raise MotionStopped('Measured position did not follow the last command')
                if all(abs(observed[k]-target[k])<=self.tolerances[k] for k in KEYS):
                    stable+=1
                    if stable>=3:
                        return {'reached':True,'observed':observed,'elapsed_s':now-start}
                else:
                    stable=0
                # Never catch up in one burst after a scheduling delay.
                dt=min(self.period,max(0.,now-previous)) if now>previous else self.period
                action={}
                for k in KEYS:
                    step=min(self.rates[k]*dt,self.relative[k])
                    delta=max(-step,min(step,target[k]-last[k]))
                    action[k]=last[k]+delta
                if cancel(): raise MotionStopped('Motion cancelled')
                sent=self._check_limits(_values(self.robot.send_action(action),'applied action'),'applied action')
                if any(abs(sent[k]-last[k])>min(self.rates[k]*dt,self.relative[k])+1e-6 for k in KEYS):
                    raise MotionStopped('Applied command exceeded the requested step')
                last=sent;previous=now
                self.sleep(self.period)
        except BaseException as exc:
            try: exc.hold_command_sent=self._hold()
            except Exception: pass
            raise
