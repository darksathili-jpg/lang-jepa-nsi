"""Contrat versionné pour une décision pédagogique experimentalement assistée."""

from dataclasses import dataclass
import math


SCHEMA = 1
ACTIONS = {
    "clarifier": "Préciser une observation, une entrée ou le sens de la question.",
    "tracer": "Suivre pas à pas une valeur, les états ou les appels sur un exemple.",
    "confronter": "Comparer deux cas, concevoir un test ou chercher un contre-exemple.",
    "justifier": "Expliquer une propriété, une garantie ou une précondition avec des raisons.",
}


class ContractError(ValueError):
    """Contrat d'entrée, de décision ou de poids invalide."""


@dataclass(frozen=True)
class Situation:
    niveau: str
    notion: str
    enonce: str
    faits: tuple[str, ...]
    message: str
    reponses_precedentes: tuple[str, ...]
    acquis: tuple[str, ...]
    erreurs: tuple[str, ...]
    objectif: str
    interventions: tuple[str, ...]

    def __post_init__(self):
        if self.niveau not in ("premiere", "terminale"):
            raise ContractError("Niveau NSI non reconnu.")
        for value, bound in ((self.notion, 120), (self.enonce, 1600), (self.message, 720), (self.objectif, 120)):
            if not isinstance(value, str) or not value.strip() or len(value) > bound:
                raise ContractError("Champ de situation invalide.")
        for group in (self.faits, self.reponses_precedentes, self.acquis, self.erreurs, self.interventions):
            if not isinstance(group, tuple) or len(group) > 12 or any(
                not isinstance(item, str) or not item.strip() or len(item) > 280 for item in group
            ):
                raise ContractError("Résumé de situation invalide.")

    def text(self):
        return "\n".join((
            f"niveau {self.niveau} notion {self.notion}", f"énoncé {self.enonce}",
            "constats " + " ".join(self.faits), f"élève {self.message}", f"objectif {self.objectif}",
            "réponses précédentes " + " ".join(self.reponses_precedentes),
            "preuves " + " ".join(self.acquis), "difficultés " + " ".join(self.erreurs),
            "approches précédentes " + " ".join(self.interventions),
        ))


@dataclass(frozen=True)
class Decision:
    objectif: str
    intervention: str
    approche: str
    source: str
    modele: str | None
    justification: str

    def __post_init__(self):
        if (not isinstance(self.objectif, str) or not self.objectif or not isinstance(self.intervention, str)
                or not self.intervention or self.approche not in ACTIONS
                or self.source not in {"regles", "jepa", "neutralise", "melange"}
                or (self.source in {"jepa", "melange"}) != bool(self.modele)
                or not isinstance(self.justification, str) or not self.justification):
            raise ContractError("Décision pédagogique invalide.")

    def public(self):
        return {
            "schema": SCHEMA, "objectif": self.objectif, "intervention": self.intervention,
            "approche": self.approche, "source": self.source, "modele": self.modele,
            "justification": self.justification,
        }


def validate_scores(scores):
    if not isinstance(scores, dict) or set(scores) != set(ACTIONS) or any(
        not isinstance(value, (int, float)) or not math.isfinite(value) or not -1.00001 <= value <= 1.00001
        for value in scores.values()
    ):
        raise ContractError("Le prédicteur n’a pas fourni tous les cosinus finis attendus.")
    return scores
