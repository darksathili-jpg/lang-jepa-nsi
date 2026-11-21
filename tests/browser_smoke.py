"""Recette navigateur facultative. Nécessite Playwright et Chromium."""

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright


APP = Path(__file__).resolve().parents[1] / "app"


def check_page(browser, url, width):
    page = browser.new_page(viewport={"width": width, "height": 900})
    requests = []
    errors = []
    origin = urlsplit(url).netloc

    def route_request(route):
        request = route.request
        requests.append((request.method, request.url))
        if urlsplit(request.url).netloc == origin:
            route.continue_()
        else:
            route.abort()

    page.route("**/*", route_request)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(url)
    expect(page.get_by_role("heading", name="Laboratoire Python")).to_have_count(1)
    page.get_by_role("button", name="Mode sombre").click()
    expect(page.get_by_role("button", name="Mode clair")).to_be_visible()
    expect(page.locator("#questions fieldset").first).to_have_css("background-color", "rgb(28, 43, 64)")
    page.get_by_role("button", name="Mode clair").click()
    page.get_by_role("button", name="Projecteur", exact=True).click()
    expect(page.locator("body")).to_have_class("projector")
    page.get_by_role("button", name="Projecteur", exact=True).click()
    for question, answer in enumerate((1, 0, 1)):
        page.locator(f'input[name="q{question}"][value="{answer}"]').check()
    expect(page.locator("#score")).to_contain_text("3/3")

    page.get_by_role("link", name="Laboratoire", exact=True).click()
    fields = {
        "Énoncé": "Chercher le maximum d’une liste.",
        "Code Python": "raise RuntimeError('Cette saisie doit rester du texte.')",
        "Ta question": "Comment tester les valeurs négatives ?",
    }
    for label, value in fields.items():
        page.get_by_label(label, exact=True).fill(value)
    page.get_by_role("button", name="Vérifier la disponibilité du tuteur").click()
    expect(page.locator("#status")).to_contain_text("aucun checkpoint LANG-JEPA")
    for label, value in fields.items():
        expect(page.get_by_label(label, exact=True)).to_have_value(value)
    assert not errors, errors
    assert set(requests) == {
        ("GET", url), ("GET", url + "app.js"), ("GET", url + "style.css")
    }, requests
    assert page.locator("html").evaluate("(el) => el.scrollWidth === el.clientWidth")
    page.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chromium", help="Chemin d’un Chromium déjà installé.")
    args = parser.parse_args()
    handler = partial(SimpleHTTPRequestHandler, directory=APP)
    with ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(executable_path=args.chromium)
                for width in (1280, 390):
                    check_page(browser, f"http://127.0.0.1:{server.server_port}/", width)
                    print(f"Recette Chromium réussie à {width} px.")
                browser.close()
        finally:
            server.shutdown()
            thread.join()


if __name__ == "__main__":
    main()
