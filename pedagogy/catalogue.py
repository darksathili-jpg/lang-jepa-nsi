"""Exercices et indices rédigés pour le parcours guidé."""

import json
from pathlib import Path

from tutor.curriculum import LEVELS, STAGES


EXERCISES = {item["id"]: item for item in json.loads(
    Path(__file__).with_name("exercices.json").read_text(encoding="utf-8")
)}


def for_level(level):
    return [
        {key: exercise[key] for key in ("id", "title", "statement", "code", "notion", "objective")}
        for exercise in EXERCISES.values() if exercise["level"] == level
    ]


def validate_catalogue():
    for exercise in EXERCISES.values():
        if exercise["level"] not in LEVELS or len(exercise["hints"]) != len(STAGES):
            raise ValueError("Niveau NSI ou progression d’indices invalide.")
        for field in ("statement", "objective", "error", "notion", "tests"):
            if not exercise[field]:
                raise ValueError(f"Métadonnée pédagogique absente : {field}")
        for hint in exercise["hints"]:
            if not hint["indice"] or not hint["question"].endswith("?"):
                raise ValueError("Un indice doit guider vers une question.")
