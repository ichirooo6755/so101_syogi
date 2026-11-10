# Motoya brushwork curriculum implementation plan

1. Replace the downloadable Aoyagi teacher with a verified, local-only S Motoya
   Seikaisho 5 ProN provider; expose environment/CLI configuration and fail
   before training if it is missing or incorrect.
2. Delete font-to-centreline fitting. Render Motoya solely into a target raster
   and test that enabling the critic preserves all AnimCJK/KanjiVG motion data.
3. Normalize final masks and add explicit stroke placement, length, angle,
   centroid/balance, technique, ink, drip, and collision score columns.
4. Extend the reservoir transfer from two edge stamps to seven independently
   loaded hair bundles shaped by entry/send/finish, technique, roll, pressure,
   and tuft opening.
5. Replace the broad four-stage schedule with gated brush handling, basic phase,
   tome/hane/harai, turn/curve/fold, radical, elementary, and joyo stages.
6. Save raw ink and comparison images, document licensing and output locations,
   run unit/package/CLI checks, generate a clearly labelled motion-only smoke
   result, and publish the scoped branch as a Draft PR.
