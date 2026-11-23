import json
from pathlib import Path
import unittest

from p7.benchmark import data, replay
from pedagogy.cases import SPECS
from pedagogy.interpretation import Intent, interpret, verified_interpretation


class P7Tests(unittest.TestCase):
    def test_free_case_corpus_proves_goals_without_models(self):
        for dialogue in data():
            for row in replay(dialogue, 'T'):
                step = row['controle']
                with self.subTest(dialogue=dialogue['id'], tour=row['tour']):
                    for key in ('objectif', 'test', 'preuve', 'statique', 'precondition', 'prediction', 'declaration', 'litteral_invalide'):
                        if step[key] is not None:
                            self.assertTrue(step[key], (key, row))
                    for negative in ('execution_fictive', 'divulgation', 'abusive', 'reponse_absente'):
                        self.assertFalse(step[negative], (negative, row))

    def test_intents_and_combined_proof_roles(self):
        spec = SPECS['maximum']
        message = interpret('Avec [-3, -4, -1] j’obtiens 0, pourtant le maximum devrait être -1.', spec)
        self.assertEqual(message.tests, ((-3,-4,-1),))
        self.assertEqual([(c.role,c.value) for c in message.claims], [(Intent.OBSERVE, 0), (Intent.EXPECT, -1)])
        message = interpret('Pourquoi mon programme renvoie 0 avec des nombres négatifs ?', spec)
        self.assertEqual(message.intentions, (Intent.EXPLAIN,))
        self.assertFalse(message.claims)

    def test_ast_limits_and_boundaries(self):
        spec = SPECS['maximum']
        for text in ('maximum([True, -1])', 'maximum(f())', 'maximum([[-1]])', 'maximum([1] + [2])',
                     'maximum([1001])', 'maximum(a=[1])', 'f(maximum([2]))', 'module.maximum([2])',
                     'maximum([2]) + work()', 'maximum([' + ','.join('0' for _ in range(21)) + '])'):
            with self.subTest(text=text):
                message = interpret(text, spec)
                self.assertFalse(message.tests)
                self.assertTrue(message.ambiguities)
        self.assertEqual(interpret('maximum([0, -3]) ?', spec).tests, ((0,-3),))
        self.assertEqual(interpret('maximum([])', spec).tests, ((),))

    def test_model_proposal_validates_a_literal_citation_only(self):
        spec = SPECS['maximum']
        source = 'Dans le fond, peux-tu expliquer le résultat'
        message = interpret(source, spec)
        base = {'schema': 1, 'intention': 'explication', 'citation': 'peux-tu expliquer le résultat'}
        accepted, yes = verified_interpretation({'finish':'stop', 'text':json.dumps(base)}, source, message)
        self.assertTrue(yes)
        self.assertEqual(accepted.intentions, (Intent.EXPLAIN,))
        self.assertFalse(accepted.claims)
        for proposal in (base | {'citation': 'explique-moi'}, base | {'preuve': True}, base | {'schema': True}, base | {'intention': 'prediction'}):
            self.assertEqual(verified_interpretation({'finish':'stop', 'text':json.dumps(proposal)}, source, message), (message, False))

    def test_dictionary_literals_keep_case(self):
        spec = SPECS['dictionnaire-comptage']
        message = interpret("Avec ['Pin', 'pin'], j’obtiens {'Pin': 1, 'pin': 1}.", spec)
        self.assertEqual(message.claims[0].value, {'Pin': 1, 'pin': 1})
        self.assertEqual(message.tests, (('Pin','pin'),))

    def test_static_profiles_abstain_on_unrecognized_code(self):
        spec = SPECS['maximum']
        case = spec.case((-2, -7), 'eleve', 'def maximum(tab):\n return max(tab)', 'id')
        self.assertEqual(case.attendu, -2)
        self.assertIsNone(case.statique)
        self.assertIsNone(case.execute)
        fact = SPECS['recursivite-base']
        code = 'def fact(n):\n if n == 0:\n  return 1\n return n * fact(n + 1)'
        self.assertEqual(fact.case(3,'eleve',code,'id').statique.kind, 'base_inaccessible')
        self.assertEqual(fact.case(0,'eleve',code,'id').statique.result, 1)
        self.assertFalse(fact.case(-1,'eleve',code,'id').precondition)


if __name__ == '__main__':
    unittest.main()
