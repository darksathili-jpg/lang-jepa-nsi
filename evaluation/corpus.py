"""Le corpus local fournit des paires texte précédent → segment suivant."""

from dataclasses import dataclass
import json
from pathlib import Path


CORPUS = Path(__file__).with_name("corpus-nsi.json")
PARTS = ("enonce", "notion", "erreur", "indice")


@dataclass(frozen=True)
class Pair:
    document: str
    family: str
    part: str
    context: str
    target: str


def load_corpus(path=CORPUS):
    docs = json.loads(path.read_text(encoding="utf-8"))
    identifiers, texts = set(), set()
    families = {"train": set(), "test": set()}
    for doc in docs:
        identifier, split, family = (doc[key] for key in ("id", "split", "family"))
        segments = doc["segments"]
        if identifier in identifiers or split not in families or set(segments) != set(PARTS):
            raise ValueError("Identifiant, répartition ou segments du corpus invalides.")
        identifiers.add(identifier)
        families[split].add(family)
        for part in PARTS:
            text = segments[part]
            if not isinstance(text, str) or not text.strip() or text.strip() in texts:
                raise ValueError("Segment vide ou dupliqué dans le corpus.")
            texts.add(text.strip())
    if not families["train"] or families["train"] != families["test"]:
        raise ValueError("Les familles doivent être représentées dans les deux répartitions.")
    return docs


def make_pairs(docs, split, window=2):
    result = []
    for doc in docs:
        if doc["split"] != split:
            continue
        parts = doc["segments"]
        for index, part in enumerate(PARTS[1:], 1):
            context = " ".join(parts[key] for key in PARTS[max(0, index - window):index])
            result.append(Pair(doc["id"], doc["family"], part, context, parts[part]))
    return result
