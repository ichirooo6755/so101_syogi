"""Inspect live Fusion documents before exporting the four V8 print parts."""
import adsk.core
import adsk.fusion
import json
from pathlib import Path

report = {
    "fusion_version": app.version,
    "active_command": ui.activeCommand,
    "active_document": app.activeDocument.name if app.activeDocument else None,
    "documents": [],
}
for document in app.documents:
    design = adsk.fusion.Design.cast(
        document.products.itemByProductType("DesignProductType")
    )
    item = {"name": document.name, "modified": document.isModified}
    try:
        item["data_id"] = document.dataFile.id
        item["version"] = document.dataFile.versionNumber
    except Exception:
        item["data_id"] = None
    if design:
        item["timeline"] = [design.timeline.markerPosition, design.timeline.count]
        item["occurrences"] = []
        for occurrence in design.rootComponent.occurrences:
            if any(key in occurrence.name for key in ("部品１", "Wrist", "Brush", "SC616")):
                item["occurrences"].append({
                    "name": occurrence.name,
                    "visible": occurrence.isVisible,
                    "transform": list(occurrence.transform2.asArray()),
                    "bodies": [{
                        "name": body.name,
                        "solid": body.isSolid,
                        "lumps": body.lumps.count,
                        "volume_mm3": body.volume * 1000,
                    } for body in occurrence.bRepBodies],
                })
    report["documents"].append(item)

path = Path("/Users/sugawaraichirou/Documents/ChatGPT/so101/tmp/print_sources_v8_initial.json")
path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
