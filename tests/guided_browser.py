"""Recette Chromium du guide indépendant des poids et du laboratoire."""

import argparse
from pathlib import Path
import tempfile

from playwright.sync_api import expect, sync_playwright

from tutor_browser import local_server, protect_page, themes


def complete(browser, origin, captures):
    page = browser.new_page(viewport={"width": 1360, "height": 950})
    external, errors = protect_page(page, origin)
    requested = []
    page.on("request", lambda request: requested.append(request.url))
    page.goto(origin)
    page.get_by_text("Résultats du pilote LANG-JEPA sur CPU").click()
    expect(page.get_by_text("Sortie JEPA enregistrée")).to_be_visible()
    if captures:
        page.locator(".jepa-results").screenshot(path=captures / "laboratoire-resultats.png")
    page.get_by_role("link", name="Ouvrir le professeur virtuel").click()
    expect(page.locator("#model-state")).to_have_text("Parcours prêt")
    expect(page.get_by_label("Exercice", exact=True)).to_have_value("maximum")
    code = page.get_by_label("Code Python")
    submit = page.get_by_role("button", name="Demander un indice")
    turns = (
        "Par où commencer ?", "Avec [-4, -2], la fonction renvoie 0.",
        "La valeur attendue sur [-4, -2] est -2.", "m reste à 0 car 0 est supérieur à -4 et à -2.",
        "Sur [-4, -2], j’obtiens -2 après ma modification.",
    )
    for index, question in enumerate(turns, 1):
        if index == 5:
            code.fill(code.input_value().replace("m = 0", "m = tab[0]"))
        page.get_by_label("Ta question ou ton observation").fill(question)
        with page.expect_response(lambda response: response.url.endswith("/api/guide")) as pending:
            submit.click()
        response = pending.value
        data = response.json()
        assert response.ok and data["stage"] == index, data
        expect(page.locator(".assistant")).to_have_count(index)
        expect(page.locator(".assistant").last).to_contain_text("Règle pédagogique")
        expect(page.locator(".assistant").last).to_contain_text("Aucune contribution de LANG-JEPA")
        expect(page.locator("#syntax")).to_contain_text("Analyse statique Python")
        print(index, f'{data["seconds"] * 1000:.3f} ms', data["indice"], data["question"], flush=True)
    expect(page.locator(".assistant").last).to_contain_text("liste non vide")
    expect(page.locator(".assistant").last).to_contain_text("[]")
    themes(page, captures)
    assert not any(url.endswith("/api/status") or url.endswith("/api/tutor") for url in requested)
    assert not external and not errors, (external, errors)
    page.close()


def mobile(browser, origin, captures):
    page = browser.new_page(viewport={"width": 390, "height": 900})
    external, errors = protect_page(page, origin)
    page.goto(origin + "/atelier")
    expect(page.locator("#model-state")).to_have_text("Parcours prêt")
    page.get_by_label("Classe", exact=True).select_option("terminale")
    expect(page.get_by_label("Exercice", exact=True)).to_have_value("recursivite-base")
    themes(page)
    if captures:
        page.screenshot(path=captures / "atelier-mobile.png", full_page=True)
    assert not external and not errors, (external, errors)
    page.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chromium")
    parser.add_argument("--captures", type=Path)
    args = parser.parse_args()
    if args.captures:
        args.captures.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright, tempfile.TemporaryDirectory() as empty:
        browser = playwright.chromium.launch(executable_path=args.chromium)
        with local_server(Path(empty), "smol") as origin:
            complete(browser, origin, args.captures)
            mobile(browser, origin, args.captures)
        browser.close()
    print("Chromium : cinq étapes guidées, deux niveaux, trois thèmes et aucun appel au modèle.")


if __name__ == "__main__":
    main()
