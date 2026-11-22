"""Prédiction latente CPU P5 avec cible EMA ou cible fixe, et poids locaux vérifiés."""

import hashlib
import io
import json
from pathlib import Path
import re
import unicodedata
import zipfile

import numpy as np

from p5.contract import ACTIONS, SCHEMA, ContractError, validate_scores


DIM_INPUT = 512
DIM_LATENT = 24
CONFIGS = ("ema-24", "fixe-24")
SHAPES = {"encoder": (DIM_INPUT, DIM_LATENT), "target": (DIM_INPUT, DIM_LATENT),
          "predictor": (DIM_LATENT, DIM_LATENT)}
MAX_BYTES = 1 << 20


def tokens(text):
    ascii_text = "".join(char for char in unicodedata.normalize("NFKD", text.casefold())
                         if not unicodedata.combining(char))
    return re.findall(r"[a-z_]+|[-+]?\d+|==|!=|<=|>=|[<>+*/%]", ascii_text)


def features(texts):
    result = np.zeros((len(texts), DIM_INPUT), dtype=np.float32)
    for row, text in zip(result, texts, strict=True):
        words = tokens(text)
        bigrams = (left + " " + right for left, right in zip(words, words[1:]))
        for token in (*words, *bigrams):
            key = int.from_bytes(hashlib.blake2s(token.encode(), digest_size=4).digest(), "little")
            row[key % DIM_INPUT] += 1 if key >> 31 else -1
        np.clip(row, -3, 3, out=row)
    return l2(result)


def l2(array):
    return array / np.maximum(np.linalg.norm(array, axis=1, keepdims=True), 1e-7)


class LatentModel:
    def __init__(self, config, encoder, target, predictor, identity="non sauvegardé", *, metadata=None):
        self.config = config
        self.encoder = encoder
        self.target = target
        self.predictor = predictor
        self.identity = identity
        self.metadata = metadata or {}
        self.candidates = None

    def embeddings(self, inputs):
        return np.tanh(inputs @ self.encoder)

    def predict(self, inputs):
        return self.embeddings(inputs) @ self.predictor

    def encode_target(self, inputs):
        return np.tanh(inputs @ self.target)

    def scores(self, situation):
        if self.candidates is None:
            self.candidates = l2(self.encode_target(features(list(ACTIONS.values()))))
        prediction = l2(self.predict(features([situation.text()])))
        return validate_scores(dict(zip(ACTIONS, map(float, (prediction @ self.candidates.T)[0]), strict=True)))


def diversity(values):
    centered = values - values.mean(axis=0)
    spectrum = np.linalg.svd(centered, compute_uv=False) ** 2
    probabilities = spectrum / max(float(spectrum.sum()), 1e-12)
    nonzero = probabilities[probabilities > 1e-10]
    similarities = l2(values) @ l2(values).T
    return {
        "ecart_type_moyen": float(values.std(axis=0).mean()),
        "rang_effectif": float(np.exp(-np.sum(nonzero * np.log(nonzero)))) if len(nonzero) else 0.0,
        "cosinus_hors_diagonale": float(similarities[~np.eye(len(values), dtype=bool)].mean()),
    }


def variance_gradient(z):
    """Charnière de variance et décorrélation, avec gradients sur l'encodeur en ligne."""
    count, dims = z.shape
    centered = z - z.mean(axis=0)
    std = np.sqrt((centered ** 2).mean(axis=0) + 1e-4)
    margin = np.maximum(0.28 - std, 0)
    grad_std = -0.8 * centered * (margin > 0) / (count * dims * std)
    cov = centered.T @ centered / count
    np.fill_diagonal(cov, 0)
    grad_cov = 0.24 * centered @ cov / (count * dims)
    penalty = 0.8 * margin.mean() + 0.06 * (cov ** 2).sum() / dims
    return grad_std + grad_cov, float(penalty)


def train(rows, config, seed, epochs):
    if config not in CONFIGS or len(rows) < 4 or not 1 <= epochs <= 1000:
        raise ContractError("Configuration d’apprentissage invalide.")
    rng = np.random.default_rng(seed)
    encoder = rng.normal(0, 0.36, SHAPES["encoder"]).astype(np.float32)
    target = encoder.copy()
    predictor = (np.eye(DIM_LATENT) + rng.normal(0, 0.08, SHAPES["predictor"])).astype(np.float32)
    model = LatentModel(config, encoder, target, predictor)
    contexts = features([row.situation.text() for row in rows])
    targets = features([row.cible for row in rows])
    means = [np.zeros_like(encoder), np.zeros_like(predictor)]
    seconds = [np.zeros_like(encoder), np.zeros_like(predictor)]
    step = 0
    losses = []
    for _ in range(epochs):
        order = rng.permutation(len(rows))
        epoch_losses = []
        for batch in np.array_split(order, max(1, len(rows) // 15)):
            x = contexts[batch]
            z = model.embeddings(x)
            pred = z @ predictor
            residual = pred - model.encode_target(targets[batch])
            d_pred = 2 * residual / residual.size
            d_z, penalty = variance_gradient(z)
            gradients = [x.T @ ((d_pred @ predictor.T + d_z) * (1 - z ** 2)), z.T @ d_pred]
            step += 1
            for i, (param, grad) in enumerate(zip((encoder, predictor), gradients, strict=True)):
                means[i] = 0.9 * means[i] + 0.1 * grad
                seconds[i] = 0.999 * seconds[i] + 0.001 * grad ** 2
                corrected = means[i] / (1 - 0.9 ** step)
                scale = np.sqrt(seconds[i] / (1 - 0.999 ** step)) + 1e-8
                param -= 0.006 * (corrected / scale + 0.005 * param)
            if config == "ema-24":
                target *= 0.985
                target += 0.015 * encoder
            epoch_losses.append((float(np.mean(residual ** 2)), penalty))
        losses.append([float(x) for x in np.mean(epoch_losses, axis=0)])
    return model, losses


def save(model, directory, metadata):
    directory.mkdir(parents=True, exist_ok=False)
    path = directory / "weights.npz"
    np.savez(path, **{key: getattr(model, key) for key in SHAPES})
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = {
        "schema": SCHEMA, "config": model.config, "sha256": digest,
        "provenance": "Corpus synthétique P5", "dimensions": [DIM_INPUT, DIM_LATENT],
        **metadata,
    }
    (directory / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                                             encoding="utf-8")
    return manifest


def load(directory):
    try:
        with (Path(directory) / "manifest.json").open("rb") as entry:
            manifest = json.loads(entry.read(16385))
        if (not isinstance(manifest, dict) or manifest.get("schema") != SCHEMA
                or manifest.get("config") not in CONFIGS or manifest.get("dimensions") != [DIM_INPUT, DIM_LATENT]
                or manifest.get("provenance") != "Corpus synthétique P5"):
            raise ContractError("Manifeste JEPA incompatible.")
        with (Path(directory) / "weights.npz").open("rb") as entry:
            raw = entry.read(MAX_BYTES + 1)
        digest = hashlib.sha256(raw).hexdigest()
        if len(raw) > MAX_BYTES or manifest.get("sha256") != digest:
            raise ContractError("Empreinte ou taille des poids JEPA invalide.")
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            blobs = archive.infolist()
            if (len(blobs) != len(SHAPES) or {x.filename for x in blobs} != {key + ".npy" for key in SHAPES}
                    or sum(x.file_size for x in blobs) > MAX_BYTES):
                raise ContractError("Structure des poids JEPA invalide.")
            arrays = {}
            for key, expected in SHAPES.items():
                with archive.open(key + ".npy") as entry:
                    if np.lib.format.read_magic(entry) != (1, 0):
                        raise ContractError("Version du tableau de poids JEPA incompatible.")
                    shape, fortran_order, dtype = np.lib.format.read_array_header_1_0(entry)
                    if shape != expected or dtype != np.float32 or fortran_order:
                        raise ContractError("Dimensions ou type des poids JEPA incompatibles.")
                    data = entry.read()
                    if len(data) != expected[0] * expected[1] * dtype.itemsize:
                        raise ContractError("Taille du tableau de poids JEPA incompatible.")
                    array = np.frombuffer(data, dtype=dtype).reshape(expected)
                    if not np.isfinite(array).all():
                        raise ContractError("Valeurs des poids JEPA incompatibles.")
                    arrays[key] = array
    except (OSError, KeyError, UnicodeError, zipfile.BadZipFile, ValueError) as exc:
        if isinstance(exc, ContractError):
            raise
        raise ContractError("Impossible de charger les poids JEPA : " + str(exc)) from exc
    return LatentModel(manifest["config"], **arrays, identity=f"P5 {manifest['config']} · {digest[:12]}", metadata=manifest)
