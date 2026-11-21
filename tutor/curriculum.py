"""Terminologie et périmètre du tuteur Python, d’après les programmes NSI."""

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
