#!/usr/bin/env python3
"""Fit a simulation-only joint-waypoint policy from successful IK demonstrations.

The model receives ground-truth source and target coordinates, predicts the five
joint waypoints once, and follows a fixed smooth phase schedule. It does not use
IK or the expert while controlling the arm. It is not a visual or real-arm policy.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from pick_place import HOME, approach_angle_for, run
from train_imitation import N_PHASES, clean, layouts

HERE = Path(__file__).resolve().parent
WAYPOINT_PHASES = (1, 2, 4, 5, 6)


class WaypointNet(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Linear(4, 128), torch.nn.Tanh(),
            torch.nn.Linear(128, 128), torch.nn.Tanh(),
            torch.nn.Linear(128, 25),
        )

    def forward(self, x):
        return self.net(x)


class WaypointPolicy:
    def __init__(self, net, xm, xd, ym, yd):
        self.net = net.eval()
        self.xm, self.xd, self.ym, self.yd = xm, xd, ym, yd
        self.cache_key = None
        self.endpoints = None
        self.open = approach_angle_for(.023 / 2, margin_m=.005)
        self.closed = .065

    def __call__(self, source, target, phase, progress):
        x = np.asarray([*source, *target], dtype=np.float32)
        key = tuple(x)
        if key != self.cache_key:
            with torch.no_grad():
                y = self.net(torch.from_numpy((x - self.xm) / self.xd)).numpy()
            above, grasp, lift, carry, place = (y * self.yd + self.ym).reshape(5, 5)
            self.endpoints = [HOME, above, grasp, grasp, lift, carry, place, place, carry]
            self.cache_key = key
        grippers = [self.open, self.open, self.open, self.closed, self.closed,
                    self.closed, self.closed, self.open, self.open]
        previous = HOME if phase == 0 else self.endpoints[phase - 1]
        prev_gripper = self.open if phase == 0 else grippers[phase - 1]
        t = min(1., progress / .6)
        mix = t * t * (3 - 2 * t)
        q = previous + (self.endpoints[phase] - previous) * mix
        return np.r_[q, prev_gripper + (grippers[phase] - prev_gripper) * mix]


def load_waypoints(filename):
    data = np.load(filename)
    features, actions = data['features'], data['actions']
    groups = {}
    for feature, action in zip(features, actions):
        key = tuple(feature[:4])
        phase = int(np.argmax(feature[5:5+N_PHASES]))
        if phase in WAYPOINT_PHASES:
            # The last sampled action is the held waypoint after the ramp.
            groups.setdefault(key, {})[phase] = action[:5]
    rows = [(x, phases) for x, phases in groups.items()
            if all(p in phases for p in WAYPOINT_PHASES)]
    if len(rows) < 4:
        raise ValueError('At least four complete successful demonstrations are needed')
    x = np.asarray([k for k, _ in rows], dtype=np.float32)
    y = np.asarray([np.concatenate([p[i] for i in WAYPOINT_PHASES]) for _, p in rows], dtype=np.float32)
    return x, y


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=Path, default=HERE / 'runs/imitation_id5/demonstrations.npz')
    parser.add_argument('--out', type=Path, default=HERE / 'runs/waypoint_id5')
    parser.add_argument('--seed', type=int, default=20261031)
    parser.add_argument('--steps', type=int, default=3000)
    parser.add_argument('--eval', type=int, default=12)
    parser.add_argument('--heldout-offset', type=int, default=2000)
    parser.add_argument('--eval-board-x', type=float, default=.265)
    args = parser.parse_args()
    if args.steps < 1 or args.eval < 1 or args.heldout_offset < 1:
        raise ValueError('Positive steps, evaluation count and held-out offset required')
    args.out.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(args.seed)
    torch.set_num_threads(2)
    x, y = load_waypoints(args.data)
    xm, xd = x.mean(0), np.maximum(x.std(0), 1e-5)
    ym, yd = y.mean(0), np.maximum(y.std(0), 1e-5)
    xt, yt = torch.from_numpy((x - xm) / xd), torch.from_numpy((y - ym) / yd)
    net = WaypointNet()
    opt = torch.optim.Adam(net.parameters(), lr=.001)
    losses = []
    for step in range(args.steps):
        loss = torch.mean((net(xt) - yt) ** 2)
        opt.zero_grad()
        loss.backward()
        opt.step()
        if step == 0 or (step + 1) % 500 == 0:
            losses.append({'step': step + 1, 'loss': float(loss.detach())})
            print('train', step + 1, 'loss', round(losses[-1]['loss'], 6), flush=True)
    torch.save({'model': net.state_dict(), 'xmean': torch.tensor(xm), 'xstd': torch.tensor(xd),
                'ymean': torch.tensor(ym), 'ystd': torch.tensor(yd), 'seed': args.seed,
                'description': 'simulator coordinates to joint waypoints; simulation only'}, args.out / 'policy.pt')
    checkpoint = torch.load(args.out / 'policy.pt', map_location='cpu', weights_only=True)
    net = WaypointNet()
    net.load_state_dict(checkpoint['model'])
    policy = WaypointPolicy(net, *(checkpoint[k].numpy() for k in ('xmean', 'xstd', 'ymean', 'ystd')))
    tests = layouts(args.seed + args.heldout_offset, args.eval)
    train_keys = {tuple(np.round(row, 6)) for row in x}
    test_keys = {tuple(np.round(np.r_[s, t], 6)) for s, t in tests}
    if train_keys & test_keys:
        raise RuntimeError('Training and held-out layouts overlap')
    evaluations = []
    for i, (source, target) in enumerate(tests):
        expert = clean(run(source, target, neighbors=True, board_x=args.eval_board_x))
        learned = clean(run(source, target, neighbors=True, policy=policy, board_x=args.eval_board_x))
        evaluations.append({'layout': i, 'expert': expert, 'learned': learned})
        print(f"held-out {i + 1}/{args.eval}: expert={expert['success']} learned={learned['success']}", flush=True)
    report = {'sim_only': True, 'training_data': str(args.data), 'training_demonstrations': len(x),'eval_board_center_x_m':args.eval_board_x,
              'optimizer_steps': args.steps, 'losses': losses, 'heldout_seed': args.seed + args.heldout_offset,
              'heldout_count': args.eval, 'train_eval_layout_overlap': len(train_keys & test_keys),
              'heldout_expert_successes': sum(v['expert']['success'] for v in evaluations),
              'heldout_learned_successes': sum(v['learned']['success'] for v in evaluations),
              'no_expert_fallback': all(v['learned'].get('controller') == 'learned_policy_no_ik_fallback'
                                        and v['learned'].get('policy_calls', 0) > 0 for v in evaluations),
              'evaluation': evaluations}
    (args.out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'evaluation'}, indent=2), flush=True)


if __name__ == '__main__':
    main()
