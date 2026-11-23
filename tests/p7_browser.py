"""Recette P7 de l’atelier réel avec propositions libres et changement de code."""

import argparse
import json
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

from tutor_browser import local_server, protect_page


def replay(browser, origin, output):
    for profile, endpoint in [('conversation', 'tutor'), ('hybrid', 'hybrid')]:
        page = browser.new_page(viewport={'width': 1672, 'height': 941})
        outside, errors = protect_page(page, origin)
        page.goto(origin + '/atelier')
        expect(page.get_by_label('Mode d’aide')).to_have_value('guided')
        page.get_by_label('Mode d’aide').select_option(profile)
        expect(page.locator('#model-state')).to_have_text('Modèle prêt', timeout=95000)
        if profile == 'hybrid':
            expect(page.locator('#hybrid-badge')).to_have_text('Hybride expérimental')
        editor = page.get_by_label('Code Python')
        code = editor.input_value()
        turns = [
            ('Pourquoi mon programme renvoie 0 quand la liste contient des nombres strictement négatifs ?', 'observed'),
            ('maximum([-3, -4, -1])', 'observed'),
            ('Je pense que ça renvoie 0, alors que ça devrait renvoyer -1.', 'trace'),
            ('False.', 'trace'),
            ('Comme les conditions sont fausses, on n’affecte jamais de nouvelle valeur à m, donc elle reste à zéro.', 'assumption'),
            ('maximum([-9, -3])', 'verification'),
            ('J’obtiens -3, pourtant le résultat attendu devrait être -3.', 'contract'),
        ]
        for index, (message, goal) in enumerate(turns, 1):
            if index == 6:
                editor.fill(code.replace('m = 0', 'm = tab[0]'))
            page.get_by_label('Ta question ou ton observation').fill(message)
            with page.expect_response(lambda r: r.url.endswith('/api/' + endpoint), timeout=115000) as pending:
                page.get_by_role('button', name='Demander un indice').click()
            response = pending.value
            data = response.json()
            assert response.ok, data
            data.pop('session', None)
            bubble = page.locator('.assistant').last
            expect(bubble).to_contain_text(data['feedback'])
            source = bubble.locator('.provenance').inner_text()
            print(json.dumps({'profil': profile, 'tour': index, 'eleve': message, 'source_affichee': source,
                              'reponse': data}, ensure_ascii=False), file=output, flush=True)
            state = data['pedagogie']
            assert state['objectif'] == goal, (profile, index, state)
            assert not state['essai_actif'] or state['essai_actif']['execute'] is None
            if index == 2:
                expect(bubble).to_contain_text('[-3, -4, -1]')
                assert '[-4, -2]' not in data['question']
                page.get_by_text('Suivi enseignant', exact=True).click()
                expect(page.locator('#teacher-content')).to_contain_text('Essai actif')
                page.get_by_text('Suivi enseignant', exact=True).click()
            if index == 3:
                assert state['essai_actif']['predit'] == 0 and state['essai_actif']['declare'] is None
            if index == 4:
                assert 'comparaison' in state['acquis'] and 'trace' not in state['acquis']
            if index == 5:
                assert 'trace' in state['acquis'] and 'tab[0]' not in data['indice'] + data['question']
            if index == 6:
                assert not state['acquis'] and state['essai_actif']['entree'] == [-9, -3]
            decision = state['derniere_intervention'] or {}
            assert ('Reclassement JEPA enregistré' in source) == bool(decision.get('source') == 'jepa' and decision.get('differe_des_regles'))
        assert not outside and not errors, (outside, errors)
        page.close()
    print('P7 : 14 tours Chromium des profils locaux réussis.', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets', type=Path, required=True)
    parser.add_argument('--weights', type=Path, required=True)
    parser.add_argument('--chromium', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with local_server(args.assets, 'smol', '--p5', 'c', '--jepa', str(args.weights), verify_shutdown=True) as origin:
        with sync_playwright() as toolkit, args.output.open('x', encoding='utf-8') as output:
            browser = toolkit.chromium.launch(executable_path=args.chromium)
            replay(browser, origin, output)
            browser.close()


if __name__ == '__main__':
    main()
