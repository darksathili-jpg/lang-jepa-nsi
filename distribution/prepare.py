"""Préparation locale et répétable du profil SmolLM3 + JEPA P5."""

import hashlib
import os
from pathlib import Path
import tarfile
import tempfile

from distribution.instance import LOCK, publish
from distribution.transfer import extract_zip, fetch, free_space
from p5.orchestration import open_experiment
from tutor.catalog import CATALOG, platform_key
from tutor.engine import LlamaEngine


def assets_for(home):
    return home / "models/smollm3", home / "models/jepa/fixe-24-17"


def prepare_jepa(destination):
    if destination.exists():
        verified = open_experiment("c", destination).status()
        if verified["state"] != "ready":
            raise ValueError(f"Poids JEPA existants non utilisables : {verified['detail']}")
        return verified
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    from p5.data import ROOT, load_corpus
    from p5.jepa import save, train

    config = LOCK["jepa"]
    digest = hashlib.sha256((ROOT / "corpus.json").read_bytes()).hexdigest()
    if config["corpus_sha256"] != digest:
        raise ValueError("Le corpus ne correspond pas à la révision du profil P5.")
    print("Entraînement local du modèle pédagogique JEPA P5…", flush=True)
    rows = [row for row in load_corpus() if row.partage == "train"]
    model, _ = train(rows, config["config"], config["seed"], config["epochs"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as work:
        bundle = Path(work) / "modele"
        from platform import python_version
        from numpy import __version__ as numpy_version

        manifest = save(model, bundle, {"corpus_sha256": digest, "graine": config["seed"], "epoques": config["epochs"],
                                        "numpy": numpy_version, "python": python_version()})
        status = open_experiment("c", bundle).status()
        if status["state"] != "ready":
            raise ValueError(f"La prédiction JEPA n’a pas été validée : {status['detail']}")
        bundle.rename(destination)
    print("JEPA · " + ("empreinte P5 identique" if manifest["sha256"] == config["p5_sha256"]
                      else "reconstruction locale avec une empreinte différente de P5")
          + f" · {manifest['sha256']}", flush=True)
    return status


def prepare(home, source=None, *, jepa_only=False):
    assets, weights = assets_for(home)
    jepa = prepare_jepa(weights)
    if jepa_only:
        return {"jepa": jepa}

    platform = platform_key()
    runtime = CATALOG["runtime"]
    artifact = runtime["platforms"][platform] | {"bytes": (
        LOCK["llama_windows_archive_bytes"] if platform == "windows-x64" else 23189794
    )}
    model = CATALOG["models"]["smol"]
    assets.mkdir(parents=True, exist_ok=True)
    pending = 0
    for item in (artifact, model):
        name = item["file"]
        if not (assets / name).exists():
            part = assets / (name + ".part")
            pending += max(0, item["bytes"] - (part.stat().st_size if part.exists() else 0))
    free_space(assets, pending + (128 * 2**20 if not (assets / "runtime").exists() else 0))
    archive = assets / artifact["file"]
    for url, metadata in (
        (f"https://github.com/ggml-org/llama.cpp/releases/download/{runtime['version']}/{archive.name}", artifact),
        (f"https://huggingface.co/{model['repository']}/resolve/{model['revision']}/{model['file']}", model),
    ):
        filename = metadata["file"]
        local = source / filename if source and (source / filename).is_file() else None
        fetch(url, assets / filename, metadata, source=local)
    destination = assets / "runtime"
    if not destination.exists():
        with tempfile.TemporaryDirectory(dir=assets) as work:
            tree = Path(work) / "runtime"
            tree.mkdir()
            if archive.suffix == ".zip":
                extract_zip(archive, tree)
            else:
                with tarfile.open(archive) as package:
                    package.extractall(tree, filter="data")
            files = {}
            for file in tree.rglob("*"):
                if file.is_file():
                    with file.open("rb") as stream:
                        files[file.relative_to(tree).as_posix()] = hashlib.file_digest(stream, "sha256").hexdigest()
            publish(tree / "release-files.json", {"archive_sha256": artifact["sha256"], "files": files})
            tree.rename(destination)
    return {"jepa": jepa, "llm": verify_engine(assets)}


def verify_engine(assets):
    engine = LlamaEngine(assets, "smol", 2, require_runtime=True)
    try:
        engine.start()
        status = engine.status()
        if status["state"] != "ready":
            raise ValueError(status["detail"])
        return status
    finally:
        engine.close()
