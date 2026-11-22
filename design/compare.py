"""Comparaison reproductible de deux vues P6 à 1672 × 941, sans masque."""

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image


SIZE = (1672, 941)
ZONES = {
    "entete": (0, 0, 1672, 86),
    "scene": (0, 86, 881, 611),
    "personnage": (22, 175, 515, 610),
    "bulle": (479, 103, 803, 357),
    "editeur": (20, 611, 428, 924),
    "exercice": (438, 611, 870, 777),
    "progression": (438, 785, 870, 924),
    "dialogue": (881, 106, 1397, 924),
    "moteurs": (1409, 122, 1660, 269),
    "explication": (1409, 286, 1660, 524),
    "jepa": (1409, 542, 1660, 807),
}


def rgba(path):
    with Image.open(path) as image:
        if image.size != SIZE:
            raise SystemExit(f"{path}: dimensions {image.size} au lieu de {SIZE}.")
        return image.convert("RGB")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path,
                        default=Path(__file__).with_name("reference") / "REFERENCE_VISUELLE_VALIDEE.png")
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    ref, actual = rgba(args.reference), rgba(args.capture)
    half = (SIZE[0] // 2, SIZE[1] // 2)
    side = Image.new("RGB", SIZE, "#0a192b")
    for index, source in enumerate((ref, actual)):
        side.paste(source.resize(half, Image.Resampling.LANCZOS), (index * half[0], (SIZE[1] - half[1]) // 2))
    side.save(args.output / "cote-a-cote.png")
    side_full = Image.new("RGB", (SIZE[0] * 2, SIZE[1]))
    side_full.paste(ref, (0, 0))
    side_full.paste(actual, (SIZE[0], 0))
    side_full.save(args.output / "cote-a-cote-1x.png")
    Image.blend(ref, actual, .5).save(args.output / "superposition-50.png")

    abs_diff = np.abs(np.asarray(ref, dtype=np.int16) - np.asarray(actual, dtype=np.int16))
    mean = abs_diff.mean(axis=2)
    heat = np.minimum(mean * 3, 255).astype(np.uint8)
    # Noir si identique, rouge et jaune pour les écarts croissants, saturation à 85/255.
    heatmap = np.stack((heat, np.maximum(heat.astype(np.int16) - 100, 0).astype(np.uint8),
                        np.zeros_like(heat)), axis=-1)
    Image.fromarray(heatmap).save(args.output / "carte-ecarts.png")

    records = {}
    for name, (x0, y0, x1, y1) in {"ensemble": (0, 0, *SIZE), **ZONES}.items():
        data = mean[y0:y1, x0:x1]
        records[name] = {"reference_px": [x0, y0, x1 - x0, y1 - y0],
                         "reference_relative": [round(x0 / SIZE[0], 4), round(y0 / SIZE[1], 4),
                                                round((x1 - x0) / SIZE[0], 4), round((y1 - y0) / SIZE[1], 4)],
                         "mae_rgb_0_255": round(float(data.mean()), 3),
                         "pixels_ecart_gt_24_pct": round(float((data > 24).mean()) * 100, 2)}
    (args.output / "ecarts.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
