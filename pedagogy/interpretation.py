"""Interprétation structurée, séparée de la validation des acquis."""

import ast
from dataclasses import asdict, dataclass, replace
from enum import StrEnum
import io
import json
import re
import tokenize

from pedagogy.cases import Input, Result, literal
from pedagogy.progress import REQUEST, normalize, requested_topic


SCHEMA = 1


class Intent(StrEnum):
    EXPLAIN = "explication"
    DEFINE = "definition"
    TEST = "proposition_essai"
    PREDICT = "prediction"
    OBSERVE = "observation"
    EXPECT = "resultat_attendu"
    REASON = "justification"
    CHANGE = "proposition_correction"
    HINT = "indice"
    SOLUTION = "corrige"
    CONFUSED = "incomprehension"
    TOPIC = "changement_notion"
    UNKNOWN = "ambigu_ou_hors_sujet"


@dataclass(frozen=True)
class Claim:
    role: Intent
    value: Result
    excerpt: str


@dataclass(frozen=True)
class Message:
    intentions: tuple[Intent, ...]
    tests: tuple[Input, ...] = ()
    claims: tuple[Claim, ...] = ()
    ambiguities: tuple[str, ...] = ()
    topic: str | None = None
    interpretation: str = "regles"

    def public(self):
        return asdict(self) | {"schema": SCHEMA}


def candidate(text, start):
    """Lire seulement le premier groupe équilibré, avec les chaînes Python tokenisées."""
    fragment = text[start:]
    stack = []
    try:
        for token in tokenize.generate_tokens(io.StringIO(fragment).readline):
            if token.start[0] != 1 or token.end[1] > 340:
                break
            if token.type != tokenize.OP:
                continue
            if token.string in ("(", "[", "{"):
                stack.append(token.string)
                if len(stack) > 3:
                    break
            elif token.string in (")", "]", "}"):
                if not stack or stack.pop() != {")": "(", "]": "[", "}": "{"}[token.string]:
                    break
                if not stack:
                    return fragment[:token.end[1]]
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return None
    return None


def extract_tests(text, spec):
    calls = list(re.finditer(rf"\b{re.escape(spec.function)}\s*(?=\()", text))
    anchors = [(m.end(), True) for m in calls] if calls else []
    if not calls and spec.kind != "integer":
        # Un accès Python comme tab[0] n’est pas une proposition de liste.
        anchors = [(m.start(), False) for m in re.finditer(r"(?<![\w\]])\[", text)]
    result, errors = [], []
    if len(anchors) > 3:
        return (), ("Propose trois essais au plus dans un message.",)
    for start, call in anchors:
        if not call and start and text[start - 1] in "[({":
            continue
        fragment = candidate(text, start)
        if fragment is None:
            errors.append("L’essai est incomplet ou trop imbriqué.")
            continue
        tail = text[start + len(fragment):].lstrip(" `\t")
        if call and (re.search(r"(?:\.|\w+\(\s*)" + re.escape(spec.function) + r"\s*$", text[:start])
                     or re.match(r"[)\[(*/%+<>=-]|\.\w|(?:or|and)\b", tail)):
            errors.append("Isole l’appel de test et son argument littéral.")
            continue
        expression = spec.function + fragment if call else fragment
        try:
            node = ast.parse(expression, mode="eval").body
            if call:
                if not isinstance(node, ast.Call) or len(node.args) != 1 or node.keywords:
                    raise ValueError("Propose un appel avec un seul argument littéral.")
                node = node.args[0]
            value = literal(node, spec.kind)
        except (ValueError, SyntaxError, RecursionError) as exc:
            errors.append(str(exc) if type(exc) is ValueError else "Cet essai n’est pas un littéral autorisé.")
            continue
        if value not in result:
            result.append(value)
    return tuple(result), tuple(dict.fromkeys(errors))


INTENT_CUES = {
    Intent.EXPLAIN: r"^(?:pourquoi|comment se fait-il|explique(?:-moi)?|peux-tu expliquer)\b",
    Intent.DEFINE: r"^(?:que (?:veut dire|signifie)|qu'est-ce qu|c'est quoi|definis)\b",
    Intent.HINT: r"\b(?:un indice|une piste|par ou commencer|aide-moi)\b",
    Intent.CONFUSED: r"\b(?:je ne sais pas|je comprend[s]? pas|je ne comprend[s]? pas|je suis perdu|aucune idee)\b",
    Intent.REASON: r"\b(?:parce que|puisque|donc|comme|car|d'ou)\b",
    Intent.CHANGE: r"\b(?:je (?:vais|pourrais|devrais)|on pourrait)\b.{0,28}\b(?:changer|remplacer|initialis\w*|choisir|diminu\w*)\b",
}
CLAIM_CUES = {
    Intent.EXPECT: r"\b(?:devrai\w*|attendu\w*|normalement|est cense)\b",
    Intent.PREDICT: r"\b(?:je pense|je predi\w*|je m'attends|je suppose|je dirais|a mon avis)\b",
    Intent.OBSERVE: r"\b(?:j'obtiens|j'ai obtenu|j'observe|j'ai vu|repond\w*|renvoie|affiche|donne|retourne)\b",
}
SOLUTION = re.compile(r"\b(?:corrige|solution|code complet|programme complet)\b")
NUMBER = r"(?<![\w-])-?\d{1,5}(?!\w)"


def claim_value(text, dictionaries):
    reference = re.search(r"\bdictionary_slot_(\d+)\b", text)
    if reference and int(reference[1]) < len(dictionaries):
        fragment = dictionaries[int(reference[1])]
        try:
            node = ast.parse(fragment, mode="eval").body if fragment else None
            if isinstance(node, ast.Dict) and len(node.keys) <= 20:
                pairs = [(literal(k, "word"), literal(v, "integer"))
                         for k, v in zip(node.keys, node.values, strict=True)]
                if len(dict(pairs)) == len(pairs):
                    return dict(pairs)
        except (SyntaxError, ValueError, RecursionError):
            return None
        return None
    match = re.search(NUMBER, text)
    return int(match[0]) if match else None


def interpret(text, spec, *, expected_role=None):
    words = normalize(text.replace("`", ""))
    tests, errors = extract_tests(text, spec)
    if REQUEST.search(words) or SOLUTION.search(words) and re.search(r"\b(?:avoir|peux|veux|donne|ecris|montre)\b", words):
        return Message((Intent.SOLUTION,), ambiguities=errors)
    topic = requested_topic(words)
    if topic:
        return Message((Intent.TOPIC,), topic=topic)
    intentions = [intent for intent, cue in INTENT_CUES.items() if re.search(cue, words)]
    if tests or errors:
        intentions.append(Intent.TEST)
    claims = []
    short = re.fullmatch(rf"({NUMBER})[.! ]*", words)
    if short and expected_role in CLAIM_CUES:
        claims.append(Claim(expected_role, int(short[1]), text))
    if Intent.EXPLAIN not in intentions and Intent.DEFINE not in intentions:
        dictionaries = []

        def preserve_literal(match):
            dictionaries.append(match[0])
            return f"dictionary_slot_{len(dictionaries) - 1}"

        evidence = re.sub(r"\bdictionary_slot_\d+\b", "", text, flags=re.I)
        if spec.kind == "words":
            evidence = re.sub(r"\{[^{}]*\}", preserve_literal, evidence)
        evidence = re.sub(r"\[[^\[\]]*\]|\b\w+\s*\(\s*-?\d+\s*\)", "", normalize(evidence.replace("`", "")))
        for clause in re.split(r"\b(?:mais|alors que|pourtant|tandis que|et (?=(?:ca|cela|le resultat|je)\b))\b|[,;.!?]", evidence):
            if re.search(r"\b(?:pas|jamais)\b", clause):
                continue
            for role, cue in CLAIM_CUES.items():
                marker = re.search(cue, clause)
                if marker and (value := claim_value(clause[marker.end():], dictionaries)) is not None:
                    claims.append(Claim(role, value, clause.strip()))
                    break
    intentions.extend(item.role for item in claims)
    if not intentions:
        intentions.append(Intent.UNKNOWN)
    return Message(tuple(dict.fromkeys(intentions)), tests, tuple(claims), errors, topic)


MODEL_INTENTS = (Intent.EXPLAIN, Intent.DEFINE, Intent.HINT, Intent.CONFUSED)


def verified_interpretation(raw, text, message):
    """Le modèle propose une lecture. Une citation vérifiable n’est jamais un acquis."""
    try:
        proposal = json.loads(raw["text"])
        role = Intent(proposal["intention"])
        citation = proposal["citation"]
        if (raw["finish"] != "stop" or set(proposal) != {"schema", "intention", "citation"}
                or type(proposal["schema"]) is not int or proposal["schema"] != SCHEMA or role not in MODEL_INTENTS
                or not isinstance(citation, str) or not 3 <= len(citation) <= 120
                or citation not in text or not re.search(INTENT_CUES[role], normalize(citation))):
            return message, False
    except (ValueError, KeyError, TypeError):
        return message, False
    return replace(message, intentions=(role,), interpretation="modele_local_verifie"), True
