"""Lanceur local pour la révision LANG-JEPA verrouillée dans p2/upstream.json."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import sys
import tarfile
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    document = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(document, dict):
        raise ValueError(f"Objet JSON attendu dans {path}")
    return document


def verify_sha256(path, expected):
    if not isinstance(expected, str) or not re.fullmatch(r"[a-f0-9]{64}", expected):
        raise ValueError(f"Empreinte SHA-256 invalide pour {path.name}")
    with path.open("rb") as stream:
        observed = hashlib.file_digest(stream, "sha256").hexdigest()
    if observed != expected:
        raise ValueError(f"Empreinte SHA-256 différente pour {path}")
    return observed


def verify_assets(bundle, decode):
    if not (bundle / "encoder.pth").is_file():
        raise FileNotFoundError(f"aucun checkpoint LANG-JEPA d’encodeur dans {bundle}")
    if decode and not (bundle / "decoder.pt").is_file():
        raise FileNotFoundError(f"checkpoint LANG-JEPA de décodeur absent dans {bundle}")

    lock = read_json(ROOT / "p2" / "upstream.json")
    manifest = read_json(bundle / "checkpoints.json")
    if manifest["upstream_revision"] != lock["revision"]:
        raise ValueError("La révision des checkpoints diffère de la révision LANG-JEPA verrouillée.")

    encoder = manifest["encoder"]
    decoder = manifest["decoder"] if decode else None
    if not encoder["provenance"].strip() or (decode and not decoder["provenance"].strip()):
        raise ValueError("Renseignez la provenance des checkpoints d’entraînement.")

    hashes = {
        name: verify_sha256(bundle / name, item["sha256"])
        for name, item in lock["files"].items()
    }
    hashes["encoder_config.yaml"] = verify_sha256(
        bundle / "encoder_config.yaml", encoder["encoder_config_sha256"]
    )
    hashes["encoder.pth"] = verify_sha256(bundle / "encoder.pth", encoder["sha256"])
    if decode:
        if decoder["encoder_sha256"] != hashes["encoder.pth"]:
            raise ValueError("Le décodeur a été associé à un autre checkpoint d’encodeur.")
        hashes["decoder.pt"] = verify_sha256(bundle / "decoder.pt", decoder["sha256"])

    return {
        "upstream_revision": lock["revision"],
        "roberta_revision": lock["roberta_revision"],
        "sha256": hashes,
        "encoder_provenance": encoder["provenance"],
        "decoder_provenance": decoder["provenance"] if decode else None,
    }


def run_cpu(args, bundle, source, assets, started):
    for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY"):
        os.environ[key] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    sys.path.insert(0, str(source))

    import psutil
    import torch
    import torch.nn.functional as F
    import yaml
    from transformers import AutoConfig, AutoTokenizer
    from src.common.config import LANGJEPAConfig
    from src.decoder.concept_extractor import ConceptExtractor
    from src.decoder.models import ConceptDecoder, DecoderConfig
    from src.encoder.models import TextPredictor, TextTransformer

    torch.set_num_threads(args.threads)
    torch.set_num_interop_threads(1)
    torch.manual_seed(0)
    torch.use_deterministic_algorithms(True)
    load_started = time.perf_counter()

    config = LANGJEPAConfig.model_validate(
        yaml.safe_load((bundle / "encoder_config.yaml").read_text(encoding="utf-8-sig"))
    )
    if config.data.tokenizer_path not in {"roberta-base", "FacebookAI/roberta-base"}:
        raise ValueError("Ce profil P2 exige le tokenizer RoBERTa-base d’origine.")
    local_roberta = bundle / "roberta-base"
    tokenizer = AutoTokenizer.from_pretrained(local_roberta, local_files_only=True)
    base = AutoConfig.from_pretrained(local_roberta, local_files_only=True)
    config.data.tokenizer_path = str(local_roberta)
    config.data.tokenizer = tokenizer
    config.meta.use_gradient_checkpointing = False
    if config.model.pretrained:
        # Reprendre la forme de l'AutoModel amont, puis charger tout l'état JEPA.
        config.model.embed_dim = base.hidden_size
        config.model.num_layers = base.num_hidden_layers
        config.model.num_heads = base.num_attention_heads
        config.model.mlp_ratio = base.intermediate_size / base.hidden_size
        config.model.pretrained = False

    encoder = TextTransformer(config).eval()
    extractor = ConceptExtractor(encoder, normalize=True)
    checkpoint = torch.load(
        bundle / "encoder.pth", map_location="cpu", weights_only=True, mmap=True
    )
    encoder.load_state_dict(checkpoint["encoder"], strict=True)
    predictor = None
    if args.mode == "prediction":
        predictor = TextPredictor(encoder.embed_dim, config.model.pred_dim).eval()
        predictor.load_state_dict(checkpoint["predictor"], strict=True)
    del checkpoint

    decoder = None
    if args.decode:
        # Le format amont contient cette dataclass et les états de l'optimiseur.
        with torch.serialization.safe_globals([DecoderConfig]):
            checkpoint = torch.load(
                bundle / "decoder.pt", map_location="cpu", weights_only=True, mmap=True
            )
        saved = checkpoint["config"]
        if not isinstance(saved, DecoderConfig):
            raise ValueError("Configuration de décodeur amont attendue.")
        expected = DecoderConfig.from_tokenizer(tokenizer, encoder.embed_dim)
        for field in ("embed_dim", "vocab_size", "pad_token_id", "bos_token_id", "eos_token_id"):
            if getattr(saved, field) != getattr(expected, field):
                raise ValueError(f"Décodeur incompatible avec l’encodeur ou le tokenizer ({field}).")
        if args.max_generated_tokens >= saved.max_length:
            raise ValueError("La longueur du décodeur doit inclure le token de début.")
        decoder = ConceptDecoder(saved, tokenizer).eval()
        decoder.load_state_dict(checkpoint["model_state_dict"], strict=True)
        del checkpoint

    load_seconds = time.perf_counter() - load_started
    text = args.input.read_text(encoding="utf-8-sig")
    if not text.strip():
        raise ValueError("Le texte d’entrée est vide.")
    input_limit = min(args.max_input_tokens, config.model.max_length, tokenizer.model_max_length)
    inference_started = time.perf_counter()
    encoded = tokenizer(text, truncation=False, return_tensors="pt")
    ids, mask = encoded["input_ids"], encoded["attention_mask"]
    if ids.shape[1] > input_limit:
        raise ValueError(f"Entrée de {ids.shape[1]} tokens, limite de {input_limit}.")
    with torch.inference_mode():
        if predictor is None:
            concept = extractor(ids, mask)
        else:
            concept = F.normalize(predictor(encoder(ids, mask), mask), p=2, dim=-1)
        decoded = None
        if decoder is not None:
            decoded = decoder.generate(
                concept, tokenizer, max_length=args.max_generated_tokens + 1, do_sample=False
            )[0]
        vector = concept[0].tolist()
    inference_seconds = time.perf_counter() - inference_started

    if sys.platform == "win32":
        peak_bytes = psutil.Process().memory_info().peak_wset
    else:
        import resource

        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        peak_bytes = peak if sys.platform == "darwin" else peak * 1024

    return {
        "assets": assets,
        "mode": args.mode,
        "input": text,
        "input_tokens": ids.shape[1],
        "concept": vector,
        "decoder_text": decoded,
        "max_input_tokens": input_limit,
        "max_generated_tokens": args.max_generated_tokens if args.decode else None,
        "runtime": {
            "device": "cpu",
            "torch": torch.__version__,
            "python": platform.python_version(),
            "platform": platform.platform(),
            "processor": (
                os.environ.get("PROCESSOR_IDENTIFIER")
                or platform.processor()
                or platform.machine()
            ),
            "machine_ram_bytes": psutil.virtual_memory().total,
            "threads": args.threads,
            "model_load_seconds": load_seconds,
            "inference_seconds": inference_seconds,
            "elapsed_seconds_before_output": time.perf_counter() - started,
            "peak_rss_bytes": peak_bytes,
        },
    }


def positive_int(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("Entier strictement positif requis.")
    return number


def main():
    started = time.perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=ROOT / "models" / "p2")
    parser.add_argument("--verify-only", action="store_true", help="Vérifier les fichiers, sans charger le modèle.")
    parser.add_argument("--decode", action="store_true", help="Exiger et utiliser le décodeur.")
    parser.add_argument("--mode", choices=("reconstruction", "prediction"), default="reconstruction")
    parser.add_argument("--input", type=Path, help="Fichier texte UTF-8.")
    parser.add_argument("--output", type=Path, help="Nouveau fichier JSON pour la sortie brute.")
    parser.add_argument("--threads", type=positive_int, default=4)
    parser.add_argument("--max-input-tokens", type=positive_int, default=128)
    parser.add_argument("--max-generated-tokens", type=positive_int, default=24)
    args = parser.parse_args()
    if not args.verify_only and (args.input is None or args.output is None):
        parser.error("--input et --output sont requis pour une inférence.")

    bundle = args.bundle.resolve()
    try:
        assets = verify_assets(bundle, args.decode)
        if args.verify_only:
            print(json.dumps(assets, ensure_ascii=True, indent=2))
            return 0
        if args.output.exists():
            raise FileExistsError(f"La sortie existe déjà : {args.output}")
        with tempfile.TemporaryDirectory(prefix="lang-jepa-p2-") as temp:
            with tarfile.open(bundle / "upstream.tar.gz", mode="r:gz") as archive:
                archive.extractall(temp, filter="data")
            source = Path(temp) / f"lang-jepa-{assets['upstream_revision']}"
            report = run_cpu(args, bundle, source, assets, started)
        serialized = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(serialized + "\n")
    except Exception as exc:
        print(f"LANG-JEPA indisponible ({type(exc).__name__}) — {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
