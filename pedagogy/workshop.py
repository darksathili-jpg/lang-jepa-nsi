"""Décision pédagogique sur un essai actif et des preuves versionnées."""

from collections import deque
from dataclasses import asdict, dataclass, field, replace
from enum import StrEnum
import json
import re
import time

from p5.contract import Decision, Situation
from pedagogy.cases import SPECS, TestCase
from pedagogy.catalogue import EXERCISES
from pedagogy.interpretation import Intent, interpret, verified_interpretation
from pedagogy.maximum import check_initialization, negative_infinity, proposal, read_order
from pedagogy.progress import Evidence, normalize
from tutor.curriculum import STAGES
from tutor.engine import EngineError


LABELS = {"observed": "Identifier le comportement", "expected": "Déterminer le résultat attendu",
          "trace": "Expliquer le comportement", "assumption": "Identifier l’hypothèse incorrecte",
          "strategy": "Proposer une stratégie", "verification": "Vérifier sur un nouvel essai",
          "contract": "Examiner la précondition"}
STAGE = {"observed": 1, "expected": 2, "trace": 3, "assumption": 4,
         "strategy": 4, "verification": 4, "contract": 5}
class Target(StrEnum):
    TEST = "essai"
    PREDICTION = "prediction"
    EXPECTED = "attendu"
    CONDITION = "condition"
    CAUSE = "justification"
    INITIAL_VALUE = "valeur_initiale"
    EXCLUDED_RESULT = "resultat_exclu"
    VERIFICATION = "programme_et_essais"
    CONTRACT = "contrat"


@dataclass(frozen=True)
class Question:
    action: str
    target: Target
    text: str


EXCLUDED_RESULT = Question("justifier", Target.EXCLUDED_RESULT,
                           "Quels choix peux-tu exclure si le résultat doit être un élément de l’entrée ?")


CORRECTION_PRINCIPLES = {
    "maximum": "Pars d’une valeur de l’entrée et conserve la plus grande des valeurs déjà examinées.",
    "boucle-while": "Fais décroître le compteur à chaque passage jusqu’à rendre la condition fausse.",
    "dictionnaire-comptage": "Initialise le compteur d’un mot lors de sa première occurrence, puis incrémente-le.",
    "recursivite-base": "Fais évoluer l’argument vers un cas de base valide à chaque appel.",
}


def select_spec(exercise, statement, level, existing=None, *, guided=False):
    if existing:
        return SPECS[existing.exercise]
    if guided:
        spec = SPECS.get(exercise)
        return spec if spec and spec.level == level else None
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
    target: Target | None = None
    target_turn: int = 0
    strategy_code: str | None = None
    strategy_excerpt: str | None = None
    verified_cases: dict[tuple[int, ...], Evidence] = field(default_factory=dict)
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
        labels = LABELS | {"observed": "Identifier le résultat observé"} if spec.id == "maximum" else LABELS
        return {"schema": 1, "notion": spec.notion, "objectif": self.goal, "objectif_libelle": labels[self.goal],
                "libelles_objectifs": labels, "acquis": proof(self.evidence), "erreurs": proof(self.errors),
                "acquis_non_demontres": [self.goal], "changements_objectif": list(self.transitions),
                "derniere_intervention": decision, "experience_jepa": latent, "essai_actif": self.active.public() if self.active else None,
                "essais_precedents": [case.public() for case in self.cases], "interpretation": message.public(),
                "clarification": clarification, "niveau_aide": self.support,
                "proposition_validee": {"code": self.strategy_code, "extrait": self.strategy_excerpt} if self.strategy_code else None,
                "essais_verifies": [{"entree": value, "tour": proof.turn, "critere": proof.criterion}
                                     for value, proof in self.verified_cases.items()],
                "question_cible": self.target,
                "questions": [{"tour": turn, "strategie": q.action, "texte": q.text, "cible": q.target}
                              for _, turn, q in self.asked],
                "evaluation": {"statut": status, "commentaire": feedback, "methode": "Critères de l’exercice et analyse statique"}}


def trace_facts(text, static):
    """Reconnaître des assertions vérifiables contre une forme connue du programme."""
    words = normalize(text.replace("`", ""))
    if static.kind == "sentinelle":
        bad = bool(re.search(r"\bm\s*(?:vaut|=)\s*(?:false|faux|true|vrai)\b|\bpas (?:toujours )?fauss?e?s?\b|"
                             r"l'affectation s'execute\b(?!\s+(?:si|quand)\b)", words)
                   or any(int(value) != 0 for value in re.findall(r"\bm\s*(?:vaut|reste (?:a )?|=)\s*(-?\d+)\b", words)))
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
    if state.goal == "verification" and state.strategy_code:
        if state.code == state.strategy_code:
            if "sortie_element" not in state.evidence:
                return [EXCLUDED_RESULT]
            return [Question("confronter", Target.VERIFICATION,
                             "Après avoir modifié le programme, quelles entrées utiliseras-tu pour le vérifier ?")]
        if not case or case.entree in state.verified_cases:
            return [Question("confronter", Target.VERIFICATION,
                             "Quel autre essai distinct peux-tu proposer pour cette version ?")]
    if not case:
        return [Question("confronter", Target.TEST, "Quel petit test choisirais-tu pour observer la sortie du programme ?"),
                Question("clarifier", Target.TEST, f"Quelle entrée simple veux-tu examiner avec {spec.function} ?"),
                Question("tracer", Target.TEST, "Quels arguments écrirais-tu pour un premier essai ?")]
    if not case.precondition or state.goal == "contract":
        return [Question("justifier", Target.CONTRACT, f"Que dit le contrat de l’exercice sur l’entrée {value} ?"),
                Question("clarifier", Target.CONTRACT, "Quelle précondition faut-il vérifier avant de choisir cet essai ?")]
    if state.goal in {"observed", "verification"}:
        return [Question("confronter", Target.PREDICTION, f"Pour {value}, quel résultat prédis-tu avec cette version du programme ?"),
                Question("tracer", Target.PREDICTION, f"Quelle sortie prévois-tu en suivant le programme sur {value} ?"),
                Question("clarifier", Target.PREDICTION, "Quel résultat prévois-tu en suivant les instructions ?")]
    if state.goal == "expected":
        return [Question("justifier", Target.EXPECTED, f"D’après l’énoncé, quel résultat devrait-on obtenir pour {value} ?"),
                Question("confronter", Target.EXPECTED, f"Quelle valeur devrait être renvoyée pour {value} d’après le contrat ?")]
    if state.goal == "assumption":
        return [Question("justifier", Target.CAUSE, "Quelle hypothèse de départ explique cet écart ?"),
                Question("confronter", Target.INITIAL_VALUE, spec.suggestion)]
    if state.goal == "strategy":
        return [Question("confronter", Target.INITIAL_VALUE, spec.suggestion),
                Question("clarifier", Target.INITIAL_VALUE, "Quelle valeur proposerais-tu comme point de départ, et pourquoi ?")]
    if case.statique and case.statique.kind == "sentinelle" and max(case.entree) <= 0:
        if "comparaison" not in state.evidence:
            return [Question("tracer", Target.CONDITION, "Quand la valeur examinée est négative et que m vaut 0, que vaut valeur > m ?"),
                    Question("confronter", Target.CONDITION, f"Sur {value}, un élément peut-il rendre valeur > m vraie ?"),
                    Question("clarifier", Target.CONDITION, "Regarde la condition seule. Est-elle vraie pour une valeur négative face à zéro ?")]
        return [Question("justifier", Target.CAUSE, "Puisque la condition est fausse, que devient l’affectation et quelle valeur conserve m ?"),
                Question("tracer", Target.CAUSE, "Suis le bloc indenté. Quelle instruction est sautée et avec quel effet sur m ?")]
    return [Question("tracer", Target.CAUSE, spec.suggestion),
            Question("clarifier", Target.CAUSE, "Sur cet essai, quel changement d’état repères-tu ?"),
            Question("justifier", Target.CAUSE, "Quelle ligne de ton programme appuie cette observation ?")]


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
             "comparaison" in state.evidence, "sortie_element" in state.evidence)
    candidates = [q for q in ask(state, spec) if not any(asked_scope == scope and q == old for asked_scope, _, old in state.asked)]
    if not candidates:
        return None, None, None
    options = [(q.action, q.text) for q in candidates]
    decision = latent = None
    if experiment and spec.id == "maximum" and (
        state.active is None or state.active.statique and state.active.statique.kind == "sentinelle"
    ):
        case_summary = () if not state.active else (f"Essai actif {rendered(state.active.entree)}",)
        situation = Situation(request["class"], spec.notion, request["statement"], case_summary,
                             request["question"], tuple(h["learner"][:280] for h in request["history"]),
                             tuple(e.criterion for e in state.evidence.values()), tuple(e.criterion for e in state.errors.values()),
                             LABELS[state.goal], tuple(q.text[:280] for _, _, q in list(state.asked)[-6:]))
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
    selected = next(q for q in candidates if (q.action, q.text) == (action, question))
    state.asked.append((scope, turn, selected))
    return selected, decision, latent


def acknowledge_strategy(state, candidate, request, turn):
    result = check_initialization(candidate, request["code"], request["statement"])
    text = request["question"]
    if result == "valid":
        state.strategy_code = state.code
        state.strategy_excerpt = text
        state.verified_cases.clear()
        state.confirm("strategy", turn, text, "Initialisation cohérente avec le parcours et la précondition.")
        state.goal = "verification"
        feedback = ("Cette valeur de départ appartient à l’entrée, puisque la liste est non vide."
                    if candidate.kind == "element" else
                    "Moins l’infini peut servir de valeur initiale. Une liste non vide d’entiers garantit qu’un élément le remplacera.")
        return "correcte", feedback, "Modifie le programme, puis vérifie-le sur deux entrées distinctes, dont une liste de nombres négatifs."
    explanations = {
        "precondition": "Il faut préciser le contrat pour la liste vide. Aucun élément de cette liste ne peut fournir la valeur renvoyée.",
        "binding": "Vérifie les noms. Il faut modifier l’accumulateur en utilisant le paramètre de cette fonction.",
        "index": "Cet indice n’est pas garanti pour une liste à un seul élément. Essaie un singleton.",
        "constant": "Une constante finie peut dépasser tous les entiers d’une liste. Cherche une liste dont tous les éléments sont plus petits.",
        "unknown": "Je ne peux pas valider cette affectation. Précise la variable et la valeur de départ choisies.",
    }
    status = "ambigue" if result == "unknown" else "incorrecte"
    if status == "incorrecte":
        state.errors["strategy"] = Evidence(turn, text, explanations[result])
    return status, explanations[result], ""


def record_verification(state, case, turn, text):
    if not (case.statique and case.statique.result == case.attendu and "expected" in state.evidence):
        return False
    if state.strategy_code:
        if state.code == state.strategy_code or case.statique.kind != "accumulation":
            return False
        if case.entree not in state.verified_cases:
            if len(state.verified_cases) == 2 and max(case.entree) < 0:
                del state.verified_cases[next(iter(state.verified_cases))]
            if len(state.verified_cases) < 2:
                state.verified_cases[case.entree] = Evidence(turn, text, "Résultat confronté à l’analyse statique de cette version.")
        if len(state.verified_cases) < 2 or not any(max(value) < 0 for value in state.verified_cases):
            return False
    state.confirm("verification", turn, text, "Résultat prévu ou déclaré cohérent avec le contrat et la forme reconnue.")
    return True


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
    target = state.target if state.target_turn == turn - 1 and state.code == digest else None
    expected_role = {Target.PREDICTION: Intent.PREDICT, Target.EXPECTED: Intent.EXPECT}.get(target)
    if expected_role:
        message = interpret(text, spec, expected_role=expected_role)
    raw = None
    model_status = "non_sollicite"
    strategy = (proposal(text, initial_value=target == Target.INITIAL_VALUE)
                if spec.id == "maximum" and state.goal in {"assumption", "strategy", "verification"} and not facts["syntax"] else None)
    minus_inf = spec.id == "maximum" and negative_infinity(text)
    if strategy is None and not minus_inf and engine and message.intentions == (Intent.UNKNOWN,) and len(text.split()) >= 5 and target != Target.CONDITION:
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
        state.verified_cases.clear()
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
    elif minus_inf and target == Target.EXCLUDED_RESULT:
        state.confirm("sortie_element", turn, text, "Moins l’infini n’est pas un entier de l’entrée.")
        status = "correcte"
        feedback = "Oui, moins l’infini est exclu comme résultat final. Il peut servir de valeur initiale, à condition d’être remplacé par un élément."
    elif strategy is not None:
        message = replace(message, intentions=(Intent.CHANGE,))
        status, feedback, hint = acknowledge_strategy(state, strategy, request, turn)
    elif minus_inf:
        if target == Target.EXPECTED or (target == Target.PREDICTION and state.active and state.active.statique):
            status = "incorrecte"
            feedback = "Moins l’infini ne correspond pas au résultat de ce cas. Le maximum demandé est un entier de la liste."
        else:
            status = "ambigue"
            feedback = "Proposes-tu moins l’infini comme valeur initiale, ou l’exclus-tu comme résultat final ?"
            no_question = True
    elif message.ambiguities or len(message.tests) > 1:
        status = "ambigue"
        feedback = message.ambiguities[0] if message.ambiguities else "Choisis l’un de ces essais pour que nous suivions ses résultats."
        no_question = True
    else:
        if message.tests:
            value = message.tests[0]
            if not state.active or state.active.entree != value:
                state.take(spec.case(value, "eleve", request["code"], digest))
                state.goal = "verification" if edited or state.strategy_code else "observed"
            feedback = f"Je retiens ton essai {rendered(value)}."
        declaration_generale = False
        if (not state.active and spec.id == "maximum" and state.goal == "observed" and not facts["syntax"]
                and re.search(r"\bnegati\w*\b", normalize(text))
                and {claim.value for claim in message.claims if claim.role == Intent.OBSERVE and type(claim.value) is int} == {0}):
            example = spec.case(spec.example, "tuteur", request["code"], digest)
            if example.statique and example.statique.kind == "sentinelle":
                state.take(example)
                state.confirm("observed", turn, text, "Observation générale cohérente avec la forme statique et un exemple du tuteur.")
                state.goal = "expected"
                declaration_generale = True
                status = "correcte"
                feedback = f"Je note que ton programme renvoie 0 sur les listes entièrement négatives. Prenons {rendered(example.entree)} comme exemple."
        if not state.active and Intent.EXPLAIN not in message.intentions and Intent.DEFINE not in message.intentions and (
            target == Target.TEST and Intent.CONFUSED in message.intentions
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
            if message.claims and not declaration_generale:
                proved_before = set(state.evidence)
                feedback = (feedback + " " + handle_claims(state, message, turn, text)).strip()
                case = state.active
                if "observed" in state.evidence and state.goal in {"observed", "verification", "expected"}:
                    pending = state.strategy_code is not None
                    if record_verification(state, case, turn, text):
                        state.goal = "contract"
                    elif pending and case.entree in state.verified_cases:
                        state.goal = "verification"
                        feedback += " Propose un second essai distinct, dont un cas entièrement négatif si tu ne l’as pas encore fait."
                    elif not pending or state.code != state.strategy_code and "expected" not in state.evidence:
                        state.goal = "trace" if "expected" in state.evidence else "expected"
                status = "incorrecte" if "observed" in state.errors else "correcte" if state.evidence.keys() - proved_before else "partielle"
            if state.goal == "trace" and case.statique:
                false, causal, wrong = trace_facts(text, case.statique)
                negative = spec.id == "maximum" and case.statique.kind == "sentinelle" and max(case.entree) <= 0
                order = read_order(text, case.entree) if negative else None
                if order and order.contradiction:
                    status = "incorrecte"
                    feedback = "Une inégalité ne correspond pas à l’ordre de ces entiers. Vérifie le sens de chaque comparaison."
                elif wrong:
                    feedback = "La comparaison produit un booléen. La variable garde une valeur entière. Vérifie le bloc concerné."
                    status = "incorrecte"
                elif order and order.covered == set(case.entree):
                    state.confirm("comparaison", turn, text, "L’ordre est établi pour toutes les valeurs de l’essai.")
                    if causal:
                        state.confirm("trace", turn, text, "L’ordre justifie l’absence d’affectation et la valeur conservée.")
                    examples = ", puis ".join(f"{entry} > 0" for entry in case.entree[:3])
                    feedback = (f"Tes inégalités établissent le bon ordre. Avec valeur > m, Python teste {examples} à partir de m = 0. "
                                "Ces tests sont faux : l’affectation ne s’exécute pas et m reste à 0.")
                    state.goal = "strategy"
                    status = "correcte"
                elif causal and (case.statique.kind != "sentinelle" or negative and (false or "comparaison" in state.evidence)):
                    state.confirm("trace", turn, text, "Le raisonnement concorde avec la forme statiquement reconnue pour cet essai.")
                    feedback = "Ton explication relie la condition, les instructions et l’effet sur cet essai." if negative else "Ton explication concorde avec le comportement analysé."
                    state.goal = "assumption"
                    status = "correcte"
                elif false and negative and target == Target.CONDITION:
                    state.confirm("comparaison", turn, text, "La comparaison avec zéro est fausse dans le cas négatif proposé.")
                    feedback = "Oui, la comparaison est fausse sur ce cas. Cherchons la conséquence sur les instructions."
                elif order and order.covered:
                    feedback = "Tu as établi l’ordre pour une partie de l’essai. Examine les autres valeurs avant de tirer une conclusion."
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
    selected, decision, latent = (None, None, None) if no_question else choose(state, spec, experiment, request, turn)
    question = selected.text if selected else ""
    if not question and not no_question:
        state.support = min(max_help, state.support + 1)
        hint = hint or explain(spec, state.active, strong=state.support >= 4)
    state.target = selected.target if selected else None
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
