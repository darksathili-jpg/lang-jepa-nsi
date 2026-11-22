# P5 · Comparaison A/B/C

## Protocole

| Profil | Configuration |
| --- | --- |
| A | SmolLM3 et contrôle commun des sorties, sans état pédagogique détaillé ni validation des acquis. |
| B | SmolLM3 et orchestrateur. L’ordre des règles sélectionne une question admissible. |
| C | Identique à B, avec classement latent des questions admissibles, variante fixe, graine 17. |
| C neutralisé | Identique à C, avec le signal JEPA neutralisé. L’ordre des règles reprend la priorité. |
| C mélangé | Identique à C, avec permutation circulaire des situations éligibles du même dialogue. La représentation provient d’un autre tour, sans point fixe. |

Les cinq configurations reçoivent le même énoncé, les mêmes modifications de code et les mêmes messages fixés à l’avance. La référence conversationnelle est SmolLM3-3B Q4_K_M `4965cb60`, llama.cpp b12600, deux fils. Les dialogues étant imposés, ils mesurent les décisions possibles sur les mêmes observations, sans mesurer une adaptation des réponses d’élèves aux questions produites. Le dialogue de 10 tours comprend les six messages réels de la régression retranscrits en scénario synthétique. Un essai complémentaire dissocie les contrôles de l’orchestrateur et du modèle sur 10, 20 et 30 tours.

La grille de référence compare l’objectif attendu, l’approche préférée, la réouverture de la trace de `m`, les questions exactes ou proches déjà posées, les signes de divulgation et les erreurs Python détectables. Le score d’approche indique un accord avec l’annotation synthétique. Plusieurs interventions peuvent être pédagogiquement défendables. Le filtre automatique de divulgation et de faits erronés cherche seulement des motifs prédéfinis. Les latences comprennent la sélection et, sur les tours sollicités, l’inférence. Un indice filtré laisse une réponse d’orchestrateur et reste distinct d’une panne du moteur.

**Décision d’intégration.** Conserver la référence stable tant que C ne dépasse pas B et les ablations sur les familles et dialogues inédits, sur plusieurs graines, avec un intervalle d’incertitude compatible avec un gain. Vérifier également que la non-divulgation, les faits Python et la latence ne se dégradent pas. Le corpus isolé de 37 situations estime l’incertitude par bootstrap apparié par famille. Un unique dialogue conversationnel par profil ne permet pas un intervalle fiable à l’échelle d’exercices indépendants. [Références isolées et par graine](P5_ENTRAINEMENT_JEPA.md)

## Évaluation à l’aveugle

Pour une évaluation indépendante, présenter à deux enseignants la saisie, le code visible et les réponses anonymisées dans un ordre aléatoire. Noter séparément l’exactitude Python, la reconnaissance explicite, la progression, l’absence de répétition injustifiée, le respect du niveau NSI et la pertinence de l’indice. Utiliser 0 pour faux, absent ou nuisible, 1 pour acceptable mais partiel et 2 pour exact et utile. Enregistrer à part toute divulgation d’une correction avant la proposition de l’élève, et toute preuve présentée comme une exécution. Comptabiliser les désaccords et discuter les cas divergents. Une relecture indépendante par des enseignants reste à organiser.

## Reproduire

```bash
OPENBLAS_NUM_THREADS=1 python -m p5.compare --weights results/p5/fixe-24-17 --output results/p5-abc.jsonl
OPENBLAS_NUM_THREADS=1 python -m p5.compare --weights results/p5/fixe-24-17 --output results/p5-long.jsonl --modes b c neutralise melange --dialogues maximum-10 maximum-20 maximum-30 --sans-llm
```

Préparer les poids avec le banc d’entraînement, et SmolLM3 avec le préparateur du tuteur. Couper la connexion avant le banc. Pour Linux, la recette a employé un espace réseau contenant uniquement `lo`. [Procédure hors ligne](P5_PERFORMANCES_WINDOWS.md)

## Résultats réels avec SmolLM3 · 10 tours par profil

| Profil | Objectifs de référence suivis | Approche préférée | Questions répétées | Indices générés affichés | Reclassements | Médiane / max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A | État détaillé absent | — | 5 | 10 | — | 16,83 / 26,54 s |
| B | 10/10 | 5/9 | 0 | 1 | 0 | 12,19 / 14,68 s |
| C | 10/10 | 4/9 | 0 | 2 | 3 | 11,50 / 13,00 s |
| C neutralisé | 10/10 | 5/9 | 0 | 1 | 0 | 11,62 / 14,38 s |
| C mélangé | 10/10 | 3/9 | 0 | 2 | 4 | 11,54 / 12,71 s |

Les cinq profils ont répondu aux 10 tours. Les contrôles automatiques n’ont détecté aucune divulgation du programme complet ni échec moteur. A revient quatre fois à la trace après la démonstration et aborde la précondition dès le premier test après modification. Avec B et C, la preuve est reconnue au quatrième tour. Le neuvième tour confirme le deuxième essai et ouvre l’examen de la liste vide. L’indice SmolLM3 sur le contrat suggère de vérifier si la fonction gère la liste vide. La question du serveur recentre sur le rôle de la précondition. Ce cas illustre une marge d’amélioration dans la pertinence des formulations générées. L’ablation mélangée a fait l’objet d’un démarrage séparé du même modèle. Comparer les latences comme des observations de développement. [Sorties brutes A/B/C et neutralisation](../p5/preuves/abc-smollm3.jsonl) · [Sorties brutes de la permutation](../p5/preuves/ablation-permutation-smollm3.jsonl)

Sur les trois variantes déterministes de 10, 20 et 30 tours, les quatre profils à état suivent chacun **60/60 objectifs** et conservent les acquis. L’accord d’approche vaut **15/27** pour B et la neutralisation, **11/27** pour C et **10/27** pour la permutation. C reclasse 10 questions sur ces dialogues. Le choix de la question dépend donc bien du signal, mais ces mesures ne justifient pas l’activation de JEPA dans le parcours principal. [Traces de l’orchestrateur, sans génération](../p5/preuves/dialogues-longs.jsonl)
