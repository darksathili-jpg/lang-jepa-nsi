"""Contrats et analyses fermées pour les essais NSI. Aucun AST élève n’est interprété."""

import ast
from dataclasses import asdict, dataclass
from math import factorial
from typing import Callable

from pedagogy.progress import code_matches_maximum


SCHEMA = 1
Input = int | tuple[int, ...] | tuple[str, ...]
Result = int | dict[str, int]


@dataclass(frozen=True)
class Static:
    kind: str
    result: Result | None = None
    detail: str = ""


@dataclass(frozen=True)
class TestCase:
    entree: Input
    auteur: str
    precondition: bool
    attendu: Result | None
    code: str
    statique: Static | None = None
    predit: Result | None = None
    declare: Result | None = None
    execute: Result | None = None

    @property
    def niveau_preuve(self):
        return "statique" if self.statique else "declaration" if self.declare is not None else (
            "prediction" if self.predit is not None else "proposition"
        )

    def public(self):
        return asdict(self) | {"schema": SCHEMA, "niveau_preuve": self.niveau_preuve}


@dataclass(frozen=True)
class ExerciseSpec:
    id: str
    notion: str
    level: str
    function: str
    kind: str
    example: Input
    precondition: str
    valid: Callable[[Input], bool]
    expected: Callable[[Input], Result]
    analyze: Callable[[str, Input], Static | None]
    focus: str
    suggestion: str

    def case(self, value, source, code, digest):
        valid = self.valid(value)
        return TestCase(value, source, valid, self.expected(value) if valid else None, digest,
                        self.analyze(code, value) if valid else None)


def literal(node, kind):
    if kind in {"integers", "words"}:
        if not isinstance(node, ast.List) or len(node.elts) > 20:
            raise ValueError("Propose une liste littérale de vingt éléments au plus.")
        return tuple(literal(item, "integer" if kind == "integers" else "word") for item in node.elts)
    if kind == "word" and isinstance(node, ast.Constant) and type(node.value) is str and 0 < len(node.value) <= 28:
        return node.value
    sign = 1
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        sign = -1 if isinstance(node.op, ast.USub) else 1
        node = node.operand
    if kind == "integer" and isinstance(node, ast.Constant) and type(node.value) is int and abs(node.value) <= 1000:
        return sign * node.value
    raise ValueError("Utilise uniquement les valeurs littérales autorisées pour cet exercice.")


def maximum_static(code, values):
    if code_matches_maximum(code, "zero"):
        best = max(values)
        return Static("sentinelle", max(0, best), "Les éléments sont comparés à une valeur de départ égale à zéro.")
    if code_matches_maximum(code, "element"):
        return Static("accumulation", max(values), "La forme reconnue compare les éléments avec une valeur issue de l’entrée.")
    return None


def function_body(code, function):
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError, RecursionError):
        return None
    match tree.body:
        case [ast.FunctionDef(name=name, decorator_list=[], args=ast.arguments(
            posonlyargs=[], args=[ast.arg(arg=arg)], vararg=None, kwonlyargs=[], kwarg=None, defaults=[]
        ), body=body)] if name == function:
            return arg, body
    return None


def while_static(code, n):
    parsed = function_body(code, "compte")
    if not parsed:
        return None
    arg, body = parsed
    match body:
        case [ast.While(test=ast.Compare(left=ast.Name(id=guard), ops=[ast.Gt()],
                       comparators=[ast.Constant(value=limit)]), body=steps, orelse=[]),
              ast.Return(value=ast.Name(id=result))] if guard == result == arg and arg != "print" and type(limit) is int and limit == 0:
            match steps:
                case [ast.Expr(value=ast.Call(func=ast.Name(id="print"), args=[ast.Name(id=shown)], keywords=[]))] if shown == arg:
                    return Static("garde_inchangee", detail="La variable de la condition ne change pas dans la boucle.") if n > 0 else Static("retour", 0)
                case [ast.Expr(value=ast.Call(func=ast.Name(id="print"), args=[ast.Name(id=shown)], keywords=[])),
                      ast.AugAssign(target=ast.Name(id=updated), op=ast.Sub(), value=ast.Constant(value=step))] if (
                          shown == updated == arg and type(step) is int and step == 1
                      ):
                    return Static("retour", 0, "L’argument diminue d’une unité par passage.")
    return None


def counts(words):
    result = {}
    for word in words:
        result[word] = result.get(word, 0) + 1
    return result


def dictionary_static(code, words):
    parsed = function_body(code, "compte")
    if not parsed:
        return None
    arg, body = parsed
    match body:
        case [ast.Assign(targets=[ast.Name(id=table)], value=ast.Dict(keys=[], values=[])),
              ast.For(target=ast.Name(id=word), iter=ast.Name(id=source), body=[instruction], orelse=[]),
              ast.Return(value=ast.Name(id=result))] if source == arg and result == table and len({arg, word, table}) == 3:
            match instruction:
                case ast.AugAssign(target=ast.Subscript(value=ast.Name(id=t), slice=ast.Name(id=w)),
                                   op=ast.Add(), value=ast.Constant(value=one)) if t == table and w == word and type(one) is int and one == 1:
                    if words:
                        return Static("cle_absente", detail="La première clé est lue dans un dictionnaire vide.")
                    return Static("retour", {})
                case ast.Assign(targets=[ast.Subscript(value=ast.Name(id=t), slice=ast.Name(id=w))],
                                value=ast.BinOp(left=ast.Call(func=ast.Attribute(value=ast.Name(id=source_table), attr="get"),
                                    args=[ast.Name(id=sought), ast.Constant(value=default)], keywords=[]),
                                    op=ast.Add(), right=ast.Constant(value=one))) if (
                                    t == source_table == table and w == sought == word
                                    and type(default) is int and default == 0 and type(one) is int and one == 1
                                ):
                    return Static("retour", counts(words), "La valeur initiale et l’incrément sont reconnaissables statiquement.")
    return None


def factorial_static(code, n):
    parsed = function_body(code, "fact")
    if not parsed:
        return None
    arg, body = parsed
    base = None
    if len(body) == 2:
        match body[0]:
            case ast.If(test=ast.Compare(left=ast.Name(id=guard), ops=[ast.Eq()], comparators=[ast.Constant(value=count)]),
                        body=[ast.Return(value=ast.Constant(value=identity))], orelse=[]) if (
                            guard == arg and type(count) is int and type(identity) is int and identity == 1
                        ):
                base = count
            case _:
                return None
    if len(body) not in (1, 2):
        return None
    match body[-1]:
        case ast.Return(value=ast.BinOp(left=ast.Name(id=multiplier), op=ast.Mult(), right=ast.Call(
            func=ast.Name(id="fact"), keywords=[], args=[ast.BinOp(left=ast.Name(id=source), op=op,
                                                                 right=ast.Constant(value=step))]
        ))) if multiplier == source == arg and arg != "fact" and type(step) is int and isinstance(op, (ast.Add, ast.Sub)):
            delta = step if isinstance(op, ast.Add) else -step
            if base is None:
                return Static("base_absente", detail="Ce corps reconnu ne contient aucun test d’arrêt.")
            distance = base - n
            if distance and (delta == 0 or distance * delta < 0 or distance % delta):
                return Static("base_inaccessible", detail=f"Le cas de base existe en {base}. À chaque appel, l’argument varie de {delta:+d}.")
            if n == base:
                return Static("retour", 1, "L’entrée satisfait le cas de base reconnu.")
            if delta == -1 and base in (0, 1) and n <= 50:
                return Static("retour", factorial(n), "L’argument atteint le cas de base reconnu.")
    return None


SPECS = {s.id: s for s in (
    ExerciseSpec("maximum", "Parcours d’une liste", "premiere", "maximum", "integers", (-4, -2),
                 "La liste doit contenir au moins un entier.", bool, max, maximum_static,
                 "Compare la valeur examinée et le maximum mémorisé.", "Quelle propriété doit respecter une valeur de départ ?"),
    ExerciseSpec("boucle-while", "Boucle non bornée", "premiere", "compte", "integer", 3,
                 "Le compteur initial doit être un entier naturel.", lambda n: n >= 0, lambda _: 0, while_static,
                 "Regarde l’évolution du compteur entre deux passages.", "Quel changement ferait évoluer la condition de la boucle ?"),
    ExerciseSpec("dictionnaire-comptage", "Dictionnaires", "premiere", "compte", "words", ("a", "b", "a"),
                 "L’entrée doit être une liste de chaînes. La liste vide est admise.", lambda _: True, counts, dictionary_static,
                 "Vérifie si la clé est présente avant sa première lecture.", "Comment distinguer la première occurrence des suivantes ?"),
    ExerciseSpec("recursivite-base", "Récursivité", "terminale", "fact", "integer", 3,
                 "L’argument doit être un entier naturel.", lambda n: n >= 0,
                 factorial, factorial_static,
                 "Observe l’évolution des arguments entre deux appels.", "Quel argument doit être atteint pour arrêter les appels ?"),
)}
