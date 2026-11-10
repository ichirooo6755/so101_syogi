"""Read Fusion data locations only, without modifying models or preferences."""
import json

data = app.data
report = {"active_project": None, "projects": []}
if data.activeProject:
    report["active_project"] = data.activeProject.name
for project in data.dataProjects:
    root_folder = project.rootFolder
    report["projects"].append({
        "name": project.name,
        "id": project.id,
        "root_folder_id": root_folder.id,
        "folders": [{"name": folder.name, "id": folder.id} for folder in root_folder.dataFolders],
        "files": [{"name": file.name, "id": file.id, "version": file.versionNumber}
                  for file in root_folder.dataFiles if "so101" in file.name.lower() or "V8" in file.name],
    })
print(json.dumps(report, ensure_ascii=False, indent=2))
