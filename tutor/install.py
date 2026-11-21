"""Prépare des ressources P3 vérifiées, à transférer ensuite sur le poste hors ligne."""

import argparse
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile
import urllib.request
import zipfile

from tutor.catalog import CATALOG, DEFAULT_ASSETS, platform_key, verify_file


def fetch(url, target, metadata):
    if target.is_file():
        verify_file(target, metadata)
        return
    print(f"Téléchargement de {target.name}…", flush=True)
    with tempfile.TemporaryDirectory(dir=target.parent) as work:
        part = Path(work) / target.name
        with urllib.request.urlopen(url, timeout=90) as source, part.open("wb") as output:
            shutil.copyfileobj(source, output, length=1024 * 1024)
        verify_file(part, metadata)
        part.replace(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=CATALOG["models"], required=True)
    parser.add_argument("--platform", choices=CATALOG["runtime"]["platforms"])
    parser.add_argument("--assets", type=Path, default=DEFAULT_ASSETS)
    args = parser.parse_args()
    assets = args.assets.resolve()
    try:
        target = args.platform or platform_key()
        version = CATALOG["runtime"]["version"]
        runtime = CATALOG["runtime"]["platforms"][target]
        model = CATALOG["models"][args.model]
        assets.mkdir(parents=True, exist_ok=True)
        archive = assets / runtime["file"]
        fetch(f"https://github.com/ggml-org/llama.cpp/releases/download/{version}/{archive.name}",
              archive, runtime)
        fetch(f"https://huggingface.co/{model['repository']}/resolve/{model['revision']}/{model['file']}",
              assets / model["file"], model)
        installation = assets / "runtime"
        marker = installation / "release.txt"
        identity = f"{target} {version} {runtime['sha256']}\n"
        if installation.is_dir():
            if not marker.is_file() or marker.read_text(encoding="utf-8") != identity:
                raise ValueError("Le dossier runtime existe avec une autre identité. Choisissez un autre dossier --assets.")
        else:
            with tempfile.TemporaryDirectory(dir=assets) as work:
                unpacked = Path(work) / "runtime"
                unpacked.mkdir()
                if archive.suffix == ".zip":
                    with zipfile.ZipFile(archive) as package:
                        package.extractall(unpacked)
                else:
                    with tarfile.open(archive) as package:
                        package.extractall(unpacked, filter="data")
                (unpacked / marker.name).write_text(identity, encoding="utf-8")
                unpacked.rename(installation)
    except (OSError, ValueError, tarfile.TarError, zipfile.BadZipFile) as exc:
        print(f"Préparation interrompue. {exc}", file=sys.stderr)
        return 1

    print(f"Ressources vérifiées dans {assets}. Modèle : {model['name']} {model['quantization']}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
