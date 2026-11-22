# P5 · Corpus et provenance

Le corpus synthétique comprend **40 situations, 122 formulations**. Il couvre l’affectation et les types, les conditions, les boucles bornées et non bornées, les fonctions, les listes, les dictionnaires, la recherche séquentielle, les cas limites, la récursivité, les piles et files, les arbres, les graphes et la correction d’algorithmes.

| Partage | Familles d’exercices | Situations verbales |
| --- | ---: | ---: |
| Entraînement | 20 | 61 |
| Validation | 8 | 24 |
| Test | 12 | 37 |

Chaque famille contient un énoncé, du code, une difficulté, un objectif, un critère de validation et des formulations correctes, partielles et incorrectes. Deux formulations ambiguës ajoutent des fautes ou une réponse très courte. Quatre cartes d’intervention constituent des choix plausibles. La grille désigne une intervention préférée par tour, même quand plusieurs auraient une valeur pédagogique. Les annotations, les textes de difficulté et les critères des cibles restent hors de l’entrée de l’encodeur contextuel. La vérité de référence relève d’une première annotation synthétique.

La séparation s’effectue par problème avec trois ensembles d’exercices distincts. Des notions apparaissent dans plusieurs ensembles afin d’évaluer le transfert entre problèmes. Le chargeur rejette les doublons de famille, d’énoncé, de code et de réponse normalisée, vérifie l’existence des trois catégories principales par famille et des quatre interventions dans chaque partage. Les contrôles d’égalité n’épuisent pas la détection de similarité sémantique. [Corpus](../p5/corpus.json) · [Contrôles](../p5/data.py)

Trois dialogues de 10, 20 et 30 tours sont réservés à l’évaluation de bout en bout. Ils couvrent les six formulations du rejeu, les variantes orthographiques, des réponses courtes et ambiguës, les demandes de corrigé, un changement de code, deux tests et le contrat de la liste vide. Les dialogues partagent le même exercice et mesurent la robustesse conversationnelle sur ce cas. Le corpus à 40 familles sert séparément à mesurer le transfert de la décision. Les données sont synthétiques et exemptes de données d’élèves. [Dialogues](../p5/dialogues.json) · [Registre](../p5/provenance.json)

Les courbes de validation à 5, 10 et 20 familles d’apprentissage mesurent l’effet de ce volume. L’absence de gain monotone et la variation entre graines invitent à enrichir le corpus avec des familles inédites et des annotations indépendantes avant de généraliser. [Courbes et mesures](P5_ENTRAINEMENT_JEPA.md)
