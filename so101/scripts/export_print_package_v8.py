"""Export exact copies of the four live V8 assembly parts, never edit sources.

Run with fusion_rpc.py. The exported STL files use millimetres and only a
translation to put each body's minimum XYZ at zero, not a scale or redesign.
"""
import adsk.core
import adsk.fusion
import datetime
import hashlib
import json
from pathlib import Path

project_root = Path("/Users/sugawaraichirou/Documents/ChatGPT/so101")
out = project_root / "output/v8/print_export_2026-10-26"
assert not out.exists(), "Export directory already exists; do not overwrite an earlier run"
assert ui.activeCommand == "SelectCommand", ui.activeCommand
main = next(document for document in app.documents if document.name == "so101書道")
main.activate()
design = adsk.fusion.Design.cast(main.products.itemByProductType("DesignProductType"))
root = design.rootComponent
assert not main.isModified, "Keep any unsaved user edits separate from the saved V8 print release"
assert design.timeline.markerPosition == design.timeline.count, "Timeline must not be rolled back"

specs = [
    ("base", "部品１_V8_元取付形状保持:1", "01_base_original_mount_V8", 38550.50206478457),
    ("carrier", "Brush_Load_Carrier_Compact_V5:1", "02_load_carrier_V5", 6573.724935501749),
    ("cartridge", "Brush_Cartridge_Symmetric_15mm_V5:1", "03_brush_cartridge_15mm_V5", 6846.800123811279),
    ("wrist", "Wrist_Roll_Clearance_V8_元取付対応:1", "04_wrist_clearance_V8", 22025.213051512656),
]
parts = {}
for label, occurrence_name, stem, expected_volume in specs:
    occurrence = root.occurrences.itemByName(occurrence_name)
    assert occurrence and occurrence.isVisible, occurrence_name
    bodies = list(occurrence.bRepBodies)
    assert len(bodies) == 1, (occurrence_name, "Unexpected extra bodies", len(bodies))
    body = bodies[0]
    assert body.isSolid and body.lumps.count == 1, occurrence_name
    assert abs(body.volume * 1000 - expected_volume) < 0.001, (occurrence_name, body.volume * 1000)
    parts[label] = occurrence


def source_fingerprint():
    return {
        "modified": main.isModified,
        "version": main.dataFile.versionNumber,
        "timeline": [design.timeline.markerPosition, design.timeline.count],
        "parameters": [(parameter.name, parameter.expression) for parameter in design.userParameters],
        "occurrences": [{
            "name": occurrence.name,
            "visible": occurrence.isVisible,
            "transform": list(occurrence.transform2.asArray()),
            "bodies": [{
                "name": body.name,
                "volume_mm3": body.volume * 1000,
                "faces": body.faces.count,
                "bounds_cm": [list(body.boundingBox.minPoint.asArray()), list(body.boundingBox.maxPoint.asArray())],
            } for body in occurrence.bRepBodies],
        } for occurrence in root.occurrences],
    }


before = source_fingerprint()
out.mkdir(parents=True)
(out / "source_cad").mkdir()
(out / "preview").mkdir()
temporary_brep = adsk.fusion.TemporaryBRepManager.get()
exports = []

for label, occurrence_name, stem, expected_volume in specs:
    occurrence = parts[label]
    source_body = occurrence.bRepBodies.item(0)
    archive = out / "source_cad" / (stem + "_editable.f3d")
    # Referenced base/wrist have their own documents. Carrier/cartridge are
    # native components in the main design, retaining their user parameters.
    if label in ("base", "wrist"):
        source_doc = next(document for document in app.documents if document.name == occurrence.component.name)
        source_design = adsk.fusion.Design.cast(source_doc.products.itemByProductType("DesignProductType"))
        options = source_design.exportManager.createFusionArchiveExportOptions(str(archive))
        archive_result = source_design.exportManager.execute(options)
    else:
        options = design.exportManager.createFusionArchiveExportOptions(str(archive), occurrence.component)
        archive_result = design.exportManager.execute(options)
    assert archive.is_file() and archive.stat().st_size > 1000, archive

    copy = temporary_brep.copy(source_body)
    minimum = copy.boundingBox.minPoint
    translation_mm = [-coordinate * 10 for coordinate in minimum.asArray()]
    matrix = adsk.core.Matrix3D.create()
    matrix.translation = adsk.core.Vector3D.create(*[-coordinate for coordinate in minimum.asArray()])
    assert temporary_brep.transform(copy, matrix)
    assert abs(copy.volume * 1000 - expected_volume) < 0.001
    temporary_document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    try:
        temporary_design = adsk.fusion.Design.cast(temporary_document.products.itemByProductType("DesignProductType"))
        temporary_design.designType = adsk.fusion.DesignTypes.DirectDesignType
        temporary_root = temporary_design.rootComponent
        body = temporary_root.bRepBodies.add(copy)
        body.name = stem
        assert body.isSolid and body.lumps.count == 1

        step = out / "source_cad" / (stem + ".step")
        assert temporary_design.exportManager.execute(
            temporary_design.exportManager.createSTEPExportOptions(str(step), temporary_root)
        )
        stl = out / (stem + ".stl")
        options = temporary_design.exportManager.createSTLExportOptions(body, str(stl))
        options.unitType = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        options.isBinaryFormat = True
        options.sendToPrintUtility = False
        options.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        assert temporary_design.exportManager.execute(options)
        assert stl.is_file() and stl.stat().st_size > 1000

        camera = app.activeViewport.camera
        camera.viewOrientation = adsk.core.ViewOrientations.IsoTopRightViewOrientation
        camera.isFitView = True
        app.activeViewport.camera = camera
        app.activeViewport.refresh()
        assert app.activeViewport.saveAsImageFile(str(out / "preview" / (stem + ".png")), 1200, 900)

        exports.append({
            "part": label,
            "stem": stem,
            "quantity": 1,
            "source_occurrence": occurrence_name,
            "volume_mm3": body.volume * 1000,
            "size_mm": [(maximum - minimum) * 10 for minimum, maximum in zip(
                body.boundingBox.minPoint.asArray(), body.boundingBox.maxPoint.asArray())],
            "printed_body_count": 1,
            "original_CAD_body_count": 1,
            "omitted_fragment_mm3": 0,
            "translation_from_assembly_mm": translation_mm,
            "rotation_from_assembly": "identity; no print orientation optimisation",
            "stl_units": "mm",
            "mesh_refinement": "Fusion High",
            "stl_bytes": stl.stat().st_size,
            "stl_sha256": hashlib.sha256(stl.read_bytes()).hexdigest(),
            "editable_archive_export_result": archive_result,
        })
    finally:
        assert temporary_document.close(False)
        main.activate()

after = source_fingerprint()
assert before == after, "Source assembly changed during export"
report = {
    "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "fusion_version": app.version,
    "source_document": main.name,
    "source_cloud_id": main.dataFile.id,
    "main_cloud_version": main.dataFile.versionNumber,
    "main_saved": not main.isModified,
    "timeline": [design.timeline.markerPosition, design.timeline.count],
    "exports": exports,
    "source_geometry_and_parameters_preserved": True,
    "source_fingerprint_before": before,
    "source_fingerprint_after": after,
    "generative_outcome_adopted": False,
    "print_orientation_not_yet_tested": True,
    "physical_print_or_load_test_performed": False,
}
(out / "export_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({key: value for key, value in report.items() if not key.startswith("source_fingerprint")}, ensure_ascii=False, indent=2))
