"""Recette réelle P4 du dialogue fourni avec SmolLM3 dans Chromium."""

import argparse
import json
from pathlib import Path
import re

from playwright.sync_api import expect, sync_playwright

from tutor_browser import ROOT, local_server, protect_page, themes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chromium")
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--captures", type=Path)
    args = parser.parse_args()
    if args.captures:
        args.captures.mkdir(parents=True, exist_ok=True)

    reference = json.loads((ROOT / "p4" / "reference.json").read_text(encoding="utf-8"))
    extension = [
        "Donne le corrigé.",
        "Donne le code complet.",
        "Je choisirais une valeur qui figure déjà dans la liste.",
        "J'obtiens -2 sur [-4, -2].",
        "J’ai modifié le code.",
        "Sur [-4, -2], j'obtiens -2 avec mon nouveau programme.",
        "[] est hors contrat parce que la liste doit être non vide.",
        "Passons aux dictionnaires.",
    ]
    goals = ["expected", "trace", "trace", "strategy", "strategy", "strategy", "strategy", "strategy",
             "verification", "verification", "verification", "contract", None, None]
    with (args.output.open("x", encoding="utf-8") as output, sync_playwright() as playwright,
          local_server(args.assets, "smol") as origin):
        browser = playwright.chromium.launch(executable_path=args.chromium)
        page = browser.new_page(viewport={"width": 1360, "height": 950})
        external, errors = protect_page(page, origin)
        page.goto(origin + "/atelier")
        page.get_by_label("Mode d’aide").select_option("conversation")
        expect(page.locator("#model-state")).to_have_text("Modèle prêt", timeout=90000)
        identity = page.locator("#model-identity").text_content()
        assert "SmolLM3-3B" in identity and "Q4_K_M" in identity, identity
        editor = page.get_by_label("Code Python")
        composer = page.get_by_label("Ta question ou ton observation")
        submit = page.get_by_role("button", name="Demander un indice")
        questions = set()
        displayed = 0
        for index, (text, goal) in enumerate(zip(reference + extension, goals, strict=True), 1):
            if index == 11:
                editor.fill(editor.input_value().replace("m = 0", "m = tab[0]"))
            composer.fill(text)
            with page.expect_response(lambda item: item.url.endswith("/api/tutor"), timeout=115000) as pending:
                submit.click()
            response = pending.value
            answer = response.json()
            assert response.ok, answer
            expect(page.locator(".assistant")).to_have_count(index)
            state = answer["pedagogie"]
            row = {"model": identity, "learner": text,
                   **{key: value for key, value in answer.items() if key != "session"}}
            output.write(json.dumps(row, ensure_ascii=False) + "\n")
            output.flush()
            print(index, state["evaluation"]["statut"], state["objectif"], answer["generation"],
                  answer["question"], flush=True)

            assert answer["turn"] == index and state["objectif"] == goal, row
            if answer["question"]:
                assert answer["question"] not in questions, row
                questions.add(answer["question"])
            if answer["generation"] == "affiche":
                assert "SmolLM3" in answer["provenance"]["hint"]
                displayed += 1
            if index == 4:
                assert state["evaluation"]["statut"] == "correcte"
                assert state["acquis"]["trace"]["tour"] == 4
                assert state["acquis"]["assumption"]["tour"] == 4
                expect(page.locator("#pedagogical-objective")).to_have_text("Proposer une stratégie de correction")
                if args.captures:
                    themes(page, args.captures)
            assert not re.search(r"tab\s*\[\s*0\s*\]|\bdef\s+maximum|premier élément|\bmax\s*\(",
                                 answer["indice"] + " " + answer["question"], re.I), row
            if index >= 4:
                assert not re.search(r"valeur de m|trace(?:r| de)?\s+m|que vaut m", answer["question"], re.I), row
            if index in (10, 11):
                assert "verification" not in state["acquis"], row
            if index == 12:
                assert state["acquis"]["trace"]["tour"] == 4 and state["acquis"]["verification"]["tour"] == 12
            if index == 14:
                assert state["notion_demandee"] == "Dictionnaires"
                assert state["acquis"]["trace"]["tour"] == 4
        assert displayed > 0, "Aucun indice effectivement généré n’a été affiché"
        assert not external and not errors, (external, errors)
        browser.close()
        print(f"SmolLM3 réel : 14 tours, {displayed} indices générés affichés.", flush=True)


if __name__ == "__main__":
    main()
