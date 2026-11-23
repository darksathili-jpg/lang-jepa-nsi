"""Comparer la chaîne P6.2 et les profils P7 sur les mêmes entrées synthétiques."""

import argparse
import hashlib
import json
from math import sqrt
from pathlib import Path
import platform
import re
import statistics
import time

from p5.orchestration import Experiment
from p7 import __file__ as package_file
from pedagogy.catalogue import EXERCISES
from tutor.benchmark import peak_memory
from tutor.dialogue import normalized
from tutor.engine import EngineError, LlamaEngine
from tutor.sessions import Sessions


CORPUS = Path(package_file).with_name("qualification.json")
LEAK = re.compile(r"\b(?:def\s+\w+|tab\s*\[\s*0\s*\]|return\s+max\s*\()")


class NoGeneration:
    def generate(self, *_args, **_kwargs):
        raise EngineError("Aucune génération dans la recette déterministe.")


def data(path=CORPUS):
    content = json.loads(path.read_text(encoding="utf-8"))
    if content["schema"] != 1:
        raise ValueError("Corpus de qualification inconnu.")
    return content["dialogues"]


def code_for(dialogue, corrected):
    key = dialogue["exercise"]
    original = dialogue.get("initial", EXERCISES[key]["code"])
    if key == "recursivite-base" and dialogue.get("variant") == "unreachable":
        original = "def fact(n):\n    if n == 0:\n        return 1\n    return n * fact(n + 1)"
    if not corrected:
        return original
    return {"maximum": lambda: original.replace("m = 0", "m = tab[0]"),
            "boucle-while": lambda: original.replace("print(n)", "print(n)\n        n -= 1"),
            "dictionnaire-comptage": lambda: original.replace("d[mot] += 1", "d[mot] = d.get(mot, 0) + 1"),
            "recursivite-base": lambda: original.replace("n + 1", "n - 1")}[key]()


def replay(dialogue, mode, engine=None, experiment=None):
    spec = EXERCISES[dialogue["exercise"]]
    sessions = Sessions(experiment, case_based=mode != "A")
    token, sequence = None, 0
    seen = set()
    for index, step in enumerate(dialogue["turns"], 1):
        request = {"class": spec["level"], "statement": spec["statement"], "code": code_for(dialogue, bool(step.get("code"))),
                   "question": step["text"], "session": token, "turn": sequence}
        captures, error, response = [], None, None
        tick = time.perf_counter()
        try:
            answer = sessions.turn("conversation", request, engine if engine is not None else NoGeneration(), capture=captures)
            token, sequence = answer["session"], answer["turn"]
            response = {key: value for key, value in answer.items() if key != "session"}
        except EngineError as exc:
            error = str(exc)
        state = (response or {}).get("pedagogie", {})
        active = state.get("essai_actif") or {}
        question = (response or {}).get("question", "")
        output = " ".join((response or {}).get(key, "") for key in ("indice", "feedback", "question"))
        proof = state.get("acquis", {})
        checks = {"objectif": state.get("objectif") == step["goal"],
                  "intention": set(state.get("interpretation", {}).get("intentions", ())) == set(step["intents"]) if "intents" in step else None,
                  "test": json.loads(json.dumps(active.get("entree"))) == step["test"] if "test" in step else None,
                  "preuve": step["confirmed"] in proof if "confirmed" in step else None,
                  "abusive": step["forbidden"] in proof if "forbidden" in step else False,
                  "statique": (active.get("statique") or {}).get("kind") == step["static"] if "static" in step else None,
                  "abstention_statique": active.get("statique") is None if step.get("abstain_static") else None,
                  "precondition": active.get("precondition") == step["precondition"] if "precondition" in step else None,
                  "litteral_invalide": bool(state.get("interpretation", {}).get("ambiguities")) if step.get("invalid") else None,
                  "prediction": active.get("predit") == step["predicted"] and active.get("declare") is None if "predicted" in step else None,
                  "declaration": active.get("declare") == step["declared"] if "declared" in step else None,
                  "execution_fictive": active.get("execute") is not None or bool(re.search(r"j'ai execute|execution reussie", normalized(output))),
                  "divulgation": not step.get("code") and bool(LEAK.search(normalized(output))),
                  "repetition": bool(question and (state.get("objectif"), question) in seen),
                  "reponse_absente": not output.strip()}
        if question:
            seen.add((state.get("objectif"), question))
        yield {"profil": mode, "dialogue": dialogue["id"], "famille": dialogue["exercise"], "tour": index,
               "attendu": step, "reponse": response, "erreur": error, "brut": captures[0] if captures else None,
               "controle": checks, "secondes": round(time.perf_counter() - tick, 4)}


def interval(success, size):
    if not size:
        return None
    z = 1.959964
    share = success / size
    center = (share + z*z / (2*size)) / (1 + z*z / size)
    half = z * sqrt((share * (1 - share) + z*z / (4*size)) / size) / (1 + z*z / size)
    return [round(max(0, center-half), 3), round(min(1, center+half), 3)]


def summarize(rows):
    results = {}
    for key in rows[0]["controle"]:
        values = [row["controle"][key] for row in rows if row["controle"][key] is not None]
        results[key] = {"effectif": len(values), "vrais": sum(values), "wilson95": interval(sum(values), len(values))}
    goals = {}
    for row in rows:
        goals.setdefault(row["dialogue"], []).append(row["controle"]["objectif"] and not row["controle"]["reponse_absente"])
    results["dialogues_objectifs_atteints"] = [sum(map(all, goals.values())), len(goals)]
    results["mediane_s"] = statistics.median(row["secondes"] for row in rows)
    model = [row["secondes"] for row in rows if row["brut"] is not None]
    results["llm"] = {"tours": len(model), "mediane_s": statistics.median(model) if model else None}
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profiles", default="ABCD")
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--weights", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, default=CORPUS)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--repetitions", type=int, choices=(1, 2, 3), default=1)
    args = parser.parse_args()
    if not set(args.profiles) <= set("ABCDT") or "D" in args.profiles and not args.weights:
        parser.error("Profils A, B, C, D ou T. D exige --weights.")
    from p5.jepa import load

    dialogues = data(args.corpus)
    args.output.mkdir(parents=True, exist_ok=True)
    for profile in args.profiles:
        engine = None if profile == "T" else LlamaEngine(args.assets, "qwen" if profile == "C" else "smol", args.threads)
        experiment = Experiment("c", load(args.weights)) if profile == "D" else None
        try:
            if engine:
                engine.start()
                if engine.status()["state"] != "ready":
                    raise SystemExit(engine.status()["detail"])
            first = []
            with (args.output / f"{profile}.jsonl").open("x", encoding="utf-8") as stream:
                for repeat in range(1, args.repetitions + 1):
                    selected = dialogues if repeat == 1 else [d for d in dialogues if d.get("sensible") or d["id"] in {"altitudes-positives", "contre-epreuve"}]
                    for dialogue in selected:
                        for row in replay(dialogue, profile, engine, experiment):
                            row["repetition"] = repeat
                            print(json.dumps(row, ensure_ascii=False), file=stream, flush=True)
                            if repeat == 1:
                                first.append(row)
            summary = {"profil": profile, "machine": platform.platform(), "corpus_sha256": hashlib.sha256(args.corpus.read_bytes()).hexdigest(),
                       "threads": args.threads, "repetitions_sensibles": args.repetitions,
                       "moteur": engine.status() if engine else None,
                       "rss_pic_moteur": peak_memory(engine.process.pid) if engine else None,
                       "mesures": summarize(first)}
            (args.output / f"{profile}.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(profile, summary["mesures"]["objectif"], summary["mesures"]["intention"], flush=True)
        finally:
            if engine:
                engine.close()


if __name__ == "__main__":
    main()
