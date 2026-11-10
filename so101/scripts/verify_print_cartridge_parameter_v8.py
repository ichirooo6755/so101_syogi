"""Test brush_dia only in an imported disposable cartridge copy; never save it."""
import adsk.core
import adsk.fusion
import json
from pathlib import Path

directory = Path("/Users/sugawaraichirou/Documents/ChatGPT/so101/output/v8/print_export_2026-10-26")
main = next(document for document in app.documents if document.name == "so101書道")
main_design = adsk.fusion.Design.cast(main.products.itemByProductType("DesignProductType"))
initial_state = (main.isModified, main_design.timeline.markerPosition, main_design.timeline.count)
path = directory / "source_cad/03_brush_cartridge_15mm_V5_editable.f3d"
options = app.importManager.createFusionArchiveImportOptions(str(path))
document = app.importManager.importToNewDocument(options)
assert document
checks = []
try:
    design = adsk.fusion.Design.cast(document.products.itemByProductType("DesignProductType"))
    root = design.rootComponent
    parameter = design.userParameters.itemByName("brush_dia")
    assert parameter and abs(parameter.value * 10 - 15) < 1e-6

    def solid_body():
        bodies = list(root.bRepBodies)
        for occurrence in root.allOccurrences:
            bodies.extend(list(occurrence.bRepBodies))
        bodies = [body for body in bodies if body.isSolid and body.volume > 1e-9]
        assert len(bodies) == 1 and bodies[0].lumps.count == 1
        return bodies[0]

    original_volume = solid_body().volume * 1000
    for diameter in (12, 17, 15):
        parameter.expression = f"{diameter} mm"
        assert design.computeAll(), diameter
        body = solid_body()
        radii = sorted({round(face.geometry.radius * 10, 6) for face in body.faces
                        if isinstance(face.geometry, adsk.core.Cylinder)})
        assert any(abs(radius - (diameter + 0.4) / 2) < 1e-5 for radius in radii), (diameter, radii)
        assert any(abs(radius - (diameter + 1) / 2) < 1e-5 for radius in radii), (diameter, radii)
        size = [(b - a) * 10 for a, b in zip(body.boundingBox.minPoint.asArray(), body.boundingBox.maxPoint.asArray())]
        assert max(abs(a - b) for a, b in zip(size, (30, 52, 24))) < 0.01, size
        components = [root] + [occurrence.component for occurrence in root.allOccurrences]
        errors = [(feature.name, feature.errorOrWarningMessage)
                  for component in components for feature in component.features
                  if feature.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]
        assert not errors, (diameter, errors)
        checks.append({"brush_dia_mm": diameter, "volume_mm3": body.volume * 1000,
                       "size_mm": size, "cylinder_radii_mm": radii, "healthy_features": True})
    assert checks[0]["volume_mm3"] > original_volume > checks[1]["volume_mm3"]
    assert abs(checks[-1]["volume_mm3"] - original_volume) < 0.01
finally:
    assert document.close(False)
    main.activate()
assert initial_state == (main.isModified, main_design.timeline.markerPosition, main_design.timeline.count)
result = {"passed": True, "file": str(path.relative_to(directory)),
          "tested_only_in_disposable_copy": True, "source_archive_not_saved_or_modified": True,
          "main_assembly_unchanged": True, "checks": checks}
(directory / "cartridge_parameter_verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
