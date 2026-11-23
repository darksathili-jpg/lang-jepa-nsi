"""Validation statique des raisonnements sur le maximum d’une liste."""

import ast
from dataclasses import dataclass
import operator
import re

from pedagogy.progress import GREATER, SMALLER, maximum_shape, normalize


@dataclass(frozen=True)
class Initialization:
    kind: str
    target: str | None = None
    source: str | None = None
    index: int | None = None


def integer(node):
    if isinstance(node, ast.Constant) and type(node.value) is int:
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        if isinstance(node.operand, ast.Constant) and type(node.operand.value) is int:
            return -node.operand.value if isinstance(node.op, ast.USub) else node.operand.value
    return None


def negative_infinity(text):
    words = normalize(text.strip(" `.?!"))
    return words == "moins l'infini" or re.fullmatch(r"-\s*(?:inf(?:inity|ini)?|∞)", words) is not None


def initializer(node, target=None):
    match node:
        case ast.Subscript(value=ast.Name(id=name), slice=index):
            return Initialization("element", target, name, integer(index))
        case ast.Call(func=ast.Name(id="float"), args=[ast.Constant(value=str() as value)], keywords=[]) if negative_infinity(value):
            return Initialization("minus_inf", target)
    value = integer(node)
    if value is not None:
        return Initialization("constant", target, index=value)
    return Initialization("unknown", target)


PROPOSAL = re.compile(
    r"^(?:(?:je|on)\s+(?:(?:vais|pourrais|va|peut)\s+)?(?:prends?|prendre|choisis|choisir|commence(?:r)?|pars|partir|initialise(?:r)?)|initialiser)\b"
)
ELEMENT = re.compile(r"(?:avec\s+)?(?:le premier element|la premiere valeur)(?: (?:de la liste|du tableau|de l'entree))?$")


def proposal(text, *, initial_value=False):
    """Lire un fragment ou une phrase de choix. La validité dépend ensuite du contrat."""
    raw = text.strip().strip('`').strip()
    if re.match(r"^\w+\s*=(?!=)", raw):
        try:
            tree = ast.parse(raw)
        except (SyntaxError, ValueError, RecursionError):
            return Initialization("unknown")
        match tree.body:
            case [ast.Assign(targets=[ast.Name(id=target)], value=value)]:
                return initializer(value, target)
        return Initialization("unknown")
    words = normalize(raw).rstrip(".!")
    if match := PROPOSAL.match(words):
        tail = words[match.end():].strip()
        if re.search(r"\b(?:mais|sauf|ou|pas|jamais)\b", tail):
            return Initialization("unknown")
        if first := ELEMENT.search(tail):
            prefix = tail[:first.start()].strip()
            if not prefix or re.fullmatch(r"\w+(?:\s+avec)?", prefix):
                target = prefix.split()[0] if prefix and prefix != "avec" else None
                return Initialization("element", target, index=0)
        # Conserver la casse des identifiants dans le fragment Python.
        fragment = re.search(r"([A-Za-z_]\w*\s*\[\s*[-+]?\d+\s*\]|float\s*\(.*\))\s*[.!]?\s*$", raw)
        if fragment:
            prefix = tail[:tail.rfind(normalize(fragment[1]))].strip()
            if prefix in {"", "avec", "par", "sur", "a"}:
                try:
                    return initializer(ast.parse(fragment[1], mode="eval").body)
                except (SyntaxError, ValueError, RecursionError):
                    return Initialization("unknown")
        if negative_infinity(tail.removeprefix("avec ")):
            return Initialization("minus_inf")
    if initial_value:
        if negative_infinity(raw):
            return Initialization("minus_inf")
        try:
            node = ast.parse(raw, mode="eval").body
        except (SyntaxError, ValueError, RecursionError):
            return None
        result = initializer(node)
        return result if result.kind != "unknown" else None
    return None


def nonempty_contract(statement):
    words = normalize(statement)
    if re.search(r"(?:meme vide|vide ou non|vide ou pleine|ou (?:une liste )?vide|vide (?:est|reste) (?:admise|autorisee))", words):
        return False
    return bool(re.search(r"\bnon[- ]vide\b|\bau moins un (?:element|entier|nombre)\b", words))


def check_initialization(candidate, code, statement):
    shape = maximum_shape(code)
    if not shape:
        return "unknown"
    source, target, item, _, _ = shape
    if candidate.target is not None and candidate.target != target or candidate.source is not None and candidate.source != source:
        return "binding"
    if candidate.kind == "element":
        if candidate.index is None:
            return "unknown"
        if candidate.index not in (0, -1):
            return "index"
        if not nonempty_contract(statement):
            return "precondition"
        return "valid"
    if candidate.kind == "minus_inf":
        if "float" in {source, target, item}:
            return "binding"
        return "valid" if nonempty_contract(statement) else "precondition"
    return "constant" if candidate.kind == "constant" else "unknown"


@dataclass(frozen=True)
class Order:
    covered: frozenset[int]
    contradiction: bool


# Comparer uniquement des valeurs littérales. Les termes équivalents sont ramenés
# aux mêmes opérateurs, et l’ellipse « 0 > a et b » réutilise le membre de gauche.
RELATION = re.compile(r"(?<![\w-])(-?\d{1,5})\s*(<=|>=|<|>)\s*(-?\d{1,5})(?!\w)(?:\s+(?:(?:est|vaut)\s+)?(faux|fausse|false|vrai|vraie|true)\b)?")
ELLIPSIS = re.compile(r"\s*(?:,|et)\s*(?:a\s+)?(-?\d{1,5})(?!\w)(?!\s*[<>\d])")
OPERATORS = {">": operator.gt, "<": operator.lt, ">=": operator.ge, "<=": operator.le}


def read_order(text, values):
    words = normalize(text.replace("`", ""))
    if re.search(r"\b(?:pas|peut-etre|si|imaginons)\b", words):
        return Order(frozenset(), False)
    words = re.sub(r"\best (?:strictement )?", "", words)
    # Les comparaisons strictes littérales gardent leurs opérateurs.
    words = re.sub(SMALLER, "<", re.sub(GREATER, ">", words))
    covered = set()
    contradiction = False
    for relation in RELATION.finditer(words):
        a, op, b, label = relation.groups()
        operands = [int(b)]
        if extra := ELLIPSIS.match(words, relation.end()):
            operands.append(int(extra[1]))
        for right in operands:
            left = int(a)
            correct = OPERATORS[op](left, right)
            asserted = label not in {"faux", "fausse", "false"}
            if not correct == asserted:
                contradiction = True
            elif left == 0 and right in values and (op == ">" and correct or op == "<" and not correct):
                covered.add(right)
            elif right == 0 and left in values and (op == "<" and correct or op == ">" and not correct):
                covered.add(left)
    return Order(frozenset(covered), contradiction)
