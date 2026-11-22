"""Recette navigateur de P6.1, avec transitions du compagnon et diagnostic local."""

import argparse
import json
from pathlib import Path
import tempfile

from playwright.sync_api import expect, sync_playwright

from p6_browser import SIZES, interactions, layouts, live_provenance
from tutor_browser import ROOT, local_server, protect_page


POSES = ("accueil", "repos", "ecoute", "reflexion", "explication", "validation", "encouragement")


def companion(browser, origin, output):
    page = browser.new_page(viewport={"width": 1672, "height": 941}, device_scale_factor=1)
    external, errors = protect_page(page, origin)
    # Observer les états sur un vrai dialogue. Délayer l’affichage de la réponse HTTP réelle pour capter la réflexion.
    page.add_init_script("""
      const originalFetch = window.fetch;
      window.fetch = async (target, options) => {
        const response = await originalFetch(target, options);
        if (target === '/api/guide') await new Promise(resolve => setTimeout(resolve, 750));
        return response;
      };
      window.poses = [];
      new MutationObserver(records => {
        for (const item of records) {
          if (item.target.id === 'scene' && item.attributeName === 'data-pose') window.poses.push(item.target.dataset.pose);
        }
      }).observe(document, {subtree: true, attributes: true});
    """)
    page.goto(origin + "/atelier")
    scene = page.locator("#scene")
    expect(scene).to_have_attribute("data-pose", "accueil")
    expect(page.locator("#model-state")).to_have_text("Parcours prêt")
    expect(scene).to_have_attribute("data-pose", "repos", timeout=13000)
    question = page.get_by_label("Ta question ou ton observation")
    button = page.get_by_role("button", name="Demander un indice")
    question.fill("Par où commencer ?")
    expect(scene).to_have_attribute("data-pose", "ecoute")
    button.click()
    expect(scene).to_have_attribute("data-pose", "reflexion")
    assert scene.locator(".companion-eyes").evaluate("(el) => el.getAnimations().length") >= 1
    expect(scene).to_have_attribute("data-pose", "explication")
    hand = scene.locator(".companion-hand")
    assert hand.evaluate("(el) => getComputedStyle(el).animationName") == "geste"
    # Capturer un instant du geste synchronisé par la Web Animations API, sans remplacer la réponse de l’atelier.
    hand.evaluate("(el) => el.getAnimations().forEach(a => { a.pause(); a.currentTime = 520; })")
    assert hand.evaluate("(el) => getComputedStyle(el).transform") != "none"
    scene.screenshot(path=output / "compagnon-explication.png")
    question.fill("Avec [-4, -2], la fonction renvoie 0.")
    button.click()
    expect(scene).to_have_attribute("data-pose", "validation")
    expect(scene).to_have_attribute("data-pose", "encouragement")
    expect(page.locator(".assistant")).to_have_count(2)
    page.emulate_media(reduced_motion="reduce")
    assert hand.evaluate("(el) => getComputedStyle(el).animationName") == "none"
    page.get_by_role("button", name="Paramètres").click()
    page.get_by_text("Diagnostic des moteurs", exact=True).click()
    version = json.loads((ROOT / "distribution" / "lock.json").read_text(encoding="utf-8"))["version"]
    expect(page.locator("#diagnostic-build")).to_contain_text(f"Version {version} · build ")
    expect(page.locator("#diagnostic-checks")).to_contain_text("Inférence validée · non confirmé")
    expect(page.locator("#diagnostic-turn")).to_contain_text("JEPA non sollicité")
    expect(page.locator("#diagnostic-turn")).to_contain_text("Question retenue")
    assert not external and not errors, (external, errors)
    states = page.evaluate("window.poses")
    assert set(POSES) <= set(states), states
    (output / "compagnon-transitions.json").write_text(json.dumps(states, ensure_ascii=False) + "\n", encoding="utf-8")
    page.close()


def browser_scales(browser, origin, output):
    for factor in (1.25, 1.5):
        page = browser.new_page(viewport={"width": 1672, "height": 941}, device_scale_factor=factor,
                                reduced_motion="reduce")
        external, errors = protect_page(page, origin)
        page.goto(origin + "/atelier")
        expect(page.locator("#model-state")).to_have_text("Parcours prêt")
        assert page.evaluate("devicePixelRatio") == factor
        assert page.evaluate("document.documentElement.scrollWidth === innerWidth")
        assert page.get_by_role("button", name="Demander un indice").is_enabled()
        page.screenshot(path=output / f"echelle-navigateur-{round(factor * 100)}.png", animations="disabled")
        assert not external and not errors, (external, errors)
        page.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--chromium", type=Path)
    parser.add_argument("--assets", type=Path)
    parser.add_argument("--weights", type=Path)
    args = parser.parse_args()
    if bool(args.assets) != bool(args.weights):
        parser.error("--assets et --weights sont requis ensemble.")
    args.output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp, local_server(Path(tmp), "smol") as origin, sync_playwright() as p:
        browser = p.chromium.launch(executable_path=args.chromium)
        layouts(browser, origin, args.output, sizes=(SIZES[0], (1920, 1080), *SIZES[1:]))
        interactions(browser, origin)
        companion(browser, origin, args.output)
        browser_scales(browser, origin, args.output)
        if args.assets:
            with local_server(args.assets, "smol", "--p5", "c", "--jepa", str(args.weights), verify_shutdown=True) as live:
                live_provenance(browser, live, args.output)
        browser.close()
    print("P6.1 : sept tailles, trois thèmes, sept états du compagnon, mouvement réduit et diagnostic.")


if __name__ == "__main__":
    main()
