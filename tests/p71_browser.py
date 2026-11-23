"""Rejeu P7.1 des cinq tours d’origine et des deux vérifications qui suivent."""

import argparse
import json
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

from tutor_browser import ROOT, local_server, protect_page


DIALOGUE = json.loads((ROOT / 'p7/dialogue_p71.json').read_text(encoding='utf-8'))


def replay(browser, origin, output):
    messages = DIALOGUE + ['Avec [-9, -3], j’obtiens -3, la valeur attendue devrait être -3.',
                           'Avec [7], j’obtiens 7, la valeur attendue devrait être 7.']
    goals = ['expected', 'trace', 'strategy', 'verification', 'verification', 'verification', 'contract']
    for profile, endpoint in [('conversation', 'tutor'), ('hybrid', 'hybrid')]:
        page = browser.new_page(viewport={'width': 1672, 'height': 941})
        external, errors = protect_page(page, origin)
        page.goto(origin + '/atelier')
        expect(page.get_by_label('Mode d’aide')).to_have_value('guided')
        page.get_by_label('Mode d’aide').select_option(profile)
        expect(page.locator('#model-state')).to_have_text('Modèle prêt', timeout=95000)
        expect(page.locator('#model-identity')).to_contain_text('SmolLM3-3B')
        if profile == 'hybrid':
            expect(page.locator('#hybrid-badge')).to_have_text('Hybride expérimental')
        editor = page.get_by_label('Code Python')
        originals = set()
        for index, (message, goal) in enumerate(zip(messages, goals, strict=True), 1):
            if index == 6:
                editor.fill(editor.input_value().replace('m = 0', 'm = tab[0]'))
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
            print(json.dumps({'profil': profile, 'tour': index, 'eleve': message,
                              'moteurs': page.locator('#model-identity').inner_text(), 'source_affichee': source,
                              'reponse': data}, ensure_ascii=False), file=output, flush=True)
            state = data['pedagogie']
            assert state['schema'] == 1 and state['objectif'] == goal, (profile, index, state)
            assert state['essai_actif']['execute'] is None
            if data['question']:
                assert data['question'] not in originals
                originals.add(data['question'])
            if index == 1:
                assert state['essai_actif']['auteur'] == 'tuteur' and state['essai_actif']['declare'] is None
            if index == 3:
                expect(bubble).to_contain_text('-4 > 0, puis -2 > 0')
                expect(bubble).to_contain_text('Ces tests sont faux')
            if index == 4:
                assert state['proposition_validee']['extrait'] == message
                expect(bubble).to_contain_text('deux entrées distinctes')
            if index == 5:
                assert 'sortie_element' in state['acquis']
                expect(bubble).to_contain_text('valeur initiale')
            if index in (6, 7):
                assert len(state['essais_verifies']) == index - 5
            decision = state['derniere_intervention'] or {}
            assert ('Reclassement JEPA enregistré' in source) == bool(decision.get('source') == 'jepa' and decision.get('differe_des_regles'))
            assert ('SmolLM3' in source) == (data['generation'] == 'affiche')
            if profile == 'conversation':
                assert not decision
        assert not external and not errors, (external, errors)
        page.close()
    print('P7.1 : 14 tours Chromium des deux profils avec modèles chargés.', flush=True)


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
