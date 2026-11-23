"""Commandes portables de préparation, de lancement, de diagnostic et d’arrêt."""

import argparse
import http.client
import os
from pathlib import Path
import platform
import secrets
import subprocess
import sys
import time
import webbrowser

from distribution.instance import BUILD_FILE, LOCK, identity, local_request, lock, publish, read, recognized
from distribution.jobs import stop_waiter
from distribution.prepare import assets_for, prepare, verify_engine
from p5.orchestration import open_experiment
from tutor.catalog import ROOT


def start(home, expected, state_file, port, browser, max_help=4):
    state = recognized(state_file, expected)
    if state is None:
        assets, jepa = assets_for(home)
        state = expected | {"instance": secrets.token_hex(16), "token": secrets.token_hex(32)}
        publish(state_file, state)
        command = [sys.executable, "-X", "utf8", "-m", "tutor.server", "--port", str(port), "--p5", "c",
                   "--assets", str(assets), "--jepa", str(jepa), "--control", str(state_file), "--verified-runtime",
                   "--aide-max", str(max_help)]
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        report = state_file.parent / f"serveur-{expected['build']}.log"
        with report.open("a", encoding="utf-8") as log:
            process = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                       creationflags=flags, start_new_session=os.name != "nt")
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline and process.poll() is None:
            found = recognized(state_file, expected)
            if found is not None:
                state = found
                break
            time.sleep(.2)
        else:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)
            raise ValueError(f"Démarrage non confirmé. Consulte {report}.")
        if port and state["port"] != port:
            print(f"Port {port} occupé ou réservé. Cette version utilise le port {state['port']}.", flush=True)
    else:
        print("Instance de cette installation déjà active.", flush=True)

    url = f"http://127.0.0.1:{state['port']}/atelier"
    print(f"LANG-JEPA NSI {state['version']} · {state['build'][:12]} · {url}", flush=True)
    if browser and not webbrowser.open(url):
        print(f"Ouvre cette adresse dans ton navigateur : {url}", flush=True)


def stop(expected, state_file):
    state = recognized(state_file, expected)
    if state is None:
        known_port = read(state_file).get("port")
        if known_port and local_request(known_port, "/api/build"):
            raise ValueError("Une autre instance occupe ce port. Aucun arrêt ne lui a été envoyé.")
        print("Aucune instance reconnue à arrêter.")
        return
    with stop_waiter(state["pid"]) as wait_exit:
        reply = local_request(state["port"], "/api/instance/stop", token=state["token"], method="POST")
        if reply != {"stopping": True}:
            raise ValueError("Le serveur n’a pas confirmé l’arrêt. Consulte les journaux.")
        deadline = time.monotonic() + 15
        while state_file.exists() and time.monotonic() < deadline:
            time.sleep(.15)
        if state_file.exists():
            raise ValueError("La fin de l’arrêt n’a pas été confirmée. Consulte les journaux.")
        wait_exit(deadline - time.monotonic())
    print("Arrêt confirmé du serveur et de son moteur local.")


def verify(home, expected, state_file):
    assets, jepa = assets_for(home)
    state = recognized(state_file, expected)
    if state:
        port = state["port"]
        status = local_request(port, "/api/status")
        deadline = time.monotonic() + 155
        while (status and (status["state"] in {"loading", "working"} or status["jepa"]["state"] in {"loading", "working"})
               and time.monotonic() < deadline):
            time.sleep(.5)
            status = local_request(port, "/api/engines")
        if not status or status["state"] != "ready" or status["jepa"]["state"] != "ready":
            raise ValueError("Les deux moteurs ne sont pas prêts. Lance Installer-Modeles.cmd ou consulte les paramètres.")
        return {"llm": {key: value for key, value in status.items() if key != "jepa"}, "jepa": status["jepa"]}
    observed = open_experiment("c", jepa, recipe=LOCK["jepa"]).status()
    if observed["state"] != "ready":
        raise ValueError(observed["detail"])
    return {"jepa": observed, "llm": verify_engine(assets)}


def main():
    import json
    import zipfile
    from urllib.error import URLError

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("start", "stop", "prepare", "verify"))
    parser.add_argument("--home", type=Path, default=ROOT.parent if BUILD_FILE.is_file() else ROOT)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--aide-max", type=int, choices=(4, 5, 6), default=4,
                        help="Plafond d’aide P7 pour le prochain démarrage.")
    parser.add_argument("--import-from", type=Path, help="Réutilise les archives officielles d’un autre dossier.")
    parser.add_argument("--jepa-only", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error("Port invalide.")
    if BUILD_FILE.is_file() and (os.name != "nt" or platform.machine().lower() not in {"amd64", "x86_64"}):
        parser.error("Ce paquet exige Windows x64.")
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    try:
        home = args.home.resolve()
        logs = home / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        expected = identity(home)
        state = logs / f"instance-{expected['build']}.json"
        with lock(logs / "operation.lock"):
            if args.command == "start":
                start(home, expected, state, args.port, not args.no_browser, args.aide_max)
            elif args.command == "stop":
                stop(expected, state)
            else:
                tick = time.monotonic()
                if args.command == "prepare":
                    if recognized(state, expected):
                        raise ValueError("Arrête cette instance avec Arreter.cmd avant de préparer ses modèles.")
                    report = prepare(home, args.import_from, jepa_only=args.jepa_only)
                else:
                    report = verify(home, expected, state)
                report.update(version=expected["version"], build=expected["build"], platform=platform.platform(),
                              elapsed_s=round(time.monotonic() - tick, 3))
                publish(logs / f"{args.command}.json", report)
                print("Vérifications réussies · " + json.dumps(report, ensure_ascii=False), flush=True)
    except KeyboardInterrupt:
        print("Opération interrompue. Les téléchargements partiels peuvent être repris.", file=sys.stderr)
        return 130
    except (OSError, ValueError, ImportError, URLError, http.client.HTTPException,
            subprocess.SubprocessError, zipfile.BadZipFile) as exc:
        print(f"LANG-JEPA NSI · {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
