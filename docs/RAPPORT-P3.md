# Rapport de validation P3

La mission part de `06a88b2`. Elle conserve le laboratoire scientifique et l’expérimentation LANG-JEPA P2, et ajoute un professeur virtuel Python séparé. Le modèle choisi sur essais est **SmolLM3-3B, GGUF Q4_K_M**, révision `4965cb60b150737b68a0408c36aeefb65078f894`, exécuté avec **llama.cpp b12600**. [Comparatif des trois modèles](COMPARATIF-P3.md) · [Architecture](ARCHITECTURE-P3.md)

## Fonctionnalités réalisées

- Atelier local avec niveau Première ou Terminale, énoncé, éditeur Python coloré, dialogue, progression de l’aide et état du moteur. Modes clair, sombre et projecteur.
- Analyse syntaxique, détection de signatures statiques et tests d’exemples de référence. Le code de l’élève reste du texte et aucune conversation n’est journalisée par l’application.
- Installation reproductible des ressources CPU, vérification SHA-256, identité visible au lancement et mode hors ligne. La procédure de restauration et les travaux LANG-JEPA P2 restent disponibles. [Guide Windows](INSTALLATION-P3.md)

## Vérification locale

Le test dans Chromium 156 a démarré deux processus locaux dans un espace réseau Linux ne contenant que l’interface de bouclage, sans route externe. Quatre échanges réels ont abouti sur le maximum d’entiers. L’exemple négatif a été proposé au premier tour, l’élève a analysé `m` au deuxième et au troisième, puis a modifié son code avant que le modèle ne pose la question du contrat pour une liste vide. L’énoncé imposait une liste non vide. Le dernier indice a abordé le bon cas limite et a laissé une ambiguïté sur la vérification à faire hors précondition. [Dialogue réel dans Chromium](../p3/preuves/maximum-chromium.txt)

Les 20 tests Python, l’analyse syntaxique JavaScript et les recettes Chromium du laboratoire ont été vérifiés. La recette de l’atelier couvre aussi le mobile, les états absent et erreur, l’affichage de l’identité et le blocage des demandes provenant d’une origine externe. [Atelier clair](captures-p3/atelier-light.png) · [Atelier sombre](captures-p3/atelier-dark.png) · [Mode projecteur](captures-p3/atelier-projector.png) · [Laboratoire](captures-p3/laboratoire.png)

## Campagne de 20 scénarios

Le profil P3-C `614a066` a généré **60 tours sur 20 scénarios** dans le même réseau isolé. **54 réponses** étaient affichables et **16 dialogues** ont eu trois réponses. Les motifs de référence ont trouvé 42 objectifs mentionnés, dont 33 dans la question. Les 6 refus de format comptent pour zéro dans la relecture. La lecture intégrale a été réalisée pendant la recette à partir de la grille publiée, sans panel d’enseignants. [Corpus](../p3/scenarios.json) · [Traces brutes](../p3/preuves/recette-smol.jsonl) · [Grille renseignée](../p3/preuves/relecture-smol.tsv) · [Méthode](EVALUATION-P3.md)

| Critère sur 60 tours | Résultat |
| --- | ---: |
| Justesse du diagnostic | 1,25 / 2 |
| Pertinence de la question | 0,92 / 2 |
| Progression de l’aide | 0,65 / 2 |
| Niveau NSI | 1,75 / 2 |
| Français et vocabulaire | 1,43 / 2 |
| Divulgation de la solution | 7 / 60 à la relecture, dont 2 repérées par les motifs automatiques |

Les réponses les moins fiables répètent la question, confondent le comportement attendu et réel, ou avancent trop vite vers la correction. Le modèle attribue par exemple à tort la non-terminaison d’une récursion à une suite d’appels en `n−1` alors que le code transmet `n` inchangé. Les demandes répétées de corrigé ont aussi montré des questions de peu d’aide même quand le code complet est écarté.

## Performances observées

| SmolLM3-3B Q4_K_M, deux fils CPU | Linux isolé, 60 tours |
| --- | ---: |
| Taille du GGUF sur disque | 1 915 305 312 octets |
| Démarrage avec vérification d’empreinte | 3,73 s |
| Temps de réponse médian | 12,87 s |
| 95ᵉ centile par rang | 18,54 s |
| Temps maximal | 19,90 s |
| Pic résident du processus llama.cpp | 3,92 Gio |

Ces mesures ont été relevées sur AMD EPYC 9V74 avec quota de deux CPU et limite de 8 Gio pour l’environnement Linux. Le pic concerne le processus natif. L’environnement Windows de la cible, le navigateur et les autres applications peuvent changer la consommation totale et la vitesse. Les chiffres Linux restent des observations de cette machine. [Détails du banc](EVALUATION-P3.md)

## Corrections et retests P3-D

La recette a motivé trois changements. Le filtre repère des substitutions explicites d’opérateur ou de valeur d’initialisation et demande alors une nouvelle génération centrée sur les tests. Les termes NSI sont harmonisés en prose. Une sortie composée de questions peut afficher sa question principale sans inventer d’indice. Sur les sorties brutes de P3-C, le nouveau filtre intercepte trois des sept divulgations relevées à la relecture.

Un retest intermédiaire a donné 12 réponses affichables sur quatre cas. Il a révélé une variante du corrigé de seuil, formulée avec « opérateur de comparaison » et des guillemets. Le contrôle a été élargi à cette variante. Sur l’énoncé ambigu, les trois questions sont désormais affichables. Au deuxième tour le modèle demande une définition de « transformer ». Les autres tours restent trop généraux pour établir le résultat attendu. [Premier retest](../p3/preuves/retest-intermediaire.jsonl) · [Retest de l’énoncé ambigu](../p3/preuves/retest-ambiguite.jsonl)

Le retest final du seuil et du comptage par dictionnaire a donné **6 réponses sur 6**, avec une substitution brute détectée puis régénérée. Sa sortie affichée propose d’examiner l’égalité à 10 sans écrire l’opérateur. La réponse suivante recommande encore une « comparaison d’égalité », ce qui peut induire une erreur pour une note supérieure à 10. Le filtre traite des formes connues. Les conseils faux ou les corrigés formulés indirectement restent des limites mesurées. [Retest final](../p3/preuves/retest-corriges.jsonl)

## Non vérifié et bloqué

- **Non vérifié sur Windows natif.** L’archive CPU Windows a été téléchargée, vérifiée et extraite. Son exécutable x64 a été identifié. L’installation, le dialogue en réseau coupé et les mesures sur le poste physique de 16 Go restent à contrôler. Ce poste était indisponible pour la recette.
- **Non validé pour un déploiement autonome en classe.** Les scores placent la progression des indices et l’exactitude des diagnostics parmi les travaux restants. Une recette menée avec des enseignants et les niveaux visés n’a pas eu lieu. Les tests de non-divulgation couvrent un ensemble fini de formulations.
- **Bloqué côté LANG-JEPA P2.** L’expérimentation indépendante dépend encore des checkpoints d’origine compatibles. Elle n’est pas une dépendance de l’atelier. [Rapport P2](RAPPORT-P2.md)
