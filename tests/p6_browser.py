"""Recette P6 des zones, des états locaux, du clavier et des formats cibles."""

import argparse
import json
from pathlib import Path
import tempfile

from playwright.sync_api import expect, sync_playwright

from tutor_browser import ROOT, local_server, protect_page


SIZES = ((1672, 941), (1440, 900), (1366, 768), (1024, 768), (390, 844), (360, 800))
ZONES = {"entete": ".topbar", "scene": ".scene", "personnage": ".scene > img", "bulle": ".speech",
          "editeur": ".editor-panel", "exercice": "#exercise-panel", "progression": ".learning",
          "dialogue": ".conversation", "moteurs": ".engines", "explication": ".how", "jepa": ".research" }


def contrast(page, selector, foreground, background):
    scores = page.locator(selector).evaluate("(el, v) => v.map(x => getComputedStyle(el).getPropertyValue(x).trim())",
                                             [foreground, background])

    def luminance(hex_color):
        if len(hex_color) == 4:
            hex_color = "#" + "".join(char * 2 for char in hex_color[1:])
        channels = (int(hex_color[index:index + 2], 16) / 255 for index in (1, 3, 5))
        red, green, blue = (x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in channels)
        return .2126 * red + .7152 * green + .0722 * blue
    low, high = sorted(luminance(score) for score in scores)
    return (high + .05) / (low + .05)


def layouts(browser, origin, output, *, sizes=SIZES):
    report = {}
    for width, height in sizes:
        page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1,
                                reduced_motion="reduce")
        external, errors = protect_page(page, origin)
        page.goto(origin + "/atelier")
        expect(page.locator("#model-state")).to_have_text("Parcours prêt")
        expect(page.locator("#mode")).to_have_value("guided")
        expect(page.locator("#hybrid-badge")).to_be_hidden()
        expect(page.locator("#llm-line")).to_have_attribute("data-state", "absent")
        expect(page.locator("#jepa-line")).to_have_attribute("data-state", "inactive")
        for theme, selector in (("sombre", "Sombre"), ("clair", "Clair"), ("projecteur", "Projecteur")):
            page.get_by_role("button", name=selector, exact=True).click()
            assert page.evaluate("document.documentElement.scrollWidth === innerWidth"), (width, theme)
            assert page.locator("#code").evaluate("(el) => el.clientWidth > 140 && el.clientHeight > 100")
            assert page.get_by_role("button", name="Exécuter", exact=True).is_enabled()
            assert page.get_by_role("button", name="Demander un indice").is_enabled()
            box = page.locator(".editor-actions").bounding_box()
            for button in page.locator(".editor-actions button").all():
                item = button.bounding_box()
                assert item["x"] + item["width"] <= box["x"] + box["width"] + 1, (width, theme, box, item)
            assert contrast(page, "#highlight", "--code-keyword", "--code-bg") >= 4.5
            assert contrast(page, "body", "--text", "--panel") >= 4.5
            assert min(contrast(page, "#execute", "--button-text", stop) for stop in ("--button", "--button-end")) >= 4.5
            if theme == "sombre":
                report[f"{width}x{height}"] = {zone: page.locator(selector).bounding_box() for zone, selector in ZONES.items()}
            if theme == "sombre" or (width, height) == sizes[0]:
                filename = f"atelier-{width}x{height}-{theme}.png"
                page.screenshot(path=output / filename, animations="disabled",
                                full_page=width <= 1024 or theme == "projecteur")
        assert not external and not errors, (external, errors)
        page.close()
    (output / "geometrie.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                                          encoding="utf-8")


def interactions(browser, origin):
    context = browser.new_context(viewport={"width": 1672, "height": 941}, permissions=["clipboard-read", "clipboard-write"])
    page = context.new_page()
    external, errors = protect_page(page, origin)
    requested = []
    page.on("request", lambda request: requested.append(request.url))
    page.goto(origin + "/atelier")
    expect(page.locator("#model-state")).to_have_text("Parcours prêt")
    assert not any(url.endswith("/api/status") for url in requested)
    page.keyboard.press("Tab")
    expect(page.get_by_role("link", name="Aller à l’atelier")).to_be_focused()
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement.matches(':focus-visible')")
    expect(page.get_by_role("button", name="Paramètres")).to_have_accessible_name("Paramètres")
    page.get_by_role("button", name="Paramètres").click()
    expect(page.get_by_role("dialog")).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.get_by_role("button", name="Paramètres")).to_be_focused()
    page.get_by_role("button", name="Plein écran").click()
    expect(page.get_by_role("button", name="Plein écran")).to_have_attribute("aria-pressed", "true")
    page.get_by_role("button", name="Plein écran").click()
    expect(page.get_by_role("button", name="Plein écran")).to_have_attribute("aria-pressed", "false")
    editor = page.get_by_label("Code Python")
    first = editor.input_value()
    editor.fill(first + "\n# Dernière ligne")
    assert page.locator("#line-numbers").text_content().strip().endswith("7")
    expect(page.locator(".token-keyword").first).to_have_text("def")
    page.get_by_role("button", name="Copier le code").click()
    expect(page.locator("#editor-feedback")).to_have_text("Code copié.")
    # CF_UNICODETEXT représente les sauts de ligne en CRLF sous Windows.
    copied = page.evaluate("navigator.clipboard.readText()")
    assert copied.replace("\r\n", "\n") == editor.input_value()
    page.get_by_role("button", name="Exécuter", exact=True).click()
    expect(page.locator("#editor-feedback")).to_contain_text("Exécution Python indisponible")
    page.get_by_role("button", name="Réinitialiser", exact=True).click()
    expect(editor).to_have_value(first)

    text = "Mon programme répond toujours 0 quand les nombres sont négatifs."
    with page.expect_file_chooser() as chooser:
        page.get_by_role("button", name="Joindre un texte ou un fichier Python").click()
    chooser.value.set_files({"name": "observation.txt", "mimeType": "text/plain", "buffer": text.encode()})
    question = page.get_by_label("Ta question ou ton observation")
    expect(question).to_have_value(text)
    editor.fill(first + "\n# Analyse locale")
    with page.expect_response("**/api/guide") as pending:
        question.press("Control+Enter")
    body = pending.value.json()
    assert body["pedagogie"]["acquis"]["observed"]["tour"] == 1
    expect(editor).to_have_value(first + "\n# Analyse locale")
    expect(page.locator(".assistant .provenance")).to_contain_text("Règle pédagogique")
    expect(page.locator(".assistant .provenance")).not_to_contain_text("Reclassement JEPA enregistré")
    expect(page.locator("#stages li[data-state=done]")).to_have_count(1)
    page.get_by_text("Suivi enseignant", exact=True).click()
    expect(page.locator("#teacher-content")).to_contain_text("Identifier le résultat observé")
    page.get_by_role("button", name="Recommencer").click()
    expect(page.locator(".assistant")).to_have_count(0)
    page.get_by_role("link", name="Parcours", exact=True).click()
    expect(page.get_by_label("Exercice", exact=True)).to_be_focused()
    page.get_by_label("Classe", exact=True).select_option("terminale")
    expect(page.get_by_label("Exercice", exact=True)).to_have_value("recursivite-base")
    page.get_by_label("Mode d’aide").select_option("hybrid")
    expect(page.locator("#hybrid-badge")).to_be_hidden()
    expect(page.get_by_role("button", name="Demander un indice")).to_be_disabled()
    page.get_by_role("link", name="Laboratoire JEPA", exact=True).click()
    expect(page.get_by_text("Bénéfice JEPA non démontré")).to_be_visible()
    page.get_by_role("link", name="Ouvrir le professeur virtuel").click()
    page.get_by_role("link", name="Résultats", exact=True).click()
    expect(page.locator("#resultats")).to_be_visible()
    page.go_back()
    page.get_by_role("link", name="Ressources", exact=True).click()
    expect(page.get_by_role("heading", name="Ressources")).to_be_visible()
    page.go_back()
    page.locator("#scene").evaluate("(el) => el.dataset.pose = 'reflexion'")
    assert page.locator("#scene").evaluate("(el) => getComputedStyle(el, '::after').animationName") == "hologram"
    page.emulate_media(reduced_motion="reduce")
    assert page.locator("#scene").evaluate("(el) => getComputedStyle(el, '::after').animationName") == "none"
    assert not external and not errors, (external, errors)
    context.close()


def live_provenance(browser, origin, output):
    page = browser.new_page(viewport={"width": 1672, "height": 941}, device_scale_factor=1)
    external, errors = protect_page(page, origin)
    page.goto(origin + "/atelier")
    expect(page.locator("#model-state")).to_have_text("Parcours prêt")
    expect(page.locator("#jepa-line")).to_have_attribute("data-state", "ready")
    expect(page.locator("#llm-line")).to_have_attribute("data-state", "standby")
    expect(page.locator("#hybrid-badge")).to_be_hidden()
    page.get_by_label("Mode d’aide").select_option("hybrid")
    expect(page.locator("#hybrid-badge")).to_have_text("Hybride expérimental", timeout=95000)
    replies = json.loads((ROOT / "p4/reference.json").read_text(encoding="utf-8"))[:2]
    for text in replies:
        page.get_by_label("Ta question ou ton observation").fill(text)
        with page.expect_response("**/api/hybrid", timeout=115000) as pending:
            page.get_by_role("button", name="Demander un indice").click()
        data = pending.value.json()
        assert pending.value.ok, data
    assert data["pedagogie"]["derniere_intervention"]["differe_des_regles"]
    assert data["generation"] == "affiche"
    source = page.locator(".assistant .provenance").last
    expect(source).to_contain_text("Reclassement JEPA enregistré")
    expect(source).to_contain_text("SmolLM3")
    page.screenshot(path=output / "hybride-reel.png", animations="disabled")
    assert not external and not errors, (external, errors)
    page.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chromium", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--assets", type=Path)
    parser.add_argument("--weights", type=Path)
    args = parser.parse_args()
    if bool(args.assets) != bool(args.weights):
        parser.error("La capture réelle exige les deux chemins --assets et --weights.")
    args.output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as empty, local_server(Path(empty), "smol") as origin, sync_playwright() as p:
        browser = p.chromium.launch(executable_path=args.chromium)
        layouts(browser, origin, args.output)
        interactions(browser, origin)
        if args.assets:
            with local_server(args.assets, "smol", "--p5", "c", "--jepa", str(args.weights), verify_shutdown=True) as live:
                live_provenance(browser, live, args.output)
        browser.close()
    print("P6 : six formats, 18 combinaisons de thème, navigation, clavier, presse-papier, états et parcours guidé.")


if __name__ == "__main__":
    main()
