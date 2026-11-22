"""Construit un ZIP portable Windows à partir d’une révision Git et de deux artefacts verrouillés."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile

from distribution.instance import LOCK, VERSION
from distribution.transfer import extract_zip, fetch
from tutor.catalog import ROOT


PAYLOAD = ("app", "tutor", "pedagogy", "p5/__init__.py", "p5/contract.py", "p5/data.py", "p5/corpus.json",
           "p5/jepa.py", "p5/orchestration.py", "p3/models.json", "p4/reference.json", "distribution",
           "design/tokens.css", "docs/P6_1_INSTALLATION.md")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default="HEAD")
    parser.add_argument("--cache", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    args.output.mkdir(parents=True, exist_ok=True)
    for name in ("python", "numpy"):
        item = LOCK[name]
        fetch(item["url"], args.cache / item["file"], item)
    commit = subprocess.check_output(["git", "rev-parse", "--verify", args.ref + "^{commit}"], cwd=ROOT, text=True).strip()
    package = args.output / f"LANG-JEPA-NSI-{VERSION}-Windows-x64.zip"
    if package.exists():
        parser.error("Choisis un dossier de sortie neuf.")
    with tempfile.TemporaryDirectory(dir=args.output) as work:
        base = Path(work)
        full = base / "LANG-JEPA-NSI-Windows"
        app = full / "application"
        runtime = full / "runtime"
        app.mkdir(parents=True)
        runtime.mkdir()
        snapshot = base / "source.zip"
        subprocess.run(["git", "archive", "--format=zip", "-o", str(snapshot.resolve()), commit, "--", *PAYLOAD],
                       cwd=ROOT, check=True)
        extract_zip(snapshot, app)
        extract_zip(args.cache / LOCK["python"]["file"], runtime)
        extract_zip(args.cache / LOCK["numpy"]["file"], runtime / "Lib" / "site-packages")
        (runtime / "python313._pth").write_bytes(b"python313.zip\r\n.\r\nLib\\site-packages\r\n..\\application\r\n")
        (app / "distribution/build.json").write_text(json.dumps({"version": VERSION, "commit": commit}) + "\n",
                                                      encoding="utf-8")
        for launcher in sorted((app / "distribution/windows").glob("*.cmd")):
            (full / launcher.name).write_bytes(launcher.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
        (full / "README-WINDOWS.md").write_bytes((app / "docs/P6_1_INSTALLATION.md").read_bytes())
        pending = base / "package.zip"
        with zipfile.ZipFile(pending, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as artifact:
            for file in sorted(full.rglob("*")):
                if file.is_file():
                    name = file.relative_to(base).as_posix()
                    artifact.writestr(zipfile.ZipInfo(name), file.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)
        pending.rename(package)
    with package.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    (args.output / "SHA256SUMS.txt").write_text(f"{digest}  {package.name}\n", encoding="ascii")
    print(f"{package} · {package.stat().st_size} octets · SHA-256 {digest}")


if __name__ == "__main__":
    main()
