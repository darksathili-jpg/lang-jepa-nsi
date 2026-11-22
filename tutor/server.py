"""Sert l’atelier sur l’interface de bouclage, sans dépendance web tierce."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import signal
import sys
import threading

from p5.contract import ContractError
from p5.orchestration import open_experiment
from pedagogy.catalogue import for_level
from tutor.catalog import CATALOG, DEFAULT_ASSETS, ROOT
from tutor.curriculum import LEVELS
from tutor.dialogue import DialogueError, RejectedReply
from tutor.engine import EngineError, LlamaEngine
from tutor.sessions import SessionConflict, Sessions


DEFAULT_MODEL = "smol"
APP = ROOT / "app"
PAGES = {
    "/": ("index.html", "text/html"),
    "/index.html": ("index.html", "text/html"),
    "/atelier": ("tutor.html", "text/html"),
    "/app.js": ("app.js", "text/javascript"),
    "/style.css": ("style.css", "text/css"),
    "/tutor.js": ("tutor.js", "text/javascript"),
    "/tutor.css": ("tutor.css", "text/css"),
}
POLICY = (
    "default-src 'none'; script-src 'self'; style-src 'self'; "
    "connect-src 'self'; img-src 'self' data:; base-uri 'none'; "
    "frame-ancestors 'none'; form-action 'none'"
)


class WorkshopServer(ThreadingHTTPServer):
    def __init__(self, port, engine, experiment=None):
        super().__init__(("127.0.0.1", port), Handler)
        self.engine = engine
        self.dialogues = Sessions(experiment)
        self.engine_thread = None
        self.engine_lock = threading.Lock()
        self.host_header = f"127.0.0.1:{self.server_port}"
        self.origin = "http://" + self.host_header

    def start_engine(self):
        with self.engine_lock:
            if self.engine_thread is None and self.engine.state == "loading":
                self.engine_thread = threading.Thread(target=self.engine.start, name="modele-cpu", daemon=True)
                self.engine_thread.start()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def setup(self):
        super().setup()
        self.connection.settimeout(15)

    def reply(self, status, content, mime):
        self.send_response(status)
        self.send_header("Content-Type", mime + "; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", POLICY)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        try:
            self.wfile.write(content)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def send_json(self, status, data):
        self.reply(status, json.dumps(data, ensure_ascii=False).encode("utf-8"), "application/json")

    def valid_host(self):
        if self.headers.get("Host") == self.server.host_header:
            return True
        self.send_json(403, {"error": "Adresse locale non reconnue."})
        return False

    def do_GET(self):
        if not self.valid_host():
            return
        if self.path == "/api/status":
            self.server.start_engine()
            experiment = self.server.dialogues.experiment
            jepa = experiment.status() if experiment else {"mode": "Conversation locale P4",
                "state": "inactive", "name": None, "detail": ""}
            self.send_json(200, self.server.engine.status() | {"jepa": jepa})
        elif self.path == "/api/exercises":
            self.send_json(200, {level: for_level(level) for level in LEVELS})
        elif self.path in PAGES:
            filename, mime = PAGES[self.path]
            self.reply(200, (APP / filename).read_bytes(), mime)
        else:
            self.send_json(404, {"error": "Page introuvable."})

    def do_POST(self):
        if not self.valid_host():
            return
        if self.path not in ("/api/tutor", "/api/guide"):
            self.send_json(404, {"error": "Page introuvable."})
            return
        if self.headers.get("Origin") != self.server.origin:
            self.send_json(403, {"error": "Seul cet atelier local peut envoyer une demande."})
            return
        if self.headers.get_content_type() != "application/json":
            self.send_json(415, {"error": "Format JSON requis."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 48 * 1024 or self.headers.get("Transfer-Encoding"):
                self.send_json(413, {"error": "Taille de demande invalide."})
                return
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, OSError):
            self.send_json(400, {"error": "Demande illisible."})
            return

        try:
            mode = "guided" if self.path == "/api/guide" else "conversation"
            if mode == "conversation":
                self.server.start_engine()
            answer = self.server.dialogues.turn(mode, payload, self.server.engine)
        except SessionConflict as exc:
            self.send_json(409, {"error": str(exc)})
        except DialogueError as exc:
            self.send_json(400, {"error": str(exc)})
        except RejectedReply as exc:
            self.send_json(422, {"error": f"{exc} Reformulez votre question pour réessayer."})
        except EngineError as exc:
            self.send_json(503, {"error": str(exc)})
        except ContractError as exc:
            self.send_json(503, {"error": str(exc)})
        else:
            self.send_json(200, answer)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=CATALOG["models"], default=DEFAULT_MODEL)
    parser.add_argument("--assets", type=Path, default=DEFAULT_ASSETS)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--p5", choices=("a", "b", "c"), help="Profil de recherche P5. L’atelier normal reste la référence P4.")
    parser.add_argument("--jepa", type=Path, help="Dossier local de poids vérifiés pour le profil C.")
    args = parser.parse_args()
    if not 1 <= args.threads <= 16 or not 0 <= args.port <= 65535:
        parser.error("Indiquez un nombre de fils entre 1 et 16 et un port TCP valide.")
    if args.p5 and args.model != "smol":
        parser.error("Les profils comparatifs P5 utilisent SmolLM3.")
    if args.jepa and args.p5 != "c":
        parser.error("L’option --jepa s’utilise avec --p5 c.")

    def stop(_signal, _frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, stop)
    engine = LlamaEngine(args.assets.resolve(), args.model, args.threads)
    experiment = open_experiment(args.p5, args.jepa) if args.p5 else None
    try:
        with WorkshopServer(args.port, engine, experiment) as server:
            print(f"Professeur virtuel : {server.origin}/atelier", flush=True)
            server.serve_forever()
    except KeyboardInterrupt:
        return 0
    except OSError:
        print("Impossible d’ouvrir le serveur local. Vérifiez que le port est disponible.", file=sys.stderr)
        return 1
    finally:
        engine.close()


if __name__ == "__main__":
    sys.exit(main())
