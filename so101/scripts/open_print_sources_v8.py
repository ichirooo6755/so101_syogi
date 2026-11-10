"""Open the existing cloud V8 assembly for read-only export, never overwrite it."""
import adsk.core
from pathlib import Path

assert ui.activeCommand == "SelectCommand", ui.activeCommand
assert not any("so101書道" in document.name for document in app.documents)
project = next(project for project in app.data.dataProjects if project.name == "書道")
source = next(file for file in project.rootFolder.dataFiles if file.name == "so101書道")
print("SOURCE", source.id, "VERSION", source.versionNumber)
document = app.documents.open(source, True)
assert document, "Unable to open the saved assembly"
print("Opened existing assembly for export; source remains untouched")
print("DOCUMENT", document.name)
inspect_path = Path(
    "/Users/sugawaraichirou/Documents/ChatGPT/so101/scripts/inspect_print_sources_v8.py"
)
exec(compile(inspect_path.read_text(encoding="utf-8"), str(inspect_path), "exec"))
