"""Recette du lanceur réel, avec port occupé et deux installations indépendantes."""

import argparse
from contextlib import ExitStack
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading

from distribution.instance import identity, local_request, read, recognized


class OldServer(BaseHTTPRequestHandler):
    stop_attempts = 0

    def log_message(self, *_args):
        pass

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Length", "3")
        self.end_headers()
        self.wfile.write(b"old")

    def do_POST(self):
        type(self).stop_attempts += 1
        self.send_error(403)


def smoke(home, packaged, old_port):
    commands = {"start": "Demarrer.cmd", "stop": "Arreter.cmd", "prepare": "Installer-Modeles.cmd"}
    if packaged:
        env = os.environ | {"NSI_NONINTERACTIVE": "1", "PATH": os.path.join(os.environ["SystemRoot"], "System32")}
        cwd = packaged
    else:
        env = os.environ.copy()
        cwd = Path(__file__).resolve().parents[1]

    def run(action, *extra):
        command = (["cmd.exe", "/D", "/C", commands[action]] if packaged else
                   [sys.executable, "-m", "distribution.launcher", action])
        result = subprocess.run([*command, "--home", str(home), *extra], env=env, cwd=cwd, check=True,
                                capture_output=True, encoding="utf-8", errors="replace", timeout=90)
        print(result.stdout, end="", flush=True)
        return result.stdout

    if packaged:
        run("prepare", "--jepa-only")
        assert read(home / "logs/prepare.json")["jepa"]["checks"]["selection"]
    try:
        run("start", "--no-browser", "--port", str(old_port))
        state_file, = (home / "logs").glob("instance-*.json")
        state = read(state_file)
        expected = {key: state[key] for key in identity(home)}
        assert state["port"] != old_port and recognized(state_file, expected)
        assert local_request(state["port"], "/api/instance/stop", token="incorrect", method="POST") is None
        assert "déjà active" in run("start", "--no-browser", "--port", str(old_port))
        assert read(state_file)["pid"] == state["pid"]
        assert local_request(state["port"], "/api/build")["build"] == state["build"]
        assert local_request(state["port"], "/api/exercises")["premiere"]
    finally:
        run("stop")
    assert not state_file.exists()
    assert local_request(state["port"], "/api/build") is None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, help="Racine du ZIP Windows extrait pour tester .cmd et Python embarqué.")
    args = parser.parse_args()
    with ExitStack() as stack:
        old = stack.enter_context(ThreadingHTTPServer(("127.0.0.1", 0), OldServer))
        worker = threading.Thread(target=old.serve_forever, daemon=True)
        worker.start()
        stack.callback(worker.join, 5)
        stack.callback(old.shutdown)
        for _ in range(2):
            home = Path(stack.enter_context(tempfile.TemporaryDirectory(prefix="NSI atelier-")))
            smoke(home, args.package.resolve() if args.package else None, old.server_port)
        assert OldServer.stop_attempts == 0
    print("Lanceurs testés : port occupé conservé, réutilisation, rejet d’arrêt non authentifié et arrêt propre.")


if __name__ == "__main__":
    main()
