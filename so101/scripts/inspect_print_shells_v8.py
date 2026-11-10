"""Read CAD lump/shell topology; enclosed void surfaces are not extra parts."""
import adsk.fusion
import json
from pathlib import Path

out = Path("/Users/sugawaraichirou/Documents/ChatGPT/so101/output/v8/print_export_2026-10-26")
export_report = json.loads((out / "export_report.json").read_text(encoding="utf-8"))
main = next(document for document in app.documents if document.name == "so101書道")
design = adsk.fusion.Design.cast(main.products.itemByProductType("DesignProductType"))
reports = []
for part in export_report["exports"]:
    occurrence = design.rootComponent.occurrences.itemByName(part["source_occurrence"])
    body = occurrence.bRepBodies.item(0)
    reports.append({
        "part": part["part"], "stem": part["stem"], "is_solid": body.isSolid,
        "lumps": [{"shells": [{"is_void": shell.isVoid, "faces": shell.faces.count}
                              for shell in lump.shells]} for lump in body.lumps],
    })
report = {"source_modified": main.isModified, "parts": reports}
(out / "cad_shell_audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
