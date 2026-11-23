"""Régression P7.1 sur le moteur normal et les contextes contradictoires."""

import json
from pathlib import Path
import unittest

from p5.contract import ACTIONS
from p5.orchestration import Experiment
from pedagogy.catalogue import EXERCISES
from tutor.dialogue import DialogueError
from tutor.sessions import Sessions


ROOT = Path(__file__).resolve().parents[1]
DIALOGUE = json.loads((ROOT / 'p7/dialogue_p71.json').read_text(encoding='utf-8'))


class Model:
    identity = 'double de classement'

    def scores(self, situation):
        return {action: float(action == 'confronter') for action in ACTIONS}


class Dialogue:
    def __init__(self, mode='conversation', experiment=None, statement=None):
        exercise = EXERCISES['maximum']
        self.sessions = Sessions(experiment)
        self.mode = mode
        self.request = {'class': 'premiere', 'exercise': 'maximum', 'statement': statement or exercise['statement'],
                        'code': exercise['code']}
        self.client = {}

    def send(self, question):
        reply = self.sessions.turn(self.mode, self.request | self.client | {'question': question}, None)
        self.client = {'session': reply['session'], 'turn': reply['turn']}
        return reply

    def through(self, count=3):
        return [self.send(text) for text in DIALOGUE[:count]]


class P71Tests(unittest.TestCase):
    def test_observed_regression_and_new_route_in_all_profiles(self):
        for label, mode, experiment in [('local', 'conversation', None),
                                         ('hybrid', 'conversation', Experiment('c', Model())),
                                         ('guided', 'guided', None)]:
            with self.subTest(label=label):
                turns = Dialogue(mode, experiment).through(5)
                states = [turn['pedagogie'] for turn in turns]
                self.assertTrue(all(s.get('schema') == 1 for s in states))
                self.assertEqual([s['objectif'] for s in states],
                                 ['expected', 'trace', 'strategy', 'verification', 'verification'])
                self.assertEqual(states[0]['essai_actif']['auteur'], 'tuteur')
                self.assertIsNone(states[0]['essai_actif']['declare'])
                self.assertEqual(states[2]['acquis']['comparaison']['extrait'], DIALOGUE[2])
                self.assertNotIn('trace', states[2]['acquis'])
                self.assertIn('-4 > 0, puis -2 > 0', turns[2]['feedback'])
                self.assertIn('Ces tests sont faux', turns[2]['feedback'])
                self.assertEqual(states[3]['proposition_validee']['extrait'], DIALOGUE[3])
                self.assertIn('deux entrées distinctes', turns[3]['indice'])
                self.assertEqual(states[3]['question_cible'], 'resultat_exclu')
                self.assertIn('sortie_element', states[4]['acquis'])
                self.assertIn('valeur initiale', turns[4]['feedback'])
                self.assertIsNone(states[4]['essai_actif']['execute'])
                self.assertEqual(len({turn['question'] for turn in turns}), 5)
                self.assertTrue(all(turn['generation'] == 'non_sollicite' for turn in turns))
                for turn, state in zip(turns, states, strict=True):
                    decision = state['derniere_intervention'] or {}
                    self.assertEqual('reclassée par JEPA' in turn['provenance']['question'],
                                     decision.get('source') == 'jepa' and bool(decision.get('differe_des_regles')))

    def test_baseline_evidence_reproduces_original_failures(self):
        rows = [json.loads(line) for line in (ROOT / 'p7/preuves-p71/avant-linux.jsonl').read_text(encoding='utf-8').splitlines()]
        self.assertEqual([row['eleve'] for row in rows], DIALOGUE * 2)
        for row in rows:
            state = row['reponse']['pedagogie']
            self.assertFalse(state.get('schema'))
            if row['tour'] == 4:
                self.assertEqual(state['objectif'], 'strategy')
                self.assertNotIn('strategy', state['acquis'])
            if row['tour'] == 5:
                self.assertEqual(state['evaluation']['statut'], 'hors_sujet')
        self.assertIn('Quels choix peux-tu exclure', rows[8]['reponse']['question'])

    def test_valid_initializations_are_equivalent_and_respect_bindings(self):
        for text in ('m = tab[0]', 'm=tab[0]', 'Initialiser m avec le premier élément.',
                     'Je prends la première valeur de la liste.', 'On commence avec tab[0].',
                     'm = tab[-1]', 'm = float("-inf")'):
            with self.subTest(text=text):
                dialogue = Dialogue()
                dialogue.through()
                state = dialogue.send(text)['pedagogie']
                self.assertEqual(state['objectif'], 'verification')
                self.assertEqual(state['acquis']['strategy']['extrait'], text)
        for text in ('s = tab[0]', 'm = valeurs[0]', 'm=tab[1]', 'm = 0', 'm = -1000',
                     'm=tab[0]; m=0', 'm=tab[f()]', 'Ne pas initialiser m avec le premier élément.'):
            with self.subTest(text=text):
                dialogue = Dialogue()
                dialogue.through()
                reply = dialogue.send(text)
                self.assertNotIn('strategy', reply['pedagogie']['acquis'])
                self.assertEqual(reply['pedagogie']['objectif'], 'strategy')
                if text == 'm = 0':
                    self.assertIn('plus petits', reply['feedback'])

    def test_nonempty_precondition_is_required_for_the_proposed_strategy(self):
        for statement in ('Trouver le maximum d’une liste pouvant être vide.',
                          'Calculer le maximum d’une liste d’entiers, non vide ou vide.'):
            with self.subTest(statement=statement):
                dialogue = Dialogue(statement=statement)
                dialogue.through()
                reply = dialogue.send('m=tab[0]')
                self.assertIn('contrat pour la liste vide', reply['feedback'])
                self.assertNotIn('strategy', reply['pedagogie']['acquis'])
        dialogue = Dialogue()
        dialogue.through()
        self.assertFalse(dialogue.send('maximum([])')['pedagogie']['essai_actif']['precondition'])

    def test_same_short_expression_gets_contextual_judgments(self):
        expected = Dialogue()
        expected.through(1)
        denied = expected.send('- inf')
        self.assertEqual(denied['pedagogie']['evaluation']['statut'], 'incorrecte')
        self.assertNotIn('expected', denied['pedagogie']['acquis'])
        strategy = Dialogue()
        strategy.through()
        accepted = strategy.send('- inf')
        self.assertEqual(accepted['pedagogie']['objectif'], 'verification')
        self.assertIn('strategy', accepted['pedagogie']['acquis'])
        self.assertNotIn('sortie_element', accepted['pedagogie']['acquis'])
        ambiguous = Dialogue().send('- inf')
        self.assertIn('valeur initiale, ou', ambiguous['feedback'])
        self.assertTrue(ambiguous['pedagogie']['clarification'])

    def test_partial_or_contradictory_orders_do_not_advance(self):
        for text in ('0 > -4', '-4 > 0 et -2 > 0', '0 > -4 mais -2 > 0',
                     'Je ne pense pas que 0 > -4 et 0 > -2.', '0 > -4 et 0 > -2 mais m vaut -2'):
            with self.subTest(text=text):
                dialogue = Dialogue()
                dialogue.through(2)
                state = dialogue.send(text)['pedagogie']
                self.assertEqual(state['objectif'], 'trace')
                self.assertNotIn('comparaison', state['acquis'])
        for text in ('-4 < 0 et -2 < 0', '-4 > 0 est faux et -2 > 0 est faux', '0 est supérieur à -4 et à -2'):
            with self.subTest(text=text):
                dialogue = Dialogue()
                dialogue.through(2)
                self.assertEqual(dialogue.send(text)['pedagogie']['objectif'], 'strategy')
        dialogue = Dialogue()
        dialogue.send('maximum([-10, -9, -7])')
        dialogue.send('Je pense que ça renvoie 0 mais le résultat devrait être -7.')
        self.assertEqual(dialogue.send('0 > -10 et 0 > -9 et 0 > -7')['pedagogie']['objectif'], 'strategy')

    def test_short_boolean_has_only_the_scope_of_the_question(self):
        dialogue = Dialogue()
        self.assertEqual(dialogue.through(1)[0]['pedagogie']['question_cible'], 'attendu')
        self.assertNotIn('comparaison', dialogue.send('toujours False')['pedagogie']['acquis'])
        expected = dialogue.send('-2')
        self.assertEqual(expected['pedagogie']['question_cible'], 'condition')
        comparison = dialogue.send('toujours False')['pedagogie']
        self.assertIn('comparaison', comparison['acquis'])
        self.assertNotIn('trace', comparison['acquis'])
        self.assertEqual(comparison['question_cible'], 'justification')

    def test_pedagogical_proof_requires_two_distinct_cases_on_revised_code(self):
        dialogue = Dialogue()
        dialogue.through(5)
        old = dialogue.send('Avec [6], j’obtiens 6, mais le résultat devrait être 6.')['pedagogie']
        self.assertEqual(old['objectif'], 'verification')
        self.assertFalse(old['essais_verifies'])
        dialogue.request['code'] = dialogue.request['code'].replace('m = 0', 'm = tab[0]')
        single = dialogue.send('Avec [-6, -8], j’obtiens -6, mais ça devrait donner -6.')['pedagogie']
        self.assertEqual(single['objectif'], 'verification')
        self.assertEqual(len(single['essais_verifies']), 1)
        self.assertNotIn('verification', single['acquis'])
        same = dialogue.send('Avec [-6, -8], j’obtiens -6, mais ça devrait donner -6.')['pedagogie']
        self.assertEqual(len(same['essais_verifies']), 1)
        double = dialogue.send('Avec [7], j’obtiens 7, mais ça devrait donner 7.')['pedagogie']
        self.assertEqual(double['objectif'], 'contract')
        self.assertEqual({row['entree'] for row in double['essais_verifies']}, {(-6, -8), (7,)})
        self.assertIn('verification', double['acquis'])
        dialogue.request['code'] = dialogue.request['code'].replace('m = tab[0]', 'm = 0')
        changed = dialogue.send('J’ai changé le code.')['pedagogie']
        self.assertFalse(changed['essais_verifies'])
        self.assertNotIn('verification', changed['acquis'])
        self.assertEqual(changed['proposition_validee']['extrait'], 'm=tab[0]')

    def test_supported_specs_use_one_engine_from_first_short_turn(self):
        for identifier, exercise in EXERCISES.items():
            for mode in ('guided', 'conversation'):
                with self.subTest(identifier=identifier, mode=mode):
                    session = Sessions()
                    result = session.turn(mode, {'class': exercise['level'], 'statement': exercise['statement'],
                                                 'exercise': identifier, 'question': '0', 'code': exercise['code']}, None)
                    self.assertEqual(result['pedagogie']['schema'], 1)
                    self.assertEqual(result['pedagogie']['question_cible'], 'essai')
                    self.assertFalse(result['pedagogie']['acquis'])
        with self.assertRaises(DialogueError):
            Dialogue(mode='guided').sessions.turn('guided', {'class':'premiere','exercise':'recursivite-base',
                'code':'','question':'0','statement':'Trouver la plus grande valeur.'}, None)

    def test_observation_in_attached_text_still_populates_teacher_evidence(self):
        guide = Dialogue(mode='guided')
        guide.request['code'] += '\n# commentaire de l’élève'
        proof = guide.send('Mon programme répond toujours 0 quand les nombres sont négatifs.')['pedagogie']
        self.assertEqual(proof['acquis']['observed']['tour'], 1)
        self.assertEqual(proof['libelles_objectifs']['observed'], 'Identifier le résultat observé')

    def test_expected_result_reformulation_applies_to_a_while_loop(self):
        exercise = EXERCISES['boucle-while']
        sessions = Sessions()
        payload = {'class': 'premiere', 'statement': exercise['statement'], 'code': exercise['code']}
        session, turn = None, 0
        for question in ('compte(0)', 'J’obtiens 0.', 'Le résultat attendu devrait être 3.'):
            reply = sessions.turn('conversation', payload | {'question': question, 'session': session, 'turn': turn}, None)
            session, turn = reply['session'], reply['turn']
        self.assertEqual(reply['pedagogie']['question_cible'], 'attendu')
        self.assertIn('renvoyée', reply['question'])
        self.assertNotIn('maximum', reply['question'])
