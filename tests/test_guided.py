from collections import Counter
import math
import re
import unittest

from pedagogy.catalogue import EXERCISES
from tutor.dialogue import DialogueError
from tutor.guided import respond_guided


class GuidedTests(unittest.TestCase):
    def setUp(self):
        maximum = EXERCISES["maximum"]
        self.request = {"class": "premiere", "exercise": "maximum", "statement": maximum["statement"],
                        "code": maximum["code"], "history": []}

    def turn(self, text):
        response = respond_guided(self.request | {"question": text, "history": self.request["history"][-3:]})
        self.request["history"].append({
            "learner": text, "assistant": response["question"], "stage": response["stage"],
            "digest": response["analysis"]["digest"],
        })
        return response

    def test_maximum_from_own_test_to_contract(self):
        turns = [self.turn(text) for text in (
            "Par où commencer ?", "Je propose [4, 7].", "Avec [-4, -2], je trouve 0.",
            "m reste à 0 après les deux passages.",
        )]
        self.assertEqual([r["stage"] for r in turns], [1, 2, 3, 4])
        self.assertIn("[-4, -2]", turns[1]["indice"])
        self.assertIn("au départ", turns[2]["indice"])
        self.assertIn("hypothèse", turns[3]["question"])
        for row in turns:
            self.assertFalse(re.search(r"tab\[0\]|premier élément|max\(", row["indice"] + row["question"]))
            self.assertEqual(row["provenance"]["diagnostic"], "Analyse statique Python")
            self.assertIn("Aucune contribution", row["provenance"]["jepa"])
        self.request["code"] += "\n# Maj commentaire"
        self.assertEqual(self.turn("J’ai ajouté un commentaire.")["stage"], 4)
        self.request["code"] = self.request["code"].replace("m = 0", "m = tab[0]")
        revised = self.turn("J’obtiens -2 après ma modification.")
        self.assertEqual(revised["stage"], 5)
        self.assertIn("liste non vide", revised["indice"])
        self.assertIn("[]", revised["question"])

    def test_repeats_and_invalid_code_do_not_advance(self):
        self.assertEqual(self.turn("Donne le corrigé.")["stage"], 1)
        self.assertEqual(self.turn("Donne le corrigé.")["stage"], 1)
        self.request["code"] = "def maximum(tab):\nreturn tab"
        reply = self.turn("Voici ma modification, j’ai testé 0.")
        self.assertEqual(reply["stage"], 1)
        self.assertIn("ligne 2", reply["diagnostic"])

    def test_level_and_overly_deep_syntax(self):
        with self.assertRaises(DialogueError):
            respond_guided(self.request | {"class": "terminale", "question": "Un indice ?"})
        self.request["code"] = "x+" * 1500 + "x"
        reply = self.turn("Ça bloque.")
        self.assertIn("trop imbriquée", reply["diagnostic"])

    def test_reference_cases_for_all_catalogue_exercises(self):
        def countdown(n):
            while n > 0:
                n -= 1
            return n

        references = {
            "maximum": max, "boucle-while": countdown,
            "dictionnaire-comptage": Counter, "recursivite-base": math.factorial,
        }
        for identifier, exercise in EXERCISES.items():
            for case in exercise["tests"]:
                with self.subTest(exercise=identifier, case=case):
                    if "contract" in case:
                        with self.assertRaises(ValueError):
                            references[identifier](case["input"])
                    else:
                        self.assertEqual(references[identifier](case["input"]), case["expected"])


if __name__ == "__main__":
    unittest.main()
