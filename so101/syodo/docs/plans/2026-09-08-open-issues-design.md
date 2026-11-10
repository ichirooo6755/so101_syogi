# Open issues: calibration, tilt integration, visual review

Scope: #13, #14, #17. Base: `f5a2608` on
`agent/motoya-brushwork-curriculum`. Work occurs in a separate worktree so the
existing uncommitted hardware height changes remain intact.

The user authorized implementation, including major changes. Replacing the
controller immediately would mix geometry, calibration, and policy regressions.
The chosen approach first closes reproducible validation gaps and makes visual
weaknesses reviewable against the adopted model. Training is a subsequent step
when its existing physical gates pass.

- #14: validate measured inputs and solved geometry at the shared `require_ready`
  boundary; invalidate geometry after motor recalibration and IK reference changes;
  detect edits to newly solved geometry with a fingerprint. Retain structurally
  valid schema-1 desks, which predate fingerprints. Test rejection before robot
  connection. Make hardware tests independent of private ignored files.
- #13: verify the existing final-CAD Y hinge and sixth-axis IK with a regression
  that changes physical brush lean while keeping tip position fixed. Document the
  final 30 mm CAD radius and distinguish mechanism acceptance from training gates.
- #17: add glyph/IoU selection and labels to PPO contact sheets; produce a review
  bundle from the complete adopted evaluation, with fixed representatives, seeded
  grade samples and worst glyph/IoU examples, exact corpus checks, hashes, and a
  ranked CSV. Missing images/metrics or failed C gates must block the A bundle.

Validation: focused regressions, full pytest, offline CLI execution, image
inspection, and a result document. No physical motor commands are needed.
Keep canonical weights, strict thresholds, and original evaluation files intact.
The final A decision remains a human review; producing images cannot grant it.
