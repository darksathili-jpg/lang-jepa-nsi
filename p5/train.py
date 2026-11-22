"""Entraîne deux JEPA sur CPU et évalue les références sur des familles disjointes."""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import platform
import random
import statistics
import sys
import time

import numpy as np

from p5.contract import ACTIONS
from p5.data import ROOT, load_corpus
from p5.jepa import CONFIGS, diversity, features, l2, load, save, tokens, train


def peak_bytes():
    if sys.platform == "linux":
        import resource

        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    if sys.platform == "win32":
        from tutor.benchmark import peak_memory
        import os

        return peak_memory(os.getpid())
    return None


def choose(scores):
    return max(ACTIONS, key=scores.__getitem__)


def rule(situation):
    words = set(tokens(situation.message))
    if len(words) < 7 or words & {"crois", "bizarre", "comment", "pk"}:
        return "clarifier"
    if words & {"puis", "apres", "iteration", "devient", "reste"}:
        return "tracer"
    if words & {"toujours", "automatiquement", "jamais", "limite", "test"}:
        return "confronter"
    return "justifier"


def lexical(train_rows, rows):
    counts = [Counter(tokens(row.situation.text())) for row in train_rows]
    df = Counter(token for count in counts for token in count)
    vocabulary = {token: col for col, token in enumerate(sorted(df))}
    idf = np.array([np.log((1 + len(counts)) / (1 + df[token])) + 1 for token in vocabulary])

    def matrix(documents):
        m = np.zeros((len(documents), len(vocabulary)))
        for i, doc in enumerate(documents):
            for word, count in doc.items():
                if word in vocabulary:
                    m[i, vocabulary[word]] = 1 + np.log(count)
        return l2(m * idf)

    queries = matrix([Counter(tokens(row.situation.text())) for row in rows])
    similarities = queries @ matrix(counts).T
    return [train_rows[i].action for i in similarities.argmax(axis=1)]


def supervised(train_rows, rows):
    x = features([row.situation.text() for row in train_rows])
    q = features([row.situation.text() for row in rows])
    y = np.array([[row.action == key for key in ACTIONS] for row in train_rows], dtype=float)
    alpha = np.linalg.solve(x @ x.T + 0.35 * np.eye(len(x)), y)
    return [tuple(ACTIONS)[i] for i in (q @ x.T @ alpha).argmax(axis=1)]


def measure(rows, picks):
    truth = [row.action for row in rows]
    correct = [guess == answer for guess, answer in zip(picks, truth, strict=True)]
    return {"correct": sum(correct), "n": len(rows), "exactitude": statistics.mean(correct),
            "choix": picks}


def paired_interval(rows, picks1, picks2):
    groups = defaultdict(list)
    for row, a, b in zip(rows, picks1, picks2, strict=True):
        groups[row.famille].append(int(a == row.action) - int(b == row.action))
    values = list(groups.values())
    rng = random.Random(901)
    estimates = [statistics.mean(x for block in rng.choices(values, k=len(values)) for x in block)
                 for _ in range(3000)]
    return [float(x) for x in np.quantile(estimates, (0.025, 0.975))]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, default=ROOT / "corpus.json")
    parser.add_argument("--epochs", type=int, default=65)
    parser.add_argument("--seeds", type=int, nargs="+", default=[17, 43, 97])
    args = parser.parse_args()
    corpus = load_corpus(args.corpus)
    train_rows, dev, test = ([row for row in corpus if row.partage == split] for split in ("train", "dev", "test"))
    args.output.mkdir(parents=True, exist_ok=False)
    start = time.perf_counter()
    digest = hashlib.sha256(args.corpus.read_bytes()).hexdigest()
    report = {
        "schema": 1, "versions": {"python": platform.python_version(), "numpy": np.__version__},
        "machine": {"platform": platform.platform(), "processeur": platform.processor() or platform.machine()},
        "corpus_sha256": digest, "epoques": args.epochs, "graines": args.seeds,
        "series": {split: len(rows) for split, rows in zip(("train", "dev", "test"), (train_rows, dev, test), strict=True)},
        "verite_test": [{"famille": row.famille, "statut": row.statut, "intervention": row.action} for row in test],
        "references": {}, "essais": [], "courbes_apprentissage": [],
    }
    random_rng = random.Random(292)
    references = {
        "aleatoire": [random_rng.choice(tuple(ACTIONS)) for _ in test],
        "regles": [rule(row.situation) for row in test],
        "tfidf": lexical(train_rows, test),
        "ridge": supervised(train_rows, test),
    }
    report["references"] = {key: measure(test, picks) for key, picks in references.items()}

    target_cards = features(list(ACTIONS.values()))
    test_inputs = features([row.situation.text() for row in test])
    for config in CONFIGS:
        for seed in args.seeds:
            tick = time.perf_counter()
            model, curve = train(train_rows, config, seed, args.epochs)
            destination = args.output / f"{config}-{seed}"
            manifest = save(model, destination, {"corpus_sha256": digest, "graine": seed, "epoques": args.epochs,
                                                 "numpy": np.__version__, "python": platform.python_version()})
            model = load(destination)
            result_dev = measure(dev, [choose(model.scores(row.situation)) for row in dev])
            result_test = measure(test, [choose(model.scores(row.situation)) for row in test])
            encoder_only = l2(model.embeddings(test_inputs)) @ l2(model.encode_target(target_cards)).T
            no_predictor = [tuple(ACTIONS)[i] for i in encoder_only.argmax(axis=1)]
            predicted = model.predict(test_inputs)
            permutation = np.roll(np.random.default_rng(290).permutation(len(test)), 1)
            # Mélange sans point fixe : déplacement circulaire à l'intérieur d'un ordre aléatoire.
            reassign = np.empty(len(test), dtype=int)
            reassign[np.roll(permutation, 1)] = permutation
            shuffled = [result_test["choix"][i] for i in reassign]
            result = {
                "config": config, "graine": seed, "empreinte": manifest["sha256"],
                "dev": result_dev, "test": result_test, "encodeur_seul": measure(test, no_predictor),
                "melange": measure(test, shuffled),
                "predictions": diversity(predicted), "cibles": diversity(model.encode_target(
                    features([row.cible for row in test]))),
                "delta_tfidf_ic95_points": [100 * x for x in paired_interval(test, result_test["choix"], references["tfidf"])],
                "pertes": curve, "secondes": time.perf_counter() - tick,
            }
            report["essais"].append(result)
            print(config, seed, "dev", result_dev["correct"], "test", result_test["correct"], flush=True)

    # La configuration suit la moyenne sur dev, puis la graine déployée dans la recette est fixée à l'avance.
    config = max(CONFIGS, key=lambda candidate: statistics.mean(
        run["dev"]["exactitude"] for run in report["essais"] if run["config"] == candidate))
    report["configuration_retenue_dev"] = config
    report["graine_recette"] = args.seeds[0]
    for fraction in (0.25, 0.5, 1.0):
        for seed in args.seeds:
            families = sorted({row.famille for row in train_rows})
            random.Random(seed).shuffle(families)
            allowed = set(families[:max(2, round(fraction * len(families)))])
            subset = [row for row in train_rows if row.famille in allowed]
            model, _ = train(subset, config, seed, args.epochs)
            result = measure(dev, [choose(model.scores(row.situation)) for row in dev])
            report["courbes_apprentissage"].append({"familles": len(allowed), "tours": len(subset), "graine": seed,
                                                     "dev": result["exactitude"]})
    report["secondes"] = time.perf_counter() - start
    report["pic_processus_octets"] = peak_bytes()
    (args.output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                                            encoding="utf-8")


if __name__ == "__main__":
    main()
