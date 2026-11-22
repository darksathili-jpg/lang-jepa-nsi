"""Adaptateur conversationnel. Seule destination utilisable : le processus local géré ici."""

import http.client
import hashlib
import json
import os
from copy import deepcopy
import secrets
import socket
import subprocess
import threading
import time

from distribution.jobs import ChildJob
from distribution.instance import LOCK
from tutor.catalog import CATALOG, platform_key, runtime_path, verify_file
from p5.contract import ACTIONS, SCHEMA


class EngineError(RuntimeError):
    pass


class IncompatibleRuntime(EngineError):
    pass


REPLY_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "tutor_reply",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "indice": {"type": "string", "minLength": 3, "maxLength": 230},
                "question": {"type": "string", "minLength": 4, "maxLength": 170},
            },
            "required": ["indice", "question"],
            "additionalProperties": False,
        },
    },
}
CONTRACT_FORMAT = deepcopy(REPLY_FORMAT)
CONTRACT_FORMAT["json_schema"]["schema"]["properties"]["indice"] = {
    "type": "string",
    "pattern": "^(La précondition|Une liste non vide|L'énoncé exige une liste non vide).{2,180}$",
}
HINT_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "socratic_hint",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "indice": {
                    "type": "string",
                    "pattern": "^(Compare|Examine|Observe|Relis|Cherche|Distingue|Imagine) .{8,90}[.]$",
                },
            },
            "required": ["indice"],
            "additionalProperties": False,
        },
    },
}
DECISION_FORMAT = deepcopy(HINT_FORMAT)
_decision_schema = DECISION_FORMAT["json_schema"]["schema"]
_decision_schema["properties"].update({"schema": {"type": "integer", "enum": [SCHEMA]},
                                      "approche": {"type": "string", "enum": list(ACTIONS)}})
_decision_schema["required"].extend(("schema", "approche"))


class LlamaEngine:
    def __init__(self, assets, model_key, threads, executable=None, *, require_runtime=False):
        self.key = model_key
        self.model = CATALOG["models"][model_key]
        self.model_file = assets / self.model["file"]
        self.executable = executable or runtime_path(assets)
        self.runtime = assets / "runtime"
        self.require_runtime = require_runtime
        self.threads = threads
        self.process = None
        self.state = "loading"
        self.detail = "Vérification des fichiers locaux."
        self.port = None
        self.token = secrets.token_hex(24)
        self.lock = threading.Lock()
        self.process_lock = threading.Lock()
        self.closed = threading.Event()
        self.job = ChildJob()
        self.checks = {"executable": bool(self.executable and self.executable.is_file()),
                       "poids": self.model_file.is_file(), "integrite": False,
                       "processus": False, "inference": False}
        self.timings = {}
        if not (self.checks["executable"] and self.checks["poids"]):
            partial = self.checks["executable"] or self.checks["poids"] or any(assets.glob("*.part"))
            self.state = "incomplete" if partial else "absent"
            self.detail = "Lance Installer-Modeles.cmd pour préparer le moteur CPU et le modèle."
        elif require_runtime and not (self.runtime / "release-files.json").is_file():
            self.state = "incomplete"
            self.detail = "Le contrôle d’installation du moteur manque. Lance Installer-Modeles.cmd."

    def status(self):
        if self.state == "ready" and self.process.poll() is not None:
            self.state = "error"
            self.detail = "Le moteur local s’est arrêté. Redémarrez l’atelier."
        return {
            "state": "working" if self.state == "ready" and self.lock.locked() else self.state,
            "detail": self.detail,
            "name": self.model["name"],
            "revision": self.model["revision"],
            "quantization": self.model["quantization"],
            "runtime": CATALOG["runtime"]["version"],
            "checks": self.checks | {"processus": bool(self.process and self.process.poll() is None)},
            "times": self.timings.copy(),
        }

    def verify_runtime(self):
        manifest = self.runtime / "release-files.json"
        if not self.require_runtime:
            return
        data = json.loads(manifest.read_text(encoding="utf-8"))
        platform = platform_key()
        expected = CATALOG["runtime"]["platforms"][platform]
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
        if hashlib.sha256(canonical).hexdigest() != LOCK["llama"][platform]["manifest_sha256"]:
            raise EngineError("L’inventaire vérifié de llama.cpp a changé. Consulte le guide Windows.")
        files = data.get("files")
        if data.get("archive_sha256") != expected["sha256"] or not isinstance(files, dict) or not files:
            raise IncompatibleRuntime("Le manifeste de llama.cpp ne correspond pas à cette plateforme.")
        runtime = self.runtime.resolve()
        actual = {item.relative_to(runtime).as_posix(): item for item in runtime.rglob("*")
                  if item.is_file() and item.name != manifest.name}
        if set(files) != set(actual) or self.executable.resolve() not in actual.values():
            raise EngineError("Le moteur CPU contient des fichiers supplémentaires ou manquants. Consulte le guide Windows.")
        for name, file in actual.items():
            if not file.resolve().is_relative_to(runtime):
                raise EngineError("Le runtime doit rester dans le dossier du paquet.")
            verify_file(file, {"sha256": files[name]})

    def _request(self, path, payload=None, timeout=1):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=timeout)
        headers = {"Authorization": f"Bearer {self.token}"}
        body = None
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        try:
            connection.request("POST" if body is not None else "GET", path, body, headers)
            response = connection.getresponse()
            return response.status, json.loads(response.read())
        finally:
            connection.close()

    def start(self):
        if self.state != "loading":
            return
        try:
            tick = time.monotonic()
            verify_file(self.model_file, self.model)
            self.verify_runtime()
            self.checks["integrite"] = True
            self.timings["integrity_s"] = round(time.monotonic() - tick, 3)
            expected = CATALOG["runtime"]
            env = {key: val for key, val in os.environ.items() if not key.startswith("LLAMA_ARG_")}
            launch_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            try:
                result = subprocess.run([str(self.executable), "--version"], capture_output=True, env=env, timeout=10,
                                        encoding="utf-8", errors="replace", check=True, creationflags=launch_flags)
            except (OSError, subprocess.CalledProcessError) as exc:
                detail = " Vérifie le redistribuable Microsoft Visual C++ x64 (guide Windows)." if os.name == "nt" else ""
                raise IncompatibleRuntime("Ce moteur CPU ne démarre pas sur cet ordinateur." + detail) from exc
            if f"build {expected['version'][1:]}, commit {expected['commit']}" not in result.stdout + result.stderr:
                raise IncompatibleRuntime(f"Version llama.cpp {expected['version']} requise.")
            with socket.socket() as reserved:
                reserved.bind(("127.0.0.1", 0))
                self.port = reserved.getsockname()[1]

            with self.process_lock:
                if self.closed.is_set():
                    return
                self.process = subprocess.Popen([
                    str(self.executable), "--model", str(self.model_file), "--alias", self.key,
                    "--host", "127.0.0.1", "--port", str(self.port), "--api-key", self.token,
                    "--offline", "--no-webui", "--no-ui-mcp-proxy", "--log-disable",
                    "--n-gpu-layers", "0", "--ctx-size", "4096", "--threads", str(self.threads),
                    "--parallel", "1", "--reasoning", "off", "--no-context-shift",
                ], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env,
                    creationflags=launch_flags)
                self.job.assign(self.process)
            self.detail = "Chargement du modèle sur le processeur."
            tick = time.monotonic()
            deadline = time.monotonic() + 90
            while not self.closed.wait(0.2) and time.monotonic() < deadline:
                if self.process.poll() is not None:
                    raise EngineError("Le moteur CPU a quitté pendant le démarrage.")
                try:
                    status, _ = self._request("/health")
                except (OSError, ValueError, http.client.HTTPException):
                    continue
                if status == 200:
                    self.timings["load_s"] = round(time.monotonic() - tick, 3)
                    self.detail = "Inférence locale de vérification en cours."
                    tick = time.monotonic()
                    try:
                        code, reply = self._request("/v1/chat/completions", {
                            "model": self.key, "messages": [{"role": "user", "content": "Dis bonjour en un mot."}],
                            "temperature": 0, "max_tokens": 12, "cache_prompt": False,
                        }, timeout=60)
                        text = reply["choices"][0]["message"]["content"]
                        if code != 200 or not isinstance(text, str) or not text.strip():
                            raise ValueError("Réponse vide")
                    except (OSError, ValueError, KeyError, TypeError, IndexError, http.client.HTTPException) as exc:
                        raise EngineError("Le modèle a chargé, mais l’inférence de vérification a échoué.") from exc
                    self.timings["probe_s"] = round(time.monotonic() - tick, 3)
                    self.checks["inference"] = True
                    self.state = "ready"
                    self.detail = "Le modèle a répondu à une inférence sur cet ordinateur."
                    return
            if not self.closed.is_set():
                raise EngineError("Le modèle met trop de temps à démarrer.")
        except (EngineError, OSError, ValueError, subprocess.SubprocessError) as exc:
            self.state = "incompatible" if isinstance(exc, IncompatibleRuntime) else "error"
            self.detail = str(exc) if isinstance(exc, (EngineError, ValueError)) else (
                "Impossible de lancer le moteur CPU. Vérifiez l’installation locale de llama.cpp."
            )
            self.close()

    def generate(self, messages, contract=False, *, hint=False, decision=False):
        self.status()
        if self.state != "ready":
            raise EngineError(self.detail)
        if not self.lock.acquire(blocking=False):
            raise EngineError("Le moteur traite déjà une demande. Réessayez après sa réponse.")
        started = time.perf_counter()
        try:
            status, data = self._request("/v1/chat/completions", {
                "model": self.key, "messages": messages, "temperature": 0, "seed": 42,
                "max_tokens": 85 if hint else 160,
                "response_format": (DECISION_FORMAT if decision else HINT_FORMAT if hint else
                                    CONTRACT_FORMAT if contract else REPLY_FORMAT),
                "cache_prompt": False,
            }, timeout=110)
            if status == 400:
                raise EngineError("Le contexte est trop long ou incompatible. Raccourcissez la demande.")
            if status != 200:
                raise EngineError("Le moteur local a interrompu la génération.")
            choice = data["choices"][0]
            return {
                "text": choice["message"]["content"], "finish": choice["finish_reason"],
                "seconds": round(time.perf_counter() - started, 3),
                "usage": data.get("usage", {}), "timings": data.get("timings", {}),
            }
        except (OSError, ValueError, KeyError, IndexError, TypeError, http.client.HTTPException) as exc:
            raise EngineError("Le moteur local n’a pas renvoyé de réponse exploitable.") from exc
        finally:
            self.lock.release()

    def close(self):
        self.closed.set()
        with self.process_lock:
            try:
                if self.process is not None and self.process.poll() is None:
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.process.kill()
                        self.process.wait()
            finally:
                self.job.close()
