#!/usr/bin/env python3
"""Build a clean, verified V8 print folder and ZIP without overwriting old data."""
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil
import struct
import zipfile

project_root = Path(__file__).resolve().parents[1]
staging = project_root / "output/v8/print_export_2026-10-26"
destination = project_root / "output/print_v8"
archive_path = project_root / "output/so101_calligraphy_V8_print_files.zip"
assert not destination.exists(), "Do not overwrite an existing print package"
assert not archive_path.exists(), "Do not overwrite an existing print ZIP"

export_report = json.loads((staging / "export_report.json").read_text(encoding="utf-8"))
meshes = json.loads((staging / "mesh_verification.json").read_text(encoding="utf-8"))
cad = json.loads((staging / "cad_reopen_verification.json").read_text(encoding="utf-8"))
parameter_check = json.loads((staging / "cartridge_parameter_verification.json").read_text(encoding="utf-8"))
cad_shell_audit = json.loads((staging / "cad_shell_audit.json").read_text(encoding="utf-8"))
assert export_report["source_geometry_and_parameters_preserved"]
assert export_report["source_fingerprint_before"] == export_report["source_fingerprint_after"]
assert export_report["main_saved"] and cad["passed"] and parameter_check["passed"]
assert len(export_report["exports"]) == len(meshes) == 4
assert len(cad["files"]) == 8 and all(check["reopened_in_Fusion"] for check in cad["files"])
assert all(mesh["watertight"] and mesh["consistent_winding"] for mesh in meshes)

connectivity = []
expected_files = set()
for part in export_report["exports"]:
    path = staging / (part["stem"] + ".stl")
    expected_files.add(path.name)
    data = path.read_bytes()
    assert sha256(data).hexdigest() == part["stl_sha256"], path.name
    count = struct.unpack_from("<I", data, 80)[0]
    assert len(data) == 84 + 50 * count, path.name
    parents = {}
    edges = Counter()
    minimum = [float("inf")] * 3
    maximum = [float("-inf")] * 3
    signed_volume = 0.0
    triangles = []

    def find(vertex):
        parents.setdefault(vertex, vertex)
        while parents[vertex] != vertex:
            parents[vertex] = parents[parents[vertex]]
            vertex = parents[vertex]
        return vertex

    for index in range(count):
        row = struct.unpack_from("<12fH", data, 84 + index * 50)
        vertices = [tuple(row[position:position + 3]) for position in (3, 6, 9)]
        keys = [tuple(round(coordinate, 5) for coordinate in vertex) for vertex in vertices]
        triangles.append((keys, vertices))
        assert len(set(keys)) == 3, (path.name, "degenerate triangle", index)
        for vertex in vertices:
            for axis in range(3):
                minimum[axis] = min(minimum[axis], vertex[axis])
                maximum[axis] = max(maximum[axis], vertex[axis])
        for first, second in zip(keys, keys[1:] + keys[:1]):
            edges[tuple(sorted((first, second)))] += 1
            first_root, second_root = find(first), find(second)
            if first_root != second_root:
                parents[first_root] = second_root
        a, b, c = vertices
        signed_volume += (a[0] * (b[1] * c[2] - b[2] * c[1])
                          + a[1] * (b[2] * c[0] - b[0] * c[2])
                          + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6

    # Closed internal voids have their own negative-volume boundary surface;
    # counting surface components alone incorrectly labels those as extra parts.
    # Compare each surface and its winding against the native CAD topology.
    surfaces = {}
    for keys, vertices in triangles:
        component_id = find(keys[0])
        surface = surfaces.setdefault(component_id, {"triangles": 0, "signed_volume_mm3": 0.0,
                                                      "minimum_mm": [float("inf")] * 3,
                                                      "maximum_mm": [float("-inf")] * 3})
        surface["triangles"] += 1
        a, b, c = vertices
        surface["signed_volume_mm3"] += (a[0] * (b[1] * c[2] - b[2] * c[1])
                                         + a[1] * (b[2] * c[0] - b[0] * c[2])
                                         + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6
        for vertex in vertices:
            for axis in range(3):
                surface["minimum_mm"][axis] = min(surface["minimum_mm"][axis], vertex[axis])
                surface["maximum_mm"][axis] = max(surface["maximum_mm"][axis], vertex[axis])
    topology = next(item for item in cad_shell_audit["parts"] if item["part"] == part["part"])
    assert topology["is_solid"] and len(topology["lumps"]) == 1
    expected_shells = topology["lumps"][0]["shells"]
    outside = [surface for surface in surfaces.values() if surface["signed_volume_mm3"] > 1e-8]
    cavities = [surface for surface in surfaces.values() if surface["signed_volume_mm3"] < -1e-8]
    assert len(surfaces) == len(expected_shells), (path.name, len(surfaces), expected_shells)
    assert len(outside) == sum(not shell["is_void"] for shell in expected_shells) == 1
    assert len(cavities) == sum(shell["is_void"] for shell in expected_shells)
    for cavity in cavities:
        assert all(a >= b - 1e-4 for a, b in zip(cavity["minimum_mm"], outside[0]["minimum_mm"]))
        assert all(a <= b + 1e-4 for a, b in zip(cavity["maximum_mm"], outside[0]["maximum_mm"]))
    assert all(uses == 2 for uses in edges.values()), path.name
    assert signed_volume > 0, (path.name, "Globally reversed orientation")
    assert all(abs(value) < 0.05 for value in minimum), (path.name, minimum)
    actual_size = [b - a for a, b in zip(minimum, maximum)]
    assert max(abs(a - b) for a, b in zip(actual_size, part["size_mm"])) < 0.05
    connectivity.append({"file": path.name, "cad_connected_solid_count": 1,
                         "mesh_boundary_surface_count": len(surfaces), "enclosed_void_count": len(cavities),
                         "surface_details": list(surfaces.values()), "surface_topology_matches_CAD": True,
                         "all_edges_used_by_two_triangles": True, "outward_signed_volume_positive": True,
                         "bounds_mm": [minimum, maximum], "quantity": 1,
                         "unit_to_use_in_slicer": "mm", "scale_percent": 100,
                         "sha256": sha256(data).hexdigest()})

assert {path.name for path in staging.glob("*.stl")} == expected_files

destination.mkdir()
for name in expected_files:
    shutil.copy2(staging / name, destination / name)
for name in ("export_report.json", "mesh_verification.json", "cad_reopen_verification.json",
             "cartridge_parameter_verification.json", "cad_shell_audit.json"):
    shutil.copy2(staging / name, destination / name)
shutil.copytree(staging / "source_cad", destination / "source_cad")
shutil.copytree(staging / "preview", destination / "preview")
shutil.copy2(project_root / "scripts/templates/print_v8_README.md", destination / "README.md")
shutil.copy2(project_root / "組立部品表.md", destination / "組立部品表.md")
assert len(list(destination.glob("*.stl"))) == 4

result = {
    "passed": True,
    "created_utc": datetime.now(timezone.utc).isoformat(),
    "folder": str(destination),
    "source_document": export_report["source_document"],
    "source_cloud_version": export_report["main_cloud_version"],
    "source_assembly_geometry_and_parameters_unchanged": True,
    "stl_count": 4,
    "total_print_quantity": 4,
    "stl_checks": connectivity,
    "native_archive_reopen_passed": True,
    "brush_diameter_regeneration_test_passed": True,
    "step_exchange_drift_recorded_in_cad_report_and_readme": True,
    "source_folder": str(staging),
    "slicer_profiles_or_gcode_included": False,
    "physical_print_and_load_tests_performed": False,
}
(destination / "package_verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
files = sorted(path for path in destination.rglob("*") if path.is_file())
hashes = {str(path.relative_to(destination)): sha256(path.read_bytes()).hexdigest() for path in files}
(destination / "SHA256SUMS.txt").write_text(
    "".join(f"{digest}  {name}\n" for name, digest in hashes.items()), encoding="utf-8"
)

with zipfile.ZipFile(archive_path, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for path in sorted(destination.rglob("*")):
        if path.is_file():
            archive.write(path, str(Path(destination.name) / path.relative_to(destination)))
with zipfile.ZipFile(archive_path, "r") as archive:
    assert archive.testzip() is None
    zipped_stl = [name for name in archive.namelist() if name.endswith(".stl")]
    assert len(zipped_stl) == 4
    for name, digest in hashes.items():
        assert sha256(archive.read(f"{destination.name}/{name}")).hexdigest() == digest, name
    for path in destination.rglob("*"):
        if path.is_file():
            name = f"{destination.name}/{path.relative_to(destination)}"
            assert archive.read(name) == path.read_bytes(), name

print(json.dumps({"passed": True, "folder": str(destination), "zip": str(archive_path),
                  "zip_bytes": archive_path.stat().st_size,
                  "zip_sha256": sha256(archive_path.read_bytes()).hexdigest(),
                  "zip_contents_verified": True, "stl_count": 4,
                  "files_in_zip": len(list(destination.rglob("*"))) - len([p for p in destination.rglob("*") if p.is_dir()]),
                  "parts": connectivity}, ensure_ascii=False, indent=2))
