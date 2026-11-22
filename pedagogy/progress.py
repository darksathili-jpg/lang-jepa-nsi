"""Critères conservateurs et état pédagogique du cas maximum de référence."""

import ast
from collections import deque
from dataclasses import dataclass, field
import re
import unicodedata

from tutor.curriculum import MAXIMUM_GOALS


def normalize(text):
    text = "".join(char for char in unicodedata.normalize("NFKD", text.casefold())
                   if not unicodedata.combining(char))
    text = text.translate(str.maketrans({"’": "'", "−": "-", "–": "-"}))
    for word, value in (("zero", "0"), ("moins deux", "-2"), ("moins quatre", "-4")):
        text = re.sub(r"\b" + word + r"\b", value, text)
    return re.sub(r"\s+", " ", text).strip()


NUMBER = r"(?<![\d\w])-?\d+(?![\d\w])"
OBSERVED = r"\b(?:repond\w*|renv\w*|retourn\w*|affich\w*|observ\w*|obtiens|obtenu|trouve|donne|sortie|c'est)\b"
EXPECTED = r"\b(?:devrai\w*|attend\w*|attendu\w*|correct\w*|serait)\b"
REQUEST = re.compile(r"\b(?:donne\w*|montre\w*|ecris|je veux)\b.{0,30}\b(?:corrige|solution|programme complet|code complet)\b")
GREATER = r"(?:>|(?:s[uou]p+[eé]r[iy]\w*|plus (?:grand\w*|haut\w*))\s+(?:a|que)\b)"
SMALLER = r"(?:<|(?:inf[eé]r[iy]\w*|plus (?:petit\w*|bas\w*))\s+(?:a|que)\b)"
NEGATIVE_PAIR = r"(?:-4\s*(?:,|et)\s*(?:a\s+)?-2|-2\s*(?:,|et)\s*(?:a\s+)?-4)(?!\d)"
STOPWORDS = set("a au aux de des du en et la le les quels quelles quel quelle que qui se ce cette tu ton est il chaque apres valeur valeurs".split())
ALIASES = {"itere": "boucle", "tour": "boucle", "iteration": "boucle", "passage": "boucle",
           "reste": "conserve", "garde": "conserve", "pourquoi": "raison"}


def near_question(left, right):
    def terms(text):
        return {ALIASES.get(word, word) for word in re.findall(r"-?\d+|[a-z]+", normalize(text))
                if word not in STOPWORDS}

    a, b = terms(left), terms(right)
    if not a or not b:
        return normalize(left) == normalize(right)
    if bool(a & {"devrait", "attendu"}) != bool(b & {"devrait", "attendu"}):
        return False
    return a == b or len(a & b) >= 2 and len(a & b) / len(a | b) >= 0.63


def requested_topic(text):
    match = re.search(
        r"\b(?:changer de notion|autre notion|pass(?:er|ons) (?:a|aux)|parlons (?:de|du|des)|"
        r"(?:travailler|etudier|aborder) (?:la|le|les))\b(.{0,120})", normalize(text),
    )
    if not match:
        return None
    for token, label in (("dictionnaire", "Dictionnaires"), ("recurs", "Récursivité"),
                         ("boucle", "Boucles"), ("maximum", "Maximum d’une liste"),
                         ("fonction", "Fonctions"), ("liste", "Listes")):
        if token in match[0]:
            return label
    return "Une autre notion"


@dataclass(frozen=True)
class Evidence:
    turn: int
    excerpt: str
    criterion: str


@dataclass(frozen=True)
class Assessment:
    status: str
    message: str
    confirmed: tuple[str, ...] = ()


@dataclass
class Progress:
    notion: str = "Maximum d’une liste"
    confirmed: dict[str, Evidence] = field(default_factory=dict)
    errors: dict[str, Evidence] = field(default_factory=dict)
    questions: deque = field(default_factory=lambda: deque(maxlen=28))
    code_digest: str | None = None
    multi_test: bool = False
    tests: dict[str, Evidence] = field(default_factory=dict)
    transitions: deque = field(default_factory=lambda: deque(maxlen=32))

    @property
    def goal(self):
        return next((goal for goal in MAXIMUM_GOALS if goal not in self.confirmed), None)

    def snapshot(self, assessment):
        def evidence(item):
            return {"tour": item.turn, "extrait": item.excerpt, "critere": item.criterion}
        pending = [goal for goal in MAXIMUM_GOALS if goal not in self.confirmed]
        return {
            "notion": self.notion, "objectif": self.goal,
            "objectif_suivant": pending[1] if len(pending) > 1 else None,
            "objectif_libelle": MAXIMUM_GOALS[self.goal][0] if self.goal else "Parcours terminé",
            "libelles_objectifs": {key: value[0] for key, value in MAXIMUM_GOALS.items()},
            "acquis": {goal: evidence(item) for goal, item in self.confirmed.items()},
            "acquis_non_demontres": pending,
            "erreurs": {goal: evidence(item) for goal, item in self.errors.items()},
            "tests_declares": {case: evidence(item) for case, item in self.tests.items()},
            "changements_objectif": list(self.transitions),
            "questions": [{"objectif": goal, "strategie": strategy, "texte": question}
                          for goal, strategy, question in self.questions],
            "evaluation": {"statut": assessment.status, "commentaire": assessment.message,
                           "methode": "Critères textuels et statiques du cas de référence"},
        }

    def acknowledge(self, key, turn, text, criterion):
        self.confirmed.setdefault(key, Evidence(turn, text, criterion))
        self.errors.pop(key, None)

    def select_question(self, selector=None):
        if self.goal is None:
            return "", None
        _, _, options = MAXIMUM_GOALS[self.goal]
        if self.goal == "verification" and self.multi_test:
            options = (
                ("essai", "Quelles sorties observes-tu avec ton nouveau code pour [-4, -2] et pour [3] ?"),
                ("rédaction", "Peux-tu noter séparément chaque entrée et sa valeur renvoyée ?"),
                ("cas discriminant", "Quel essai permet de distinguer les deux versions du programme, et pourquoi ?"),
            )
        previous = self.questions[-1] if self.questions else None
        available = []
        for strategy, question in options:
            if previous and previous[0] == self.goal and previous[1] == strategy:
                continue
            if any(near_question(question, asked) for _, _, asked in self.questions):
                continue
            available.append((strategy, question))
        if not available:
            return "", None
        strategy, question = selector(available) if selector else available[0]
        self.questions.append((self.goal, strategy, question))
        return question, strategy


def value_after(pattern, text):
    # Restreindre l'assertion à sa proposition pour séparer observé et attendu.
    for marker in re.finditer(pattern, text):
        tail = re.split(r"[.!?;]|\bmais\b", text[marker.end():], maxsplit=1)[0]
        tail = re.sub(r"\[[^\]]*\]", "", tail)
        match = re.search(NUMBER, tail[:52])
        prefix = text[max(0, marker.start() - 16):marker.start()]
        if match and not re.search(r"\b(?:pas|jamais|ni)\b", tail[:match.start()]) and not re.search(
            r"\bne\s*$|\bn'\s*$", prefix,
        ):
            return int(match[0])
    return None


def compare_zero(text):
    if re.search(r"\b(?:pas|jamais)\s+(?:s[uou]p|plus grand|inf|que\b)", text):
        return False
    greater = r"(?<![-\w])0\b\s*(?:est\s+)?(?:strictement\s+)?" + GREATER + r"\s*"
    smaller = r"\s*(?:aussi\s+)?(?:(?:est|sont)\s+)?(?:strictement\s+)?" + SMALLER + r"\s*0\b"
    together = re.search(greater + NEGATIVE_PAIR, text) or re.search(NEGATIVE_PAIR + smaller, text)
    separate = all(re.search(greater + value + r"(?!\d)", text) or re.search(value + smaller, text)
                   for value in ("-4", "-2"))
    general = re.search(r"(?:negati\w*|aucun nombre|entiers de la liste)[^.!?;]{0,35}"
                        r"(?:inferieur\w* a|en dessous de|ne depasse\w* pas)\s*0\b", text)
    return bool(together or separate or general)


def wrong_comparison(text):
    return bool(re.search(r"\b0\b\s*(?:est\s+)?(?:strictement\s+)?" + SMALLER + r".{0,20}-[24]", text)
                or re.search(r"-[24].{0,36}" + GREATER + r"\s*0\b", text))


def code_matches_maximum(code, start):
    """Reconnaître une forme d'accumulation sur l'AST sans exécuter le programme."""
    try:
        body = ast.parse(code).body
    except (SyntaxError, ValueError, RecursionError):
        return False
    match body:
        case [ast.FunctionDef(name="maximum", decorator_list=[], returns=None, args=ast.arguments(
            posonlyargs=[], args=[ast.arg(arg=tab, annotation=None)], vararg=None, kwonlyargs=[], kwarg=None, defaults=[]
        ), body=[
            ast.Assign(targets=[ast.Name(id=acc)], value=initial),
            ast.For(target=ast.Name(id=item), iter=sequence, orelse=[], body=[
                ast.If(test=ast.Compare(left=ast.Name(id=lhs), ops=[ast.Gt()],
                       comparators=[ast.Name(id=rhs)]), orelse=[], body=[
                    ast.Assign(targets=[ast.Name(id=updated)], value=ast.Name(id=value)),
                ]),
            ]),
            ast.Return(value=ast.Name(id=result)),
        ])]:
            if len({tab, acc, item}) != 3 or (lhs, rhs, updated, value, result) != (item, acc, acc, item, acc):
                return False
            if start == "zero":
                return (isinstance(initial, ast.Constant) and type(initial.value) is int
                        and initial.value == 0 and isinstance(sequence, ast.Name) and sequence.id == tab)
            match initial:
                case ast.Subscript(value=ast.Name(id=source), slice=ast.Constant(value=index)) if (
                    source == tab and type(index) is int and index == 0
                ):
                    match sequence:
                        case ast.Name(id=source):
                            return source == tab
                        case ast.Subscript(value=ast.Name(id=source),
                                           slice=ast.Slice(lower=ast.Constant(value=index), upper=None, step=None)):
                            return source == tab and type(index) is int and index == 1
    return False


def assess(progress, answer, code, facts, statement, turn):
    words = normalize(answer)
    excerpt = answer[:280]
    if progress.code_digest and progress.code_digest != facts["structure_digest"]:
        for key in ("verification", "contract"):
            progress.confirmed.pop(key, None)
            progress.errors.pop(key, None)
        progress.tests.clear()
    progress.code_digest = facts["structure_digest"]
    if facts["syntax"]:
        return Assessment("ambigue", "Le parseur ne permet pas encore d’examiner cette version du programme.")
    if REQUEST.search(words):
        return Assessment("hors_sujet", "La demande de corrigé laisse l’objectif en cours. Essaie l’un des indices.")
    goal = progress.goal
    if goal is None:
        return Assessment("hors_sujet", "Les étapes de cet exercice sont terminées.")
    if (re.fullmatch(r"(?:oui|non|ok|d'accord|je ne sais pas|\?+)[.! ]*", words)
            or words.endswith("?") or re.search(r"\b(?:peut-etre|je ne suis pas sur)\b", words)):
        return Assessment("ambigue", "La réponse ne précise pas encore ton observation ou ton raisonnement.")

    broken = code_matches_maximum(code, "zero")
    corrected = code_matches_maximum(code, "element")
    known_case = broken or bool(progress.confirmed.get("observed"))
    actual_clause, _, expected_clause = words.partition(" mais ")
    actual = value_after(OBSERVED, actual_clause)
    expected = value_after(EXPECTED, expected_clause or words)
    case_named = ({"-4", "-2"} <= set(re.findall(NUMBER, words))
                  or bool(re.search(r"negati\w*|en dessous de 0", words)))
    input_lists = re.findall(r"\[[^\]]*\]", words)
    explicit_test = bool(input_lists) and all(re.fullmatch(r"\[\s*-4\s*,\s*-2\s*\]", item) for item in input_lists)
    reference_context = not input_lists or explicit_test
    just_number = re.fullmatch(r"(-?\d+)[.! ]*", words)
    short = int(just_number[1]) if just_number else None
    trace_value = value_after(r"\bm\s*(?:vaut|reste(?:\s+a)?|=|prend|garde)", words)
    wrong_causal = wrong_comparison(words)
    proposal = re.search(r"(?:valeur|element|nombre).{0,32}(?:de|dans|appart\w* a|figur\w* dans) (?:la|ma|une|l')\s*(?:liste|entree)"
                         r"|premi[eè]r\w* (?:element|valeur|entier)|\btab\s*\[\s*0\s*\]", words)
    proposes_change = re.search(r"\b(?:choisir\w*|partir\w*|commenc\w*|initialis\w*|prendr\w*|remplac\w*)\b"
                                r"|^(?:une valeur|un element|le premier|tab\s*\[)", words)
    contract = re.search(r"liste vide|\[\s*\]", words) and re.search(
        r"non[ -]vide|hors (?:du|de la) (?:contrat|precondition)|excl\w*|au moins un", words,
    ) and not re.search(r"(?:est|reste) (?:valide|autorisee|admise)", words)
    found = []

    def confirm(key, criterion):
        if key not in progress.confirmed:
            found.append(key)
        progress.acknowledge(key, turn, excerpt, criterion)

    if known_case and reference_context and (
        actual == 0 and (case_named or goal == "observed") or goal == "observed" and short == 0 and progress.questions
    ):
        confirm("observed", "Sortie 0 déclarée pour le test négatif de référence.")
    if reference_context and (expected == -2 or goal == "expected" and (actual == -2 or short == -2)) and (
        case_named or goal == "expected" or "observed" in progress.confirmed
    ):
        confirm("expected", "Valeur −2 identifiée comme résultat attendu pour [-4, -2].")
    if known_case and not wrong_causal and compare_zero(words) and trace_value in (None, 0):
        confirm("trace", "Comparaison correcte : aucun des deux entiers ne dépasse zéro, donc m reste inchangé.")
        confirm("assumption", "L’élève met en évidence que le zéro de départ dépasse les éléments de ce test.")
    if "assumption" in progress.confirmed and (
        corrected or proposal and proposes_change and not re.search(r"\b(?:pas|jamais|hors)\b", words)
    ):
        confirm("strategy", "Proposition d’une valeur issue de la liste, dans la réponse ou l’AST.")
    previous_test = progress.questions and progress.questions[-1][0] == "verification" and "[-4, -2]" in progress.questions[-1][2]
    observed_fix = (actual == -2 or goal == "verification" and short == -2) and (
        explicit_test or previous_test and not progress.multi_test and not input_lists
    )
    ready_for_test = corrected and {"observed", "expected", "trace", "assumption", "strategy"} <= progress.confirmed.keys()
    if ready_for_test and progress.multi_test:
        cases = {"[-4, -2]": observed_fix,
                 "[3]": actual == 3 and bool(input_lists) and all(re.fullmatch(r"\[\s*3\s*\]", item) for item in input_lists)}
        for case, success in cases.items():
            if success:
                progress.tests.setdefault(case, Evidence(turn, excerpt, "Entrée et sortie cohérentes déclarées sur la version reconnue."))
        if len(progress.tests) == len(cases):
            confirm("verification", "Forme reconnue statiquement et sorties cohérentes déclarées sur [-4, -2] et [3].")
        elif any(cases.values()):
            return Assessment("partielle", "Ce test est cohérent. Un deuxième cas reste à vérifier.")
    elif ready_for_test and observed_fix:
        confirm("verification", "Forme d’accumulation reconnue statiquement et −2 déclaré pour le test de référence.")
    if "verification" in progress.confirmed and contract and "non vide" in normalize(statement):
        confirm("contract", "La réponse relie l’exclusion de [] à la précondition non vide.")
    if found:
        return Assessment("correcte", "Les éléments relevés dans ta réponse permettent d’avancer sur cet exercice.", tuple(found))

    numeric_claim = short if short is not None else actual
    wrong = (goal == "observed" and broken and numeric_claim not in (None, 0)
             or goal == "expected" and (expected if expected is not None else numeric_claim) not in (None, -2)
             or goal in ("trace", "assumption") and (wrong_causal or trace_value not in (None, 0))
             or goal == "verification" and (broken and observed_fix or corrected and reference_context
                                             and numeric_claim not in (None, -2)))
    if wrong:
        criterion = ("La forme du programme ne permet pas de confirmer ce résultat déclaré."
                     if goal == "verification" else "Ce résultat ou cette comparaison contredit le test de référence.")
        progress.errors[goal] = Evidence(turn, excerpt, criterion)
        return Assessment("incorrecte", criterion)
    if goal == "verification" and observed_fix and not corrected:
        return Assessment("partielle", "Le résultat déclaré correspond au test. Cette forme du programme reste à vérifier.")
    if goal == "strategy" and "trace" in progress.confirmed and (
        trace_value == 0 or short == 0 or re.search(r"(?:chaque fois|toujours).{0,18}\b0\b", words)
    ):
        return Assessment("partielle", "Le comportement de m est déjà relevé. Il reste à proposer un choix de départ.")
    if any(value is not None for value in (short, actual, expected, trace_value)) or re.search(
        r"\bm\b|\bliste\b|\bvaleur\b|compar|negati|essai|test|precondition|hypothese|chang|modifi|depart", words,
    ):
        return Assessment("partielle", "Cette observation peut servir. Précise le point demandé pour avancer.")
    return Assessment("hors_sujet", "La réponse ne donne pas d’élément exploitable pour l’objectif en cours.")
