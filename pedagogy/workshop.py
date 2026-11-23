"""Décision pédagogique sur un essai actif et des preuves versionnées."""

from collections import deque
from dataclasses import asdict, dataclass, field, replace
import json
import re
import time

from p5.contract import Decision, Situation
from pedagogy.cases import SPECS, TestCase
from pedagogy.catalogue import EXERCISES
from pedagogy.interpretation import Intent, interpret, verified_interpretation
from pedagogy.progress import Evidence, normalize
from tutor.curriculum import STAGES
from tutor.engine import EngineError


LABELS = {"observed": "Identifier le comportement", "expected": "Déterminer le résultat attendu",
          "trace": "Expliquer le comportement", "assumption": "Identifier l’hypothèse incorrecte",
          "strategy": "Proposer une stratégie", "verification": "Vérifier sur un nouvel essai",
          "contract": "Examiner la précondition"}
STAGE = {"observed": 1, "expected": 2, "trace": 3, "assumption": 4,
         "strategy": 4, "verification": 4, "contract": 5}
OPENERS = {Intent.EXPLAIN, Intent.DEFINE, Intent.TEST}
CORRECTION_PRINCIPLES = {
    "maximum": "Pars d’une valeur de l’entrée et conserve la plus grande des valeurs déjà examinées.",
    "boucle-while": "Fais décroître le compteur à chaque passage jusqu’à rendre la condition fausse.",
    "dictionnaire-comptage": "Initialise le compteur d’un mot lors de sa première occurrence, puis incrémente-le.",
    "recursivite-base": "Fais évoluer l’argument vers un cas de base valide à chaque appel.",
}


def select_spec(exercise, statement, level, existing=None):
    if existing:
        return SPECS[existing.exercise]
    actual = normalize(statement)
    for key, spec in SPECS.items():
        if spec.level == level and (key == exercise or actual == normalize(EXERCISES[key]["statement"])):
            return spec
    if level == "premiere" and re.search(r"\b(?:maximum|plus grande valeur|plus grand entier)\b", actual):
        return SPECS["maximum"]
    return None


def rendered(value):
    return json.dumps(list(value) if isinstance(value, tuple) else value, ensure_ascii=False)


@dataclass
class Workshop:
    exercise: str
    code: str | None = None
    active: TestCase | None = None
    cases: deque = field(default_factory=lambda: deque(maxlen=10))
    evidence: dict[str, Evidence] = field(default_factory=dict)
    errors: dict[str, Evidence] = field(default_factory=dict)
    asked: deque = field(default_factory=lambda: deque(maxlen=28))
    transitions: deque = field(default_factory=lambda: deque(maxlen=32))
    goal: str = "observed"
    target: str | None = None
    target_turn: int = 0
    support: int = 1
    solution_requests: int = 0

    def take(self, case):
        if self.active is not None:
            self.cases.append(self.active)
        self.active = case
        self.evidence.clear()
        self.errors.clear()
        self.target = None
        self.support = 1

    def confirm(self, goal, turn, text, reason):
        self.evidence.setdefault(goal, Evidence(turn, text, reason))
        self.errors.pop(goal, None)

    def snapshot(self, spec, status, feedback, message, decision, latent, clarification):
        def proof(records):
            return {key: {"tour": value.turn, "extrait": value.excerpt, "critere": value.criterion}
                    for key, value in records.items()}
        return {"schema": 1, "notion": spec.notion, "objectif": self.goal, "objectif_libelle": LABELS[self.goal],
                "libelles_objectifs": LABELS, "acquis": proof(self.evidence), "erreurs": proof(self.errors),
                "acquis_non_demontres": [self.goal], "changements_objectif": list(self.transitions),
                "derniere_intervention": decision, "experience_jepa": latent, "essai_actif": self.active.public() if self.active else None,
                "essais_precedents": [case.public() for case in self.cases], "interpretation": message.public(),
                "clarification": clarification, "niveau_aide": self.support,
                "questions": [{"tour": turn, "strategie": action, "texte": question} for _, turn, action, question in self.asked],
                "evaluation": {"statut": status, "commentaire": feedback, "methode": "Critères de l’exercice et analyse statique"}}


def trace_facts(text, static):
    """Reconnaître des assertions vérifiables contre une forme connue du programme."""
    words = normalize(text.replace("`", ""))
    if static.kind == "sentinelle":
        bad = bool(re.search(r"\bm\s*(?:vaut|=)\s*(?:false|faux|true|vrai)\b|\bpas (?:toujours )?fauss?e?s?\b|"
                             r"l'affectation s'execute\b(?!\s+(?:si|quand)\b)", words))
        false = bool(re.fullmatch(r"(?:toujours )?(?:false|faux|fausse)[.! ]*", words)
                     or re.search(r"\b(?:condition|conditions|comparaison|comparaisons)\s+(?:est|sont)\s+(?:toujours )?fausses?\b"
                                  r"|\baucun\w*.{0,22}ne depasse\w* 0\b", words))
        skipped = bool(re.search(r"(?:ne|n')\s*(?:affecte|execute|met|s'execute)\w*\s+(?:pas|jamais)|"
                                 r"\b(?:m = valeur|l'affectation|l'instruction) ne s'execute pas\b", words))
        unchanged = bool(re.search(r"\b(?:m|elle|il) (?:reste|vaut|garde) (?:a )?0\b", words))
        causal = skipped and unchanged and bool(re.search(r"\b(?:donc|comme|car|puisque|parce que)\b", words))
        return false, causal, bad
    if static.kind == "garde_inchangee":
        return False, bool(re.search(r"\b(?:n|compteur|variable)\b.{0,18}(?:ne change pas|reste identique|n'est pas modifi)", words)), False
    if static.kind == "cle_absente":
        return False, bool(re.search(r"\bcle\b.{0,28}(?:absente|n'existe pas|n'est pas presente)", words)), False
    if static.kind in {"base_inaccessible", "base_absente"}:
        direction = "augmente" if " +" in static.detail else "diminue"
        causal = bool(re.search(r"\b(?:n|argument)\b.{0,22}" + direction + r"\b", words)
                      and re.search(r"(?:n'atteint|ne peut pas atteindre|s'eloigne|n'arrive|n'ira pas)", words))
        return False, causal and static.kind == "base_inaccessible", False
    return False, False, False


def ask(state, spec):
    case = state.active
    value = rendered(case.entree) if case else ""
    if not case:
        return [("confronter", "Quel petit test choisirais-tu pour observer la sortie du programme ?"),
                ("clarifier", f"Quelle entrée simple veux-tu examiner avec {spec.function} ?"),
                ("tracer", "Quels arguments écrirais-tu pour un premier essai ?")]
    if not case.precondition or state.goal == "contract":
        return [("justifier", f"Que dit le contrat de l’exercice sur l’entrée {value} ?"),
                ("clarifier", "Quelle précondition faut-il vérifier avant de choisir cet essai ?")]
    if state.goal in {"observed", "verification"}:
        return [("confronter", f"Pour {value}, quel résultat prédis-tu avec cette version du programme ?"),
                ("tracer", f"Quelle sortie prévois-tu en suivant le programme sur {value} ?"),
                ("clarifier", "Quel résultat prévois-tu, ou quel comportement observes-tu ?")]
    if state.goal == "expected":
        return [("justifier", f"D’après l’énoncé, quel résultat devrait-on obtenir pour {value} ?"),
                ("confronter", "La réponse attendue et ta prévision sont-elles compatibles ?")]
    if state.goal == "assumption":
        return [("justifier", "Quelle hypothèse de départ explique cet écart ?"), ("confronter", spec.suggestion)]
    if state.goal == "strategy":
        return [("confronter", spec.suggestion), ("tracer", "Comment vérifierais-tu ta nouvelle méthode sur un autre essai ?")]
    if case.statique and case.statique.kind == "sentinelle" and max(case.entree) <= 0:
        if "comparaison" not in state.evidence:
            return [("tracer", "Quand la valeur examinée est négative et que m vaut 0, que vaut valeur > m ?"),
                    ("confronter", f"Sur {value}, un élément peut-il rendre valeur > m vraie ?"),
                    ("clarifier", "Regarde la condition seule. Est-elle vraie pour une valeur négative face à zéro ?")]
        return [("justifier", "Puisque la condition est fausse, que devient l’affectation et quelle valeur conserve m ?"),
                ("tracer", "Suis le bloc indenté. Quelle instruction est sautée et avec quel effet sur m ?")]
    return [("tracer", spec.suggestion), ("clarifier", "Sur cet essai, quel changement d’état repères-tu ?"),
            ("justifier", "Quelle ligne de ton programme appuie cette observation ?")]


def explain(spec, case, strong=False):
    if case and case.statique and case.precondition:
        if case.statique.kind == "base_inaccessible":
            return case.statique.detail + " Suis les arguments pour voir si le test d’arrêt deviendra vrai."
        return case.statique.detail or spec.focus
    if spec.id == "maximum" and strong:
        return "Si le test d’une condition est faux, les instructions de son bloc ne s’exécutent pas."
    return spec.focus


def choose(state, spec, experiment, request, turn):
    scope = (state.code, state.active.entree if state.active else None, state.goal,
             "comparaison" in state.evidence)
    options = [(action, text) for action, text in ask(state, spec)
               if not any(asked_scope == scope and text == old for asked_scope, _, _, old in state.asked)]
    if not options:
        return "", None, None
    decision = latent = None
    if experiment and spec.id == "maximum" and (
        state.active is None or state.active.statique and state.active.statique.kind == "sentinelle"
    ):
        case_summary = () if not state.active else (f"Essai actif {rendered(state.active.entree)}",)
        situation = Situation(request["class"], spec.notion, request["statement"], case_summary,
                             request["question"], tuple(h["learner"][:280] for h in request["history"]),
                             tuple(e.criterion for e in state.evidence.values()), tuple(e.criterion for e in state.errors.values()),
                             LABELS[state.goal], tuple(t[:280] for _, _, _, t in list(state.asked)[-6:]))
        ranked, source, scores = experiment.rank(situation, options, turn)
        action, question = ranked[0]
        model = experiment.model.identity if scores is not None else None
        reason = "Intervention admissible pour l’objectif et le même niveau d’aide."
        decision = Decision(state.goal, action, action, source, model, reason).public() | {
            "differe_des_regles": ranked[0] != options[0]
        }
        latent = {"situation": asdict(situation), "classement_regles": options, "classement_experimental": ranked,
                  "scores": scores, "retenue": question, "modele": model, "justification": reason}
    else:
        action, question = options[0]
    state.asked.append((scope, turn, action, question))
    return question, decision, latent


def handle_claims(state, message, turn, text):
    case = state.active
    feedback = []
    conflicting = {claim.role for claim in message.claims
                   if any(other.role is claim.role and other.value != claim.value for other in message.claims)}
    if conflicting:
        return "Tu cites des résultats différents pour le même rôle. Lequel veux-tu retenir ?"
    for claim in message.claims:
        if claim.role is Intent.EXPECT:
            if claim.value == case.attendu:
                state.confirm("expected", turn, text, "Résultat attendu conforme à la spécification.")
                feedback.append("Le résultat attendu correspond à l’énoncé.")
            else:
                feedback.append("Vérifie ce que l’énoncé demande pour cette entrée.")
            continue
        if claim.role is Intent.PREDICT:
            case = replace(case, predit=claim.value)
            feedback.append("Je note ta prédiction.")
        else:
            case = replace(case, declare=claim.value)
            feedback.append("Je note le résultat que tu déclares.")
        if case.statique and case.statique.kind in {"sentinelle", "accumulation", "retour"}:
            if claim.value == case.statique.result:
                state.confirm("observed", turn, text, "Valeur cohérente avec l’analyse statique du code courant.")
            elif case.statique.result is not None:
                state.errors["observed"] = Evidence(turn, text, "La valeur proposée contredit la forme statiquement reconnue.")
                feedback.append("Cette valeur mérite une vérification en suivant les instructions.")
    state.active = case
    if case.statique and case.statique.result is not None and case.statique.result != case.attendu and "observed" in state.evidence:
        feedback.append("Il y a un écart à expliquer entre le comportement du programme et le contrat.")
    return " ".join(dict.fromkeys(feedback))


def workshop_reply(engine, request, facts, spec, state, message, turn, *, experiment=None, max_help=4):
    started = time.perf_counter()
    text = request["question"]
    digest = facts["structure_digest"]
    before = state.goal
    expected_role = Intent.PREDICT if state.target == "prediction" and state.target_turn == turn - 1 and state.code == digest else (
        Intent.EXPECT if state.target == "attendu" and state.target_turn == turn - 1 and state.code == digest else None
    )
    if expected_role:
        message = interpret(text, spec, expected_role=expected_role)
    raw = None
    model_status = "non_sollicite"
    if engine and message.intentions == (Intent.UNKNOWN,) and len(text.split()) >= 5 and state.target != "condition":
        task = f"Notion : {spec.notion}. Objectif : {LABELS[state.goal]}."
        if state.active:
            task += f" Entrée étudiée : {rendered(state.active.entree)[:100]}."
        prompts = [{"role": "system", "content": "Identifie une demande d'aide locale. Cite un segment exact du message. Utilise abstention si incertain. Ne produis ni solution ni évaluation."},
                   {"role": "user", "content": f"{task} Message cité {json.dumps(text, ensure_ascii=False)}"}]
        try:
            raw = engine.generate(prompts, interpretation=True)
        except EngineError:
            model_status = "indisponible"
        else:
            message, accepted = verified_interpretation(raw, text, message)
            model_status = "interpretation_verifiee" if accepted else "ecarte"
    edited = bool(state.code and state.code != digest)
    if edited:
        state.take(spec.case(state.active.entree, state.active.auteur, request["code"], digest) if state.active else None)
        state.goal = "verification"
    state.code = digest
    feedback, hint, status = "", "", "partielle"
    decision = latent = None
    no_question = False
    if Intent.TOPIC in message.intentions:
        status = "changement_notion"
        feedback = f"Choisis un autre exercice pour travailler {message.topic}."
        no_question = True
    elif Intent.SOLUTION in message.intentions:
        state.solution_requests += 1
        feedback = "Je peux t’aider à débloquer une étape de ton raisonnement."
        hint = explain(spec, state.active, strong=state.solution_requests >= 3 and max_help >= 5)
        if max_help == 6 and state.solution_requests >= 3 and "trace" in state.evidence:
            hint = CORRECTION_PRINCIPLES[spec.id]
        state.support = min(max_help, max(state.support, 4 if state.solution_requests >= 2 else 3))
    elif message.ambiguities or len(message.tests) > 1:
        status = "ambigue"
        feedback = message.ambiguities[0] if message.ambiguities else "Choisis l’un de ces essais pour que nous suivions ses résultats."
        no_question = True
    else:
        if message.tests:
            value = message.tests[0]
            if not state.active or state.active.entree != value:
                state.take(spec.case(value, "eleve", request["code"], digest))
                state.goal = "verification" if edited else "observed"
            feedback = f"Je retiens ton essai {rendered(value)}."
        if not state.active and Intent.EXPLAIN not in message.intentions and Intent.DEFINE not in message.intentions and (
            state.target == "essai" and Intent.CONFUSED in message.intentions
        ):
            state.take(spec.case(spec.example, "tuteur", request["code"], digest))
            feedback = f"Essayons {rendered(spec.example)}."
        case = state.active
        if facts["syntax"]:
            feedback = f"Python signale un problème de syntaxe près de la ligne {facts['syntax']}."
            no_question = True
        elif case and not case.precondition:
            state.goal = "contract"
            feedback += " " + spec.precondition
            if Intent.REASON in message.intentions and re.search(r"non vide|hors (?:contrat|precondition)|naturel", normalize(text)):
                state.confirm("contract", turn, text, "Précondition reliée à l’entrée proposée.")
                status = "correcte"
        elif Intent.EXPLAIN in message.intentions or Intent.DEFINE in message.intentions:
            status = "demande"
            feedback = "Examinons le comportement du programme." if Intent.EXPLAIN in message.intentions else "Reprenons la notion en jeu."
            hint = explain(spec, case, strong=True)
        elif not message.claims and (Intent.HINT in message.intentions or Intent.CONFUSED in message.intentions) and not feedback:
            state.support = min(max_help, state.support + 1)
            feedback = "Reprenons une seule étape du raisonnement."
            hint = explain(spec, case, strong=state.support >= 3)
        elif case:
            if state.goal in {"observed", "verification"} and case.statique and case.statique.kind in {
                "base_inaccessible", "base_absente", "garde_inchangee", "cle_absente"
            }:
                state.goal = "trace"
                hint = case.statique.detail
            if message.claims:
                feedback = (feedback + " " + handle_claims(state, message, turn, text)).strip()
                case = state.active
                if "observed" in state.evidence and state.goal in {"observed", "verification", "expected"}:
                    state.goal = "trace" if "expected" in state.evidence else "expected"
                    if case.statique and case.statique.result == case.attendu and "expected" in state.evidence:
                        state.confirm("verification", turn, text, "Résultat prévu ou déclaré cohérent avec le contrat et la forme reconnue.")
                        state.goal = "contract"
                status = "incorrecte" if "observed" in state.errors else "correcte" if "verification" in state.evidence else "partielle"
            if state.goal == "trace" and case.statique:
                false, causal, wrong = trace_facts(text, case.statique)
                target = state.target if state.target_turn == turn - 1 else None
                negative = spec.id == "maximum" and case.statique.kind == "sentinelle" and max(case.entree) <= 0
                if wrong:
                    feedback = "La comparaison produit un booléen. La variable garde une valeur entière. Vérifie le bloc concerné."
                    status = "incorrecte"
                elif causal and (case.statique.kind != "sentinelle" or negative and (false or "comparaison" in state.evidence)):
                    state.confirm("trace", turn, text, "Le raisonnement concorde avec la forme statiquement reconnue pour cet essai.")
                    feedback = "Ton explication relie la condition, les instructions et l’effet sur cet essai." if negative else "Ton explication concorde avec le comportement analysé."
                    state.goal = "assumption"
                    status = "correcte"
                elif false and negative and target == "condition":
                    state.confirm("comparaison", turn, text, "La comparaison avec zéro est fausse dans le cas négatif proposé.")
                    feedback = "Oui, la comparaison est fausse sur ce cas. Cherchons la conséquence sur les instructions."
            if state.goal in {"assumption", "strategy"} and Intent.CHANGE in message.intentions:
                state.goal = "verification"
                feedback = "Vérifions ton idée sur le code modifié et une nouvelle entrée."
            elif state.goal == "assumption" and before == "assumption" and Intent.REASON in message.intentions:
                words = normalize(text)
                if (spec.id == "maximum" and re.search(r"\b0\b", words) and re.search(r"depart|initial", words)
                        and re.search(r"superieur|plus grand|depass", words) and not re.search(r"\b(?:pas|jamais)\b", words)):
                    state.confirm("assumption", turn, text, "Le seuil initial peut dépasser toutes les valeurs du test.")
                    state.goal = "strategy"
            if case.statique and case.statique.kind == "base_inaccessible" and not feedback:
                feedback = case.statique.detail
        if not feedback:
            feedback = "Précise ce que tu veux tester ou la difficulté que tu rencontres."
            status = "ambigue"
    question, decision, latent = ("", None, None) if no_question else choose(state, spec, experiment, request, turn)
    if not question and not no_question:
        state.support = min(max_help, state.support + 1)
        hint = explain(spec, state.active, strong=state.support >= 4)
    if state.goal == "trace" and question and "comparaison" not in state.evidence and (
        "valeur > m" in question or "Est-elle vraie" in question
    ):
        state.target = "condition"
    elif question and state.active is None:
        state.target = "essai"
    elif question and state.goal in {"observed", "verification"}:
        state.target = "prediction"
    else:
        state.target = "attendu" if question and state.goal == "expected" else None
    state.target_turn = turn
    if before != state.goal:
        state.transitions.append({"tour": turn, "avant": before, "apres": state.goal, "motif": feedback.strip()})
    stage = STAGE[state.goal]
    if latent:
        latent["affiche"] = {"retour": feedback.strip(), "indice": hint, "question": question}
    changed = bool(decision and decision["source"] == "jepa" and decision["differe_des_regles"])
    return {"indice": hint, "question": question, "feedback": feedback.strip(), "stage": stage,
            "stage_name": STAGES[stage][0], "analysis": facts,
            "pedagogie": state.snapshot(spec, status, feedback.strip(), message, decision, latent, status == "ambigue"),
            "provenance": {"hint": "Règle pédagogique locale", "diagnostic": "Analyse statique Python",
                           "question": ("Question reclassée par JEPA et validée par l’orchestrateur" if changed else
                                        "Question retenue par les règles pédagogiques" if question else ""),
                           "jepa": "Reclassement enregistré" if changed else "Aucune contribution de LANG-JEPA."},
            "generation": model_status, "seconds": round(time.perf_counter() - started, 4)}, raw
