"""Sample small simultaneous board translations and yaw; no hardware."""
from __future__ import annotations
import itertools
import json
from pathlib import Path

from study_75_layouts import FOCUS, Study

ROOT=Path(__file__).resolve().parents[1]


def main():
    study=Study();rows=[]
    try:
        for dx,dy,yaw in itertools.product((-5,5),(-5,5),(-5,5)):
            result=study.evaluate((240+dx)/1000,dy/1000,yaw,0.,FOCUS)
            result['offset_mm']=[dx,dy]
            rows.append(result)
            print('offset',dx,dy,'yaw',yaw,'base',result['base_board_distance_mm'],
                  'IK',result['ik_count'],'clear',result['clear_count'],flush=True)
        report={'scope':'Eight corner samples only; static poses at six near squares and three far '
                        'sentinels, convex collision model. No full motion, pieces, '
                        'camera, wires, force, board calibration, or hardware validation.',
                'nominal_center_mm':[240,0], 'offsets_mm':[-5,5], 'yaw_deg':[-5,5],
                'board_mm':[330,360,12], 'samples':rows}
        (ROOT/'output/upper_arm_extension/board_shift_75_samples.json').write_text(
            json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    finally: study.close()


if __name__=='__main__': main()
