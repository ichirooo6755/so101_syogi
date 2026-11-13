"""Install a pinned SO-101 game engine from its upstream distribution."""

import argparse
from hashlib import file_digest
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parent
KATAGO = "https://github.com/lightvector/KataGo/releases/download/v1.17.1/"
YANEURAOU = "https://github.com/yaneurao/YaneuraOu/releases/download/V9.00/"
STOCKFISH = "https://github.com/official-stockfish/Stockfish/releases/download/sf_19/"
HAO_TAG = "tanuki-.halfkp_256x2-32-32.2023-05-08"
HALFKP = "NNUE_halfkp_256x2_32_32"
GO_MODEL = "b10c384h6nbttflrs.bin.gz"
ASSETS = {
    GO_MODEL: (KATAGO + GO_MODEL, "0ba27eced5180b3e3d0b898b280c541112989765e789d1eb6cd0d31b2b2c1229"),
    "katago-v1.17.1-eigen-windows-x64.zip": (
        KATAGO + "katago-v1.17.1-eigen-windows-x64.zip",
        "3a7538ecb6facefcfe16d649fd695c29e44f8372cb7de8c316eee5779865f379",
    ),
    "KataGo-v1.17.1.tar.gz": (
        "https://codeload.github.com/lightvector/KataGo/tar.gz/refs/tags/v1.17.1",
        "c5d422fe85d1876d67a45540277c8d59ec5d97f91692113ab0fde205604441d4",
    ),
    "yaneuraou-V900-git-mac-all.7z": (
        YANEURAOU + "yaneuraou-V900-git-mac-all.7z",
        "3aad1e03386ab6e311fd592da20974f0a032c169177783ab97c2ec745df33418",
    ),
    "yaneuraou-V900-git-win64-all.7z": (
        YANEURAOU + "yaneuraou-V900-git-win64-all.7z",
        "6517997dd05ba049a2244a828216967a0ad351d975ec52a0f358e2883197dec6",
    ),
    HAO_TAG + ".7z": (
        f"https://github.com/nodchip/tanuki-/releases/download/{HAO_TAG}/{HAO_TAG}.7z",
        "f16dc66c529857bf08fce8cee4f1e53a6993297644100267a6ccccd62e43dbba",
    ),
    "stockfish-windows-x86-64-universal.zip": (
        STOCKFISH + "stockfish-windows-x86-64-universal.zip",
        "3c8bf1f9ea66a09350a40df4f632288285ac206d99f33ab5842c408fc30b48a7",
    ),
    "stockfish-macos-universal.tar.gz": (
        STOCKFISH + "stockfish-macos-universal.tar.gz",
        "a1f0e3bcc5a6927a11fe6fc8e54a779754645f3c2bae2cf13420fd1957adaa77",
    ),
}


def sha256(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def obtain(name, cache):
    url, expected = ASSETS[name]
    archive = cache / name
    if not archive.is_file() or sha256(archive) != expected:
        print(f"Downloading {name}", flush=True)
        with tempfile.TemporaryDirectory(dir=cache) as temp:
            download = Path(temp) / name
            with urlopen(url, timeout=60) as response, download.open("wb") as output:
                shutil.copyfileobj(response, output)
            if sha256(download) != expected:
                raise ValueError(f"SHA-256 mismatch: {name}")
            download.replace(archive)
    return archive


def install_file(source, target, executable=False):
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file():
        if sha256(source) != sha256(target):
            raise ValueError(f"Existing file differs: {target}. Move it before reinstalling.")
        if executable and os.name != "nt":
            target.chmod(0o755)
        return
    with tempfile.TemporaryDirectory(dir=target.parent) as temp:
        candidate = Path(temp) / target.name
        shutil.copyfile(source, candidate)
        if executable and os.name != "nt":
            candidate.chmod(0o755)
        candidate.replace(target)


def extract(archive, dest, *members):
    tar = "tar"
    if os.name == "nt" and (system_root := os.environ.get("SystemRoot")):
        tar = str(Path(system_root) / "System32" / "tar.exe")
    subprocess.run([tar, "-xf", str(archive), "-C", str(dest), *members], check=True)


def install_go(dest, target, cache, staging):
    model = obtain(GO_MODEL, cache)
    if target == "windows-x64":
        archive = obtain("katago-v1.17.1-eigen-windows-x64.zip", cache)
        extract(archive, staging)
        for library in staging.glob("*.dll"):
            install_file(library, dest / "engine" / library.name)
        engine = staging / "katago.exe"
    else:
        arch = "arm64" if target == "macos-arm64" else "x86_64"
        if platform.system() != "Darwin" or platform.machine().lower() != arch:
            raise ValueError(f"Run the KataGo build with a native macOS {arch} Python.")
        installed = dest / "engine" / "katago"
        if installed.is_file():
            version = subprocess.check_output([str(installed), "version"], text=True).splitlines()
            if not version or version[0] != "KataGo v1.17.1":
                raise ValueError(f"Existing engine is a different version: {installed}")
            install_file(model, dest / "models" / GO_MODEL)
            print(f"Using existing {installed}")
            return
        archive = obtain("KataGo-v1.17.1.tar.gz", cache)
        extract(archive, staging)
        source = staging / "KataGo-1.17.1" / "cpp"
        build = staging / "build"
        subprocess.run([
            "cmake", "-S", str(source), "-B", str(build), "-DUSE_BACKEND=EIGEN",
            "-DNO_GIT_REVISION=1", "-DCMAKE_BUILD_TYPE=Release", f"-DCMAKE_OSX_ARCHITECTURES={arch}",
        ], check=True)
        subprocess.run(["cmake", "--build", str(build), "--parallel", "4"], check=True)
        engine = build / "katago"
    install_file(model, dest / "models" / GO_MODEL)
    install_file(engine, dest / "engine" / engine.name, executable=True)


def install_shogi(dest, target, cache, staging):
    windows = target == "windows-x64"
    os_name = "win64" if windows else "mac"
    cpu = {"windows-x64": "SSE41.exe", "macos-arm64": "APPLEM1", "macos-x64": "APPLESSE42"}[target]
    binary = f"{HALFKP}/YaneuraOu_{HALFKP}-V900Git_{cpu}"
    engine = dest / "engine"
    archive = obtain(f"yaneuraou-V900-git-{os_name}-all.7z", cache)
    extract(archive, staging, binary)
    eval_archive = obtain(HAO_TAG + ".7z", cache)
    extract(eval_archive, staging, "eval/nn.bin", "gpl-3.0.txt")
    install_file(staging / "eval/nn.bin", engine / "eval/nn.bin")
    install_file(staging / "gpl-3.0.txt", engine / "eval/COPYING.txt")
    install_file(staging / binary, engine / ("yaneuraou.exe" if windows else "yaneuraou"), executable=True)


def install_chess(dest, target, cache, staging):
    windows = target == "windows-x64"
    asset = "stockfish-windows-x86-64-universal" if windows else "stockfish-macos-universal"
    binary = f"stockfish/{asset}{'.exe' if windows else ''}"
    archive = obtain(asset + (".zip" if windows else ".tar.gz"), cache)
    extract(archive, staging, binary, "stockfish/Copying.txt", "stockfish/AUTHORS")
    engine = dest / "engine"
    for name in ("Copying.txt", "AUTHORS"):
        install_file(staging / "stockfish" / name, engine / name)
    install_file(staging / binary, engine / ("stockfish.exe" if windows else "stockfish"), executable=True)


def main():
    games = {
        "go": ("KataGo", install_go, "go/run_katago.py"),
        "shogi": ("YaneuraOu", install_shogi, "shogi/app/shogi_engine.py"),
        "chess": ("Stockfish", install_chess, "chess/run_stockfish.py"),
    }
    target = {
        ("Windows", "amd64"): "windows-x64",
        ("Windows", "x86_64"): "windows-x64",
        ("Darwin", "arm64"): "macos-arm64",
        ("Darwin", "x86_64"): "macos-x64",
    }.get((platform.system(), platform.machine().lower()))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game", choices=[game for game, (_, _, entry) in games.items() if (ROOT / entry).is_file()])
    parser.add_argument("--target", choices=("windows-x64", "macos-arm64", "macos-x64"), default=target)
    parser.add_argument("--cache", type=Path, help="Keep and reuse verified upstream archives here.")
    args = parser.parse_args()
    if args.target is None:
        parser.error("Unsupported host. Use --target to prepare files for a supported OS and CPU.")
    name, installer, _ = games[args.game]
    dest = ROOT / args.game / "vendor" / name
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".install-", dir=dest.parent) as temp:
            staging = Path(temp)
            cache = args.cache.resolve() if args.cache else staging / "downloads"
            cache.mkdir(parents=True, exist_ok=True)
            installer(dest, args.target, cache, staging)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(error, file=sys.stderr)
        return 1
    print(f"{name}: {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
