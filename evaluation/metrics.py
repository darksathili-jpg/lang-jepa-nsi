"""Références déterministes et mesures de classement."""

from collections import Counter
import math
import re
import unicodedata


def words(text):
    return re.findall(r"[^\W_]+", unicodedata.normalize("NFC", text).casefold())


def lexical_reference(texts):
    documents = [set(words(text)) for text in texts]
    frequency = Counter(word for doc in documents for word in doc)
    idf = {word: 1 + math.log((1 + len(documents)) / (1 + count)) for word, count in frequency.items()}

    def vector(text):
        weighted = {word: count * idf[word] for word, count in Counter(words(text)).items() if word in idf}
        length = math.sqrt(sum(score ** 2 for score in weighted.values())) or 1
        return {word: score / length for word, score in weighted.items()}

    return vector


def lexical_cosine(left, right):
    return sum(value * right.get(word, 0.0) for word, value in left.items())


def rank(scores, expected):
    order = sorted(scores, key=lambda item: (-scores[item], item))
    position = next(index for index, item in enumerate(order, 1) if item in expected)
    return {"rank": position, "order": order, "scores": scores, "expected": sorted(expected)}


def summarize(rows):
    return {
        "count": len(rows),
        "top1": sum(row["rank"] == 1 for row in rows) / len(rows),
        "mrr": sum(1 / row["rank"] for row in rows) / len(rows),
    }
