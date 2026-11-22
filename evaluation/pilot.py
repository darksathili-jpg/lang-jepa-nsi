"""Expérience comparative hors ligne de l’architecture LANG-JEPA d’origine."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import platform
import shutil
from statistics import mean
import sys
import tempfile
import time

from evaluation.corpus import CORPUS, PARTS, load_corpus, make_pairs
from evaluation.metrics import lexical_cosine, lexical_reference, rank, summarize, words
from jepa.resources import upstream


DEFAULTS = {
    "width": 32, "train_batch": 4, "evaluation_batch": 1, "window": 2, "max_input_tokens": 112,
    "max_new_tokens": 30, "encoder_steps": 48, "decoder_steps": 72, "encoder_lr": 0.001,
    "decoder_lr": 0.002, "momentum": 0.97, "weight_decay": 0.01, "device": "cpu",
    "encoder_loss": "smooth_l1_sur_vecteurs_normalises", "decoder_loss": "cross_entropy_teacher_forcing",
}


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def rank_vectors(query, candidates, names, expected):
    return rank(dict(zip(names, (candidates @ query).tolist(), strict=True)), expected)


def representation_metrics(model, test, train, heldout):
    import torch

    errors = [doc["segments"]["erreur"] for doc in test]
    hints = [doc["segments"]["indice"] for doc in train]
    error_vector = model.represent(errors, "online")
    hint_vector = model.represent(hints, "online")
    predicted = model.represent([pair.context for pair in heldout], "predicted")
    targets = model.represent([pair.target for pair in heldout], "target")
    context_control = model.represent([pair.context for pair in heldout], "target")
    lexical = lexical_reference([doc["segments"][key] for doc in train for key in PARTS])
    similarity = error_vector @ error_vector.T
    pairs = [{
        "left": left["id"], "right": right["id"], "related": left["family"] == right["family"],
        "cosine": similarity[i, j].item(),
        "lexical_cosine": lexical_cosine(lexical(errors[i]), lexical(errors[j])),
    } for i, left in enumerate(test) for j, right in enumerate(test) if i < j]
    entropy = []
    for vectors in (error_vector, predicted, targets):
        variance = torch.linalg.svdvals(vectors - vectors.mean(dim=0)).square()
        total = variance.sum().item()
        probs = [value / total for value in variance.tolist() if value > 0] if total else []
        entropy.append({
            "spectral_effective_rank": math.exp(-sum(p * math.log(p) for p in probs)) if total else 0.0,
            "mean_dimension_std": vectors.std(dim=0, unbiased=False).mean().item(),
            "mean_off_diagonal_cosine": (vectors @ vectors.T).triu(1).sum().item() / math.comb(len(vectors), 2),
        })
    repeated = model.represent(errors, "online")
    padded = model.represent(errors, "online", batch_size=4)
    changed = model.represent([text.rstrip(".") + " !" for text in errors], "online")
    stability = {
        "repeat_max_abs_delta": (error_vector - repeated).abs().max().item(),
        "padding_max_abs_delta": (error_vector - padded).abs().max().item(),
        "punctuation_cosine": (error_vector * changed).sum(dim=1).tolist(),
    }

    retrieval = []
    for i, doc in enumerate(test):
        ids = [item["id"] for item in train]
        match = {item["id"] for item in train if item["family"] == doc["family"]}
        scores = {key: lexical_cosine(lexical(errors[i]), lexical(hint)) for key, hint in zip(ids, hints)}
        retrieval.append({
            "query": doc["id"], "jepa": rank_vectors(error_vector[i], hint_vector, ids, match),
            "lexical": rank(scores, match),
        })

    prediction = []
    for i, pair in enumerate(heldout):
        # Candidats du même rôle documentaire. Il n'y a aucun texte du test dans l'entraînement.
        pool = [index for index, item in enumerate(heldout) if item.part == pair.part]
        ids = [heldout[index].document for index in pool]
        scores = {
            heldout[index].document: lexical_cosine(lexical(pair.context), lexical(heldout[index].target))
            for index in pool
        }
        match = {pair.document}
        prediction.append({
            "query": pair.document, "part": pair.part, "cosine_with_actual_target": (predicted[i] @ targets[i]).item(),
            "smooth_l1": torch.nn.functional.smooth_l1_loss(predicted[i], targets[i]).item(),
            "jepa": rank_vectors(predicted[i], targets[pool], ids, match),
            "context_control": rank_vectors(context_control[i], targets[pool], ids, match),
            "lexical": rank(scores, match),
        })

    def result(rows, methods):
        return {key: summarize([row[key] for row in rows]) for key in methods}

    return {
        "similarity": {
            "pairs": pairs, "same_family_mean": mean(row["cosine"] for row in pairs if row["related"]),
            "other_family_mean": mean(row["cosine"] for row in pairs if not row["related"]),
            "lexical_same_family_mean": mean(row["lexical_cosine"] for row in pairs if row["related"]),
            "lexical_other_family_mean": mean(row["lexical_cosine"] for row in pairs if not row["related"]),
        },
        "spread": dict(zip(("errors_online", "predicted", "targets_ema"), entropy, strict=True)),
        "stability": stability, "retrieval": retrieval, "prediction": prediction,
        "retrieval_summary": result(retrieval, ("jepa", "lexical")),
        "prediction_summary": result(prediction, ("jepa", "context_control", "lexical")),
        "vectors": {
            "errors_online": error_vector.tolist(), "hints_online": hint_vector.tolist(),
            "predicted": predicted.tolist(), "targets_ema": targets.tolist(),
            "heldout_pairs": [vars(pair) for pair in heldout],
        },
    }


def decoder_metrics(model, train, test, heldout):
    started = time.perf_counter()
    examples = []
    for first, other, split in ((train[0], train[2], "train_control"), (test[0], test[2], "test")):
        for part in ("enonce", "notion"):
            text, control = first["segments"][part], other["segments"][part]
            concepts = model.represent([text, control], "online")
            examples.append({
                "document": first["id"], "condition": "reconstruction", "split": split, "part": part,
                **model.decode(text, concepts[0:1], concepts[1:2]),
            })

    selected = [pair for pair in heldout if pair.part == "indice"]
    vectors = model.represent([pair.context for pair in selected], "predicted")
    for i, pair in enumerate(selected):
        control = next(index for index, other in enumerate(selected) if other.family != pair.family)
        examples.append({
            "document": pair.document, "condition": "prediction", "split": "test", "part": pair.part,
            **model.decode(pair.target, vectors[i:i + 1], vectors[control:control + 1]),
        })
    for item in examples:
        reference = words(item["reference"])
        generated = words(item["generated"])
        union = set(reference + generated)
        item["word_jaccard"] = len(set(reference) & set(generated)) / len(union) if union else 0
        item["exact_words"] = reference == generated
    return examples, time.perf_counter() - started


def peak_memory():
    if sys.platform == "win32":
        import psutil
        return psutil.Process().memory_info().peak_wset
    import resource
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return peak if sys.platform == "darwin" else peak * 1024


def timed(call):
    started = time.perf_counter()
    result = call()
    return result, time.perf_counter() - started


def run(assets, output, settings):
    started = time.perf_counter()
    docs = load_corpus()
    train = [doc for doc in docs if doc["split"] == "train"]
    test = [doc for doc in docs if doc["split"] == "test"]
    train_pairs, heldout = [make_pairs(docs, split, settings["window"]) for split in ("train", "test")]
    if output.exists():
        raise FileExistsError(f"Le dossier de sortie existe déjà : {output}")
    with upstream(assets) as (source, resources):
        from importlib.metadata import version
        from jepa.pilot import Pilot

        model = Pilot(assets, source, settings)
        startup = time.perf_counter() - started
        initial = representation_metrics(model, test, train, heldout)
        encoder_loss, encoder_seconds = timed(lambda: model.train_encoder(train_pairs))
        trained = representation_metrics(model, test, train, heldout)
        decoder_loss, decoder_seconds = timed(lambda: model.train_decoder([
            doc["segments"][part] for doc in train for part in PARTS
        ]))
        decoding, decoding_seconds = decoder_metrics(model, train, test, heldout)
        probe = test[0]["segments"]["erreur"]
        _, inference_seconds = timed(lambda: model.represent([probe], "online"))
        with tempfile.TemporaryDirectory(prefix="resultat-jepa-", dir=output.parent) as tmp:
            stage = Path(tmp) / "run"
            stage.mkdir()
            model.save(stage)
            checkpoints = {name: digest(stage / name) for name in ("encoder.pth", "decoder.pt", "encoder_config.yaml")}
            for relative in resources["sha256"]:
                target = stage / relative
                target.parent.mkdir(exist_ok=True)
                shutil.copyfile(assets / relative, target)
            manifest = {
                "upstream_revision": resources["upstream_revision"],
                "encoder": {"sha256": checkpoints["encoder.pth"], "encoder_config_sha256": checkpoints["encoder_config.yaml"],
                            "provenance": f"Pilote LANG-JEPA NSI sur corpus synthétique, seed {settings['seed']}"},
                "decoder": {"sha256": checkpoints["decoder.pt"], "encoder_sha256": checkpoints["encoder.pth"],
                            "provenance": f"Décodeur LANG-JEPA du pilote NSI, seed {settings['seed']}"},
            }
            (stage / "checkpoints.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            report = {
                "settings": settings, "resources": resources, "corpus_sha256": digest(CORPUS),
                "documents": {"train": [doc["id"] for doc in train], "test": [doc["id"] for doc in test]},
                "counts": {"train_pairs": len(train_pairs), "test_pairs": len(heldout)},
                "model_parameters": {name: sum(p.numel() for p in module.parameters()) for name, module in (
                    ("encoder", model.encoder), ("predictor", model.predictor), ("decoder", model.decoder)
                )},
                "software": {name: version(name) for name in ("torch", "transformers", "PyYAML", "pydantic", "psutil")},
                "platform": platform.platform(), "python": platform.python_version(),
                "runtime": {"startup_seconds": startup, "encoder_seconds": encoder_seconds,
                            "decoder_seconds": decoder_seconds, "decode_evaluation_seconds": decoding_seconds,
                            "single_warm_embedding_seconds": inference_seconds, "peak_rss_bytes": peak_memory(),
                            "total_seconds": time.perf_counter() - started},
                "checkpoint_sha256": checkpoints, "before_training": initial, "after_training": trained,
                "training_losses": {"encoder": encoder_loss, "decoder": decoder_loss}, "decoder_examples": decoding,
            }
            (stage / "report.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8",
            )
            stage.rename(output)
    return output / "report.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="Nouveau dossier dans results/ ou hors dépôt.")
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--threads", type=int, choices=range(1, 5), default=2)
    args = parser.parse_args()
    try:
        if not args.output.parent.is_dir():
            raise FileNotFoundError("Le dossier parent du résultat doit exister.")
        print(run(args.assets.resolve(), args.output.resolve(), DEFAULTS | {"seed": args.seed, "threads": args.threads}))
    except KeyboardInterrupt:
        print("Pilote annulé. Aucun résultat partiel n’a été publié.", file=sys.stderr)
        return 130
    except (OSError, ValueError, ImportError) as exc:
        print(f"Pilote LANG-JEPA impossible. {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
