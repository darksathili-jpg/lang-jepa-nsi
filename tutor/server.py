"""Sert l’atelier sur l’interface de bouclage, sans dépendance web tierce."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import signal
import sys
import threading

from tutor.catalog import CATALOG, DEFAULT_ASSETS, ROOT
from tutor.dialogue import DialogueError, RejectedReply, respond
from tutor.engine import EngineError, LlamaEngine


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
    def __init__(self, port, engine):
        super().__init__(("127.0.0.1", port), Handler)
        self.engine = engine
        self.host_header = f"127.0.0.1:{self.server_port}"
        self.origin = "http://" + self.host_header


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
            self.send_json(200, self.server.engine.status())
        elif self.path in PAGES:
            filename, mime = PAGES[self.path]
            self.reply(200, (APP / filename).read_bytes(), mime)
        else:
            self.send_json(404, {"error": "Page introuvable."})

    def do_POST(self):
        if not self.valid_host():
            return
        if self.path != "/api/tutor":
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
            answer, _ = respond(self.server.engine, payload)
        except DialogueError as exc:
            self.send_json(400, {"error": str(exc)})
        except RejectedReply as exc:
            self.send_json(422, {"error": f"{exc} Reformulez votre question pour réessayer."})
        except EngineError as exc:
            self.send_json(503, {"error": str(exc)})
        else:
            self.send_json(200, answer)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=CATALOG["models"], default=DEFAULT_MODEL)
    parser.add_argument("--assets", type=Path, default=DEFAULT_ASSETS)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args()
    if not 1 <= args.threads <= 16 or not 0 <= args.port <= 65535:
        parser.error("Indiquez un nombre de fils entre 1 et 16 et un port TCP valide.")

    def stop(_signal, _frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, stop)
    engine = LlamaEngine(args.assets.resolve(), args.model, args.threads)
    try:
        with WorkshopServer(args.port, engine) as server:
            threading.Thread(target=engine.start, name="modele-cpu", daemon=True).start()
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
