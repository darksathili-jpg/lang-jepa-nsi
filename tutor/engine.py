"""Adaptateur conversationnel. Seule destination utilisable : le processus local géré ici."""

import http.client
import json
import os
from copy import deepcopy
import secrets
import socket
import subprocess
import threading
import time

from tutor.catalog import CATALOG, runtime_path, verify_file


class EngineError(RuntimeError):
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


class LlamaEngine:
    def __init__(self, assets, model_key, threads, executable=None):
        self.key = model_key
        self.model = CATALOG["models"][model_key]
        self.model_file = assets / self.model["file"]
        self.executable = executable or runtime_path(assets)
        self.threads = threads
        self.process = None
        self.state = "loading"
        self.detail = "Vérification des fichiers locaux."
        self.port = None
        self.token = secrets.token_hex(24)
        self.lock = threading.Lock()
        self.closed = threading.Event()
        if not self.executable or not self.executable.is_file() or not self.model_file.is_file():
            self.state = "absent"
            self.detail = "Installez le moteur CPU et les poids locaux indiqués dans le guide P3."

    def status(self):
        if self.state == "ready" and self.process.poll() is not None:
            self.state = "error"
            self.detail = "Le moteur local s’est arrêté. Redémarrez l’atelier."
        return {
            "state": self.state,
            "detail": self.detail,
            "name": self.model["name"],
            "revision": self.model["revision"],
            "quantization": self.model["quantization"],
            "runtime": CATALOG["runtime"]["version"],
        }

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
        if self.state == "absent":
            return
        try:
            verify_file(self.model_file, self.model)
            expected = CATALOG["runtime"]
            env = {key: val for key, val in os.environ.items() if not key.startswith("LLAMA_ARG_")}
            result = subprocess.run(
                [str(self.executable), "--version"], capture_output=True, env=env, timeout=10,
                encoding="utf-8", errors="replace", check=True,
            )
            if f"build {expected['version'][1:]}, commit {expected['commit']}" not in result.stdout + result.stderr:
                raise EngineError(f"Version llama.cpp {expected['version']} requise.")
            with socket.socket() as reserved:
                reserved.bind(("127.0.0.1", 0))
                self.port = reserved.getsockname()[1]

            with self.lock:
                if self.closed.is_set():
                    return
                self.process = subprocess.Popen([
                    str(self.executable), "--model", str(self.model_file), "--alias", self.key,
                    "--host", "127.0.0.1", "--port", str(self.port), "--api-key", self.token,
                    "--offline", "--no-webui", "--no-ui-mcp-proxy", "--log-disable",
                    "--n-gpu-layers", "0", "--ctx-size", "4096", "--threads", str(self.threads),
                    "--parallel", "1", "--reasoning", "off", "--no-context-shift",
                ], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
            self.detail = "Chargement du modèle sur le processeur."
            deadline = time.monotonic() + 90
            while not self.closed.wait(0.2) and time.monotonic() < deadline:
                if self.process.poll() is not None:
                    raise EngineError("Le moteur CPU a quitté pendant le démarrage.")
                try:
                    status, _ = self._request("/health")
                    if status == 200:
                        self.state = "ready"
                        self.detail = "Le modèle répond sur cet ordinateur."
                        return
                except (OSError, ValueError, http.client.HTTPException):
                    continue
            if not self.closed.is_set():
                raise EngineError("Le modèle met trop de temps à démarrer.")
        except (EngineError, OSError, ValueError, subprocess.SubprocessError) as exc:
            self.state = "error"
            self.detail = str(exc) if isinstance(exc, (EngineError, ValueError)) else (
                "Impossible de lancer le moteur CPU. Vérifiez l’installation locale de llama.cpp."
            )
            self.close()

    def generate(self, messages, contract=False, *, hint=False):
        if self.status()["state"] != "ready":
            raise EngineError(self.detail)
        if not self.lock.acquire(blocking=False):
            raise EngineError("Le moteur traite déjà une demande. Réessayez après sa réponse.")
        started = time.perf_counter()
        try:
            status, data = self._request("/v1/chat/completions", {
                "model": self.key, "messages": messages, "temperature": 0, "seed": 42,
                "max_tokens": 85 if hint else 160,
                "response_format": HINT_FORMAT if hint else CONTRACT_FORMAT if contract else REPLY_FORMAT,
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
        with self.lock:
            if self.process is None or self.process.poll() is not None:
                return
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
