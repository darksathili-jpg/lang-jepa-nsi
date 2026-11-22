"""Rejoue le tour contextualisé dans les deux profils avec les ressources locales."""

import argparse
import json
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

from tutor_browser import local_server, protect_page


CONDITION = "Que donne la comparaison avec la valeur de départ quand la boucle rencontre -4 puis -2 ?"
FALSE = "toujours False"
CAUSE = "La condition est fausse, donc m = valeur ne s’exécute pas et m reste à zéro."


def replay(browser, origin, output, *, before=False, captures=None):
    for mode, endpoint in (("conversation", "tutor"), ("hybrid", "hybrid")):
        if before and mode != "conversation":
            continue
        page = browser.new_page(viewport={"width": 1660, "height": 940})
        external, errors = protect_page(page, origin)
        page.goto(origin + "/atelier")
        assert page.get_by_label("Mode d’aide").input_value() == "guided"
        page.get_by_label("Mode d’aide").select_option(mode)
        expect(page.locator("#model-state")).to_have_text("Modèle prêt", timeout=95000)
        if mode == "hybrid":
            expect(page.locator("#hybrid-badge")).to_have_text("Hybride expérimental")

        def send(text):
            target = page.get_by_label("Ta question ou ton observation")
            target.fill(text)
            with page.expect_response(lambda response: response.url.endswith("/api/" + endpoint), timeout=115000) as pending:
                page.get_by_role("button", name="Demander un indice").click()
            response = pending.value
            data = response.json()
            assert response.ok, data
            bubble = page.locator(".assistant").last
            expect(bubble).to_contain_text(data["feedback"])
            visible_source = bubble.locator(".provenance").inner_text()
            print(json.dumps({"profil": mode, "eleve": text, "source_affichee": visible_source,
                              "reponse": {key: value for key, value in data.items() if key != "session"}},
                             ensure_ascii=False), file=output, flush=True)
            return data, visible_source

        rows = [send("Mon programme répond toujours 0 quand les nombres sont négatifs."),
                send("Avec la fonction maximum c'est 0 mais elle devrait répondre -2.")]
        for _ in range(3):
            if rows[-1][0]["question"] == CONDITION:
                break
            rows.append(send("toujours 0 avec ma fonction"))
        assert rows[-1][0]["question"] == CONDITION, rows[-1][0]["question"]
        observed = send(FALSE)
        rows.append(observed)
        data, _ = observed
        state = data["pedagogie"]
        if captures:
            page.screenshot(path=captures / f"{mode}-comparaison.png")
        if before:
            assert state["evaluation"]["statut"] == "hors_sujet", state["evaluation"]
            assert "trace" not in state["acquis"]
        else:
            assert state["objectif"] == "trace" and "trace" not in state["acquis"]
            assert state["faits_trace"]["comparaison_fausse"]["extrait"] == FALSE
            assert "fausse" in data["feedback"] and "-4" in data["feedback"] and "-2" in data["feedback"]
            assert "m = valeur" in data["question"] and any(word in data["question"] for word in ("condition", "test"))
            rows.append(send(CAUSE))
            data, _ = rows[-1]
            assert data["pedagogie"]["objectif"] in {"assumption", "strategy"}
            assert data["pedagogie"]["acquis"]["trace"]["extrait"] == CAUSE
            assert data["question"] != CONDITION and "tab[0]" not in data["question"] + data["indice"]
            if captures:
                page.screenshot(path=captures / f"{mode}-raisonnement.png")
        decisions = [bool((data["pedagogie"]["derniere_intervention"] or {}).get("differe_des_regles"))
                     for data, _ in rows]
        assert (any(decisions) and not all(decisions)) if mode == "hybrid" else not any(decisions)
        for (data, source), reclassified in zip(rows, decisions):
            assert ("Reclassement JEPA enregistré" in source) == reclassified, source
            assert ("SmolLM3" in source) == (data["generation"] == "affiche"), source
        assert not external and not errors, (external, errors)
        page.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chromium", type=Path)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--captures", type=Path)
    parser.add_argument("--before", action="store_true")
    args = parser.parse_args()
    if args.captures:
        args.captures.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright, args.output.open("x", encoding="utf-8") as output:
        browser = playwright.chromium.launch(executable_path=args.chromium)
        with local_server(args.assets, "smol", "--p5", "c", "--jepa", str(args.weights)) as origin:
            replay(browser, origin, output, before=args.before, captures=args.captures)
        browser.close()


if __name__ == "__main__":
    main()
