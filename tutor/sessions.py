"""Sessions locales bornées et progression sous le contrôle du serveur."""

from collections import OrderedDict, deque
from copy import deepcopy
from dataclasses import dataclass, field
import re
import secrets
import threading
import time

from pedagogy.progress import Progress, code_matches_maximum
from pedagogy.interpretation import interpret
from pedagogy.workshop import Workshop, select_spec, workshop_reply
from tutor.analysis import analyze
from tutor.dialogue import DialogueError, maximum_reply, normalized, respond, validate
from tutor.guided import respond_guided


RECENT_TURNS = 6
SESSION_TTL = 45 * 60
MAX_SESSIONS = 32


class SessionConflict(DialogueError):
    pass


@dataclass
class Session:
    scope: tuple
    statement: str
    touched: float
    round: int = 0
    recent: deque = field(default_factory=lambda: deque(maxlen=RECENT_TURNS))
    progress: Progress | None = None
    workshop: Workshop | None = None
    last_input: tuple | None = None
    last_answer: dict | None = None
    lock: threading.Lock = field(default_factory=threading.Lock)


class Sessions:
    def __init__(self, experiment=None, *, case_based=True, max_help=4):
        self.items = OrderedDict()
        self.lock = threading.Lock()
        self.experiment = experiment
        self.case_based = case_based
        self.max_help = max_help

    def pick(self, token, scope, statement):
        now = time.monotonic()
        with self.lock:
            for name, session in tuple(self.items.items()):
                if now - session.touched > SESSION_TTL and not session.lock.locked():
                    del self.items[name]
            if token is None:
                while len(self.items) >= MAX_SESSIONS:
                    oldest = next((name for name, item in self.items.items() if not item.lock.locked()), None)
                    if oldest is None:
                        raise SessionConflict("Tous les dialogues sont occupés. Réessaie dans un instant.")
                    del self.items[oldest]
                token = secrets.token_urlsafe(24)
                self.items[token] = Session(scope, statement, now)
            session = self.items.get(token)
            if session is None or session.scope != scope:
                raise SessionConflict("Ce dialogue a expiré ou changé de contexte. Choisis Recommencer.")
            if not session.lock.acquire(blocking=False):
                raise SessionConflict("Une réponse est déjà en préparation.")
            self.items.move_to_end(token)
            session.touched = now
            return token, session

    def turn(self, mode, payload, engine, *, capture=None):
        if not isinstance(payload, dict):
            raise DialogueError("La demande doit être structurée.")
        # La progression, l’analyse et l’historique envoyés par le navigateur sont ignorés.
        level, statement, code, question, _ = validate(payload | {"history": []})
        exercise = payload.get("exercise") if mode == "guided" else None
        if exercise is not None and (not isinstance(exercise, str) or len(exercise) > 80):
            raise DialogueError("Exercice invalide.")
        token = payload.get("session")
        sequence = payload.get("turn", 0)
        if (token is not None and (not isinstance(token, str) or not re.fullmatch(r"[A-Za-z0-9_-]{32}", token))
                or type(sequence) is not int or sequence < 0 or token is None and sequence != 0):
            raise DialogueError("Identifiant ou numéro de tour invalide.")
        key = (statement, code, question)
        token, session = self.pick(token, (mode, level, exercise), statement)
        try:
            if sequence == session.round - 1 and key == session.last_input:
                return session.last_answer
            if sequence != session.round:
                raise SessionConflict("Ce tour n’est plus à jour. Réessaie depuis le dernier échange.")

            same_statement = normalized(statement) == normalized(session.statement)
            history = list(session.recent) if same_statement else []
            progress = deepcopy(session.progress) if same_statement else None
            workshop = deepcopy(session.workshop) if same_statement else None
            facts = analyze(code)
            experiment = self.experiment if mode == "conversation" else None
            if experiment:
                experiment.require_model()
            model_only = bool(experiment and experiment.mode == "a")
            historical = not self.case_based and not model_only
            maximum = historical and (exercise == "maximum" or mode == "conversation" and (
                progress is not None or facts["maximum_function"] and code_matches_maximum(code, "zero") and re.search(
                    r"maximum|plus grande valeur|plus grand entier", normalized(statement),
                )
            ))
            if maximum and progress is None:
                progress = Progress(multi_test=bool(experiment))

            request = {"class": level, "exercise": exercise, "statement": statement,
                       "code": code, "question": question, "history": history}
            raw = None
            spec = select_spec(exercise, statement, level, workshop, guided=mode == "guided") if self.case_based and not model_only else None
            if spec:
                workshop = workshop or Workshop(spec.id)
                message = interpret(question, spec)
                answer, raw = workshop_reply(engine if mode == "conversation" else None, request, facts, spec,
                                             workshop, message, sequence + 1, experiment=experiment, max_help=self.max_help)
            elif mode == "guided":
                answer = respond_guided(request, progress=progress, turn=sequence + 1, history_limit=RECENT_TURNS)
            elif maximum:
                answer, raw = maximum_reply(engine, request if experiment else request | {"history": []},
                                            progress, sequence + 1, experiment=experiment)
            else:
                answer, raw = respond(engine, request, history_limit=RECENT_TURNS)
                answer["generation"] = "affiche"
                answer["provenance"] = {
                    "hint": engine.status()["name"] + " · génération locale",
                    "diagnostic": "Analyse statique Python",
                    "jepa": "Aucune contribution de LANG-JEPA.",
                }
                if experiment and experiment.mode != "a":
                    answer["provenance"]["jepa"] = "Hors du scénario expérimental du maximum · Conversation locale sans JEPA."

            if not same_statement:
                session.recent.clear()
            session.statement = statement
            session.progress = progress
            session.workshop = workshop
            session.recent.append({
                "learner": question,
                "assistant": " ".join(filter(None, (answer.get("feedback") if spec else None,
                                                        answer["indice"], answer["question"])))[:640],
                "stage": answer["stage"], "digest": answer["analysis"]["digest"],
            })
            session.round += 1
            session.last_input = key
            session.last_answer = answer | {"session": token, "turn": session.round}
            if capture is not None:
                capture.append(raw)
            return session.last_answer
        finally:
            session.lock.release()
