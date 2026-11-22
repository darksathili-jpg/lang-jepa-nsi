"""Chargement et contrôles de provenance du corpus synthétique P5."""

from dataclasses import dataclass
import json
from pathlib import Path
import re

from p5.contract import ACTIONS, SCHEMA, ContractError, Situation
from tutor.analysis import analyze


ROOT = Path(__file__).resolve().parent
SPLITS = ("train", "dev", "test")
STATUSES = {"correcte", "partielle", "incorrecte", "ambigue", "hors_sujet"}


@dataclass(frozen=True)
class Example:
    famille: str
    partage: str
    situation: Situation
    action: str
    statut: str
    cible: str


def static_facts(code, facts):
    if facts["syntax"]:
        return ("syntaxiquement invalide",)
    observations = ["syntaxe analysée", *facts["notions"]]
    if facts["maximum_zero"]:
        observations.append("maximum avec affectation initiale de zéro")
    if facts["unchanged_guard"]:
        observations.append("garde sans affectation directe")
    tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*|==|!=|<=|>=|[<>+*/%]", code)
    observations.append("instructions et opérateurs " + " ".join(tokens)[:205])
    return tuple(observations)


def normalize_key(text):
    return " ".join(re.findall(r"\w+", text.casefold()))


def load_corpus(path=ROOT / "corpus.json"):
    data = json.loads(path.read_text(encoding="utf-8"))
    if data["schema"] != SCHEMA or data["provenance"] != "p5/provenance.json":
        raise ContractError("Révision ou registre de provenance du corpus invalide.")
    families, statements, snippets, replies = set(), set(), set(), set()
    examples = []
    for case in data["exercices"]:
        family, split = case["famille"], case["partage"]
        statement, snippet = normalize_key(case["enonce"]), case["code"].strip()
        if (family in families or split not in SPLITS or not re.fullmatch(r"[a-z0-9-]+", family)
                or not statement or statement in statements or not snippet or snippet in snippets):
            raise ContractError(f"Famille, énoncé ou fragment dupliqué ou invalide : {family}.")
        families.add(family)
        statements.add(statement)
        snippets.add(snippet)
        facts = static_facts(snippet, analyze(snippet))
        if not {"correcte", "partielle", "incorrecte"} <= {turn["statut"] for turn in case["tours"]}:
            raise ContractError(f"Les réponses de référence sont incomplètes : {family}.")
        for turn in case["tours"]:
            reply = normalize_key(turn["reponse"])
            if not reply or reply in replies or turn["intervention"] not in ACTIONS or turn["statut"] not in STATUSES:
                raise ContractError(f"Tour dupliqué ou invalide : {family}.")
            replies.add(reply)
            situation = Situation(case["niveau"], case["notion"], case["enonce"], facts, turn["reponse"],
                                  (), (), (), case["objectif"], ())
            target = ACTIONS[turn["intervention"]] + " " + case["critere"]
            examples.append(Example(family, split, situation, turn["intervention"], turn["statut"], target))
    for split in SPLITS:
        if {item.action for item in examples if item.partage == split} != set(ACTIONS):
            raise ContractError(f"Au moins une intervention manque dans le partage {split}.")
    return examples
