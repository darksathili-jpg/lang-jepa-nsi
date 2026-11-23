"""Mesure d’un vrai dialogue Chromium lancé et arrêté par la distribution."""

import argparse
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import threading
import time

import psutil
from playwright.sync_api import sync_playwright

from context_browser import replay as contextual_replay
from distribution.instance import local_request, read
from hybrid_browser import hybrid
from p7_browser import replay as p7_replay
from p71_browser import replay as p71_replay
from p5.compare import read_dialogues


def processes(root):
    try:
        return root.children(recursive=True)
    except psutil.NoSuchProcess:
        return []


def sample(server, browser_parent, stop, observation):
    known = {}
    while not stop.wait(.2):
        current = [server, *processes(server), *processes(browser_parent)]
        rss, cpu = 0, 0
        for process in current:
            handle = known.setdefault(process.pid, process)
            try:
                rss += handle.memory_info().rss
                cpu += handle.cpu_percent()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        observation["rss_peak_bytes"] = max(observation.get("rss_peak_bytes", 0), rss)
        observation["cpu_peak_percent_one_core"] = max(observation.get("cpu_peak_percent_one_core", 0), cpu)
        observation["samples"] = observation.get("samples", 0) + 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--package", type=Path)
    parser.add_argument("--chromium", type=Path)
    parser.add_argument("--context", action="store_true")
    parser.add_argument("--p7", action="store_true")
    parser.add_argument("--p71", action="store_true")
    args = parser.parse_args()
    current = args.p7 or args.p71
    if current and args.context:
        parser.error("Rejoue les parcours historique et courant séparément, dans deux recettes.")
    args.output.mkdir(parents=True, exist_ok=True)

    def command(action, *extra):
        wrappers = {"start": "Demarrer.cmd", "stop": "Arreter.cmd"}
        names = (["cmd.exe", "/D", "/C", wrappers[action]] if args.package else
                 [sys.executable, "-m", "distribution.launcher", action])
        result = subprocess.run([*names, "--home", str(args.home.resolve()), *extra],
                                cwd=args.package, env=os.environ | {"NSI_NONINTERACTIVE": "1"},
                                check=True, capture_output=True, encoding="utf-8", errors="replace", timeout=45)
        print(result.stdout, end="", flush=True)

    stats = {"platform": platform.platform(), "logical_cpu": psutil.cpu_count(),
             "physical_ram_bytes": psutil.virtual_memory().total}
    tick = time.monotonic()
    command("start", "--no-browser", *([] if current else ["--parcours-historique"]))
    stats["launch_s"] = round(time.monotonic() - tick, 3)
    state_file, = (args.home / "logs").glob("instance-*.json")
    state = read(state_file)
    origin = f"http://127.0.0.1:{state['port']}"
    server = psutil.Process(state["pid"])
    stop = threading.Event()
    observer = threading.Thread(target=sample, args=(server, psutil.Process(), stop, stats), daemon=True)
    observer.start()
    outlines = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=args.chromium)
            if not current:
                evidence = args.output / "hybride.jsonl"
                case = next(item for item in read_dialogues() if item["id"] == "maximum-30")
                with evidence.open("x", encoding="utf-8") as stream:
                    hybrid(browser, origin, stream, None, case)
                outlines.append(evidence)
            if args.context:
                contextual_path = args.output / "tour-contextuel.jsonl"
                with contextual_path.open("x", encoding="utf-8") as contextual:
                    contextual_replay(browser, origin, contextual)
                stats["contextual_turns"] = len(contextual_path.read_text(encoding="utf-8").splitlines())
            if current:
                workshop_path = args.output / "p7-atelier.jsonl"
                with workshop_path.open("x", encoding="utf-8") as workshop:
                    p7_replay(browser, origin, workshop)
                stats["p7_turns"] = len(workshop_path.read_text(encoding="utf-8").splitlines())
                outlines.append(workshop_path)
            if args.p71:
                regression = args.output / "p71-atelier.jsonl"
                with regression.open("x", encoding="utf-8") as workshop:
                    p71_replay(browser, origin, workshop)
                stats["p71_turns"] = len(regression.read_text(encoding="utf-8").splitlines())
                outlines.append(regression)
            browser.close()
        stats["engines"] = local_request(state["port"], "/api/engines")
    finally:
        children = [server, *processes(server)]
        stop.set()
        observer.join(5)
        command("stop")
    running = []
    for process in children:
        try:
            if process.is_running() and process.status() not in (psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD):
                running.append(process.pid)
        except psutil.NoSuchProcess:
            pass
    assert not running, running
    assert not state_file.exists()
    rounds = [json.loads(line)["reponse"] for path in outlines for line in path.read_text(encoding="utf-8").splitlines()]
    generated = [line["seconds"] for line in rounds if line["generation"] != "non_sollicite"]
    stats["dialogue"] = {"turns": len(rounds), "median_all_s": statistics.median(line["seconds"] for line in rounds),
                         "llm_requested": len(generated), "median_llm_s": statistics.median(generated) if generated else None,
                         "max_s": max(line["seconds"] for line in rounds)}
    stats["active_after_stop"] = len(running)
    (args.output / "mesures.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Recette réelle · {len(rounds)} tours · aucun processus actif après arrêt.")


if __name__ == "__main__":
    main()
