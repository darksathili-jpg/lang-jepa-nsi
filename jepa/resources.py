"""Prépare les modules amont vérifiés pour un processus expérimental local."""

from contextlib import contextmanager
import os
from pathlib import Path
import sys
import tarfile
import tempfile

from scripts.lang_jepa_cpu import ROOT, read_json, verify_sha256


@contextmanager
def upstream(assets):
    lock = read_json(ROOT / "p2" / "upstream.json")
    hashes = {
        name: verify_sha256(assets / name, item["sha256"])
        for name, item in lock["files"].items()
    }
    for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY"):
        os.environ[key] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    with tempfile.TemporaryDirectory(prefix="jepa-nsi-") as temp:
        with tarfile.open(assets / "upstream.tar.gz", "r:gz") as archive:
            archive.extractall(temp, filter="data")
        source = Path(temp) / f"lang-jepa-{lock['revision']}"
        sys.path.insert(0, str(source))
        try:
            yield source, {
                "upstream_revision": lock["revision"], "roberta_revision": lock["roberta_revision"],
                "sha256": hashes,
            }
        finally:
            sys.path.remove(str(source))
