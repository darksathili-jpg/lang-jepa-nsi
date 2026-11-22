# P5 · Audit initial

État initial `7efcd17`, sur `main`, avant développement. Les 36 tests Python et le test de régression P4 passent.

| Composant | État initial |
| --- | --- |
| `tutor/dialogue.py` | Échanges structurés, filtre de divulgation, générateur local interchangeable. Pour le maximum, les règles valident les acquis et posent la question. SmolLM3 propose un indice facultatif. Pour les autres exercices, choix de phase historique et heuristique. |
| `tutor/guided.py`, `tutor/curriculum.py` | Parcours rédigés pour le maximum, le décompte, les boucles, les dictionnaires et la récursivité selon le niveau. Le catalogue public ne livre pas les solutions. |
| `tutor/analysis.py` | Analyse AST bornée par la validation d’entrée. Aucune exécution du code de l’élève. L’analyse ne permet pas de déduire l’ensemble des comportements à l’exécution. |
| `tutor/sessions.py`, `pedagogy/progress.py` | État serveur, six échanges récents, 32 sessions en mémoire et expiration à 45 minutes. Objectifs, preuves et questions structurés pour le maximum. Deux versions de code successives peuvent partager des acquis, mais la vérification et le contrat sont révoqués si la structure change. P4 demande un seul test négatif avant consolidation. |
| `tutor/engine.py` | SmolLM3-3B Q4_K_M, révision `4965cb60`, llama.cpp b12600, CPU, boucle locale, délais, contraintes JSON et empreintes. Modèle 1,92 Go sur disque. P3 a observé 3,92 Gio au pic du moteur et une médiane de 12,87 s en Linux. Ces mesures ne couvrent ni Windows ni l’ensemble des processus. |
| `jepa/pilot.py`, `jepa/resources.py`, `evaluation/pilot.py` | Classes de l’amont figé et objectif latent à cible EMA. Deux graines expérimentales, poids locaux privés disponibles à l’audit. Aucun checkpoint officiel prêt à l’emploi identifié. Aucun signal du pilote injecté dans le tuteur. |
| Tests | Validation des contrats P2, contrôle du corpus et du partage des familles, provenance, saisies, non-exécution et non-divulgation, tests Chromium des trois thèmes, trace SmolLM3 P4 de 14 tours. |

Le pilote P3 emploie 24 paires d’entraînement et 24 de test. Sur huit indices, il en classe 4 puis 2 correctement selon la graine, contre 4 pour TF-IDF. Le cosinus moyen entre prédictions dépasse 0,998 pour les deux graines. Ces résultats justifient de concevoir un prototype pédagogique distinct, sans réutiliser les poids du pilote dans le parcours. [Expérience antérieure](EXPERIENCE-JEPA-NSI.md)

Le catalogue SmolLM3 déclare Apache-2.0 et llama.cpp MIT. Les empreintes des fichiers locaux sont vérifiées avant chargement. La source LANG-JEPA amont n’affiche pas de licence claire à la révision retenue dans l’audit précédent. Aucun téléchargement ni redistribution de cet amont ou de ses poids n’est nécessaire en P5. Le prototype P5 est une implémentation indépendante de l’objectif JEPA, avec corpus synthétique et dépendance NumPy sous BSD-3-Clause. Un encodeur externe ajouterait une provenance et une dépendance à vérifier. La comparaison initiale emploie donc deux encodeurs entraînables ou figés localement. [Audit amont](AUDIT-JEPA-NSI.md) · [Versions et droits du LLM](../p3/models.json) · [Licence NumPy](https://numpy.org/doc/stable/license.html)

## Boucle du maximum

Le dépôt contient déjà le correctif P4. Le rejeu P5 sur une archive de `46da3f3` avec SmolLM3 réel et seulement la boucle locale retrouve la même question aux tours 2, 4 et 6, et le rejet du tour 5. Après « Car 0 est supérieur à -4 et à -2. », l’ancien tuteur redemande la valeur de `m`. Le test de régression vérifie l’identité des questions et la stagnation du niveau. Sur la baseline P5, le test de progression vérifie les six entrées, confirme la cause au quatrième tour et passe à la stratégie. Ce comportement constitue le contrôle de non-régression de P5. [Entrées synthétiques](../p4/reference.json) · [Rejeu P5 du défaut](../p5/preuves/rejeu-46da3f3.jsonl) · [Sorties sur le correctif P4](../p4/preuves/apres-chromium.jsonl)
