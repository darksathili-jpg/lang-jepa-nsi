"""Révisions locales utilisées par le tuteur et la recette."""

import hashlib
import json
from pathlib import Path
import platform
import sys


ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads((ROOT / "p3" / "models.json").read_text(encoding="utf-8"))
DEFAULT_ASSETS = ROOT / "models" / "tutor"


def platform_key():
    if platform.machine().lower() not in {"amd64", "x86_64"}:
        raise ValueError("Le paquet fourni nécessite un processeur x64.")
    if sys.platform == "win32":
        return "windows-x64"
    if sys.platform == "linux":
        return "linux-x64"
    raise ValueError("Paquet CPU fourni pour Windows et Linux x64.")


def verify_file(path, metadata):
    if "bytes" in metadata and path.stat().st_size != metadata["bytes"]:
        raise ValueError(f"Taille inattendue pour {path.name}.")
    with path.open("rb") as stream:
        sha = hashlib.file_digest(stream, "sha256").hexdigest()
    if sha != metadata["sha256"]:
        raise ValueError(f"Empreinte SHA-256 invalide pour {path.name}.")


def runtime_path(assets):
    filename = "llama-server.exe" if sys.platform == "win32" else "llama-server"
    binaries = sorted((assets / "runtime").rglob(filename))
    return binaries[0] if len(binaries) == 1 else None
