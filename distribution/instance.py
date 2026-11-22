"""Identité et verrou coopératif propres à un dossier d’installation."""

from contextlib import contextmanager
import hashlib
import http.client
import json
import os
from pathlib import Path
import tempfile

from tutor.catalog import ROOT


LOCK = json.loads((ROOT / "distribution/lock.json").read_text(encoding="utf-8"))
BUILD_FILE = ROOT / "distribution/build.json"
VERSION = LOCK["version"]


def build_id():
    if BUILD_FILE.is_file():
        return json.loads(BUILD_FILE.read_text(encoding="utf-8"))["commit"]
    return "source-" + hashlib.sha256((ROOT / "tutor/server.py").read_bytes()
                                      + (ROOT / "app/tutor.js").read_bytes()).hexdigest()[:16]


def identity(home):
    installation = hashlib.sha256(os.fsencode(os.path.normcase(str(home.resolve())))).hexdigest()[:24]
    return {"application": "LANG-JEPA NSI", "version": VERSION, "build": build_id(), "installation": installation}


def publish(path, data):
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as entry:
        pending = Path(entry.name)
        json.dump(data, entry)
    try:
        os.replace(pending, path)
    finally:
        pending.unlink(missing_ok=True)


def read(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


@contextmanager
def lock(path):
    with path.open("a+b") as file:
        file.seek(0, os.SEEK_END)
        if not file.tell():
            file.write(b"\0")
            file.flush()
        file.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise ValueError("Une opération est déjà en cours pour ce dossier. Réessaie après sa fin.") from exc
        yield
        # La fermeture du descripteur libère le verrou, y compris après interruption.


def local_request(port, path, *, token=None, method="GET", timeout=0.8):
    if type(port) is not int or not 1 <= port <= 65535:
        return None
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
    try:
        connection.request(method, path, headers={"X-NSI-Instance": token} if token else {})
        response = connection.getresponse()
        if response.status != 200:
            return None
        return json.loads(response.read(65536))
    except (OSError, ValueError, http.client.HTTPException):
        return None
    finally:
        connection.close()


def recognized(path, expected):
    state = read(path)
    if not isinstance(state.get("token"), str) or any(state.get(key) != value for key, value in expected.items()):
        return None
    public = {key: expected[key] for key in ("application", "version", "build")}
    if local_request(state.get("port"), "/api/build") != public:
        return None
    reply = local_request(state.get("port"), "/api/instance", token=state["token"])
    if not isinstance(reply, dict):
        return None
    confirmed = {key: state.get(key) for key in (*expected, "instance", "pid", "port")}
    return state if reply == confirmed else None
