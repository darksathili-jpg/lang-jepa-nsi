"""Sélection d’indices rédigés à partir des étapes et des observations déclarées."""

import re
import time

from pedagogy.catalogue import EXERCISES
from tutor.analysis import analyze
from tutor.curriculum import STAGES
from tutor.dialogue import DialogueError, maximum_reply, normalized, validate


def guided_stage(exercise, words, history, facts):
    previous = history[-1] if history else None
    stage = previous["stage"] if previous else 1
    if not previous or facts["syntax"]:
        return stage
    maximum = exercise["id"] == "maximum"
    observation = bool(re.search(r"\d|j'ai (?:test|essay|obtenu|trace)|je (?:vois|trouve|constate)", words))
    if maximum:
        observed_trace = bool(re.search(r"\bm\b.{0,35}(?:\d|reste|change)|0\s*[,;]\s*0", words))
    else:
        observed_trace = observation
    if stage >= 3 and facts["notions"] and previous["digest"] != facts["structure_digest"]:
        if not maximum or (facts["maximum_function"] and not facts["maximum_zero"]):
            return 5
    if stage == 5 and maximum and facts["maximum_zero"]:
        return 4
    if stage == 1 and (observation or re.search(r"je ne sais|aucune idee", words)):
        return 2
    if stage == 2 and observation:
        return 3
    if stage == 3 and observed_trace:
        return 4
    return stage


def respond_guided(payload, *, progress=None, turn=1, history_limit=3):
    started = time.perf_counter()
    level, statement, code, question, history = validate(payload, history_limit=history_limit)
    exercise_id = payload.get("exercise")
    exercise = EXERCISES.get(exercise_id) if isinstance(exercise_id, str) else None
    if exercise is None or exercise["level"] != level:
        raise DialogueError("Choisissez un exercice du niveau indiqué.")
    if exercise_id == "maximum" and progress is not None:
        answer, _ = maximum_reply(None, payload | {"history": []}, progress, turn)
        return answer
    facts = analyze(code)
    stage = guided_stage(exercise, normalized(question), history, facts)
    diagnostic = "Syntaxe analysée. Le résultat du programme reste à vérifier."
    hint = exercise["hints"][stage - 1]
    if not code.strip():
        diagnostic = "Aucune instruction Python à analyser."
        hint = {"indice": "Colle le code que tu veux étudier.", "question": "Quelle fonction dois-tu examiner ?"}
    elif facts.get("analysis_too_deep"):
        diagnostic = "Expression trop imbriquée pour l’analyse locale."
        hint = {"indice": "Isole une partie de l’expression avant de l’examiner.",
                "question": "Quel fragment plus court veux-tu analyser ?"}
    elif facts["syntax"]:
        diagnostic = f"Syntaxe Python signalée près de la ligne {facts['syntax']}."
        hint = {"indice": "Compare le bloc avec les instructions voisines.",
                "question": "Quel retrait ou signe manque à cette instruction ?"}
    elif stage >= 2 and exercise_id == "maximum" and facts["maximum_zero"]:
        diagnostic = "Le parseur repère une affectation de 0 à m et une boucle bornée dans maximum."
    elif stage >= 2 and exercise_id == "boucle-while" and facts["unchanged_guard"]:
        diagnostic = f"Aucune affectation directe à {facts['unchanged_guard']} dans le corps de la boucle."
    if stage == 5 and not facts["syntax"] and facts["maximum_function"] and exercise_id == "maximum" and not re.search(
        r"non[- ]vide", normalized(statement),
    ):
        hint = {
            "indice": "Rejoue le cas des entiers négatifs et examine aussi le contrat pour [].",
            "question": "Que doit préciser ta spécification pour une liste vide ?",
        }
    return {
        **hint, "stage": stage, "stage_name": STAGES[stage][0],
        "analysis": facts | {"digest": facts["structure_digest"]}, "diagnostic": diagnostic,
        "provenance": {"hint": "Règle pédagogique · indice rédigé", "diagnostic": "Analyse statique Python",
                       "jepa": "Aucune contribution de LANG-JEPA à cet indice."},
        "seconds": time.perf_counter() - started,
    }
