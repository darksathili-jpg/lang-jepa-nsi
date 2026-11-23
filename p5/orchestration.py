"""Orchestration P5. Les règles bornent les choix avant l'appel du prédicteur."""

from dataclasses import dataclass, field, replace
from pathlib import Path
import threading
import time

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
    "portee": "clarifier", "separer": "tracer", "consequence": "justifier",
    "branche": "clarifier", "chaine": "tracer",
}


@dataclass(frozen=True)
class Experiment:
    mode: str
    model: object = None
    error: str = ""
    donors: dict | None = None
    state: str | None = None
    checks: dict = field(default_factory=dict)
    seconds: float | None = None
    running: object = field(default_factory=threading.Lock, compare=False, repr=False)

    def status(self):
        if self.mode == "c":
            status = self.state or ("ready" if self.model else "error" if self.error else "absent")
            return {"mode": "C · JEPA expérimental + orchestrateur + SmolLM3",
                    "state": "working" if status == "ready" and self.running.locked() else status,
                    "name": self.model.identity if self.model else None,
                    "detail": self.error or "Expérimentation sur le maximum de référence.",
                    "checks": self.checks.copy(), "times": {"probe_s": self.seconds} if self.seconds is not None else {}}
        return {"mode": {"a": "A · LLM seul", "b": "B · Orchestrateur sans JEPA",
                         "neutralise": "C · Signal neutralisé", "melange": "C · Signal mélangé"}[self.mode],
                "state": "inactive", "name": None, "detail": ""}

    def require_model(self):
        if self.mode in {"c", "melange"} and self.model is None:
            raise ContractError(self.error or "JEPA indisponible. Relance l’atelier en profil B pour travailler sans JEPA.")

    def rank(self, situation, options, turn):
        """Classer des interventions déjà admissibles avec ou sans signal latent."""
        if self.mode not in {"c", "melange"}:
            return options, "neutralise" if self.mode == "neutralise" else "regles", None
        self.require_model()
        encoded = self.donors.get(turn) if self.mode == "melange" and self.donors else situation
        if self.mode == "melange" and (not self.donors or encoded is None):
            raise ContractError("Représentation mélangée manquante pour ce tour.")
        with self.running:
            scores = validate_scores(self.model.scores(encoded))
        ranked = sorted(options, key=lambda option: -scores[option[0]])
        return ranked, "jepa" if self.mode == "c" else "melange", scores

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
            with self.running:
                scores = validate_scores(self.model.scores(donor))
            ranked = sorted(options, key=lambda option: -scores[APPROACHES[option[0]]])
            source = "jepa" if self.mode == "c" else "melange"
        method, question = ranked[0]
        model = self.model.identity if scores is not None else None
        justification = ("Cosinus latent entre la cible prédite et les interventions autorisées."
                         if scores is not None else "Première intervention autorisée sans répétition.")
        decision = Decision(progress.goal, method, APPROACHES[method], source, model, justification)
        return decision, question, method != default


def open_experiment(mode, directory: Path | None, *, recipe=None):
    if mode != "c":
        return Experiment(mode)
    present = {"manifeste": bool(directory and (directory / "manifest.json").is_file()),
               "poids": bool(directory and (directory / "weights.npz").is_file()),
               "integrite": False, "chargement": False, "prediction": False, "selection": False}
    if not (present["manifeste"] and present["poids"]):
        state = "incomplete" if present["manifeste"] or present["poids"] else "absent"
        error = "JEPA indisponible. Lance Installer-Modeles.cmd pour préparer les poids du profil expérimental."
        return Experiment(mode, error=error, state=state, checks=present)
    tick = time.monotonic()
    try:
        from p5.jepa import load
        from pedagogy.catalogue import EXERCISES
        from pedagogy.progress import Progress
        from tutor.analysis import analyze

        model = load(directory)
        present.update(integrite=True, chargement=True)
        if recipe:
            expected = {"config": recipe["config"], "graine": recipe["seed"], "epoques": recipe["epochs"],
                        "corpus_sha256": recipe["corpus_sha256"], "numpy": "2.3.5"}
            if any(model.metadata.get(key) != value for key, value in expected.items()):
                return Experiment(mode, error="Ce modèle n’a pas le profil de reconstruction P5 verrouillé.",
                                  state="incompatible", checks=present)
        loaded = Experiment(mode, model, checks=present)
        exercise = EXERCISES["maximum"]
        request = {"class": "premiere", "statement": exercise["statement"], "code": exercise["code"],
                   "question": "Le résultat observé vaut zéro."}
        options = MAXIMUM_GOALS["observed"][2]
        decision, question, _ = loaded.select(request, Progress(), analyze(request["code"]), [], 1, options)
        if decision.source != "jepa" or (decision.intervention, question) not in options:
            raise ContractError("La prédiction latente n’a pas produit de sélection admissible.")
        present.update(prediction=True, selection=True)
        return replace(loaded, seconds=round(time.monotonic() - tick, 4))
    except ImportError:
        return Experiment(mode, error="La pile NumPy P5 est absente ou incompatible.", state="incompatible", checks=present)
    except ContractError as exc:
        return Experiment(mode, error=str(exc), state="error", checks=present)
