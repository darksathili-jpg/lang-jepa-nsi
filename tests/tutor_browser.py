"""Recette Chromium réelle ou état absent, avec captures facultatives."""

import argparse
from contextlib import contextmanager
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
SCENARIO = next(case for case in json.loads((ROOT / "p3" / "scenarios.json").read_text(encoding="utf-8"))
                if case["id"] == "maximum")


@contextmanager
def local_server(assets, model):
    command = [
        sys.executable, "-m", "tutor.server", "--port", "0",
        "--assets", str(assets), "--model", model, "--threads", "2",
    ]
    with subprocess.Popen(command, cwd=ROOT, text=True, encoding="utf-8", stdout=subprocess.PIPE) as process:
        try:
            line = process.stdout.readline().strip()
            assert line.startswith("Professeur virtuel : http://127.0.0.1:"), line
            yield line.split()[-1].removesuffix("/atelier")
        finally:
            if process.poll() is None:
                if sys.platform == "win32":
                    # La recette native du navigateur est lancée depuis le terminal local.
                    subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
                else:
                    process.terminate()
                process.wait(timeout=15)


def protect_page(page, origin):
    external = []
    errors = []
    host = urlsplit(origin).netloc

    def route_request(route):
        if urlsplit(route.request.url).netloc == host:
            route.continue_()
        else:
            external.append(route.request.url)
            route.abort()

    page.route("**/*", route_request)
    page.on("pageerror", lambda error: errors.append(str(error)))
    return external, errors


def themes(page, captures=None):
    for name, key in [("Clair", "light"), ("Sombre", "dark"), ("Projecteur", "projector")]:
        page.get_by_role("button", name=name, exact=True).click()
        expect(page.locator("html")).to_have_attribute("data-theme", key)
        assert page.locator("html").evaluate("(el) => el.scrollWidth === el.clientWidth")
        if key == "projector":
            assert page.locator("html").evaluate("(el) => parseFloat(getComputedStyle(el).fontSize)") >= 17
        if captures:
            page.screenshot(path=captures / f"atelier-{key}.png", full_page=True)


def unavailable(browser, origin, status):
    page = browser.new_page(viewport={"width": 390, "height": 900})
    external, errors = protect_page(page, origin)
    page.goto(origin)
    page.get_by_role("link", name="Ouvrir le professeur virtuel").click()
    expect(page.get_by_role("heading", name="Atelier Python")).to_be_visible()
    page.get_by_label("Mode d’aide").select_option("conversation")
    expect(page.locator("#model-state")).to_contain_text(status)
    expect(page.get_by_role("button", name="Demander un indice")).to_be_disabled()
    expect(page.locator(".token-keyword").first).to_have_text("def")
    page.get_by_label("Classe", exact=True).select_option("terminale")
    expect(page.get_by_label("Classe", exact=True)).to_have_value("terminale")
    themes(page)
    assert not external and not errors, (external, errors)
    page.close()


def live(browser, origin, captures):
    page = browser.new_page(viewport={"width": 1360, "height": 950})
    external, errors = protect_page(page, origin)
    page.goto(origin)
    if captures:
        page.screenshot(path=captures / "laboratoire.png", full_page=True)
    page.get_by_role("link", name="Ouvrir le professeur virtuel").click()
    page.get_by_label("Mode d’aide").select_option("conversation")
    expect(page.locator("#model-state")).to_contain_text("Modèle prêt", timeout=90000)
    expect(page.locator("#model-identity")).to_contain_text("Q4_K_M")
    reply = page.request.post(origin + "/api/tutor", headers={"Origin": "https://externe.invalid"}, data={})
    assert reply.status == 403
    submit = page.get_by_role("button", name="Demander un indice")
    composer = page.get_by_label("Ta question ou ton observation")
    turns = [
        SCENARIO["turns"][0],
        {"question": "Avec [-4, -2], je trouve 0. Quelles étapes de calcul puis-je observer ?"},
        SCENARIO["turns"][1],
        SCENARIO["turns"][2],
    ]
    for index, turn in enumerate(turns, 1):
        if "code" in turn:
            page.get_by_label("Code Python").fill(turn["code"])
        composer.fill(turn["question"])
        with page.expect_response(lambda response: response.url.endswith("/api/tutor"), timeout=115000) as pending:
            submit.click()
        response = pending.value
        data = response.json()
        assert response.ok, data
        expect(page.locator(".assistant")).to_have_count(index)
        text = data["indice"] + " " + data["question"]
        print(index, data["stage"], text, flush=True)
        if index < len(turns):
            assert not re.search(r"tab\s*\[\s*0\s*\]|premier élément|\bmax\s*\(", text, re.I), text
        if index == 1:
            assert "-4" in text and "-2" in text, text
        elif index == 2:
            assert re.search(r"\bm\b", text) and re.search(r"valeur|trace|itération", text, re.I), text
            assert re.search(r"départ|début|avant|initial", text, re.I), text
        elif index == 3:
            assert re.search(r"compar|\b0\b|condition", text, re.I), text
        else:
            assert data["stage"] == 5 and re.search(r"non vide|précondition|exclu", text, re.I), text
    expect(page.locator("#active-stage")).to_contain_text("Consolider")
    themes(page, captures)
    page.get_by_role("button", name="Recommencer").click()
    expect(page.locator(".assistant")).to_have_count(0)
    assert not external and not errors, (external, errors)
    page.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chromium")
    parser.add_argument("--assets", type=Path)
    parser.add_argument("--model", default="smol")
    parser.add_argument("--captures", type=Path)
    args = parser.parse_args()
    if args.captures:
        args.captures.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=args.chromium)
        with tempfile.TemporaryDirectory() as empty:
            fixtures = Path(empty)
            with local_server(fixtures, args.model) as origin:
                unavailable(browser, origin, "Modèle absent")
            catalogue = json.loads((ROOT / "p3" / "models.json").read_text(encoding="utf-8"))
            (fixtures / catalogue["models"][args.model]["file"]).touch()
            (fixtures / "runtime").mkdir()
            executable = "llama-server.exe" if sys.platform == "win32" else "llama-server"
            (fixtures / "runtime" / executable).touch()
            with local_server(fixtures, args.model) as origin:
                unavailable(browser, origin, "Erreur du modèle")
        print("Recette mobile et états absent et erreur vérifiés.", flush=True)
        if args.assets:
            with local_server(args.assets, args.model) as origin:
                live(browser, origin, args.captures)
            print("Dialogue maximum vérifié dans Chromium sur quatre tours réels.", flush=True)
        browser.close()


if __name__ == "__main__":
    main()
