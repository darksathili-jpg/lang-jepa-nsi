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


# L’objectif et les questions de référence sont choisis indépendamment du modèle.
MAXIMUM_GOALS = {
    "observed": ("Identifier le résultat observé", 1, (
        ("essai", "Quel résultat ton programme renvoie-t-il pour la liste [-4, -2] ?"),
        ("proposition", "Quel petit test choisirais-tu pour observer la sortie du programme ?"),
        ("prévision", "Comment comparerais-tu la sortie sur une liste positive et sur une liste négative ?"),
    )),
    "expected": ("Déterminer le résultat attendu", 2, (
        ("spécification", "Sur [-4, -2], quelle valeur devrait renvoyer la fonction d’après l’énoncé ?"),
        ("ordre", "Entre -4 et -2, lequel est le plus grand sur la droite des nombres ?"),
        ("confrontation", "Quelle valeur de cette liste respecte la définition du maximum ?"),
    )),
    "trace": ("Expliquer le comportement de m", 3, (
        ("trace", "Quelles valeurs prend m au départ, après -4 et après -2 ?"),
        ("condition", "Que donne la comparaison avec la valeur de départ quand la boucle rencontre -4 puis -2 ?"),
        ("tableau", "Peux-tu annoter un tableau avec la condition et les mises à jour à chaque passage ?"),
        ("ligne", "Dans quel cas l’affectation située dans la boucle s’exécute-t-elle ?"),
    )),
    "assumption": ("Identifier l’hypothèse incorrecte", 4, (
        ("hypothèse", "Quelle hypothèse sur les éléments rend le zéro de départ inadapté ici ?"),
        ("contre-exemple", "Quel point commun aux deux entiers fait échouer ce choix de départ ?"),
        ("invariant", "La valeur retenue appartient-elle toujours aux éléments examinés ?"),
    )),
    "strategy": ("Proposer une stratégie de correction", 4, (
        ("propriété", "Quelle propriété devrait avoir la valeur de départ pour fonctionner aussi avec des nombres négatifs ?"),
        ("validation", "Comment pourrais-tu choisir un départ compatible avec l’énoncé pour toute liste non vide ?"),
        ("contre-exemple", "Peux-tu proposer un autre choix et chercher un contre-exemple à ce choix ?"),
        ("contrainte", "Quels choix peux-tu exclure si le résultat doit être un élément de l’entrée ?"),
    )),
    "verification": ("Vérifier le nouveau programme", 4, (
        ("essai", "Après ta modification, quel résultat observes-tu sur [-4, -2] et comment le compares-tu au résultat attendu ?"),
        ("rédaction", "Peux-tu écrire ton idée dans l’éditeur et relever l’entrée et la valeur renvoyée ?"),
        ("cas discriminant", "Quel essai distinguerait les deux versions du programme ?"),
    )),
    "contract": ("Examiner les cas limites et les préconditions", 5, (
        ("contrat", "Quel rôle joue la précondition « liste non vide » pour l’entrée [] ?"),
        ("spécification", "Que faudrait-il préciser dans le contrat si l’on voulait aussi accepter [] ?"),
        ("domaine", "À quelles entrées l’énoncé garantit-il une plus grande valeur ?"),
    )),
}
