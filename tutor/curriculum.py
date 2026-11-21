"""Terminologie et périmètre du tuteur Python, d’après les programmes NSI."""

import re

LEVELS = {
    "premiere": (
        "Première NSI. Types et valeurs, affectation, conditions, boucles, fonctions, "
        "listes (tableaux Python), dictionnaires, recherche séquentielle et parcours."
    ),
    "terminale": (
        "Terminale NSI. Mobiliser les acquis de Première, la récursivité avec son cas de base, "
        "les structures de données et le raisonnement sur l'algorithme."
    ),
}

VOCABULARY = (
    "Employer au besoin : variable de type entier, affecter une valeur à une variable, "
    "boucle bornée (for), boucle non bornée (while), instruction, expression, paramètre, valeur renvoyée."
)

STAGES = {
    1: ("Comprendre", "Reformule le doute. Demande ce qui a été essayé ou ce que le programme renvoie."),
    2: ("Orienter", "Nomme la notion qui permet d'avancer. Pose une question ciblée."),
    3: ("Expérimenter", "Fais tracer une variable ou une itération sur un petit exemple."),
    4: ("Débloquer", "Donne un indice précis sur le raisonnement, sans donner la modification exacte."),
    5: ("Consolider", "La modification vient de l'élève. Fais justifier et examiner un autre cas limite."),
}


def display_terms(text):
    """Harmonise les mentions en prose et préserve le code entre accents graves."""
    parts = text.split("`")
    for index in range(0, len(parts), 2):
        prose = parts[index]
        if index + 2 < len(parts) and parts[index + 1] in {"for", "while"}:
            loop = "boucle bornée" if parts[index + 1] == "for" else "boucle non bornée"
            revised = re.sub(r"\bboucle\s+$", loop + " (", prose, flags=re.I)
            if revised != prose:
                prose = revised
                parts[index + 2] = ")" + parts[index + 2]
        prose = re.sub(r"\bboucle for\b", "boucle bornée (for)", prose, flags=re.I)
        prose = re.sub(r"\bboucle while\b", "boucle non bornée (while)", prose, flags=re.I)
        prose = re.sub(r"\bvaleur de retour\b", "valeur renvoyée", prose, flags=re.I)
        parts[index] = re.sub(r"\bvariable entière\b", "variable de type entier", prose, flags=re.I)
    return "`".join(parts)
