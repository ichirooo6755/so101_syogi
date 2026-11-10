"""Reopen every exported STEP/F3D and verify solid count, volume, and scale."""
import adsk.core
import adsk.fusion
import json
from pathlib import Path

directory = Path("/Users/sugawaraichirou/Documents/ChatGPT/so101/output/v8/print_export_2026-10-26")
report = json.loads((directory / "export_report.json").read_text(encoding="utf-8"))
main = next(document for document in app.documents if document.name == report["source_document"])
main_design = adsk.fusion.Design.cast(main.products.itemByProductType("DesignProductType"))
source_state = (main.isModified, main.dataFile.versionNumber,
                main_design.timeline.markerPosition, main_design.timeline.count)
assert source_state[0] is False
checks = []

for part in report["exports"]:
    for extension in ("_editable.f3d", ".step"):
        path = directory / "source_cad" / (part["stem"] + extension)
        if extension.endswith("f3d"):
            options = app.importManager.createFusionArchiveImportOptions(str(path))
        else:
            options = app.importManager.createSTEPImportOptions(str(path))
        document = app.importManager.importToNewDocument(options)
        assert document, path
        try:
            design = adsk.fusion.Design.cast(document.products.itemByProductType("DesignProductType"))
            root = design.rootComponent
            bodies = list(root.bRepBodies)
            for occurrence in root.allOccurrences:
                bodies.extend(list(occurrence.bRepBodies))
            bodies = [body for body in bodies if body.isSolid and body.volume > 1e-9]
            assert len(bodies) == 1, (path.name, len(bodies))
            body = bodies[0]
            assert body.lumps.count == 1, path.name
            volume_error = abs(body.volume * 1000 - part["volume_mm3"])
            # The authoritative native archive is expected to preserve volume.
            # STEP reimport can re-tolerate analytic/NURBS faces; record that
            # measured exchange-format drift separately rather than hiding it.
            volume_tolerance = 0.01 if extension.endswith("f3d") else max(0.01, part["volume_mm3"] * 0.001)
            assert volume_error < volume_tolerance, (path.name, body.volume * 1000)
            size = [(b - a) * 10 for a, b in zip(body.boundingBox.minPoint.asArray(), body.boundingBox.maxPoint.asArray())]
            assert max(abs(a - b) for a, b in zip(size, part["size_mm"])) < 0.01, (path.name, size)
            parameters = [{"name": parameter.name, "expression": parameter.expression}
                          for parameter in design.userParameters]
            checks.append({
                "file": str(path.relative_to(directory)),
                "reopened_in_Fusion": True,
                "solid_body_count": 1,
                "lump_count": 1,
                "volume_mm3": body.volume * 1000,
                "volume_error_mm3": volume_error,
                "volume_error_fraction": volume_error / part["volume_mm3"],
                "volume_tolerance_mm3": volume_tolerance,
                "size_mm": size,
                "user_parameters": parameters,
            })
        finally:
            assert document.close(False)
            main.activate()

assert source_state == (main.isModified, main.dataFile.versionNumber,
                        main_design.timeline.markerPosition, main_design.timeline.count)
result = {"passed": True, "source_assembly_unchanged": True, "files": checks}
(directory / "cad_reopen_verification.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
)
summary = {"passed": True, "source_assembly_unchanged": True, "files": [
    {key: value for key, value in item.items() if key != "user_parameters"} |
    {"brush_parameters": [parameter for parameter in item["user_parameters"] if "brush" in parameter["name"] and "dia" in parameter["name"]]}
    for item in checks
]}
print(json.dumps(summary, ensure_ascii=False, indent=2))
