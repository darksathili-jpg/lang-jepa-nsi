"""Recette P5 réelle dans Chromium, avec poids vérifiés et réseau bloqué."""

import argparse
import json
from pathlib import Path
import re
import tempfile

from playwright.sync_api import expect, sync_playwright

from tutor_browser import ROOT, local_server, protect_page, themes


def absent(browser):
    with tempfile.TemporaryDirectory() as directory, local_server(Path(directory), "smol", "--p5", "c") as origin:
        page = browser.new_page(viewport={"width": 390, "height": 900})
        external, errors = protect_page(page, origin)
        page.goto(origin + "/atelier")
        page.get_by_label("Mode d’aide").select_option("hybrid")
        expect(page.locator("#jepa-status")).to_contain_text("JEPA absent")
        expect(page.get_by_role("button", name="Demander un indice")).to_be_disabled()
        page.get_by_label("Mode d’aide").select_option("guided")
        expect(page.locator("#model-state")).to_have_text("Parcours prêt")
        page.get_by_label("Classe", exact=True).select_option("terminale")
        expect(page.get_by_label("Exercice", exact=True)).to_have_value("recursivite-base")
        themes(page)
        assert not external and not errors, (external, errors)
        page.close()


def hybrid(browser, origin, output, captures, case):
    page = browser.new_page(viewport={"width": 1360, "height": 950})
    external, errors = protect_page(page, origin)
    page.goto(origin + "/atelier")
    page.get_by_label("Mode d’aide").select_option("hybrid")
    expect(page.locator("#model-state")).to_have_text("Modèle prêt", timeout=95000)
    expect(page.locator("#model-identity")).to_contain_text("SmolLM3-3B")
    status = page.locator("#jepa-status")
    expect(status).to_contain_text("JEPA prêt")
    expect(status).to_have_attribute("title", re.compile("P5"))
    expect(page.locator("#hybrid-badge")).to_have_text("Hybride expérimental")
    assert page.request.post(origin + "/api/hybrid", data={}, headers={"Origin": "https://externe.invalid"}).status == 403
    assert page.request.post(origin + "/api/hybrid", data={"question": "a" * (49 * 1024)},
                             headers={"Origin": origin}).status == 413
    submit = page.get_by_role("button", name="Demander un indice")
    editor = page.get_by_label("Code Python")
    original = editor.input_value()
    seen = set()
    changes = shown = 0
    teacher = page.get_by_text("Suivi enseignant", exact=True)
    for i, step in enumerate(case["tours"], 1):
        if step.get("code") == "corrige":
            editor.fill(original.replace("m = 0", "m = tab[0]"))
        page.get_by_label("Ta question ou ton observation").fill(step["texte"])
        with page.expect_response(lambda response: response.url.endswith("/api/hybrid"), timeout=115000) as pending:
            submit.click()
        response = pending.value
        data = response.json()
        assert response.ok, data
        output.write(json.dumps(dict(tour=i, eleve=step["texte"],
                                     reponse={k: v for k, v in data.items() if k != "session"}),
                                ensure_ascii=False) + "\n")
        output.flush()
        state = data["pedagogie"]
        print(i, state["objectif"], data["generation"], data["question"], flush=True)
        assert state["objectif"] == step["objectif"]
        if step.get("code") != "corrige":
            assert not re.search(r"tab\s*\[\s*0\s*\]|\bdef\s+maximum|premier élément|\bmax\s*\(",
                                 data["indice"] + " " + data["question"], re.I)
        if data["question"]:
            assert data["question"] not in seen
            seen.add(data["question"])
            decision = state["derniere_intervention"]
            assert decision["schema"] == 1 and decision["source"] == "jepa"
            changes += decision["differe_des_regles"]
        source = page.locator(".assistant .provenance").last
        if state["derniere_intervention"] and state["derniere_intervention"]["differe_des_regles"]:
            expect(source).to_contain_text("Reclassement JEPA enregistré")
        else:
            expect(source).to_contain_text("Aucun reclassement JEPA")
        if data["generation"] == "affiche":
            assert "SmolLM3" in data["provenance"]["hint"]
            expect(source).to_contain_text("SmolLM3")
            shown += 1
        else:
            expect(source).not_to_contain_text("SmolLM3")
        if i == 4:
            assert state["acquis"]["trace"]["tour"] == 4
            expect(page.locator("#pedagogical-objective")).to_contain_text("stratégie")
            teacher.click()
            expect(page.locator("#teacher-content")).to_contain_text("Aucun reclassement JEPA")
            expect(page.locator("#teacher-content")).to_contain_text("Acquis confirmés")
            themes(page, captures)
            teacher.click()
        if i == len(case["tours"]) - 2:
            assert "verification" not in state["acquis"]
        if i == len(case["tours"]) - 1:
            assert set(state["tests_declares"]) == {"[-4, -2]", "[3]"}
    assert changes > 0 and shown > 0, (changes, shown)
    assert not external and not errors, (external, errors)
    print(f"Chromium P5 : {len(case['tours'])} tours, {changes} questions reclassées, "
          f"{shown} indices SmolLM3 affichés.", flush=True)
    page.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chromium")
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--captures", type=Path)
    parser.add_argument("--dialogue", choices=("maximum-10", "maximum-20", "maximum-30"), default="maximum-10")
    args = parser.parse_args()
    if args.captures:
        args.captures.mkdir(parents=True, exist_ok=True)
    cases = json.loads((ROOT / "p5/dialogues.json").read_text(encoding="utf-8"))["dialogues"]
    case = next(item for item in cases if item["id"] == args.dialogue)
    with sync_playwright() as playwright, args.output.open("x", encoding="utf-8") as output:
        browser = playwright.chromium.launch(executable_path=args.chromium)
        absent(browser)
        with local_server(args.assets, "smol", "--p5", "c", "--jepa", str(args.weights), "--parcours-historique", verify_shutdown=True) as origin:
            hybrid(browser, origin, output, args.captures, case)
        browser.close()


if __name__ == "__main__":
    main()
