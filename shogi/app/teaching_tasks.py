"""Identify candidate squares to teach from an unsuccessful offline trial.

These are diagnostics, not proofs of physical unreachability or usable robot
motions. A failure during transport or at the stand is not assigned to a board
square just to fill the list.
"""
from __future__ import annotations
import math
import re
import hashlib
from pathlib import Path

SIMULATION_INPUTS=(
    'app/board_map.py', 'simulation/pick_place.py', 'simulation/scene.py',
    'simulation/train_waypoints.py', 'simulation/model/upstream_scene.xml',
    'simulation/model/so101_new_calib.xml',
    'vendor/so101-manipulation-eval/src/sim/so101_kinematics.py',
    'vendor/so101-manipulation-eval/src/sim/check_contact.py',
)


def simulation_fingerprints(root):
    """Hash the specific local code/models used in this simulation."""
    return {name:hashlib.sha256((Path(root)/name).read_bytes()).hexdigest()
            for name in SIMULATION_INPUTS}


def _board_endpoints(move, role):
    source=move.get('source');destination=move.get('destination')
    if role=='captured_to_stand': return destination,None
    if role=='drop': return None,destination
    if role in ('move','own_to_board'): return source,destination
    return None,None


def _bad_residual(value, *, position=4.):
    if not isinstance(value,dict): return False
    try:
        p=float(value.get('position_mm',0));a=float(value.get('angle_deg',0))
    except (TypeError,ValueError): return False
    return math.isfinite(p) and math.isfinite(a) and (p>position or a>15.)


def from_failure(move, report, role='move', origin='plan'):
    """Return likely pick/place teaching candidates with their evidence."""
    if not isinstance(move,dict) or not isinstance(report,dict) or report.get('success') is not False:
        return []
    source,destination=_board_endpoints(move,role)
    result=[];seen=set()

    def add(square,operation,stage,evidence):
        if not isinstance(square,str) or not re.fullmatch(r'[1-9][a-i]',square): return
        key=(square,operation)
        if key in seen: return
        seen.add(key)
        result.append({'square':square,'operation':operation,'stage':stage,
                       'evidence':evidence,'role':role,'origin':origin})

    reason=report.get('reason')
    if reason=='grasp_folded':
        add(source,'pick','grasp','grasp_folded')
    if reason=='ik_unreachable':
        residuals=report.get('ik_residuals') or {}
        if isinstance(residuals,dict):
            if _bad_residual(residuals.get('grasp')): add(source,'pick','grasp','ik_residual')
            if _bad_residual(residuals.get('place')): add(destination,'place','place','ik_residual')
            if not result:
                if _bad_residual(residuals.get('lift'),position=8.): add(source,'pick','lift','ik_residual')
                if _bad_residual(residuals.get('carry'),position=8.): add(destination,'place','carry','ik_residual')
        if not result and report.get('failure_phase')=='grasp_settle':
            add(source,'pick','grasp','simulated_grasp_settle')
    collision=report.get('first_collision')
    if isinstance(collision,dict):
        phase=collision.get('phase')
        # A collision during carry/clear is a route issue, not one endpoint.
        if phase in ('approach','descend','close','lift'): add(source,'pick',phase,'simulated_contact')
        elif phase in ('place','hover','release'): add(destination,'place',phase,'simulated_contact')
    if not result and collision is None and 'max_lift_mm' in report and 'both_jaws_airborne_steps' in report:
        try:
            lift=float(report['max_lift_mm']);both=float(report['both_jaws_airborne_steps'])
        except (TypeError,ValueError): lift=both=math.nan
        if math.isfinite(lift) and math.isfinite(both) and (lift<20. or both<200.):
            add(source,'pick','lift','simulated_grasp')
        elif math.isfinite(lift) and lift>=20. and both>=200.:
            try: err=float(report.get('position_error_mm',0));limit=float(report.get('target_radius_mm',8))
            except (TypeError,ValueError): err=limit=math.nan
            if math.isfinite(err) and math.isfinite(limit) and err>limit:
                add(destination,'place','place','simulated_placement')
    return result


def from_simulation(move, report):
    if not isinstance(report,dict): return []
    if report.get('reason')=='capture_preview_only':
        return (from_failure(move,report.get('captured_to_stand'),'captured_to_stand','simulation')+
                from_failure(move,report.get('own_piece_to_board'),'own_to_board','simulation'))
    role='drop' if move.get('drop') else 'move'
    origin='learned_simulation' if report.get('controller')=='learned_policy_no_ik_fallback' else 'simulation'
    return from_failure(move,report,role,origin)


def combine(existing, additions):
    """Keep distinct previously observed pick/place failures for this move."""
    result=[];seen=set()
    for item in [*existing,*additions]:
        key=(item.get('square'),item.get('operation'))
        if key not in seen:
            result.append(item);seen.add(key)
    return result


def learned_report_candidates(report, side, board_pose, checkpoint_sha256, input_fingerprints):
    """Read historical learned-policy failures only for the same assumed setup."""
    if not isinstance(report,dict) or report.get('stock_arm') is not True:
        return []
    if report.get('board_side')!=side or report.get('board_mm')!=[330,360,12]:
        return []
    if not isinstance(checkpoint_sha256,str) or report.get('checkpoint_sha256')!=checkpoint_sha256:
        return []
    if not isinstance(input_fingerprints,dict) or report.get('input_fingerprints')!=input_fingerprints:
        return []
    try:
        matches=(abs(float(report['board_center_x_m'])-float(board_pose['x']))<.0005 and
                 abs(float(report['board_y_m'])-float(board_pose['y']))<.0005 and
                 abs(math.radians(float(report['board_yaw_deg']))-float(board_pose['yaw']))<math.radians(.1))
    except (KeyError,TypeError,ValueError): return []
    if not matches: return []
    candidates=[]
    for case in report.get('cases',[]):
        if not isinstance(case,dict): continue
        result=case.get('result')
        if not isinstance(result,dict) or result.get('controller')!='learned_policy_no_ik_fallback': continue
        source=case.get('source_square');destination=case.get('destination_square')
        if not all(isinstance(s,str) and re.fullmatch(r'[1-9][a-i]',s) for s in (source,destination)):
            continue
        move={'source':source,'destination':destination,'drop':False,'capture':False}
        found=from_simulation(move,result)
        for item in found:
            item['simulated_move']=source+destination
        candidates=combine(candidates,found)
    return candidates
