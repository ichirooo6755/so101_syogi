# Offline hardware regression fixtures

`hardware-desk.json` retains numerical geometry and taught poses from the 12 cm
desk used by the existing hardware tests. Device bindings, motor hashes, current
pressure observations and personal machine paths have been removed.
`follower-calibration.json` contains only the six axis IDs and encoder limits
needed to reproduce those geometry regressions. Tests copy both into temporary
directories. Neither file is a calibration for another physical arm; production
commands continue to use `data/hardware/desk.json` obtained through teach/solve.
