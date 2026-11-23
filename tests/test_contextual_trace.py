import json
import unittest

from p5.contract import ACTIONS
from p5.orchestration import Experiment
from pedagogy.catalogue import EXERCISES
from tutor.sessions import SessionConflict, Sessions


OBSERVED = "Mon programme répond toujours 0 quand les nombres sont négatifs."
EXPECTED = "Avec la fonction maximum c'est 0 mais elle devrait répondre -2."
CAUSE = "La condition est fausse, donc m = valeur ne s’exécute pas et m reste à zéro."


class PrioritiseCondition:
    identity = "JEPA de test"

    def scores(self, situation):
        preferred = "justifier" if situation.objectif == "Expliquer le comportement de m" else "clarifier"
        return {action: float(action == preferred) for action in ACTIONS}


class RejectedEngine:
    def generate(self, messages, *, hint, decision=False):
        return {"finish": "stop", "text": json.dumps({"indice": "Remplace m par tab[0]."})}


class Dialogue:
    def __init__(self, experiment=None, *, guided=False):
        exercise = EXERCISES["maximum"]
        self.sessions = Sessions(experiment, case_based=False)
        self.mode = "guided" if guided else "conversation"
        self.request = {"class": "premiere", "statement": exercise["statement"], "code": exercise["code"]}
        if guided:
            self.request["exercise"] = "maximum"
        self.client = {}

    def send(self, text, **patch):
        self.last_request = self.request | self.client | {"question": text} | patch
        answer = self.sessions.turn(self.mode, self.last_request, None if self.mode == "guided" else RejectedEngine())
        self.client = {"session": answer["session"], "turn": answer["turn"]}
        return answer

    def through(self, target):
        self.send(OBSERVED)
        answer = self.send(EXPECTED)
        if target == "comparaison" and (answer["pedagogie"].get("contexte_question") or {}).get("cible") != target:
            answer = self.send("toujours 0 avec ma fonction")
        assert answer["pedagogie"]["contexte_question"]["cible"] == target, answer
        return answer


class ContextualTraceTests(unittest.TestCase):
    def test_actual_conversation_recognises_false_then_advances_after_cause(self):
        dialogue = Dialogue()
        dialogue.send(OBSERVED)
        dialogue.send(EXPECTED)
        comparison = dialogue.send("toujours 0 avec ma fonction")
        self.assertIn("comparaison", comparison["question"])
        answer = dialogue.send("toujours False")
        state = answer["pedagogie"]
        self.assertEqual(state["evaluation"]["statut"], "partielle")
        self.assertIn("fausse pour -4 et pour -2", answer["feedback"])
        self.assertEqual(state["objectif"], "trace")
        self.assertNotIn("trace", state["acquis"])
        self.assertIn("m = valeur", answer["question"])
        self.assertEqual(state["faits_trace"]["comparaison_fausse"]["question"], comparison["pedagogie"]["contexte_question"])
        answer = dialogue.send(CAUSE)
        self.assertEqual(answer["pedagogie"]["objectif"], "assumption")
        self.assertEqual(answer["pedagogie"]["acquis"]["trace"]["extrait"], CAUSE)
        self.assertNotIn("tab[0]", answer["question"] + answer["indice"])
        self.assertNotIn("comparaison avec la valeur de départ", answer["question"])

    def test_identical_short_answer_on_variable_does_not_confirm_comparison(self):
        dialogue = Dialogue()
        dialogue.through("valeur_m")
        result = dialogue.send("toujours False", contexte_question={"cible": "comparaison"})
        self.assertFalse(result["pedagogie"]["faits_trace"])
        self.assertIn("entier", result["feedback"])
        self.assertIn("condition", result["feedback"])
        result = dialogue.send("m reste à zéro")
        self.assertEqual(set(result["pedagogie"]["faits_trace"]), {"valeur_m"})
        self.assertEqual(result["pedagogie"]["objectif"], "trace")

    def test_equivalent_formulations_and_short_causal_answer(self):
        for answer in ("faux dans les deux cas", "la condition n’est vraie à aucun des deux passages",
                       "La condition n’est vraie pour aucune des deux valeurs.",
                       "La condition vaut `False` pour -4 et pour -2.",
                       "Pour [-4, -2] la condition vaut toujours False."):
            with self.subTest(answer=answer):
                dialogue = Dialogue()
                dialogue.through("comparaison")
                state = dialogue.send(answer)["pedagogie"]
                self.assertIn("comparaison_fausse", state["faits_trace"])
                self.assertEqual(state["objectif"], "trace")
                result = dialogue.send("Elle ne s’exécute pas et m reste à zéro.")
                self.assertEqual(result["pedagogie"]["objectif"], "assumption")

    def test_complete_explanation_needs_no_tracing_reminder(self):
        dialogue = Dialogue()
        dialogue.through("comparaison")
        result = dialogue.send(CAUSE)
        self.assertEqual(result["pedagogie"]["objectif"], "assumption")
        self.assertIn("trace", result["pedagogie"]["acquis"])
        self.assertIsNone(result["pedagogie"]["contexte_question"])

    def test_stagnation_changes_strategy_after_confirming_the_condition(self):
        dialogue = Dialogue()
        dialogue.through("comparaison")
        first = dialogue.send("toujours False")
        second = dialogue.send("je ne sais pas")
        self.assertIn("Relis l’indentation", second["question"])
        self.assertNotEqual(first["question"], second["question"])
        self.assertEqual(second["pedagogie"]["faits_trace"], first["pedagogie"]["faits_trace"])
        self.assertEqual(second["pedagogie"]["objectif"], "trace")

    def test_scope_and_contradictions_confirm_nothing(self):
        for text, status in (("faux", "ambigue"), ("pas toujours faux", "incorrecte"),
                             ("`m` vaut `False`", "incorrecte"),
                             ("La condition est fausse mais l’affectation s’exécute", "incorrecte"),
                             ("Toujours False, mais vrai pour -2.", "incorrecte"),
                             ("toujours False sauf pour -2", "incorrecte"),
                             ("Pour [3, 7], la condition vaut toujours False.", "partielle"),
                             ("Donne-moi le corrigé, j’ai vu False.", "hors_sujet")):
            with self.subTest(text=text):
                dialogue = Dialogue()
                comparison = dialogue.through("comparaison")
                result = dialogue.send(text)
                state = result["pedagogie"]
                self.assertEqual(state["evaluation"]["statut"], status)
                self.assertFalse(state["faits_trace"])
                self.assertNotIn("trace", state["acquis"])
                self.assertNotEqual(result["question"], comparison["question"])
                if text == "faux":
                    self.assertEqual(state["contexte_question"]["cible"], "comparaison")
                    self.assertIn("des deux", result["feedback"])

    def test_code_edit_invalidates_prompt_but_comment_preserves_it(self):
        for edit, valid in (("\n# commentaire", True), (None, False)):
            with self.subTest(edit=edit):
                dialogue = Dialogue()
                dialogue.through("comparaison")
                code = dialogue.request["code"]
                code = code + edit if edit else code.replace("m = 0", "m = -9")
                state = dialogue.send("toujours False", code=code)["pedagogie"]
                self.assertEqual("comparaison_fausse" in state["faits_trace"], valid)
                self.assertEqual(set(state["acquis"]), {"observed", "expected"})
        with self.subTest(edit="énoncé"):
            dialogue = Dialogue()
            dialogue.through("comparaison")
            state = dialogue.send("toujours False", statement="Trouver le maximum d’une liste.")["pedagogie"]
            self.assertFalse(state["faits_trace"] or state["acquis"])

    def test_hybrid_question_context_matches_actual_reclassification_and_retry(self):
        dialogue = Dialogue(Experiment("c", PrioritiseCondition()))
        asked = dialogue.through("comparaison")
        self.assertTrue(asked["pedagogie"]["derniere_intervention"]["differe_des_regles"])
        self.assertIn("reclassée par JEPA", asked["provenance"]["question"])
        result = dialogue.send("toujours False")
        self.assertEqual(result["pedagogie"]["contexte_question"]["cible"], "consequence")
        self.assertFalse(result["pedagogie"]["derniere_intervention"]["differe_des_regles"])
        self.assertEqual(result["provenance"]["jepa"], "Aucune contribution de LANG-JEPA.")
        self.assertEqual(result["generation"], "ecarte")
        self.assertIn("règles pédagogiques", result["provenance"]["question"])
        self.assertEqual(dialogue.sessions.turn("conversation", dialogue.last_request, RejectedEngine()), result)
        with self.assertRaises(SessionConflict):
            dialogue.sessions.turn("conversation", dialogue.last_request | {"question": CAUSE}, RejectedEngine())
        self.assertEqual(dialogue.send(CAUSE)["pedagogie"]["objectif"], "assumption")

    def test_later_confirmation_keeps_trace_proof_on_its_original_version(self):
        dialogue = Dialogue(guided=True)
        dialogue.through("comparaison")
        dialogue.send("toujours False")
        proof = dialogue.send(CAUSE)["pedagogie"]["acquis"]["trace"]
        change = dialogue.send("J’ai modifié le programme.", code=dialogue.request["code"].replace("m = 0", "m = tab[0]"))
        state = change["pedagogie"]
        self.assertFalse(state["faits_trace"])
        self.assertEqual(state["acquis"]["trace"], proof)
        self.assertNotEqual(proof["question"]["code_structure"], change["analysis"]["structure_digest"])


if __name__ == "__main__":
    unittest.main()
