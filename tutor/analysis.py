"""Analyse statique bornée du texte Python. Aucun code élève n’est exécuté."""

import ast
import hashlib


def analyze(code):
    digest = hashlib.sha256(code.encode("utf-8")).hexdigest()
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError, RecursionError) as exc:
        line = getattr(exc, "lineno", None)
        return {
            "digest": digest, "syntax": line or 1, "maximum_function": False,
            "maximum_zero": False, "notions": [], "unchanged_guard": None,
        }

    nodes = list(ast.walk(tree))
    features = [
        (ast.Assign, "affectations"), (ast.If, "conditions"), (ast.For, "boucle bornée"),
        (ast.While, "boucle non bornée"), (ast.FunctionDef, "fonctions"),
        (ast.List, "listes"), (ast.Dict, "dictionnaires"),
    ]
    notions = [label for kind, label in features if any(isinstance(node, kind) for node in nodes)]
    maximum_functions = [
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "maximum"
    ]
    maximum_zero = any(
        any(isinstance(child, ast.For) for child in node.body)
        and any(
            isinstance(child, ast.Assign) and isinstance(child.value, ast.Constant)
            and type(child.value.value) is int and child.value.value == 0
            and any(isinstance(target, ast.Name) and target.id == "m" for target in child.targets)
            for child in node.body
        )
        for node in maximum_functions
    )
    unchanged_guard = None
    for node in nodes:
        if isinstance(node, ast.While) and isinstance(node.test, ast.Compare) and isinstance(node.test.left, ast.Name):
            name = node.test.left.id
            if not any(
                isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store) and child.id == name
                for statement in node.body for child in ast.walk(statement)
            ):
                unchanged_guard = name
                break
    return {
        "digest": digest, "syntax": None, "maximum_zero": maximum_zero,
        "maximum_function": bool(maximum_functions), "notions": notions, "unchanged_guard": unchanged_guard,
    }
