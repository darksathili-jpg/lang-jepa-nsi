# Architecture P3 · Professeur virtuel NSI

Le tuteur Python est le parcours principal. Le laboratoire scientifique conserve son quiz, ses explications et l’expérimentation LANG-JEPA P2. Il fonctionne indépendamment des poids conversationnels. [Architecture P2](ARCHITECTURE-P2.md)

| Composant | Responsabilité |
| --- | --- |
| Atelier navigateur | Énoncé, éditeur Python coloré, thème clair/sombre/projecteur, classe, historique en mémoire et état du modèle. |
| Service local | Sert l’atelier et la page scientifique, expose un statut et reçoit des demandes JSON de la même origine sur 127.0.0.1. Aucun travail élève n’est écrit sur disque. |
| Adaptateur conversationnel | Pilote un processus llama.cpp CPU, vérifie l’identité et l’empreinte du modèle, communique uniquement en boucle locale. Le catalogue dissocie modèle et application. |
| Orchestrateur | Valide les champs et l’historique récent, choisit l’étape selon les signaux du tour, assemble une consigne et contrôle la réponse avant l’affichage. |
| Analyse Python | Analyse l’arbre syntaxique et rapporte des indices statiques. Les tests sur des programmes de référence sont exécutés uniquement dans la suite de tests. |
| Évaluation | Rejoue des scénarios synthétiques, conserve sorties brutes, refus, métriques et signaux de référence. |
| Laboratoire P2 | Garde le lanceur et la procédure de LANG-JEPA indépendants du service d’atelier. |

L’état d’aide peut rester stable, avancer si l’élève a essayé une trace, s’orienter vers une erreur de syntaxe ou demander une consolidation après une modification. Les stades sont Comprendre, Orienter, Expérimenter, Débloquer et Consolider. Le stade Consolidation déclenche une vérification proposée à l’élève, sans présumer que sa correction fonctionne. Les signaux textuels et la modification du code sont des heuristiques documentées.

Pour le scénario du maximum, la consolidation utilise l’énoncé et le dernier message de l’élève. Les indices générés sur l’ancien code avaient tendance à revenir dans la réponse. Cette consigne recentre le modèle sur le contrat du nouvel état, notamment la précondition d’une liste non vide.

L’adaptateur ne charge que des fichiers locaux. Il n’accepte ni URL de modèle ni URL de service depuis le navigateur. Les états modèle absent, chargement, prêt et erreur sont distincts. Les erreurs et refus sont affichés comme états, sans réponse de remplacement. Le modèle reçoit au plus trois tours précédents et des entrées bornées. Pour une question refusée, l’atelier permet de reformuler et réessayer.

Quand le modèle propose une substitution explicite repérée par le filtre, l’orchestrateur demande une seule nouvelle génération centrée sur le cas limite. Si le texte contient seulement des questions, l’atelier peut afficher la question générée et laisser l’indice vide. Les termes de boucle et de valeur renvoyée sont harmonisés en prose sans modifier les extraits Python.

## Référentiel pédagogique

- Première. Types et valeurs, affectations, expressions, conditions, boucles bornées et non bornées, fonctions, parcours de tableaux Python et dictionnaires, recherche séquentielle. [Programme officiel de Première](https://www.education.gouv.fr/bo/19/Special1/MENE1901633A.htm)
- Terminale. Réinvestissement des acquis, récursivité, structures de données et raisonnement sur les algorithmes. Le corpus P3 vérifie un sous-ensemble Python et distingue le cas de base de la progression d’un appel récursif. [Programme officiel de Terminale](https://www.education.gouv.fr/bo/19/Special8/MENE1921247A.htm) · [Ressources Éduscol](https://eduscol.education.gouv.fr/5823/programmes-et-ressources-en-numerique-et-sciences-informatiques-voie-g)

Le référentiel alimente la consigne avec le vocabulaire attendu. Les bornes techniques et le contrôle de format réduisent certains écarts. Le français, l’exactitude, la conformité au niveau et les divulgations s’apprécient aussi sur les sorties réelles.
