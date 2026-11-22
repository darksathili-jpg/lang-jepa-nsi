"""Orchestration P5. Les règles bornent les choix avant l'appel du prédicteur."""

from dataclasses import dataclass
from pathlib import Path

from p5.contract import ContractError, Decision, Situation, validate_scores
from p5.data import static_facts
from tutor.curriculum import MAXIMUM_GOALS


APPROACHES = {
    "essai": "confronter", "proposition": "clarifier", "prévision": "confronter",
    "spécification": "justifier", "ordre": "tracer", "confrontation": "confronter",
    "trace": "tracer", "condition": "justifier", "tableau": "tracer", "ligne": "clarifier",
    "hypothèse": "justifier", "contre-exemple": "confronter", "invariant": "justifier",
    "propriété": "justifier", "validation": "clarifier", "contrainte": "justifier",
    "rédaction": "clarifier", "cas discriminant": "confronter", "contrat": "justifier",
    "domaine": "clarifier",
}


@dataclass(frozen=True)
class Experiment:
    mode: str
    model: object = None
    error: str = ""
    donors: dict | None = None

    def status(self):
        if self.mode == "c":
            return {"mode": "C · JEPA expérimental + orchestrateur + SmolLM3",
                    "state": "ready" if self.model else "error" if self.error else "absent",
                    "name": self.model.identity if self.model else None,
                    "detail": self.error or "Expérimentation sur le maximum de référence."}
        return {"mode": {"a": "A · LLM seul", "b": "B · Orchestrateur sans JEPA",
                         "neutralise": "C · Signal neutralisé", "melange": "C · Signal mélangé"}[self.mode],
                "state": "inactive", "name": None, "detail": ""}

    def require_model(self):
        if self.mode in {"c", "melange"} and self.model is None:
            raise ContractError(self.error or "JEPA indisponible. Relance l’atelier en profil B pour travailler sans JEPA.")

    def select(self, request, progress, facts, history, turn, options):
        default, _ = options[0]
        ranked = options
        scores = None
        source = "neutralise" if self.mode == "neutralise" else "regles"
        if self.mode in {"c", "melange"}:
            self.require_model()
            situation = Situation(
                request["class"], progress.notion, request["statement"],
                static_facts(request["code"], facts), request["question"],
                tuple(exchange["learner"][:280] for exchange in history),
                tuple(evidence.criterion[:280] for evidence in progress.confirmed.values()),
                tuple(evidence.criterion[:280] for evidence in progress.errors.values()),
                MAXIMUM_GOALS[progress.goal][0],
                tuple(question[:280] for _, _, question in list(progress.questions)[-8:]),
            )
            donor = self.donors.get(turn) if self.mode == "melange" and self.donors else None
            if self.mode == "melange" and donor is None:
                raise ContractError("Représentation mélangée manquante pour ce tour.")
            donor = donor or situation
            scores = validate_scores(self.model.scores(donor))
            ranked = sorted(options, key=lambda option: -scores[APPROACHES[option[0]]])
            source = "jepa" if self.mode == "c" else "melange"
        method, question = ranked[0]
        model = self.model.identity if scores is not None else None
        justification = ("Cosinus latent entre la cible prédite et les interventions autorisées."
                         if scores is not None else "Première intervention autorisée sans répétition.")
        decision = Decision(progress.goal, method, APPROACHES[method], source, model, justification)
        return decision, question, method != default


def open_experiment(mode, directory: Path | None):
    if mode != "c" or directory is None or not directory.is_dir():
        return Experiment(mode)
    try:
        from p5.jepa import load

        return Experiment(mode, load(directory))
    except ImportError:
        return Experiment(mode, error="Dépendance JEPA absente. Installez la pile NumPy P5 hors ligne.")
    except ContractError as exc:
        return Experiment(mode, error=str(exc))
