import json
import unittest

from pedagogy.catalogue import EXERCISES
from pedagogy.progress import near_question
from tutor.catalog import ROOT
from tutor.dialogue import DialogueError, read_maximum_hint
from tutor.engine import EngineError
from tutor.sessions import RECENT_TURNS, SessionConflict, Sessions


REFERENCE = json.loads((ROOT / "p4/reference.json").read_text(encoding="utf-8"))


class RegressionEvidenceTests(unittest.TestCase):
    def test_original_model_repeated_question_after_causal_explanation(self):
        rows = [json.loads(line) for line in (ROOT / "p4/preuves/avant.jsonl").read_text(
            encoding="utf-8").splitlines()]
        self.assertEqual([row["learner"] for row in rows], REFERENCE)
        self.assertEqual(rows[1]["answer"]["question"], rows[3]["answer"]["question"])
        self.assertEqual(rows[1]["answer"]["stage"], rows[3]["answer"]["stage"])
        self.assertIn("valeur de `m`", rows[3]["answer"]["question"])
        self.assertEqual(rows[3]["raw"]["finish"], "stop")


class SocraticTests(unittest.TestCase):
    def setUp(self):
        self.sessions = Sessions()
        exercise = EXERCISES["maximum"]
        self.payload = {"class": "premiere", "exercise": "maximum", "statement": exercise["statement"],
                        "code": exercise["code"]}
        self.corrected = exercise["code"].replace("m = 0", "m = tab[0]")
        self.client = {}

    def turn(self, text, *, mode="guided", engine=None, **patch):
        answer = self.sessions.turn(mode, self.payload | self.client | {"question": text} | patch, engine)
        self.client = {"session": answer["session"], "turn": answer["turn"]}
        return answer

    def through_trace(self):
        for text in REFERENCE[:4]:
            self.turn(text)

    def test_provided_dialogue_advances_after_correct_explanation(self):
        rows = [self.turn(learner) for learner in REFERENCE]
        self.assertEqual([row["pedagogie"]["objectif"] for row in rows],
                         ["expected", "trace", "trace", "strategy", "strategy", "strategy"])
        fourth = rows[3]["pedagogie"]
        self.assertEqual(fourth["evaluation"]["statut"], "correcte")
        for key in ("trace", "assumption"):
            self.assertEqual(fourth["acquis"][key]["tour"], 4)
            self.assertEqual(fourth["acquis"][key]["extrait"], REFERENCE[3])
        self.assertEqual(len({row["question"] for row in rows}), 6)
        self.assertIn("déjà relevé", rows[-1]["feedback"])
        self.assertEqual([item["strategie"] for item in fourth["questions"]][-1], "propriété")
        self.assertNotEqual(rows[4]["question"], rows[5]["question"])

    def test_observed_expected_partial_and_wrong_answers(self):
        self.assertEqual(self.turn("Ça donne zéro pour des nombres négatifs.")["pedagogie"]["objectif"], "expected")
        wrong = self.turn("-4")["pedagogie"]
        self.assertEqual(wrong["evaluation"]["statut"], "incorrecte")
        self.assertIn("expected", wrong["erreurs"])
        self.assertEqual(self.turn("moins deux")["pedagogie"]["objectif"], "trace")
        self.assertEqual(self.turn("m vaut zéro.")["pedagogie"]["evaluation"]["statut"], "partielle")
        wrong = self.turn("0 < -4 et -2.")["pedagogie"]
        self.assertEqual(wrong["evaluation"]["statut"], "incorrecte")
        self.assertIn("trace", wrong["erreurs"])
        answer = self.turn("Car zéro est supperieur à moins quatre et moins deux.")["pedagogie"]
        self.assertEqual(answer["objectif"], "strategy")
        self.assertNotIn("trace", answer["erreurs"])
        self.assertNotIn("expected", answer["erreurs"])

    def test_negation_and_wrong_test_do_not_validate_claim(self):
        self.assertEqual(self.turn("Pour [4, 7], mon programme renvoie 0.")["pedagogie"]["objectif"], "observed")
        self.assertEqual(self.turn("Le programme ne renvoie pas zéro.")["pedagogie"]["objectif"], "observed")
        self.turn(REFERENCE[0])
        self.turn(REFERENCE[1])
        self.assertEqual(self.turn("Je ne pense pas que 0 est supérieur à -4 et à -2.")["pedagogie"]["objectif"], "trace")
        self.assertEqual(self.turn("-4 est inférieur à 0 et -2 est positif.")["pedagogie"]["objectif"], "trace")
        self.assertEqual(self.turn("oui")["pedagogie"]["evaluation"]["statut"], "ambigue")
        self.assertEqual(self.turn("Paris est une ville.")["pedagogie"]["evaluation"]["statut"], "hors_sujet")
        self.assertEqual(self.turn("-4 est plus petit que zéro, et -2 < 0 aussi.")["pedagogie"]["objectif"], "strategy")

    def test_server_ignores_claimed_history_and_replays_once(self):
        payload = self.payload | {"question": "Je ne sais pas.", "pedagogie": {"acquis": ["verification"]},
                                  "history": [{"stage": 5, "digest": "0" * 64}]}
        initial = self.sessions.turn("guided", payload, None)
        self.assertEqual(initial["pedagogie"]["acquis"], {})
        next_payload = payload | {"session": initial["session"], "turn": 1, "question": REFERENCE[0]}
        original = self.sessions.turn("guided", next_payload, None)
        self.assertEqual(original, self.sessions.turn("guided", next_payload, None))
        self.assertEqual(original["turn"], 2)
        with self.assertRaises(SessionConflict):
            self.sessions.turn("guided", next_payload | {"question": "autre message"}, None)
        with self.assertRaises(SessionConflict):
            self.sessions.turn("conversation", next_payload | {"turn": 2}, None)
        with self.assertRaises(DialogueError):
            self.sessions.turn("guided", next_payload | {"turn": True}, None)

    def test_retains_evidence_after_ten_turns_and_requires_proven_correction(self):
        self.through_trace()
        for _ in range(7):
            answer = self.turn("Donne-moi le corrigé.")
        self.assertEqual(answer["turn"], 11)
        self.assertEqual(answer["pedagogie"]["objectif"], "strategy")
        self.assertEqual(answer["question"], "")
        self.assertEqual(len(self.sessions.items[self.client["session"]].recent), RECENT_TURNS)
        def state(text, **patch):
            return self.turn(text, **patch)["pedagogie"]

        strategy = state("Je choisirais une valeur qui figure déjà dans la liste.")
        self.assertEqual(strategy["objectif"], "verification")
        self.assertEqual(strategy["acquis"]["trace"]["tour"], 4)
        self.assertEqual(state("J’obtiens -2 sur [-4, -2].")["objectif"], "verification")
        self.assertEqual(state("J’ai ajouté un commentaire.", code=self.payload["code"] + "\n# note")["objectif"], "verification")
        asked_before_edit = [item[2] for item in self.sessions.items[self.client["session"]].progress.questions]
        self.assertEqual(state("J’ai modifié le code.", code=self.corrected)["objectif"], "verification")
        asked_after_edit = [item[2] for item in self.sessions.items[self.client["session"]].progress.questions]
        self.assertEqual(asked_after_edit[:len(asked_before_edit)], asked_before_edit)
        self.assertEqual(len(set(asked_after_edit)), len(asked_after_edit))
        self.assertEqual(state("Sur [3, 7], j’obtiens -2.", code=self.corrected)["objectif"], "verification")
        verified = state("J’obtiens -2 sur [-4, -2].", code=self.corrected)
        self.assertEqual(verified["objectif"], "contract")
        self.assertIn("statique", verified["acquis"]["verification"]["critere"])
        self.assertIsNone(state("[] est hors contrat car la liste doit être non vide.", code=self.corrected)["objectif"])
        change = state("Passons aux dictionnaires.", code=self.corrected)
        self.assertEqual(change["notion_demandee"], "Dictionnaires")
        self.assertEqual(change["acquis"]["trace"]["tour"], 4)
        self.assertEqual(state("J’annule ma modification.")["objectif"], "verification")

    def test_semantic_similarity_and_model_guard(self):
        self.assertTrue(near_question("Quelle est la valeur de m après chaque itération ?",
                                      "Que vaut m après chaque tour ?"))
        self.assertFalse(near_question("Quel résultat observes-tu ?", "Quel résultat devrait-on obtenir ?"))
        raw = {"finish": "stop", "text": json.dumps({"indice": "Examine les choix de départ compatibles avec le contrat."})}
        self.assertTrue(read_maximum_hint(raw, "strategy", "Quelle propriété chercher ?", []))
        for hint in ("La valeur doit être inférieure à tous les éléments.",
                     "Vérifie que la valeur de départ est supérieure à tous les éléments de la liste.",
                     "Compare avec le premier élément.", "Observe la valeur de m à chaque itération.",
                     "Compare avec tab[0].", "Examine ce que retournerait max(tab)."):
            with self.subTest(hint=hint):
                self.assertEqual(read_maximum_hint(raw | {"text": json.dumps({"indice": hint})},
                                                   "strategy", "Quelle propriété chercher ?", []), "")

    def test_model_unavailable_keeps_rule_feedback_visible(self):
        class Engine:
            def generate(self, messages, *, hint):
                raise EngineError("interrompu")
        answer = self.turn(REFERENCE[0], mode="conversation", engine=Engine())
        self.assertEqual(answer["generation"], "indisponible")
        self.assertEqual(answer["pedagogie"]["objectif"], "expected")
        self.assertEqual(answer["provenance"]["hint"], "Règle pédagogique locale")

    def test_expired_session_refuses_old_client_progress(self):
        self.turn(REFERENCE[0])
        session = self.sessions.items[self.client["session"]]
        session.touched -= 3600
        with self.assertRaises(SessionConflict):
            self.turn(REFERENCE[1])
        self.assertEqual(self.sessions.items, {})


if __name__ == "__main__":
    unittest.main()
