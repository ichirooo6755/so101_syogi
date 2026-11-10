# Professional calligraphy implementation plan

> Superseded on 2026-08-15 by
> `2026-08-15-motoya-brushwork-curriculum-implementation.md`. The Aoyagi
> download and centreline fitting steps below are historical and were removed.

## 1. Data and provenance

- Add a pinned Aoyagi Kouzan font downloader, checksum, glyph-mask renderer,
  cache, and license notice.
- Extend KANJIDIC2 selection to grades 1–6 and 8; verify exactly 2,136 joyo
  entries and verify KanjiVG/AnimCJK coverage before training.
- Add fixtures for font masks and joyo counts without network-dependent tests.

## 2. Independent models

- Extract the current brush measurements behind a `BrushPhysics` protocol and
  implement legacy and segmented adapters.
- Extract paper transfer behind an `InkModel` protocol; retain the existing
  renderer as legacy and add core/surface reservoirs, capillary flow, loading,
  wiping, drip prediction, and multi-bundle transfer.
- Extract trajectory profiles behind `BrushworkPlanner`; retain legacy and add
  traditional entry, press/lift, corner, finish, roll, and minimum-jerk timing.
- Add explicit feature configuration and ablation labels to run metadata.

## 3. MuJoCo scene and episode state machine

- Replace the single tuft with a stable three-segment, six-passive-DOF tuft.
- Add inkstone pool, lip, legal tuft contacts, and viewer materials.
- Add load, wipe, carry, settle, write, and re-ink phases to reset/step while
  keeping six robot joint actions.
- Version and expand observations with module state and target phase.

## 4. Scores and reporting

- Add professional glyph-mask similarity and negative-space metrics.
- Add per-episode component scores for shape, width, trajectory, stroke order,
  smoothness, brushwork, ink, loading, drip, collision, and balance.
- Preserve raw metrics and fixed weights in JSON, Monitor CSV, replay output,
  and all-character CSV.

## 5. Training and replay

- Add ink-loading/no-drip/brushwork curricula and behavior-cloning samples.
- Extend the resumable curriculum to all joyo kanji and component-based hard
  example mining.
- Add matched ablation evaluation and robust checkpoint selection.
- Render inkstone phases and save final ink plus professional target/difference
  panels.

## 6. Verification and delivery

- Run deterministic physics, model, trajectory, environment, PPO, packaging,
  and CLI tests on CPU.
- Run real staged PPO training, ablations, representative image review, and all
  2,136-character evaluation.
- Continue hard-example training while it improves the lower tail; report
  honestly if mean 75/minimum 60 is not attained.
- Commit trained artifacts, results, source notices, and documentation; push
  `master` only after tests and remote comparison pass.
