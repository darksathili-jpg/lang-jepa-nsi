"""Téléchargement explicite avec reprise et promotion des fichiers vérifiés."""

import re
import shutil
import urllib.request
import zipfile
from pathlib import PurePosixPath
from urllib.parse import urlparse

from tutor.catalog import verify_file


CHUNK = 1 << 20


def free_space(path, needed):
    if shutil.disk_usage(path).free < needed:
        raise ValueError(f"Espace disque insuffisant dans {path} ({needed / 2**30:.2f} Gio nécessaires).")


def fetch(url, target, metadata, *, source=None):
    """Ne remplacer que le fichier temporaire appartenant à ce téléchargement."""
    if target.exists():
        verify_file(target, metadata)
        print(f"Vérifié et réutilisé · {target.name}", flush=True)
        return
    size = metadata["bytes"]
    part = target.with_name(target.name + ".part")
    offset = part.stat().st_size if part.exists() else 0
    if offset > size or source is not None:
        part.unlink(missing_ok=True)
        offset = 0
    free_space(target.parent, size - offset)

    if source is not None:
        verify_file(source, metadata)
        shutil.copyfile(source, part)
    elif offset < size:
        if urlparse(url).scheme != "https":
            raise ValueError("Une source de téléchargement HTTPS est requise.")
        request = urllib.request.Request(url, headers={"Range": f"bytes={offset}-"} if offset else {})
        print(f"Téléchargement · {target.name} · reprise à {offset * 100 // size} %", flush=True)
        with urllib.request.urlopen(request, timeout=60) as stream:
            if urlparse(stream.geturl()).scheme != "https":
                raise ValueError("Redirection de téléchargement non chiffrée.")
            if stream.status == 206 and offset:
                match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", stream.headers.get("Content-Range", ""))
                if not match or tuple(map(int, match.groups())) != (offset, size - 1, size):
                    part.unlink(missing_ok=True)
                    raise ValueError("La reprise a été refusée par la source. Relance la préparation.")
            elif stream.status == 200:
                offset = 0
                free_space(target.parent, max(0, size - part.stat().st_size) if part.exists() else size)
            else:
                raise ValueError(f"Réponse HTTP inattendue ({stream.status}).")
            progress = offset * 100 // size
            with part.open("ab" if offset else "wb") as output:
                while block := stream.read(CHUNK):
                    offset += len(block)
                    if offset > size:
                        raise ValueError(f"La source dépasse la taille attendue pour {target.name}.")
                    output.write(block)
                    percent = offset * 100 // size
                    if percent >= progress + 5 or percent == 100:
                        print(f"{target.name} · {percent} %", flush=True)
                        progress = percent

    if part.stat().st_size != size:
        raise ValueError(f"Le téléchargement de {target.name} est incomplet. Relance pour reprendre.")
    try:
        verify_file(part, metadata)
    except ValueError:
        part.unlink()
        raise
    part.rename(target)
    print(f"Empreinte vérifiée · {target.name}", flush=True)


def extract_zip(path, destination):
    with zipfile.ZipFile(path) as archive:
        for entry in archive.infolist():
            name = PurePosixPath(entry.filename)
            if (name.is_absolute() or ".." in name.parts or "\\" in entry.filename
                    or ":" in entry.filename or (entry.external_attr >> 16) & 0o170000 == 0o120000):
                raise ValueError(f"Entrée ZIP non autorisée : {entry.filename}.")
        archive.extractall(destination)
