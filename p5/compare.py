"""Recette A/B/C P5 à entrées identiques, sur des dialogues synthétiques gelés."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import statistics
import time

from p5.contract import ACTIONS
from p5.data import ROOT
from p5.orchestration import Experiment
from p5.train import peak_bytes
from pedagogy.catalogue import EXERCISES
from pedagogy.progress import near_question
from tutor.benchmark import peak_memory
from tutor.catalog import DEFAULT_ASSETS
from tutor.dialogue import RejectedReply, normalized
from tutor.engine import EngineError, LlamaEngine
from tutor.sessions import Sessions


MODES = ("a", "b", "c", "neutralise", "melange")
LEAK = re.compile(r"tab\s*\[\s*0\s*\]|\bdef\s+maximum|\bmax\s*\(|premier (?:element|entier)|moins l'infini")
FALSE_CLAIM = re.compile(r"\bj'ai execute\b|0 est inferieur a -[24]|-[24] est superieur a 0")


def read_dialogues():
    data = json.loads((ROOT / "dialogues.json").read_text(encoding="utf-8"))
    if data["schema"] != 1:
        raise ValueError("Version du dialogue inconnue.")
    return data["dialogues"]


def replay(mode, engine, model, donors, case):
    exercise = EXERCISES["maximum"]
    original = exercise["code"]
    corrected = original.replace("m = 0", "m = tab[0]")
    sessions = Sessions(Experiment(mode, model, donors=donors))
    token, turn = None, 0
    seen = []
    for index, step in enumerate(case["tours"], 1):
        code = corrected if step.get("code") == "corrige" else original
        payload = {"class": "premiere", "statement": exercise["statement"], "code": code,
                   "question": step["texte"], "session": token, "turn": turn}
        captures = []
        start = time.perf_counter()
        try:
            answer = sessions.turn("conversation", payload, engine, capture=captures)
            token, turn = answer["session"], answer["turn"]
            answer = {k: v for k, v in answer.items() if k != "session"}
            raw = captures[0]
            error = None
        except (RejectedReply, EngineError) as exc:
            answer, error, raw = None, str(exc), getattr(exc, "evidence", None)
        state = answer.get("pedagogie") if answer else None
        decision = state["derniere_intervention"] if state else None
        question = answer["question"] if answer else ""
        shown = normalized(" ".join(answer.get(key, "") for key in ("indice", "question", "feedback"))) if answer else ""
        repeat = bool(question and any(near_question(question, earlier) for earlier in seen))
        if question:
            seen.append(question)
        yield {
            "kind": "turn", "mode": mode, "dialogue": case["id"], "tour": index, "entree": step,
            "reponse": answer, "sortie_brute": raw, "erreur": error,
            "secondes": round(time.perf_counter() - start, 4),
            "pic_moteur_octets": peak_memory(engine.process.pid) if engine else None,
            "pic_python_octets": peak_bytes(),
            "mesures": {
                "objectif": state["objectif"] == step["objectif"] if state else None,
                "approche": decision["approche"] == step["reference"] if decision and step["reference"] else None,
                "redite": repeat,
                "reouvre_trace": index >= 4 and bool(re.search(r"valeur de .?m|m reste|trace de m", normalized(question))),
                "divulgation": step.get("code") != "corrige" and bool(LEAK.search(shown)),
                "inexactitude_detectee": bool(FALSE_CLAIM.search(shown)),
                "reclassement": bool(decision and decision["differe_des_regles"]),
                "hint_llm": (answer.get("generation") == "affiche" or mode == "a") if answer else False,
                "echec_generation": bool(error or (answer and answer.get("generation") == "indisponible")),
            },
        }


def shuffled_donors(case):
    """Permutation circulaire des situations éligibles du même dialogue, sans point fixe."""
    situations = []

    class Capture:
        identity = "Neutralisation de contrôle"

        def scores(self, situation):
            situations.append(situation)
            return dict.fromkeys(ACTIONS, 0.0)

    turns = [row["tour"] for row in replay("c", None, Capture(), None, case)
             if row["reponse"]["pedagogie"]["derniere_intervention"]]
    if len(turns) < 2:
        raise ValueError("Le mélange exige au moins deux interventions.")
    return dict(zip(turns, situations[1:] + situations[:1], strict=True))


def summary(rows):
    considered = [row for row in rows if row["mesures"]["approche"] is not None]
    objectives = [row for row in rows if row["mesures"]["objectif"] is not None]
    return {
        "n": len(rows), "reponses": sum(row["reponse"] is not None for row in rows),
        "objectifs": [sum(row["mesures"]["objectif"] for row in objectives), len(objectives)],
        "approches": [sum(row["mesures"]["approche"] for row in considered), len(considered)],
        "median_s": statistics.median(row["secondes"] for row in rows),
        "max_s": max(row["secondes"] for row in rows),
        "pic_moteur_octets": max((row["pic_moteur_octets"] for row in rows if row["pic_moteur_octets"]), default=None),
        "pic_python_octets": max((row["pic_python_octets"] for row in rows if row["pic_python_octets"]), default=None),
        **{key: sum(row["mesures"][key] for row in rows) for key in
           ("redite", "reouvre_trace", "divulgation", "inexactitude_detectee", "reclassement", "hint_llm", "echec_generation")},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--assets", type=Path, default=DEFAULT_ASSETS)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--threads", type=int, choices=range(1, 17), default=2)
    parser.add_argument("--modes", choices=MODES, nargs="+", default=MODES)
    parser.add_argument("--dialogues", nargs="+", default=["maximum-10"])
    parser.add_argument("--sans-llm", action="store_true")
    args = parser.parse_args()
    if args.sans_llm and "a" in args.modes:
        parser.error("Le mode A exige un véritable LLM.")
    from p5.jepa import load

    model = load(args.weights)
    dialogues = [group for group in read_dialogues() if group["id"] in args.dialogues]
    if len(dialogues) != len(set(args.dialogues)):
        parser.error("Dialogue expérimental inconnu.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    engine = None if args.sans_llm else LlamaEngine(args.assets, "smol", args.threads)
    try:
        with args.output.open("x", encoding="utf-8") as output:
            def write(row):
                output.write(json.dumps(row, ensure_ascii=False) + "\n")
                output.flush()

            startup = None
            if engine:
                start = time.perf_counter()
                engine.start()
                startup = time.perf_counter() - start
                if engine.state != "ready":
                    raise EngineError(engine.detail)
            write({"kind": "run", "schema": 1, "threads": args.threads, "theta": model.identity,
                   "llm": engine.status() if engine else None, "demarrage_s": startup,
                   "dialogues_sha256": hashlib.sha256((ROOT / "dialogues.json").read_bytes()).hexdigest()})
            for mode in args.modes:
                rows = []
                for dialogue in dialogues:
                    donors = shuffled_donors(dialogue) if mode == "melange" else None
                    for row in replay(mode, engine, model, donors, dialogue):
                        rows.append(row)
                        write(row)
                    print(mode, dialogue["id"], summary(rows), flush=True)
                write({"kind": "summary", "mode": mode, **summary(rows)})
    finally:
        if engine:
            engine.close()


if __name__ == "__main__":
    main()
