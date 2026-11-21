import json
from pathlib import Path
import re
import unittest

from tutor.analysis import analyze
from tutor.benchmark import evidence
from tutor.catalog import ROOT, verify_file
from tutor.dialogue import DialogueError, choose_stage, read_reply, validate


CASES = json.loads((ROOT / "p3" / "scenarios.json").read_text(encoding="utf-8"))
MAXIMUM = next(case for case in CASES if case["id"] == "maximum")


# Ces fonctions sont des programmes de référence écrits ici et audités.
def reference_maximum(tab):
    return max(tab)


def reference_zero_sentinel(tab):
    m = 0
    for valeur in tab:
        if valeur > m:
            m = valeur
    return m


class TutorTests(unittest.TestCase):
    def test_reference_maximum(self):
        self.assertEqual(reference_zero_sentinel([-4, -2]), 0)
        self.assertEqual(reference_maximum([-4, -2]), -2)
        self.assertEqual(reference_maximum([0]), 0)
        with self.assertRaises(ValueError):
            reference_maximum([])

    def test_analysis_never_executes_code(self):
        result = analyze("raise RuntimeError('Cette instruction ne sera pas exécutée')")
        self.assertIsNone(result["syntax"])
        self.assertEqual(analyze("def pair(n):\nreturn n")["syntax"], 2)
        self.assertTrue(analyze(MAXIMUM["code"])["maximum_zero"])
        self.assertFalse(analyze(MAXIMUM["turns"][-1]["code"])["maximum_zero"])

    def test_stages_follow_attempts_and_code_changes(self):
        initial = analyze(MAXIMUM["code"])
        self.assertEqual(choose_stage("Explique-moi.", [], initial), 1)
        history = [{"stage": 1, "digest": initial["digest"]}]
        self.assertEqual(choose_stage("Je ne comprends pas.", history, initial), 2)
        self.assertEqual(choose_stage("Je trace m pour [-4, -2].", history, initial), 3)
        history[-1]["stage"] = 3
        self.assertEqual(choose_stage("Donne le corrigé.", history, initial), 4)
        self.assertEqual(choose_stage("Donne le corrigé.", [{"stage": 4, "digest": initial["digest"]}], initial), 4)
        self.assertEqual(choose_stage("J’ai modifié mon code.", history, analyze(MAXIMUM["turns"][-1]["code"])), 5)
        self.assertEqual(choose_stage("J’ai modifié mon code.", history, analyze("for")), 2)

    def test_leaks_and_invalid_format_are_refused(self):
        facts = analyze(MAXIMUM["code"])
        for hint in ("m = tab[0]", "Choisis le premier élément.", "Utilise max(tab).", "```py\ndef maximum(tab):\n```"):
            with self.subTest(hint=hint), self.assertRaises(DialogueError):
                read_reply({"finish": "stop", "text": json.dumps({"indice": hint, "question": "Que se passe-t-il ?"})}, facts)
        with self.assertRaises(DialogueError):
            read_reply({"finish": "length", "text": "{"}, facts)
        with self.assertRaises(DialogueError):
            read_reply({"finish": "stop", "text": '{"indice":"Indice","question":"Trace m."}'}, facts)
        reply = read_reply({"finish": "stop", "text": '{"indice":"Teste [-4, -2].","question":"Observe ? Que vaut m ?"}'}, facts)
        self.assertEqual(reply["question"], "Que vaut m?")

    def test_invalid_input_is_refused(self):
        base = {"class": "premiere", "statement": "Exercice", "code": "", "question": "Pourquoi ?"}
        self.assertEqual(validate(base)[0], "premiere")
        for patch in ({"class": []}, {"code": "x" * 3601}, {"question": " "}, {"history": [{}]}, {"history": [1] * 4}):
            with self.subTest(patch=patch), self.assertRaises(DialogueError):
                validate(base | patch)

    def test_scenarios_define_three_turns_and_reference_signals(self):
        self.assertEqual(len({case["id"] for case in CASES}), 20)
        self.assertEqual(sum(case["compare"] for case in CASES), 6)
        for case in CASES:
            self.assertGreaterEqual(len(case["turns"]), 3)
            for turn in case["turns"]:
                re.compile(turn["focus"])
                validate(dict(case, question=turn["question"]))
            for forbidden in case["forbidden"]:
                re.compile(forbidden)
        signals = evidence(MAXIMUM, MAXIMUM["turns"][0], None, {"text": "m = tab[0]"}, MAXIMUM["code"])
        self.assertTrue(signals["raw_leak_signal"])
        self.assertFalse(signals["displayed_leak_signal"])

    def test_checksum_rejects_wrong_asset(self):
        with self.assertRaisesRegex(ValueError, "Empreinte"):
            verify_file(Path(__file__), {"sha256": "0" * 64})


if __name__ == "__main__":
    unittest.main()
