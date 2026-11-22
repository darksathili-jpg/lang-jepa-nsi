"""Extraire des actifs dessinés de la maquette P6 verrouillée, sans la photo privée."""

import hashlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "design/reference/REFERENCE_VISUELLE_VALIDEE.png"
APP_ASSETS = ROOT / "app/assets"
SHA256 = "29a5bd4c27654317a7926797f40c818e871f03017e00ce08a56d6e463d4f517d"


def main():
    if hashlib.sha256(REFERENCE.read_bytes()).hexdigest() != SHA256:
        raise ValueError("La maquette P6 ne correspond pas au manifeste.")
    APP_ASSETS.mkdir(exist_ok=True)
    with Image.open(REFERENCE) as reference:
        if reference.size != (1672, 941):
            raise ValueError("Dimensions inhabituelles pour la maquette P6.")
        scene = reference.crop((0, 86, 881, 611))
        # Libérer uniquement la composition typographique à l'intérieur de la bulle.
        # Préserver son contour, le dessin et la position de la main.
        text_lines = ((532, 130, 617, 152), (532, 154, 713, 174), (543, 187, 747, 210),
                      (543, 211, 750, 233), (543, 235, 759, 256), (543, 259, 773, 281),
                      (543, 283, 765, 304))
        draw = ImageDraw.Draw(scene)
        for left, top, right, bottom in text_lines:
            draw.rectangle((left, top - 86, right, bottom - 86), fill=(253, 253, 253))
        scene.save(APP_ASSETS / "scene-bd.webp", lossless=True, method=6)
        # Repères du dessin P6, dans le système de coordonnées de la scène.
        for name, box, polygon in (
            ("regard", (304, 181, 517, 249), ((6, 26), (55, 14), (102, 16), (157, 14), (205, 28),
                                               (199, 48), (157, 60), (111, 50), (58, 57), (14, 46))),
            ("geste", (261, 368, 449, 525), ((28, 9), (56, 6), (65, 71), (89, 81), (146, 73),
                                               (175, 85), (170, 122), (122, 150), (26, 151), (8, 129))),
        ):
            detail = scene.crop(box).convert("RGBA")
            mask = Image.new("L", detail.size)
            ImageDraw.Draw(mask).polygon(polygon, fill=255)
            detail.putalpha(mask.filter(ImageFilter.GaussianBlur(3)))
            detail.save(APP_ASSETS / f"compagnon-{name}.webp", lossless=True, method=6)
        reference.crop((1416, 551, 1655, 725)).save(APP_ASSETS / "illustration-jepa.webp", lossless=True, method=6)
        reference.crop((908, 269, 955, 320)).save(APP_ASSETS / "portrait-bd.webp", lossless=True, method=6)

        mark = reference.crop((32, 9, 108, 85)).convert("RGBA")
        pixels = mark.load()
        for y in range(mark.height):
            for x in range(mark.width):
                r, g, b, _ = pixels[x, y]
                pixels[x, y] = r, g, b, min(255, max(0, 3 * (g - 55)))
        mark.save(APP_ASSETS / "marque-reseau.webp", lossless=True, method=6)


if __name__ == "__main__":
    main()
